"""Tests for LLM client."""

import pytest
from src.llm_client import LLMClient


class TestLLMClient:
    """Test LLMClient class."""

    def test_llm_client_initialization(self):
        """Test creating LLMClient instance."""
        client = LLMClient(api_key="test_key_123")
        assert client is not None

    def test_analyze_style(self, mocker):
        """Test analyzing writing style from content."""
        # Mock OpenAI client
        mock_completion = mocker.Mock()
        mock_completion.choices = [mocker.Mock(message=mocker.Mock(content="Professional and concise style"))]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")
        style_profile = client.analyze_style("Sample content for analysis")

        assert style_profile == "Professional and concise style"
        mock_client.chat.completions.create.assert_called_once()

        # Verify the call includes the content
        call_args = mock_client.chat.completions.create.call_args
        assert "Sample content for analysis" in str(call_args)

    def test_generate_article(self, mocker):
        """Test generating article with style profile."""
        # Mock OpenAI client
        mock_completion = mocker.Mock()
        mock_completion.choices = [
            mocker.Mock(message=mocker.Mock(content="Generated article about AI"))
        ]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")
        article = client.generate_article(
            topic="The Future of AI", style_profile="Professional and concise style"
        )

        assert article == "Generated article about AI"
        mock_client.chat.completions.create.assert_called_once()

        # Verify the call includes topic and style
        call_args = mock_client.chat.completions.create.call_args
        assert "The Future of AI" in str(call_args)
        assert "Professional and concise style" in str(call_args)

    def test_analyze_style_with_api_error(self, mocker):
        """Test handling API errors during style analysis."""
        # Mock OpenAI client to raise an error
        mock_client = mocker.Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception, match="API Error"):
            client.analyze_style("Sample content")

    def test_generate_article_with_api_error(self, mocker):
        """Test handling API errors during article generation."""
        # Mock OpenAI client to raise an error
        mock_client = mocker.Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")

        with pytest.raises(Exception, match="API Error"):
            client.generate_article(topic="Test", style_profile="Test style")

    def test_uses_correct_model(self, mocker):
        """Test that LLMClient uses the correct model."""
        mock_completion = mocker.Mock()
        mock_completion.choices = [mocker.Mock(message=mocker.Mock(content="Result"))]

        mock_client = mocker.Mock()
        mock_client.chat.completions.create.return_value = mock_completion

        mocker.patch("src.llm_client.OpenAI", return_value=mock_client)

        client = LLMClient(api_key="test_key")
        client.analyze_style("Content")

        # Verify model is specified
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert "model" in call_kwargs
        assert "claude" in call_kwargs["model"].lower() or "gpt" in call_kwargs["model"].lower()
