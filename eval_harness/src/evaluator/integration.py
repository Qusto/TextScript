# AICODE-NOTE: T061 - UglyScriptAdapter for article generation
# AICODE-NOTE: Adapts existing Ugly Script (src.llm_client + src.cost_tracker)
# AICODE-NOTE: Wraps analyze_style() and generate_article() with error handling

"""Integration adapter for Ugly Script article generation."""

import sys
from pathlib import Path
from typing import Dict, List, Callable, Optional

from loguru import logger

# AICODE-NOTE: Lazy import setup for Ugly Script components
# AICODE-NOTE: We delay importing until runtime to avoid import conflicts during testing
# AICODE-NOTE: The parent project's src uses "from src.xxx" which conflicts with eval_harness/src
_parent_dir = Path(__file__).parent.parent.parent.parent
_ugly_script_src = _parent_dir / "src"

def _setup_ugly_script_imports():
    """Setup sys.path for Ugly Script imports.

    AICODE-NOTE: Called lazily when UglyScriptAdapter is instantiated
    AICODE-NOTE: Avoids import-time conflicts with test mocking
    """
    if str(_parent_dir) not in sys.path:
        sys.path.insert(0, str(_parent_dir))
    if str(_ugly_script_src) not in sys.path:
        sys.path.insert(0, str(_ugly_script_src))


class UglyScriptAdapter:
    """Adapter for Ugly Script article generation.

    AICODE-NOTE: T061-T065 - Wraps Ugly Script for evaluation use
    AICODE-NOTE: Handles style analysis → article generation pipeline
    AICODE-NOTE: Formats topic + theses into content prompt
    """

    def __init__(
        self,
        llm_client: 'LLMClient',  # eval_harness LLMClient
        generation_model_id: str
    ):
        """Initialize adapter with generation model config.

        Args:
            llm_client: Eval harness LLM client (for API key)
            generation_model_id: Model ID for generation (e.g., meta-llama/llama-3-8b-instruct)

        AICODE-NOTE: T062 - Loads generation_model_id from EvalConfig
        """
        self.generation_model_id = generation_model_id

        # AICODE-NOTE: Extract API key from eval harness client
        api_key = llm_client.api_key

        # AICODE-NOTE: Setup imports for Ugly Script (lazy loading)
        _setup_ugly_script_imports()

        # AICODE-NOTE: Import Ugly Script components dynamically
        from llm_client import LLMClient as UglyScriptLLMClient
        from cost_tracker import CostTracker

        # AICODE-NOTE: Create Ugly Script LLM client with generation model
        self.ugly_script_client = UglyScriptLLMClient(
            api_key=api_key,
            model=generation_model_id
        )

        # AICODE-NOTE: Wrap with cost tracker for Ugly Script interface
        self.cost_tracker = CostTracker(self.ugly_script_client)

        logger.info(
            f"UglyScriptAdapter initialized (model={generation_model_id})"
        )

    def generate_article(
        self,
        source_texts: str,
        topic_data: Dict[str, any],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        """Generate article using Ugly Script.

        Args:
            source_texts: Combined source texts for style analysis
            topic_data: Dict with 'topic' and 'theses' keys
            progress_callback: Optional callback for progress updates

        Returns:
            Generated article text

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If API call fails

        AICODE-NOTE: T063 - Calls analyze_style() and generate_article()
        AICODE-NOTE: T064 - Wraps exceptions with context
        AICODE-NOTE: T065 - Supports progress callback
        """
        # AICODE-NOTE: Validate inputs
        if not source_texts or not source_texts.strip():
            raise ValueError("source_texts cannot be empty")

        if not topic_data or "topic" not in topic_data:
            raise ValueError("topic_data must contain 'topic' key")

        if "theses" not in topic_data:
            raise ValueError("topic_data must contain 'theses' key")

        topic = topic_data["topic"]
        theses = topic_data["theses"]

        if not isinstance(theses, list) or len(theses) == 0:
            raise ValueError("topic_data['theses'] must be non-empty list")

        logger.info("Starting article generation with Ugly Script...")

        try:
            # AICODE-NOTE: T063 - Step 1: Analyze style from source texts
            if progress_callback:
                progress_callback("Analyzing writing style from source texts...")

            logger.debug("Analyzing style profile...")
            style_profile = self.cost_tracker.analyze_style(source_texts)

            if not style_profile or not style_profile.strip():
                raise RuntimeError("Style analysis returned empty profile")

            logger.success(f"Style profile analyzed ({len(style_profile)} chars)")

            # AICODE-NOTE: T063 - Step 2: Format topic + theses into content prompt
            if progress_callback:
                progress_callback("Generating article with analyzed style...")

            # AICODE-NOTE: Format topic prompt
            # Include topic and all theses for content generation
            content_prompt = f"{topic}\n\nKey points to cover:\n"
            for i, thesis in enumerate(theses, 1):
                content_prompt += f"{i}. {thesis}\n"

            logger.debug(f"Content prompt: {content_prompt[:100]}...")

            # AICODE-NOTE: T063 - Step 3: Generate article with style profile
            generated_article = self.cost_tracker.generate_article(
                topic=content_prompt,
                style_profile=style_profile
            )

            if not generated_article or not generated_article.strip():
                raise RuntimeError("Article generation returned empty text")

            logger.success(
                f"Article generated successfully ({len(generated_article)} chars)"
            )

            if progress_callback:
                progress_callback("Article generation complete")

            return generated_article

        except TimeoutError as e:
            # AICODE-NOTE: T064 - Specific error handling for timeout
            error_msg = f"Timeout during article generation: {e}"
            logger.error(error_msg)
            raise RuntimeError(
                f"Article generation failed: style analysis or generation timed out"
            ) from e

        except Exception as e:
            # AICODE-NOTE: T064 - Wrap exceptions with context
            error_msg = f"Error during article generation: {e}"
            logger.exception(error_msg)

            # AICODE-NOTE: Provide context about which step failed
            if "style" in str(e).lower() or "analysis" in str(e).lower():
                raise RuntimeError(
                    f"Article generation failed during style analysis: {e}"
                ) from e
            else:
                raise RuntimeError(
                    f"Article generation failed during content generation: {e}"
                ) from e
