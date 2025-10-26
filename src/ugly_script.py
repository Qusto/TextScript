"""Main entry point for the style article generator."""

import sys
import hashlib
from pathlib import Path
from loguru import logger

from src.config import load_config
from src.url_fetcher import fetch_url, extract_text_from_html
from src.models import URLSource, ContentCollection, StyleProfile, GeneratedArticle
from src.llm_client import LLMClient


def configure_logging():
    """Configure Loguru for beautiful console output."""
    # AICODE-NOTE: Loguru format string for CLI aesthetics
    # We use this custom format for a clean, colorful CLI experience:
    # - <green>{time:HH:mm:ss}</green>: Timestamp in green for readability
    # - <level>{level: <8}</level>: Log level with 8-char padding, auto-colored by level
    # - <level>{message}</level>: Message colored by level (INFO=white, SUCCESS=green, WARNING=yellow, ERROR=red)
    # This gives us a nice looking output like:
    #   18:30:45 | INFO     | Fetching content from 3 URLs...
    #   18:30:47 | SUCCESS  | ✓ Style profile analyzed
    #   18:30:50 | WARNING  | ⚠ Failed to fetch https://example.com
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )


def read_input_files() -> tuple[list[str], str]:
    """Read links.txt and topic.txt from current directory.

    Returns:
        Tuple of (urls list, topic string)

    Raises:
        FileNotFoundError: If required input files are missing
    """
    links_file = Path("links.txt")
    topic_file = Path("topic.txt")

    if not links_file.exists():
        logger.error("✗ links.txt not found in current directory")
        raise FileNotFoundError("links.txt not found")

    if not topic_file.exists():
        logger.error("✗ topic.txt not found in current directory")
        raise FileNotFoundError("topic.txt not found")

    # Read URLs from links.txt (one per line, skip empty lines)
    urls = [
        line.strip()
        for line in links_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # Read topic from topic.txt
    topic = topic_file.read_text(encoding="utf-8").strip()

    if not urls:
        logger.error("✗ links.txt is empty")
        raise ValueError("links.txt contains no URLs")

    if not topic:
        logger.error("✗ topic.txt is empty")
        raise ValueError("topic.txt contains no topic")

    return urls, topic


def fetch_and_extract_content(
    urls: list[str], config
) -> ContentCollection:
    """Fetch URLs and extract text content.

    Args:
        urls: List of URLs to fetch
        config: Configuration with limits

    Returns:
        ContentCollection with fetched content
    """
    logger.info(f"Fetching content from {len(urls[:config.max_urls])} URLs...")

    sources = []
    for i, url in enumerate(urls[: config.max_urls], 1):
        logger.info(f"  [{i}/{min(len(urls), config.max_urls)}] Fetching {url}...")

        html = fetch_url(url, timeout=config.url_fetch_timeout)

        if html is None:
            sources.append(URLSource(url=url, status="failed", error="Fetch failed"))
            continue

        # Extract text from HTML
        text = extract_text_from_html(html)

        # Truncate per-URL limit
        if len(text) > config.max_content_per_url:
            text = text[: config.max_content_per_url]
            logger.info(
                f"    Truncated to {config.max_content_per_url} chars (per-URL limit)"
            )

        sources.append(
            URLSource(url=url, content=text, status="success")
        )
        logger.success(f"    ✓ Extracted {len(text)} characters")

    collection = ContentCollection(sources=sources)

    # Apply total content limit
    if collection.total_chars > config.max_total_content:
        logger.info(
            f"Applying total content limit: {collection.total_chars} → {config.max_total_content} chars"
        )
        collection.truncate_to_limit(config.max_total_content)

    logger.success(
        f"✓ Content collection complete: {collection.success_count} successful, {collection.failure_count} failed"
    )
    logger.info(f"  Total content: {collection.total_chars} characters")

    return collection


def generate_url_hash(urls: list[str]) -> str:
    """Generate MD5 hash from sorted URLs for cache key.

    Args:
        urls: List of URLs

    Returns:
        MD5 hash hex string
    """
    sorted_urls = sorted(urls)
    combined = "".join(sorted_urls)
    return hashlib.md5(combined.encode()).hexdigest()


def main():
    """Main entry point for style article generator."""
    configure_logging()

    logger.info("=== Style Article Generator ===")
    logger.info("")

    try:
        # Load configuration
        config = load_config()
        logger.success(f"✓ Configuration loaded (model: {config.model})")

        # Read input files
        urls, topic = read_input_files()
        logger.success(f"✓ Loaded {len(urls)} URLs and topic: '{topic}'")

        # Fetch and extract content
        collection = fetch_and_extract_content(urls, config)

        if collection.success_count == 0:
            logger.error("✗ No content could be fetched from any URL")
            sys.exit(1)

        # Initialize LLM client
        client = LLMClient(api_key=config.api_key, model=config.model)

        # Analyze writing style
        logger.info("")
        logger.info("Analyzing writing style...")
        style_profile_text = client.analyze_style(collection.combined_content)
        logger.success("✓ Style analysis complete")

        # Create style profile object
        url_hash = generate_url_hash(urls)
        style_profile = StyleProfile(
            profile_text=style_profile_text,
            source_urls=urls,
            url_hash=url_hash,
            cached=False,
        )

        # Generate article
        logger.info("")
        logger.info(f"Generating article about '{topic}'...")
        article_content = client.generate_article(topic, style_profile.profile_text)
        logger.success("✓ Article generation complete")

        # Create article object
        article = GeneratedArticle(
            content=article_content, topic=topic, style_hash=url_hash
        )

        # Print article to stdout
        logger.info("")
        article.print_to_stdout()

        logger.info("")
        logger.success(
            f"✓ Article generated successfully ({article.word_count} words)"
        )

    except FileNotFoundError as e:
        logger.error(f"✗ {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"✗ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
