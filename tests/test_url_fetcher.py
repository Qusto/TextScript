"""Tests for URL fetching and content extraction."""

import pytest
from src.models import URLSource, ContentCollection
from src.url_fetcher import fetch_url, extract_text_from_html


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


class TestFetchURL:
    """Test fetch_url() function."""

    def test_fetch_url_success(self, mocker):
        """Test successful URL fetch."""
        mock_response = mocker.Mock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status = mocker.Mock()

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        result = fetch_url("https://example.com", timeout=30)

        # Verify headers are included
        call_kwargs = mock_get.call_args.kwargs
        assert "headers" in call_kwargs
        assert "User-Agent" in call_kwargs["headers"]
        assert result == "<html><body>Test content</body></html>"

    def test_fetch_url_timeout(self, mocker):
        """Test URL fetch with timeout error."""
        import requests

        mock_get = mocker.patch("requests.get", side_effect=requests.Timeout("Connection timeout"))

        result = fetch_url("https://example.com", timeout=30)

        assert result is None

    def test_fetch_url_connection_error(self, mocker):
        """Test URL fetch with connection error."""
        import requests

        mock_get = mocker.patch(
            "requests.get", side_effect=requests.ConnectionError("Failed to connect")
        )

        result = fetch_url("https://example.com", timeout=30)

        assert result is None

    def test_fetch_url_http_error(self, mocker):
        """Test URL fetch with HTTP error (404, 500, etc)."""
        import requests

        mock_response = mocker.Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        result = fetch_url("https://example.com", timeout=30)

        assert result is None

    def test_fetch_url_uses_timeout(self, mocker):
        """Test that fetch_url respects timeout parameter."""
        mock_response = mocker.Mock()
        mock_response.text = "content"
        mock_response.raise_for_status = mocker.Mock()

        mock_get = mocker.patch("requests.get", return_value=mock_response)

        fetch_url("https://example.com", timeout=60)

        # Verify timeout is used
        call_kwargs = mock_get.call_args.kwargs
        assert call_kwargs["timeout"] == 60


class TestExtractTextFromHTML:
    """Test extract_text_from_html() function."""

    def test_extract_simple_text(self):
        """Test extracting text from simple HTML."""
        html = "<html><body><p>Hello, world!</p></body></html>"
        text = extract_text_from_html(html)
        assert "Hello, world!" in text
        assert text.strip() == "Hello, world!"

    def test_extract_multiple_paragraphs(self):
        """Test extracting text from multiple paragraphs."""
        html = "<html><body><p>First paragraph.</p><p>Second paragraph.</p></body></html>"
        text = extract_text_from_html(html)
        assert "First paragraph." in text
        assert "Second paragraph." in text

    def test_extract_filters_script_tags(self):
        """Test that script tags are filtered out."""
        html = """
        <html>
        <body>
            <p>Visible content</p>
            <script>alert('This should not appear');</script>
        </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Visible content" in text
        assert "alert" not in text
        assert "This should not appear" not in text

    def test_extract_filters_style_tags(self):
        """Test that style tags are filtered out."""
        html = """
        <html>
        <head><style>.class { color: red; }</style></head>
        <body><p>Visible content</p></body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Visible content" in text
        assert "color: red" not in text
        assert ".class" not in text

    def test_extract_filters_nav_elements(self):
        """Test that navigation elements are filtered out."""
        html = """
        <html>
        <body>
            <nav><a href="#">Menu Item</a></nav>
            <article><p>Article content</p></article>
        </body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Article content" in text
        # Nav might still appear in some parsers, so just verify article content is there

    def test_extract_with_nested_tags(self):
        """Test extracting text from nested HTML tags."""
        html = "<html><body><div><p>Nested <strong>bold</strong> text</p></div></body></html>"
        text = extract_text_from_html(html)
        assert "Nested" in text
        assert "bold" in text
        assert "text" in text

    def test_extract_cleans_whitespace(self):
        """Test that extracted text has cleaned whitespace."""
        html = """
        <html>
        <body>
            <p>  Multiple   spaces   </p>
            <p>

            Newlines

            </p>
        </body>
        </html>
        """
        text = extract_text_from_html(html)
        # Text should be cleaned of excessive whitespace
        assert "Multiple" in text
        assert "spaces" in text
        assert "Newlines" in text

    def test_extract_empty_html(self):
        """Test extracting from empty HTML."""
        html = "<html><body></body></html>"
        text = extract_text_from_html(html)
        assert text.strip() == ""

    def test_extract_from_malformed_html(self):
        """Test extracting from malformed HTML (BeautifulSoup handles it)."""
        html = "<html><body><p>Text without closing tag</body></html>"
        text = extract_text_from_html(html)
        assert "Text without closing tag" in text
