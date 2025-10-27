"""Cost tracking for OpenRouter API calls."""

import logging
import requests
from typing import Callable

from src.llm_client import LLMClient
from src.models import GenerationCost, ArticleCostReport

logger = logging.getLogger(__name__)


class CostTracker:
    """Wrapper around LLMClient that tracks API costs.

    This class intercepts LLM API calls, extracts generation IDs,
    and fetches detailed cost information from OpenRouter's /generation endpoint.
    """

    def __init__(self, llm_client: LLMClient):
        """Initialize cost tracker with LLM client.

        Args:
            llm_client: LLMClient instance to wrap and track
        """
        self.llm_client = llm_client
        self.generation_ids: list[tuple[str, str]] = []

    def _track_api_call(
        self, method: Callable, stage_name: str, *args, **kwargs
    ) -> str:
        """Track an API call and extract generation ID.

        Args:
            method: LLMClient method to call
            stage_name: Name of the generation stage (e.g., "style_analysis")
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Generated text content from LLM

        Raises:
            Exception: If API call fails
        """
        # Call the underlying LLM client method
        # IMPORTANT: We need to intercept at the OpenAI SDK level to get response.id
        # Since LLMClient methods only return content string, we need to modify approach

        # Get the client's OpenAI client
        client = self.llm_client.client

        # Depending on the method, we call different underlying APIs
        if stage_name == "style_analysis":
            # Load and render prompt template (same as LLMClient.analyze_style)
            template = self.llm_client.prompt_manager.get_style_analysis_prompt()
            prompt = self.llm_client.prompt_manager.render_prompt(
                template, content=args[0], content_length=len(args[0])
            )

            logger.info("Analyzing writing style...")
            response = client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": "user", "content": prompt}],
            )

        elif stage_name == "article_generation":
            # Load and render prompt template (same as LLMClient.generate_article)
            template = self.llm_client.prompt_manager.get_article_generation_prompt()
            prompt = self.llm_client.prompt_manager.render_prompt(
                template, topic=args[0], style_profile=args[1]
            )

            logger.info(f"Generating article about '{args[0]}'...")
            response = client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": "user", "content": prompt}],
            )

        elif stage_name in [
            "generic_generation",
            "style_hints_extraction",
            "research",
        ]:
            # Generic generation (same as LLMClient.generate)
            model_to_use = kwargs.get("model") or self.llm_client.model
            logger.debug(f"Generating with model {model_to_use}...")

            response = client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": args[0]}],
            )

        else:
            raise ValueError(f"Unknown stage name: {stage_name}")

        # Extract generation ID and track it
        generation_id = response.id
        self.generation_ids.append((generation_id, stage_name))

        logger.debug(f"Tracked generation ID: {generation_id} ({stage_name})")

        # Return the content (same interface as LLMClient methods)
        return response.choices[0].message.content

    def analyze_style(self, content: str) -> str:
        """Analyze writing style and track cost.

        Args:
            content: Text content to analyze

        Returns:
            Style analysis description from LLM
        """
        return self._track_api_call(
            self.llm_client.analyze_style, "style_analysis", content
        )

    def generate_article(self, topic: str, style_profile: str) -> str:
        """Generate article and track cost.

        Args:
            topic: Article topic
            style_profile: Style description to emulate

        Returns:
            Generated article text
        """
        return self._track_api_call(
            self.llm_client.generate_article, "article_generation", topic, style_profile
        )

    def generate(
        self, prompt: str, model: str | None = None, stage_name: str | None = None
    ) -> str:
        """Generate text and track cost.

        Args:
            prompt: User prompt text
            model: Optional model override
            stage_name: Optional stage name for cost tracking.
                       If not provided, defaults to "generic_generation".

        Returns:
            Generated text from LLM
        """
        stage = stage_name or "generic_generation"
        return self._track_api_call(
            self.llm_client.generate, stage, prompt, model=model
        )

    def _fetch_generation_cost(
        self, generation_id: str, stage: str
    ) -> GenerationCost | None:
        """Fetch cost information from OpenRouter /generation endpoint.

        Args:
            generation_id: OpenRouter generation ID
            stage: Stage name for this generation

        Returns:
            GenerationCost object or None if fetch fails
        """
        try:
            url = f"https://openrouter.ai/api/v1/generation?id={generation_id}"
            headers = {
                "Authorization": f"Bearer {self.llm_client.client.api_key}",
            }

            logger.debug(f"Fetching cost for generation {generation_id}...")

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()["data"]

            cost = GenerationCost(
                model=data["model"],
                prompt_tokens=data["native_tokens_prompt"],
                completion_tokens=data["native_tokens_completion"],
                total_tokens=data["native_tokens_prompt"]
                + data["native_tokens_completion"],
                cost_usd=data["total_cost"],
                generation_id=generation_id,
                stage=stage,
            )

            logger.debug(
                f"Cost fetched: ${cost.cost_usd:.4f} ({cost.total_tokens} tokens)"
            )

            return cost

        except Exception as e:
            logger.warning(
                f"Failed to fetch cost for generation {generation_id}: {e}"
            )
            return None

    def get_cost_report(self) -> ArticleCostReport:
        """Generate cost report for all tracked API calls.

        Fetches cost information for each tracked generation ID
        and returns an aggregated report.

        Returns:
            ArticleCostReport with all costs
        """
        costs = []

        for generation_id, stage in self.generation_ids:
            cost = self._fetch_generation_cost(generation_id, stage)
            if cost is not None:
                costs.append(cost)

        return ArticleCostReport(costs=costs)
