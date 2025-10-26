"""Tests for style profile caching."""

import pytest
from pathlib import Path
from src.style_cache import generate_url_hash, StyleCache


class TestGenerateUrlHash:
    """Test URL hash generation."""

    def test_hash_single_url(self):
        """Test hash generation for single URL."""
        urls = ["https://example.com/article"]
        hash_result = generate_url_hash(urls)

        # Should return a consistent hash
        assert isinstance(hash_result, str)
        assert len(hash_result) == 32  # MD5 hash length

        # Same input should give same hash
        assert generate_url_hash(urls) == hash_result

    def test_hash_multiple_urls(self):
        """Test hash generation for multiple URLs."""
        urls = ["https://example.com/1", "https://example.com/2", "https://example.com/3"]
        hash_result = generate_url_hash(urls)

        assert isinstance(hash_result, str)
        assert len(hash_result) == 32

    def test_hash_order_independence(self):
        """Test that URL order doesn't affect hash (sorted internally)."""
        urls1 = ["https://example.com/a", "https://example.com/b", "https://example.com/c"]
        urls2 = ["https://example.com/c", "https://example.com/a", "https://example.com/b"]
        urls3 = ["https://example.com/b", "https://example.com/c", "https://example.com/a"]

        hash1 = generate_url_hash(urls1)
        hash2 = generate_url_hash(urls2)
        hash3 = generate_url_hash(urls3)

        # All should produce the same hash
        assert hash1 == hash2 == hash3

    def test_hash_different_urls_different_hash(self):
        """Test that different URLs produce different hashes."""
        urls1 = ["https://example.com/article1"]
        urls2 = ["https://example.com/article2"]

        hash1 = generate_url_hash(urls1)
        hash2 = generate_url_hash(urls2)

        assert hash1 != hash2

    def test_hash_empty_list(self):
        """Test hash generation with empty list."""
        hash_result = generate_url_hash([])

        assert isinstance(hash_result, str)
        assert len(hash_result) == 32


class TestStyleCache:
    """Test StyleCache class."""

    def test_init_creates_directory(self, tmp_path):
        """Test that initialization creates cache directory."""
        cache_dir = tmp_path / "test_cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_init_existing_directory(self, tmp_path):
        """Test initialization with existing directory."""
        cache_dir = tmp_path / "existing_cache"
        cache_dir.mkdir()

        # Should not raise error
        cache = StyleCache(cache_dir=str(cache_dir))
        assert cache_dir.exists()

    def test_save_to_cache(self, tmp_path):
        """Test saving style profile to cache."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls = ["https://example.com/article"]
        style_profile = "Test style profile content"

        cache.save_to_cache(urls, style_profile)

        # Check file was created
        url_hash = generate_url_hash(urls)
        cache_file = cache_dir / f"{url_hash}.txt"
        assert cache_file.exists()

        # Check content
        content = cache_file.read_text(encoding="utf-8")
        assert content == style_profile

    def test_load_from_cache_exists(self, tmp_path):
        """Test loading existing style profile from cache."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls = ["https://example.com/article"]
        style_profile = "Cached style profile"

        # Save first
        cache.save_to_cache(urls, style_profile)

        # Load back
        loaded = cache.load_from_cache(urls)
        assert loaded == style_profile

    def test_load_from_cache_not_exists(self, tmp_path):
        """Test loading non-existent cache returns None."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls = ["https://example.com/nonexistent"]
        loaded = cache.load_from_cache(urls)

        assert loaded is None

    def test_cache_hit_check(self, tmp_path):
        """Test checking if cache exists."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls = ["https://example.com/article"]

        # Initially no cache
        assert cache.has_cache(urls) is False

        # After saving
        cache.save_to_cache(urls, "test content")
        assert cache.has_cache(urls) is True

    def test_cache_multiple_profiles(self, tmp_path):
        """Test caching multiple different profiles."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls1 = ["https://example.com/article1"]
        urls2 = ["https://example.com/article2"]
        style1 = "Style profile 1"
        style2 = "Style profile 2"

        cache.save_to_cache(urls1, style1)
        cache.save_to_cache(urls2, style2)

        # Both should be retrievable
        assert cache.load_from_cache(urls1) == style1
        assert cache.load_from_cache(urls2) == style2

    def test_cache_overwrite(self, tmp_path):
        """Test that saving to same URLs overwrites cache."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls = ["https://example.com/article"]

        # Save first version
        cache.save_to_cache(urls, "Version 1")
        assert cache.load_from_cache(urls) == "Version 1"

        # Overwrite with second version
        cache.save_to_cache(urls, "Version 2")
        assert cache.load_from_cache(urls) == "Version 2"

    def test_cache_unicode_content(self, tmp_path):
        """Test caching content with unicode characters."""
        cache_dir = tmp_path / "cache"
        cache = StyleCache(cache_dir=str(cache_dir))

        urls = ["https://example.com/article"]
        style_profile = "Стиль с русским текстом и эмодзи 🎨📝"

        cache.save_to_cache(urls, style_profile)
        loaded = cache.load_from_cache(urls)

        assert loaded == style_profile
        assert "русским" in loaded
        assert "🎨" in loaded

    def test_default_cache_directory(self):
        """Test default cache directory is 'style_profiles'."""
        cache = StyleCache()
        assert cache.cache_dir == Path("style_profiles")
