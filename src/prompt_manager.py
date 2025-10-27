"""Prompt template management."""

from pathlib import Path
from loguru import logger


# Default prompts as fallback if files are missing
DEFAULT_STYLE_ANALYSIS = """Analyze the writing style of the following text. Describe the author's:
- Tone and voice
- Sentence structure and rhythm
- Vocabulary choices
- Use of rhetorical devices
- Overall stylistic characteristics

Text to analyze:
{content}

Provide a detailed style analysis that could be used to replicate this writing style."""


DEFAULT_ARTICLE_GENERATION = """Write an article about "{topic}" in the following writing style:

{style_profile}

Generate a well-structured article that matches this style profile."""


class PromptManager:
    """Manage prompt templates from files with fallback to defaults."""

    def __init__(self, prompts_dir: str = "prompts"):
        """Initialize PromptManager.

        Args:
            prompts_dir: Directory containing prompt template files
        """
        self.prompts_dir = Path(prompts_dir)

    def load_prompt(self, template_name: str, default: str) -> str:
        """Load prompt template from file or use default.

        Args:
            template_name: Name of template file (without .txt extension)
            default: Default prompt template if file not found

        Returns:
            Prompt template string
        """
        template_file = self.prompts_dir / f"{template_name}.txt"

        try:
            if template_file.exists():
                prompt = template_file.read_text(encoding="utf-8")
                logger.debug(f"Loaded prompt from {template_file}")
                return prompt
            else:
                logger.debug(
                    f"Prompt file {template_file} not found, using default"
                )
                return default
        except Exception as e:
            logger.warning(
                f"Failed to load prompt from {template_file}: {e}, using default"
            )
            return default

    def get_style_analysis_prompt(self) -> str:
        """Get style analysis prompt template.

        Returns:
            Style analysis prompt template
        """
        return self.load_prompt("style_analysis", DEFAULT_STYLE_ANALYSIS)

    def get_article_generation_prompt(self) -> str:
        """Get article generation prompt template.

        Returns:
            Article generation prompt template
        """
        return self.load_prompt("article_generation", DEFAULT_ARTICLE_GENERATION)

    def render_prompt(self, template: str, **kwargs) -> str:
        """Render prompt template with provided values.

        Args:
            template: Prompt template with {placeholders}
            **kwargs: Values to fill in placeholders

        Returns:
            Rendered prompt string
        """
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing placeholder in prompt template: {e}")
            raise ValueError(f"Missing placeholder in prompt template: {e}")
