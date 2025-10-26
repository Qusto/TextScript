"""Tests for URL fetching and content extraction."""

import pytest
from src.models import URLSource, ContentCollection


class TestURLSource:
    """Test URLSource dataclass."""

    def test_create_url_source_success(self):
        """Test creating successful URLSource."""
        source = URLSource(
            url="https://example.com",
            content="Test content here",
            status="success"
        )
        assert source.url == "https://example.com"
        assert source.content == "Test content here"
        assert source.status == "success"
        assert source.error is None
        assert source.char_count == 17

    def test_create_url_source_failed(self):
        """Test creating failed URLSource."""
        source = URLSource(
            url="https://example.com",
            status="failed",
            error="Connection timeout"
        )
        assert source.url == "https://example.com"
        assert source.content is None
        assert source.status == "failed"
        assert source.error == "Connection timeout"
        assert source.char_count == 0

    def test_url_source_char_count_property(self):
        """Test char_count property calculation."""
        source_with_content = URLSource(
            url="https://example.com",
            content="Hello, world!",
            status="success"
        )
        assert source_with_content.char_count == 13

        source_without_content = URLSource(
            url="https://example.com",
            status="failed"
        )
        assert source_without_content.char_count == 0

    def test_url_source_truncate(self):
        """Test truncating content to max length."""
        source = URLSource(
            url="https://example.com",
            content="This is a long piece of content that needs truncation",
            status="success"
        )
        source.truncate(20)
        assert len(source.content) == 20
        assert source.content == "This is a long piece"
        assert source.char_count == 20

    def test_url_source_truncate_no_content(self):
        """Test truncating when content is None."""
        source = URLSource(
            url="https://example.com",
            status="failed"
        )
        source.truncate(10)  # Should not raise error
        assert source.content is None
        assert source.char_count == 0

    def test_url_source_truncate_shorter_content(self):
        """Test truncating when content is already shorter than limit."""
        source = URLSource(
            url="https://example.com",
            content="Short",
            status="success"
        )
        source.truncate(100)
        assert source.content == "Short"  # Unchanged
        assert source.char_count == 5


class TestContentCollection:
    """Test ContentCollection dataclass."""

    def test_create_content_collection(self):
        """Test creating ContentCollection with sources."""
        sources = [
            URLSource(url="https://example.com/1", content="Content 1", status="success"),
            URLSource(url="https://example.com/2", content="Content 2", status="success"),
        ]
        collection = ContentCollection(sources=sources)
        assert len(collection.sources) == 2

    def test_combined_content_property(self):
        """Test combined_content concatenation."""
        sources = [
            URLSource(url="https://example.com/1", content="First article", status="success"),
            URLSource(url="https://example.com/2", content="Second article", status="success"),
            URLSource(url="https://example.com/3", content="Third article", status="success"),
        ]
        collection = ContentCollection(sources=sources)
        expected = "First article\n\nSecond article\n\nThird article"
        assert collection.combined_content == expected

    def test_combined_content_skips_failed_sources(self):
        """Test that combined_content skips failed sources."""
        sources = [
            URLSource(url="https://example.com/1", content="Success", status="success"),
            URLSource(url="https://example.com/2", status="failed", error="Timeout"),
            URLSource(url="https://example.com/3", content="Also success", status="success"),
        ]
        collection = ContentCollection(sources=sources)
        expected = "Success\n\nAlso success"
        assert collection.combined_content == expected

    def test_combined_content_skips_none_content(self):
        """Test that combined_content skips sources with None content."""
        sources = [
            URLSource(url="https://example.com/1", content="Has content", status="success"),
            URLSource(url="https://example.com/2", content=None, status="success"),
        ]
        collection = ContentCollection(sources=sources)
        assert collection.combined_content == "Has content"

    def test_total_chars_property(self):
        """Test total_chars calculation."""
        sources = [
            URLSource(url="https://example.com/1", content="12345", status="success"),
            URLSource(url="https://example.com/2", content="67890", status="success"),
        ]
        collection = ContentCollection(sources=sources)
        # "12345\n\n67890" = 5 + 2 + 5 = 12 characters
        assert collection.total_chars == 12

    def test_success_count_property(self):
        """Test success_count calculation."""
        sources = [
            URLSource(url="https://example.com/1", content="A", status="success"),
            URLSource(url="https://example.com/2", status="failed", error="Error"),
            URLSource(url="https://example.com/3", content="B", status="success"),
            URLSource(url="https://example.com/4", status="failed", error="Error"),
        ]
        collection = ContentCollection(sources=sources)
        assert collection.success_count == 2

    def test_failure_count_property(self):
        """Test failure_count calculation."""
        sources = [
            URLSource(url="https://example.com/1", content="A", status="success"),
            URLSource(url="https://example.com/2", status="failed", error="Error"),
            URLSource(url="https://example.com/3", content="B", status="success"),
            URLSource(url="https://example.com/4", status="failed", error="Error"),
        ]
        collection = ContentCollection(sources=sources)
        assert collection.failure_count == 2

    def test_truncate_to_limit(self):
        """Test truncating combined content to limit."""
        sources = [
            URLSource(url="https://example.com/1", content="A" * 100, status="success"),
            URLSource(url="https://example.com/2", content="B" * 100, status="success"),
        ]
        collection = ContentCollection(sources=sources)
        assert collection.total_chars > 50

        collection.truncate_to_limit(50)

        assert collection.total_chars <= 50
        # After truncation, combined_content should be limited
        assert len(collection.combined_content) == 50

    def test_truncate_to_limit_no_op_when_under_limit(self):
        """Test truncate_to_limit doesn't change content when already under limit."""
        sources = [
            URLSource(url="https://example.com/1", content="Short", status="success"),
        ]
        collection = ContentCollection(sources=sources)
        original_content = collection.combined_content

        collection.truncate_to_limit(1000)

        assert collection.combined_content == original_content

    def test_empty_collection(self):
        """Test empty ContentCollection."""
        collection = ContentCollection(sources=[])
        assert collection.combined_content == ""
        assert collection.total_chars == 0
        assert collection.success_count == 0
        assert collection.failure_count == 0
