# AICODE-NOTE: Unit tests for file utilities (T015-T017)
# AICODE-NOTE: Tests UTF-8 file I/O, directory creation, text truncation

"""Unit tests for shared/file_utils.py"""

import pytest
from pathlib import Path

from src.shared.file_utils import (
    read_text_file,
    write_text_file,
    ensure_directory,
    truncate_text
)


def test_write_and_read_text_file(tmp_path):
    """Test writing and reading UTF-8 text file.

    AICODE-NOTE: Tests T015 - basic file I/O
    """
    test_file = tmp_path / "test.txt"
    content = "Hello, world! This is a test."

    write_text_file(test_file, content)
    result = read_text_file(test_file)

    assert result == content


def test_write_text_file_creates_parents(tmp_path):
    """Test write_text_file creates parent directories.

    AICODE-NOTE: Tests T015 - automatic parent directory creation
    """
    test_file = tmp_path / "nested" / "dirs" / "test.txt"
    content = "Test content"

    write_text_file(test_file, content, create_parents=True)

    assert test_file.exists()
    assert read_text_file(test_file) == content


def test_read_text_file_not_found():
    """Test read_text_file raises error for missing file.

    AICODE-NOTE: Tests T015 - error handling for missing files
    """
    with pytest.raises(FileNotFoundError):
        read_text_file("/nonexistent/file.txt")


def test_ensure_directory_creates_path(tmp_path):
    """Test ensure_directory creates nested directories.

    AICODE-NOTE: Tests T016 - directory creation with parents
    """
    new_dir = tmp_path / "level1" / "level2" / "level3"

    result = ensure_directory(new_dir)

    assert result.exists()
    assert result.is_dir()


def test_ensure_directory_idempotent(tmp_path):
    """Test ensure_directory is idempotent (safe to call multiple times).

    AICODE-NOTE: Tests T016 - exist_ok=True behavior
    """
    new_dir = tmp_path / "test_dir"

    # AICODE-NOTE: Call twice - should not raise error
    ensure_directory(new_dir)
    ensure_directory(new_dir)

    assert new_dir.exists()


def test_truncate_text_within_limit():
    """Test truncate_text returns original when within limit.

    AICODE-NOTE: Tests T017 - no truncation when unnecessary
    """
    text = "Short text."
    result = truncate_text(text, max_tokens=100)

    assert result == text


def test_truncate_text_at_sentence_boundary():
    """Test truncate_text breaks at sentence boundary.

    AICODE-NOTE: Tests T017 - sentence boundary truncation
    """
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."

    # AICODE-NOTE: max_tokens=20 = 80 chars (1 token ≈ 4 chars)
    result = truncate_text(text, max_tokens=20)

    # AICODE-NOTE: Should end at sentence boundary
    assert result.endswith(".")
    assert len(result) <= 80


def test_truncate_text_handles_multiple_sentence_endings():
    """Test truncate_text works with various punctuation.

    AICODE-NOTE: Tests T017 - handles . ! ? sentence endings
    """
    text = "Question? Exclamation! Statement. Another statement."

    result = truncate_text(text, max_tokens=15)

    # AICODE-NOTE: Should end at one of the sentence boundaries
    assert result[-1] in ".!?"


def test_truncate_text_no_sentence_boundary():
    """Test truncate_text falls back to word boundary.

    AICODE-NOTE: Tests T017 - word boundary fallback
    """
    # AICODE-NOTE: Long text without sentence endings
    text = "word " * 100

    result = truncate_text(text, max_tokens=20)

    # AICODE-NOTE: Should break at word boundary
    assert result.endswith(" word")
    assert len(result) <= 100  # Approximate


def test_truncate_text_custom_ratio():
    """Test truncate_text with custom tokens_per_char ratio.

    AICODE-NOTE: Tests T017 - configurable token approximation
    """
    text = "a" * 200

    # AICODE-NOTE: Use different ratio: 1 token = 2 chars
    result = truncate_text(text, max_tokens=50, tokens_per_char=0.5)

    assert len(result) <= 100  # 50 tokens * 2 chars/token
