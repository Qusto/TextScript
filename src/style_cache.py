"""Style profile caching."""

import hashlib
from pathlib import Path
from typing import List, Optional
from loguru import logger


# AICODE-NOTE: MD5 choice for cache keys
# We use MD5 instead of SHA-256 because:
# 1. No security needed - cache keys are not cryptographic use case
# 2. MD5 is faster than SHA-256 for non-security purposes
# 3. 32-character hash is shorter and easier to work with
# 4. Collision risk is negligible for small number of URL combinations
# This is a common pattern for cache key generation


def generate_url_hash(urls: List[str]) -> str:
    """Generate MD5 hash from list of URLs.

    Args:
        urls: List of URLs to hash

    Returns:
        MD5 hash as hexadecimal string (32 characters)
    """
    # Sort URLs to ensure consistent hash regardless of order
    sorted_urls = sorted(urls)

    # Join URLs with newline separator
    content = "\n".join(sorted_urls)

    # Generate MD5 hash
    hash_obj = hashlib.md5(content.encode("utf-8"))
    return hash_obj.hexdigest()


class StyleCache:
    """Manage style profile caching to disk."""

    def __init__(self, cache_dir: str = "style_profiles"):
        """Initialize StyleCache.

        Args:
            cache_dir: Directory to store cached style profiles
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def has_cache(self, urls: List[str]) -> bool:
        """Check if cache exists for given URLs.

        Args:
            urls: List of URLs to check

        Returns:
            True if cache file exists, False otherwise
        """
        cache_file = self._get_cache_file(urls)
        return cache_file.exists()

    def load_from_cache(self, urls: List[str]) -> Optional[str]:
        """Load style profile from cache.

        Args:
            urls: List of URLs that were analyzed

        Returns:
            Cached style profile or None if not found
        """
        cache_file = self._get_cache_file(urls)

        if not cache_file.exists():
            return None

        try:
            content = cache_file.read_text(encoding="utf-8")
            logger.debug(f"Loaded style profile from cache: {cache_file.name}")
            return content
        except Exception as e:
            logger.warning(f"Failed to load cache from {cache_file}: {e}")
            return None

    def save_to_cache(self, urls: List[str], style_profile: str) -> None:
        """Save style profile to cache.

        Args:
            urls: List of URLs that were analyzed
            style_profile: Style analysis result to cache
        """
        cache_file = self._get_cache_file(urls)

        try:
            cache_file.write_text(style_profile, encoding="utf-8")
            logger.debug(f"Saved style profile to cache: {cache_file.name}")
        except Exception as e:
            logger.warning(f"Failed to save cache to {cache_file}: {e}")

    def _get_cache_file(self, urls: List[str]) -> Path:
        """Get cache file path for given URLs.

        Args:
            urls: List of URLs

        Returns:
            Path to cache file
        """
        url_hash = generate_url_hash(urls)
        return self.cache_dir / f"{url_hash}.txt"
