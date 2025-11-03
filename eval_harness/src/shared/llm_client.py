# AICODE-NOTE: T011 - Unified LLM API client class
# AICODE-NOTE: Reuses .env OPENAI_API_KEY from repository root
# AICODE-NOTE: Supports OpenRouter/OpenAI/Anthropic via model ID prefix
# AICODE-NOTE: Model ID format: "openai/gpt-4o", "anthropic/claude-3-5-sonnet", etc.

"""Unified LLM API client with retry logic and multi-provider support."""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from anthropic import Anthropic
from loguru import logger
from openai import OpenAI
from pydantic import BaseModel


class LLMClient:
    """Unified LLM API client supporting multiple providers.

    AICODE-NOTE: T012 - Loads API key from .env at repository root
    AICODE-NOTE: Exponential backoff retry: 1s, 2s, 4s on failures
    AICODE-NOTE: Supports three provider modes:
    - OpenRouter (default): Any model ID without special prefix
    - OpenAI direct: Model IDs starting with "openai/"
    - Anthropic direct: Model IDs starting with "anthropic/"
    """

    def __init__(
        self,
        timeout: int = 120,
        max_retries: int = 3,
        env_path: Optional[Path] = None
    ):
        """Initialize LLM client with API key and configuration.

        Args:
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum retry attempts (default: 3)
            env_path: Path to .env file (default: repository root)

        AICODE-NOTE: T012 - Implements initialization with .env loading
        AICODE-NOTE: Uses python-dotenv to load OPENAI_API_KEY
        AICODE-NOTE: Supports HTTP_PROXY for proxied API requests
        """
        # AICODE-NOTE: Load environment variables from .env
        if env_path is None:
            # AICODE-NOTE: Default to repository root (4 levels up from this file)
            env_path = Path(__file__).parent.parent.parent.parent / ".env"

        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.debug(f"Loaded environment from {env_path}")
        else:
            logger.warning(f".env file not found at {env_path}")

        # AICODE-NOTE: Get API key from environment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment. "
                "Please set it in .env file at repository root."
            )

        self.timeout = timeout
        self.max_retries = max_retries

        # AICODE-NOTE: Get HTTP proxy from environment if set
        self.http_proxy = os.getenv("HTTP_PROXY")
        if self.http_proxy:
            logger.info(f"HTTP proxy configured: {self.http_proxy}")
            # AICODE-NOTE: Create httpx client with proxy for all API calls
            self._http_client = httpx.Client(
                proxy=self.http_proxy,
                timeout=timeout
            )
        else:
            self._http_client = None

        # AICODE-NOTE: Initialize provider clients lazily (only when needed)
        self._openrouter_client: Optional[OpenAI] = None
        self._openai_client: Optional[OpenAI] = None
        self._anthropic_client: Optional[Anthropic] = None

        logger.info(
            f"LLMClient initialized (timeout={timeout}s, max_retries={max_retries})"
        )

    def _get_openrouter_client(self) -> OpenAI:
        """Get or create OpenRouter client.

        AICODE-NOTE: Uses HTTP proxy if configured via HTTP_PROXY env var
        """
        if self._openrouter_client is None:
            kwargs = {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": self.api_key,
                "timeout": self.timeout
            }

            # AICODE-NOTE: Add proxy support if configured
            if self._http_client:
                kwargs["http_client"] = self._http_client

            self._openrouter_client = OpenAI(**kwargs)
            logger.debug("Initialized OpenRouter client")
        return self._openrouter_client

    def _get_openai_client(self) -> OpenAI:
        """Get or create OpenAI direct client.

        AICODE-NOTE: Uses HTTP proxy if configured via HTTP_PROXY env var
        """
        if self._openai_client is None:
            kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout
            }

            # AICODE-NOTE: Add proxy support if configured
            if self._http_client:
                kwargs["http_client"] = self._http_client

            self._openai_client = OpenAI(**kwargs)
            logger.debug("Initialized OpenAI client")
        return self._openai_client

    def _get_anthropic_client(self) -> Anthropic:
        """Get or create Anthropic client.

        AICODE-NOTE: Uses HTTP proxy if configured via HTTP_PROXY env var
        """
        if self._anthropic_client is None:
            kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout
            }

            # AICODE-NOTE: Add proxy support if configured
            if self._http_client:
                kwargs["http_client"] = self._http_client

            self._anthropic_client = Anthropic(**kwargs)
            logger.debug("Initialized Anthropic client")
        return self._anthropic_client

    def generate(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate completion from LLM with retry logic.

        Args:
            model_id: Model identifier (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")
            messages: List of message dicts with "role" and "content"
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 4000)
            response_format: Optional format specification (e.g., {"type": "json_object"})

        Returns:
            Generated text response

        Raises:
            ValueError: If API key missing or model_id invalid
            RuntimeError: If all retry attempts fail

        AICODE-NOTE: T013 - Implements retry logic with exponential backoff
        AICODE-NOTE: Retry on 429 (rate limit) and 5xx (server errors)
        AICODE-NOTE: Don't retry on 401 (auth) or 400 (bad request)
        AICODE-NOTE: Backoff delays: 1s, 2s, 4s
        """
        retry_delays = [1, 2, 4]  # AICODE-NOTE: Exponential backoff
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(
                    f"LLM API call attempt {attempt + 1}/{self.max_retries} "
                    f"(model={model_id})"
                )

                # AICODE-NOTE: Route to appropriate provider based on model_id prefix
                if model_id.startswith("anthropic/"):
                    # AICODE-NOTE: Anthropic API has different message format
                    response = self._call_anthropic(
                        model_id.replace("anthropic/", ""),
                        messages,
                        temperature,
                        max_tokens
                    )
                elif model_id.startswith("openai/"):
                    # AICODE-NOTE: OpenAI direct API
                    response = self._call_openai(
                        model_id.replace("openai/", ""),
                        messages,
                        temperature,
                        max_tokens,
                        response_format
                    )
                else:
                    # AICODE-NOTE: Default to OpenRouter for all other models
                    response = self._call_openrouter(
                        model_id,
                        messages,
                        temperature,
                        max_tokens,
                        response_format
                    )

                logger.success(f"LLM API call successful (model={model_id})")
                return response

            except Exception as e:
                last_exception = e

                # AICODE-NOTE: Check if error is retryable
                error_str = str(e).lower()
                status_code = getattr(e, 'status_code', None)

                # AICODE-NOTE: Don't retry on auth or bad request errors
                if status_code == 401 or "unauthorized" in error_str:
                    logger.error(f"Authentication error (401): {e}")
                    raise ValueError(f"API authentication failed: {e}") from e

                if status_code == 400 or "bad request" in error_str:
                    logger.error(f"Bad request error (400): {e}")
                    raise ValueError(f"Invalid API request: {e}") from e

                # AICODE-NOTE: Retry on rate limits and server errors
                should_retry = (
                    status_code in [429, 500, 502, 503, 504] or
                    "rate limit" in error_str or
                    "timeout" in error_str or
                    "server error" in error_str
                )

                if should_retry and attempt < self.max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        f"Retryable error on attempt {attempt + 1}: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Non-retryable error or max retries reached: {e}")
                    break

        # AICODE-NOTE: All retries exhausted
        raise RuntimeError(
            f"LLM API call failed after {self.max_retries} attempts. "
            f"Last error: {last_exception}"
        ) from last_exception

    def _call_openrouter(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]]
    ) -> str:
        """Call OpenRouter API."""
        client = self._get_openrouter_client()

        kwargs = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _call_openai(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        response_format: Optional[Dict[str, str]]
    ) -> str:
        """Call OpenAI API directly."""
        client = self._get_openai_client()

        kwargs = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    def _call_anthropic(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Call Anthropic API.

        AICODE-NOTE: Anthropic uses different message format:
        - System message is separate parameter
        - Only user/assistant messages in messages list
        """
        client = self._get_anthropic_client()

        # AICODE-NOTE: Extract system message if present
        system_message = None
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append(msg)

        kwargs = {
            "model": model_id,
            "messages": anthropic_messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        if system_message:
            kwargs["system"] = system_message

        response = client.messages.create(**kwargs)
        return response.content[0].text

    def parse_json_response(self, response: str, schema: Optional[type[BaseModel]] = None) -> Dict[str, Any]:
        """Parse and validate JSON response from LLM.

        Args:
            response: Raw text response from LLM
            schema: Optional Pydantic model for validation

        Returns:
            Parsed JSON as dictionary

        Raises:
            ValueError: If JSON is malformed or validation fails

        AICODE-NOTE: T014 - Handles Claude/GPT JSON formatting differences
        AICODE-NOTE: Claude sometimes wraps JSON in markdown code blocks
        AICODE-NOTE: GPT-4 may include explanatory text before/after JSON
        """
        # AICODE-NOTE: Strip markdown code blocks if present
        response = response.strip()

        if response.startswith("```json"):
            response = response[7:]  # Remove ```json
        elif response.startswith("```"):
            response = response[3:]  # Remove ```

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        # AICODE-NOTE: Try to find JSON object in response
        # Some models may add explanatory text before/after
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError(f"No JSON object found in response: {response[:100]}...")

        json_str = response[json_start:json_end]

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Failed to parse: {json_str[:200]}...")
            raise ValueError(f"Invalid JSON in LLM response: {e}") from e

        # AICODE-NOTE: Validate with Pydantic schema if provided
        if schema:
            try:
                validated = schema(**data)
                return validated.model_dump()
            except Exception as e:
                logger.error(f"Schema validation failed: {e}")
                raise ValueError(f"JSON doesn't match expected schema: {e}") from e

        return data
