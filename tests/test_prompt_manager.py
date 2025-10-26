"""Tests for prompt template management."""

import pytest
from pathlib import Path
from src.prompt_manager import PromptManager, DEFAULT_STYLE_ANALYSIS, DEFAULT_ARTICLE_GENERATION


class TestPromptManager:
    """Test PromptManager class."""

    def test_load_prompt_from_file(self, tmp_path):
        """Test loading prompt from existing file."""
        # Create test prompts directory
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Write test prompt
        test_prompt = "Test prompt with {placeholder}"
        (prompts_dir / "test.txt").write_text(test_prompt, encoding="utf-8")

        # Load prompt
        manager = PromptManager(prompts_dir=str(prompts_dir))
        result = manager.load_prompt("test", "default prompt")

        assert result == test_prompt

    def test_load_prompt_missing_file_uses_default(self, tmp_path):
        """Test that missing prompt file returns default."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        manager = PromptManager(prompts_dir=str(prompts_dir))
        default = "This is the default prompt"
        result = manager.load_prompt("nonexistent", default)

        assert result == default

    def test_load_prompt_missing_directory_uses_default(self):
        """Test that missing prompts directory returns default."""
        manager = PromptManager(prompts_dir="/nonexistent/directory")
        default = "This is the default prompt"
        result = manager.load_prompt("test", default)

        assert result == default

    def test_get_style_analysis_prompt_default(self):
        """Test getting style analysis prompt with default."""
        manager = PromptManager(prompts_dir="/nonexistent")
        prompt = manager.get_style_analysis_prompt()

        assert prompt == DEFAULT_STYLE_ANALYSIS
        assert "{content}" in prompt

    def test_get_article_generation_prompt_default(self):
        """Test getting article generation prompt with default."""
        manager = PromptManager(prompts_dir="/nonexistent")
        prompt = manager.get_article_generation_prompt()

        assert prompt == DEFAULT_ARTICLE_GENERATION
        assert "{topic}" in prompt
        assert "{style_profile}" in prompt

    def test_get_style_analysis_prompt_from_file(self, tmp_path):
        """Test loading style analysis prompt from file."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        custom_prompt = "Custom style analysis: {content}"
        (prompts_dir / "style_analysis.txt").write_text(custom_prompt, encoding="utf-8")

        manager = PromptManager(prompts_dir=str(prompts_dir))
        prompt = manager.get_style_analysis_prompt()

        assert prompt == custom_prompt

    def test_get_article_generation_prompt_from_file(self, tmp_path):
        """Test loading article generation prompt from file."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        custom_prompt = "Write about {topic} in style: {style_profile}"
        (prompts_dir / "article_generation.txt").write_text(custom_prompt, encoding="utf-8")

        manager = PromptManager(prompts_dir=str(prompts_dir))
        prompt = manager.get_article_generation_prompt()

        assert prompt == custom_prompt

    def test_render_prompt_success(self):
        """Test rendering prompt with valid placeholders."""
        manager = PromptManager()
        template = "Hello {name}, you are {age} years old"
        result = manager.render_prompt(template, name="Alice", age=30)

        assert result == "Hello Alice, you are 30 years old"

    def test_render_prompt_missing_placeholder(self):
        """Test rendering prompt with missing placeholder raises error."""
        manager = PromptManager()
        template = "Hello {name}, you are {age} years old"

        with pytest.raises(ValueError, match="Missing placeholder"):
            manager.render_prompt(template, name="Alice")

    def test_render_prompt_extra_kwargs(self):
        """Test rendering prompt with extra kwargs (should be ignored)."""
        manager = PromptManager()
        template = "Hello {name}"
        result = manager.render_prompt(template, name="Alice", extra="ignored")

        assert result == "Hello Alice"

    def test_render_prompt_empty_template(self):
        """Test rendering empty template."""
        manager = PromptManager()
        result = manager.render_prompt("", name="Alice")

        assert result == ""

    def test_render_prompt_no_placeholders(self):
        """Test rendering template without placeholders."""
        manager = PromptManager()
        template = "This is a static prompt"
        result = manager.render_prompt(template)

        assert result == template

    def test_default_style_analysis_has_required_placeholders(self):
        """Test that default style analysis prompt has required placeholders."""
        assert "{content}" in DEFAULT_STYLE_ANALYSIS

    def test_default_article_generation_has_required_placeholders(self):
        """Test that default article generation prompt has required placeholders."""
        assert "{topic}" in DEFAULT_ARTICLE_GENERATION
        assert "{style_profile}" in DEFAULT_ARTICLE_GENERATION

    def test_render_with_multiline_content(self):
        """Test rendering prompt with multiline content."""
        manager = PromptManager()
        template = "Content:\n{content}\n\nAnalyze this."
        content = "Line 1\nLine 2\nLine 3"

        result = manager.render_prompt(template, content=content)

        assert "Line 1\nLine 2\nLine 3" in result
        assert result.startswith("Content:\n")

    def test_load_prompt_with_special_characters(self, tmp_path):
        """Test loading prompt with special characters."""
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Prompt with various special characters
        special_prompt = "Test: {var} with \"quotes\" and 'apostrophes' and newlines\n\nАnd unicode: тест"
        (prompts_dir / "special.txt").write_text(special_prompt, encoding="utf-8")

        manager = PromptManager(prompts_dir=str(prompts_dir))
        result = manager.load_prompt("special", "default")

        assert result == special_prompt
        assert "тест" in result
