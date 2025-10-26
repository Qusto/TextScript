"""Integration tests for end-to-end workflows."""

import pytest
from pathlib import Path
from src.models import GeneratedArticle


class TestFileOutput:
    """Test file output functionality."""

    def test_save_to_file_creates_file(self, tmp_path):
        """Test that save_to_file creates output file."""
        article = GeneratedArticle(
            content="This is a test article about AI.",
            topic="Artificial Intelligence",
            style_hash="abc123",
        )

        output_file = tmp_path / "output.txt"
        article.save_to_file(str(output_file))

        assert output_file.exists()
        assert output_file.is_file()

    def test_save_to_file_correct_content(self, tmp_path):
        """Test that saved file contains correct content."""
        content = "This is my article content.\n\nWith multiple paragraphs."
        article = GeneratedArticle(
            content=content, topic="Test Topic", style_hash="xyz789"
        )

        output_file = tmp_path / "output.txt"
        article.save_to_file(str(output_file))

        saved_content = output_file.read_text(encoding="utf-8")
        assert saved_content == content

    def test_save_to_file_overwrites_existing(self, tmp_path):
        """Test that save_to_file overwrites existing file."""
        output_file = tmp_path / "output.txt"

        # Create first article and save
        article1 = GeneratedArticle(
            content="First version", topic="Topic 1", style_hash="hash1"
        )
        article1.save_to_file(str(output_file))
        assert output_file.read_text(encoding="utf-8") == "First version"

        # Create second article and save (should overwrite)
        article2 = GeneratedArticle(
            content="Second version", topic="Topic 2", style_hash="hash2"
        )
        article2.save_to_file(str(output_file))
        assert output_file.read_text(encoding="utf-8") == "Second version"

    def test_save_to_file_unicode_content(self, tmp_path):
        """Test saving content with unicode characters."""
        content = "Статья на русском языке с эмодзи 🚀📝 and special chars: «»„"
        article = GeneratedArticle(
            content=content, topic="Тема", style_hash="hash123"
        )

        output_file = tmp_path / "output.txt"
        article.save_to_file(str(output_file))

        saved_content = output_file.read_text(encoding="utf-8")
        assert saved_content == content
        assert "русском" in saved_content
        assert "🚀" in saved_content

    def test_save_to_file_default_filename(self, tmp_path, monkeypatch):
        """Test saving with default filename 'output.txt'."""
        # Change to tmp directory
        monkeypatch.chdir(tmp_path)

        article = GeneratedArticle(
            content="Test content", topic="Test", style_hash="hash"
        )

        # Save with default filename
        article.save_to_file()

        default_file = tmp_path / "output.txt"
        assert default_file.exists()
        assert default_file.read_text(encoding="utf-8") == "Test content"

    def test_save_to_file_creates_parent_directories(self, tmp_path):
        """Test that save_to_file creates parent directories if needed."""
        article = GeneratedArticle(
            content="Test", topic="Test", style_hash="hash"
        )

        nested_path = tmp_path / "nested" / "dir" / "output.txt"
        article.save_to_file(str(nested_path))

        assert nested_path.exists()
        assert nested_path.read_text(encoding="utf-8") == "Test"

    def test_save_to_file_empty_content(self, tmp_path):
        """Test saving article with empty content."""
        article = GeneratedArticle(content="", topic="Empty", style_hash="hash")

        output_file = tmp_path / "output.txt"
        article.save_to_file(str(output_file))

        assert output_file.exists()
        assert output_file.read_text(encoding="utf-8") == ""

    def test_save_to_file_long_content(self, tmp_path):
        """Test saving very long article content."""
        # Create a long article
        long_content = "This is a paragraph.\n\n" * 1000  # ~20KB
        article = GeneratedArticle(
            content=long_content, topic="Long Article", style_hash="hash"
        )

        output_file = tmp_path / "output.txt"
        article.save_to_file(str(output_file))

        saved_content = output_file.read_text(encoding="utf-8")
        assert len(saved_content) == len(long_content)
        assert saved_content == long_content
