"""Main entry point for the style article generator."""

import os
import sys
from pathlib import Path

# AICODE-NOTE: Fix sys.path for Docker environment where script is run from /src/
# When running /src/ugly_script.py, Python adds /src to sys.path[0], which breaks
# 'from src.X' imports. Insert '/' early in sys.path to ensure src package is found.
if sys.path[0] == str(Path(__file__).parent):
    # Script is being run from /src directory, insert / right after
    sys.path.insert(1, '/')
elif '/' not in sys.path[:3]:
    # Fallback: ensure / is in first 3 positions
    sys.path.insert(0, '/')

from loguru import logger

from src.config import load_config
from src.url_fetcher import fetch_url, extract_text_from_html
from src.models import URLSource, ContentCollection, StyleProfile, GeneratedArticle
from src.llm_client import LLMClient
from src.style_cache import StyleCache, generate_url_hash
from src.style_hints_extractor import StyleHintsExtractor
from src.research_client import ResearchClient
from src.prompt_manager import PromptManager
from src.cost_tracker import CostTracker


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


def load_profile_from_env() -> str | None:
    """
    Load style profile from STYLE_PROFILE_TEXT environment variable.

    AICODE-NOTE: T139 - Load profile for V2 API generation mode.
    Returns None for free-style generation, or profile text for styled generation.

    Returns:
        str | None: Profile text or None for free-style
    """
    profile_text = os.getenv('STYLE_PROFILE_TEXT', '').strip()

    if profile_text:
        # AICODE-NOTE: Log profile length, not full content (best practice)
        logger.info(f"✓ Loaded style profile from environment ({len(profile_text)} chars)")
        if len(profile_text) > 50:
            logger.debug(f"  Profile preview: {profile_text[:50]}...")
        return profile_text
    else:
        logger.info("✓ No style profile provided - using free-style generation")
        return None


def main():
    """Main entry point for style article generator."""
    configure_logging()

    logger.info("=== Style Article Generator ===")
    logger.info("")

    # AICODE-NOTE: T138 - Parse command line arguments for V2 API mode
    import argparse
    parser = argparse.ArgumentParser(
        description="Generate styled articles with AI"
    )
    parser.add_argument(
        '--skip-style-analysis',
        action='store_true',
        help='Skip URL fetching and style analysis (use existing profile from env)'
    )
    parser.add_argument(
        '--profile-from-env',
        action='store_true',
        help='Load style profile from STYLE_PROFILE_TEXT environment variable'
    )
    args = parser.parse_args()

    try:
        # Load configuration
        config = load_config()
        logger.success(f"✓ Configuration loaded (model: {config.model})")

        # AICODE-NOTE: T140 - Conditional logic based on mode
        # MODE 1: Traditional style analysis from URLs (existing flow)
        # MODE 2: Direct generation with pre-analyzed profile (V2 API)

        if not args.skip_style_analysis:
            # === MODE 1: Traditional style analysis ===
            logger.info("Mode: Style analysis from URLs")

            # Read input files
            urls, topic = read_input_files()
            logger.success(f"✓ Loaded {len(urls)} URLs and topic: '{topic}'")

            # Fetch and extract content
            collection = fetch_and_extract_content(urls, config)

            if collection.success_count == 0:
                logger.error("✗ No content could be fetched from any URL")
                sys.exit(1)

            # Initialize LLM client, cost tracker, and cache
            client = LLMClient(api_key=config.api_key, model=config.model)
            cost_tracker = CostTracker(client)
            cache = StyleCache()

            # Check cache for existing style profile
            logger.info("")
            cached_profile = cache.load_from_cache(urls)

            if cached_profile:
                logger.success("✓ Using cached style profile")
                style_profile_text = cached_profile
                is_cached = True
            else:
                # Analyze writing style with LLM (tracked for cost)
                logger.info("Analyzing writing style...")
                style_profile_text = cost_tracker.analyze_style(collection.combined_content)
                logger.success("✓ Style analysis complete")

                # Save to cache
                cache.save_to_cache(urls, style_profile_text)
                logger.info("  Saved style profile to cache")
                is_cached = False

            # Create style profile object
            url_hash = generate_url_hash(urls)
            style_profile = StyleProfile(
                profile_text=style_profile_text,
                source_urls=urls,
                url_hash=url_hash,
                cached=is_cached,
            )

        else:
            # === MODE 2: Direct generation with pre-analyzed profile ===
            # AICODE-NOTE: T141 - V2 API mode: no URL fetching, profile from environment
            logger.info("Mode: Direct generation (V2 API)")

            # T141: Read only topic.txt (title) - validation required
            topic_file = Path("topic.txt")
            if not topic_file.exists():
                logger.error("✗ topic.txt not found in current directory")
                raise FileNotFoundError("topic.txt is required for direct generation mode")

            topic = topic_file.read_text(encoding="utf-8").strip()

            if not topic:
                logger.error("✗ topic.txt is empty")
                raise ValueError("topic.txt contains no topic")

            logger.success(f"✓ Loaded topic: '{topic}'")

            # T139: Load style profile from environment variable
            if args.profile_from_env:
                style_profile_text = load_profile_from_env()
            else:
                # No profile specified - free-style generation
                logger.info("✓ No profile flag provided - using free-style generation")
                style_profile_text = None

            # Initialize LLM client for generation
            # AICODE-NOTE: T124 - API key still required even for free-style
            # (best practice: fail fast with clear error)
            client = LLMClient(api_key=config.api_key, model=config.model)
            cost_tracker = CostTracker(client)

            # Create minimal style profile object (or None for free-style)
            # AICODE-NOTE: T140 - Define url_hash for both styled and free-style modes
            url_hash = "v2-api-free-style"  # Placeholder hash for V2 API

            if style_profile_text:
                url_hash = "v2-api-profile"  # Placeholder hash for V2 API with profile
                style_profile = StyleProfile(
                    profile_text=style_profile_text,
                    source_urls=[],  # No source URLs in V2 API
                    url_hash=url_hash,
                    cached=False,
                )
            else:
                # Free-style: no profile object needed
                style_profile = None

        # Optional research stage (US7)
        # AICODE-NOTE: Research can work both with and without style profile
        # With profile: uses style hints for targeted research
        # Without profile: uses generic research for the topic
        research_result = None
        if config.research_enabled:
            logger.info("")
            logger.info("=== Research Enhancement Stage ===")

            # Extract style hints from profile if available
            style_hints = None
            if style_profile:
                logger.info("Extracting style hints from profile...")
                hints_extractor = StyleHintsExtractor(config, llm_client=cost_tracker)
                style_hints = hints_extractor.extract(style_profile)
                logger.success(
                    f"✓ Style hints extracted: {style_hints.content_depth}, "
                    f"{style_hints.technical_level}, {style_hints.preferred_sources}"
                )
            else:
                logger.info("No style profile - using generic research approach")

            # Perform research (works with or without style hints)
            research_client = ResearchClient(config, llm_client=cost_tracker)
            research_result = research_client.research(topic, style_hints)
            logger.success(
                f"✓ Research complete: {len(research_result.facts_and_stats)} facts, "
                f"{len(research_result.quotes_and_sources)} quotes"
            )
        else:
            logger.info("")
            logger.info("Research stage disabled (RESEARCH_ENABLED=false)")

        # Generate article (with research if available)
        # AICODE-NOTE: T140 - Support free-style generation (style_profile can be None)
        logger.info("")
        logger.info(f"Generating article about '{topic}'...")

        if research_result:
            # Use enhanced generation with research data
            prompt_manager = PromptManager()
            template = prompt_manager.get_article_generation_prompt()

            # Build research context for prompt
            research_context = f"""

RESEARCH DATA (use this to enrich the article):

Facts and Statistics:
{chr(10).join(f'- {fact}' for fact in research_result.facts_and_stats)}

Quotes and Sources:
{chr(10).join(f'- {quote["text"]}' for quote in research_result.quotes_and_sources)}

Full Research:
{research_result.full_research_text}

Please integrate these facts, quotes, and findings naturally into the article.
"""

            # Render prompt with research context
            enhanced_prompt = prompt_manager.render_prompt(
                template,
                topic=topic,
                style_profile=style_profile.profile_text + research_context,
            )

            article_content = cost_tracker.generate(enhanced_prompt)
        else:
            # Standard generation (with or without profile)
            # AICODE-NOTE: T140 - Pass None for free-style generation
            profile_text = style_profile.profile_text if style_profile else None
            article_content = cost_tracker.generate_article(topic, profile_text)

        logger.success("✓ Article generation complete")

        # Create article object
        article = GeneratedArticle(
            content=article_content, topic=topic, style_hash=url_hash
        )

        # Print article to stdout
        logger.info("")
        article.print_to_stdout()

        # Save article to file
        article.save_to_file("output.txt")
        logger.success("✓ Article saved to output.txt")

        # Display cost report
        cost_report = cost_tracker.get_cost_report()
        cost_report.print_report()

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
