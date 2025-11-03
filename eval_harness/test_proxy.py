#!/usr/bin/env python3
"""Test script to verify HTTP proxy works with OpenRouter API."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loguru import logger
from src.shared.llm_client import LLMClient


def test_proxy_connection():
    """Test simple API call through proxy."""
    logger.info("Testing OpenRouter API connection through proxy...")

    try:
        # Initialize client (will load HTTP_PROXY from .env)
        client = LLMClient(timeout=30, max_retries=1)

        # Test simple generation via OpenRouter
        # NOTE: Model ID WITHOUT "openai/" prefix routes to OpenRouter
        logger.info("Sending test request to OpenRouter...")
        response = client.generate(
            model_id="gpt-4o-mini",  # OpenRouter format (no openai/ prefix)
            messages=[
                {"role": "user", "content": "Say 'Hello, proxy works!' and nothing else."}
            ],
            temperature=0,
            max_tokens=50
        )

        logger.success("API call successful!")
        logger.info(f"Response: {response}")
        return True

    except Exception as e:
        logger.error(f"API call failed: {e}")
        return False


if __name__ == "__main__":
    success = test_proxy_connection()
    sys.exit(0 if success else 1)
