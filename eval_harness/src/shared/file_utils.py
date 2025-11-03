# AICODE-NOTE: T015 - File utility functions for reading/writing UTF-8 text files
# AICODE-NOTE: Handles encoding errors gracefully with replacement strategy
# AICODE-NOTE: Provides directory management and text truncation utilities

"""File utilities for StyleGuard Eval Harness.

This module provides helper functions for:
- Reading/writing UTF-8 text files with error handling
- Creating directories with parent path validation
- Truncating text at sentence boundaries for token limits
"""

import re
from pathlib import Path
from typing import Optional

from loguru import logger


def read_text_file(file_path: Path | str, encoding: str = "utf-8") -> str:
    """Read text file with UTF-8 encoding and error handling.

    Args:
        file_path: Path to text file
        encoding: Text encoding (default: utf-8)

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read

    AICODE-NOTE: T015 - Handles encoding errors by replacing invalid chars
    AICODE-NOTE: Uses 'replace' error handler to avoid crashes on malformed UTF-8
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # AICODE-NOTE: 'replace' error handler substitutes invalid chars with �
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            content = f.read()

        logger.debug(f"Read {len(content)} chars from {file_path}")
        return content

    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise IOError(f"Cannot read file {file_path}: {e}") from e


def write_text_file(
    file_path: Path | str,
    content: str,
    encoding: str = "utf-8",
    create_parents: bool = True
) -> None:
    """Write text to file with UTF-8 encoding.

    Args:
        file_path: Path to output file
        content: Text content to write
        encoding: Text encoding (default: utf-8)
        create_parents: Create parent directories if missing (default: True)

    Raises:
        IOError: If file cannot be written

    AICODE-NOTE: Creates parent directories automatically if missing
    """
    file_path = Path(file_path)

    if create_parents and not file_path.parent.exists():
        ensure_directory(file_path.parent)

    try:
        with open(file_path, "w", encoding=encoding, errors="replace") as f:
            f.write(content)

        logger.debug(f"Wrote {len(content)} chars to {file_path}")

    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        raise IOError(f"Cannot write file {file_path}: {e}") from e


def ensure_directory(dir_path: Path | str) -> Path:
    """Create directory with parent paths if missing.

    Args:
        dir_path: Directory path to create

    Returns:
        Path object for created directory

    Raises:
        OSError: If directory cannot be created

    AICODE-NOTE: T016 - Creates parent directories if missing
    AICODE-NOTE: Uses exist_ok=True to avoid errors if already exists
    """
    dir_path = Path(dir_path)

    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")
        return dir_path

    except Exception as e:
        logger.error(f"Failed to create directory {dir_path}: {e}")
        raise OSError(f"Cannot create directory {dir_path}: {e}") from e


def truncate_text(
    text: str,
    max_tokens: int,
    tokens_per_char: float = 0.25
) -> str:
    """Truncate text to token limit at sentence boundaries.

    Args:
        text: Input text to truncate
        max_tokens: Maximum tokens allowed
        tokens_per_char: Token approximation ratio (default: 0.25 = 1 token per 4 chars)

    Returns:
        Truncated text ending at sentence boundary

    AICODE-NOTE: T017 - Token limit truncation at sentence boundaries
    AICODE-NOTE: Approximation: 1 token ≈ 4 characters (tokens_per_char=0.25)
    AICODE-NOTE: Tries to break at sentence end (. ! ?) when possible
    """
    # AICODE-NOTE: Convert token limit to character limit
    max_chars = int(max_tokens / tokens_per_char)

    if len(text) <= max_chars:
        # AICODE-NOTE: Text already within limit
        return text

    # AICODE-NOTE: Truncate to character limit
    truncated = text[:max_chars]

    # AICODE-NOTE: Find last sentence boundary (. ! ? followed by space or end)
    sentence_pattern = re.compile(r'[.!?](?:\s|$)')
    matches = list(sentence_pattern.finditer(truncated))

    if matches:
        # AICODE-NOTE: Truncate at last sentence boundary
        last_sentence_end = matches[-1].end()
        truncated = truncated[:last_sentence_end].strip()
        logger.debug(
            f"Truncated text from {len(text)} to {len(truncated)} chars "
            f"at sentence boundary (target: {max_chars} chars)"
        )
    else:
        # AICODE-NOTE: No sentence boundary found, truncate at word boundary
        last_space = truncated.rfind(" ")
        if last_space > max_chars * 0.8:  # At least 80% of target
            truncated = truncated[:last_space].strip()
            logger.debug(
                f"Truncated text from {len(text)} to {len(truncated)} chars "
                f"at word boundary (target: {max_chars} chars)"
            )
        else:
            # AICODE-NOTE: Hard truncate if no good boundary found
            truncated = truncated.strip()
            logger.warning(
                f"Hard truncated text from {len(text)} to {len(truncated)} chars "
                f"(no sentence/word boundary found)"
            )

    return truncated
