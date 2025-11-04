"""Integration tests for CLI argument parsing and handling.

AICODE-NOTE: Tests new --test-mode and --prompt-version arguments
AICODE-NOTE: Tests backward compatibility with --perfect-test
"""

import pytest
import subprocess
import sys
from pathlib import Path


class TestCLITestMode:
    """Tests for --test-mode argument."""

    def test_help_shows_test_mode_option(self):
        """Test that --help shows --test-mode option."""
        result = subprocess.run(
            ["poetry", "run", "python", "run_eval.py", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "--test-mode" in result.stdout
        assert "perfect" in result.stdout
        assert "generation" in result.stdout

    def test_help_shows_prompt_version_option(self):
        """Test that --help shows --prompt-version option."""
        result = subprocess.run(
            ["poetry", "run", "python", "run_eval.py", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "--prompt-version" in result.stdout


class TestCLIBackwardCompatibility:
    """Tests for backward compatibility with --perfect-test."""

    def test_perfect_test_flag_still_works(self):
        """Test that legacy --perfect-test flag still works."""
        # Note: This will fail config validation but should parse args successfully
        result = subprocess.run(
            ["poetry", "run", "python", "run_eval.py", "--perfect-test", "--help"],
            capture_output=True,
            text=True
        )

        # Should show help (--help takes precedence)
        assert result.returncode == 0
        assert "--perfect-test" in result.stdout

    def test_perfect_test_shows_deprecation_in_help(self):
        """Test that --perfect-test shows deprecation notice in help."""
        result = subprocess.run(
            ["poetry", "run", "python", "run_eval.py", "--help"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0
        assert "--perfect-test" in result.stdout
        assert "Deprecated" in result.stdout or "deprecated" in result.stdout


class TestCLIArgumentParsing:
    """Tests for argument parsing logic."""

    def test_missing_config_file_shows_error(self):
        """Test that missing config file shows clear error."""
        result = subprocess.run(
            ["poetry", "run", "python", "run_eval.py", "--config", "/nonexistent/config.yml"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        assert result.returncode == 1  # EXIT_CONFIG_ERROR
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_invalid_test_mode_shows_error(self):
        """Test that invalid test mode shows error."""
        result = subprocess.run(
            ["poetry", "run", "python", "run_eval.py", "--test-mode", "invalid"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 2  # argparse error
        assert "invalid choice" in result.stderr.lower()
