"""URL fetching and content extraction."""

import requests
from bs4 import BeautifulSoup
from loguru import logger

# AICODE-NOTE: Using requests library over urllib for URL fetching because:
# 1. Cleaner error handling: requests raises specific exceptions (Timeout, ConnectionError, HTTPError)
#    vs urllib's generic URLError that requires manual inspection
# 2. Simpler API: requests.get(url, timeout=N) vs urllib.request.Request + opener setup
# 3. Better timeouts: requests has built-in connection+read timeout support
# 4. More Pythonic: response.text vs response.read().decode()
# 5. Industry standard: requests is the de facto HTTP library in Python ecosystem
# urllib is stdlib but more verbose for common HTTP tasks


def fetch_url(url: str, timeout: int = 30) -> str | None:
    """Fetch HTML content from a URL with error handling.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds (default: 30)

    Returns:
        HTML content as string if successful, None if fetch failed

    Raises:
        None - all exceptions are caught and logged
    """
    # Add User-Agent header to avoid 403 blocks from sites like Wikipedia
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StyleArticleBot/1.0; +https://github.com/Qusto/TextScript)"
    }

    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.Timeout:
        logger.warning(f"⚠ Timeout fetching {url}")
        return None
    except requests.ConnectionError:
        logger.warning(f"⚠ Connection error fetching {url}")
        return None
    except requests.HTTPError as e:
        logger.warning(f"⚠ HTTP error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"⚠ Unexpected error fetching {url}: {e}")
        return None


def extract_text_from_html(html: str) -> str:
    """Extract clean text content from HTML using BeautifulSoup.

    Filters out script, style, and navigation elements, then extracts
    and cleans the remaining text content.

    Args:
        html: Raw HTML string

    Returns:
        Cleaned text content with normalized whitespace
    """
    soup = BeautifulSoup(html, "lxml")

    # AICODE-NOTE: Filtering strategy for content extraction
    # We remove these elements because they contain non-article content that would pollute style analysis:
    # - script: JavaScript code, not prose
    # - style: CSS rules, not prose
    # - nav: Navigation menus and links (repeated across pages, not unique writing style)
    # - header/footer: Site-wide boilerplate (copyright, contact info, etc.)
    # This ensures we analyze only the article's main textual content
    # Future: Could add <aside>, <form>, <button> if needed
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()

    # Get text and clean whitespace
    text = soup.get_text(separator=" ", strip=True)

    # Normalize whitespace: collapse multiple spaces/newlines into single space
    import re

    text = re.sub(r"\s+", " ", text)

    return text.strip()
