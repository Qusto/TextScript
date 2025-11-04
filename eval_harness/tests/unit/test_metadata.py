"""Unit tests for test run metadata and prompt versioning.

AICODE-NOTE: Tests for TestRunMetadata dataclass and helper functions
AICODE-NOTE: Tests prompt version detection and file hashing
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import yaml

from src.evaluator.config import TestRunMetadata


class TestTestRunMetadata:
    """Tests for TestRunMetadata dataclass."""

    def test_create_metadata_generation_mode(self):
        """Test creating metadata for generation mode."""
        metadata = TestRunMetadata(
            test_mode="generation",
            prompt_version="v1.0",
            prompt_hash="abc123def456",
            generation_model_id="gpt-4o-mini",
            judge_model_id="gpt-4o",
            embedding_model="all-roberta-large-v1",
            timestamp=datetime(2025, 11, 4, 12, 30, 0),
            run_id="20251104_123000"
        )

        assert metadata.test_mode == "generation"
        assert metadata.prompt_version == "v1.0"
        assert metadata.prompt_hash == "abc123def456"
        assert metadata.generation_model_id == "gpt-4o-mini"
        assert metadata.run_id == "20251104_123000"

    def test_create_metadata_perfect_mode(self):
        """Test creating metadata for perfect test mode."""
        metadata = TestRunMetadata(
            test_mode="perfect",
            prompt_version=None,
            prompt_hash=None,
            generation_model_id="gpt-4o-mini",
            judge_model_id="gpt-4o",
            embedding_model="all-roberta-large-v1",
            timestamp=datetime(2025, 11, 4, 12, 30, 0),
            run_id="20251104_123000"
        )

        assert metadata.test_mode == "perfect"
        assert metadata.prompt_version is None
        assert metadata.prompt_hash is None

    def test_metadata_validation_invalid_test_mode(self):
        """Test that invalid test_mode raises validation error."""
        with pytest.raises(ValueError, match="test_mode"):
            TestRunMetadata(
                test_mode="invalid",  # type: ignore
                prompt_version="v1.0",
                prompt_hash="abc123",
                generation_model_id="gpt-4o-mini",
                judge_model_id="gpt-4o",
                embedding_model="all-roberta-large-v1",
                timestamp=datetime.now(),
                run_id="20251104_123000"
            )


class TestComputeFileHash:
    """Tests for compute_file_hash helper function."""

    def test_compute_hash_of_file(self, tmp_path: Path):
        """Test computing SHA256 hash of a file."""
        # Import function
        from run_eval import compute_file_hash

        # Create temp file with known content
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, world!")

        # Compute hash
        file_hash = compute_file_hash(test_file)

        # Verify it's a valid SHA256 hex string (64 chars)
        assert len(file_hash) == 64
        assert all(c in "0123456789abcdef" for c in file_hash)

    def test_compute_hash_same_content_same_hash(self, tmp_path: Path):
        """Test that same content produces same hash."""
        from run_eval import compute_file_hash

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        content = "Identical content"
        file1.write_text(content)
        file2.write_text(content)

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 == hash2

    def test_compute_hash_different_content_different_hash(self, tmp_path: Path):
        """Test that different content produces different hash."""
        from run_eval import compute_file_hash

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        file1.write_text("Content A")
        file2.write_text("Content B")

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 != hash2


class TestDetectPromptVersion:
    """Tests for detect_prompt_version function."""

    def test_detect_version_explicit_current(self, tmp_path: Path):
        """Test detecting version with explicit 'current' argument."""
        from run_eval import detect_prompt_version

        # Setup mock prompts directory
        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create metadata.yml
        metadata = {
            "current": {
                "version": "v1.0",
                "file": "article_generation.txt"
            }
        }
        (prompts_dir / "metadata.yml").write_text(yaml.dump(metadata))

        # Create prompt file
        prompt_file = prompts_dir / "article_generation.txt"
        prompt_file.write_text("Test prompt content")

        # Test with mocked prompts_dir
        version, file_path = detect_prompt_version(
            prompt_version_arg="current",
            prompts_dir=prompts_dir
        )

        assert version == "v1.0"
        assert file_path == prompt_file

    def test_detect_version_explicit_version(self, tmp_path: Path):
        """Test detecting specific version."""
        from run_eval import detect_prompt_version

        # Setup mock prompts directory
        prompts_dir = tmp_path / "prompts"
        versions_dir = prompts_dir / "versions"
        versions_dir.mkdir(parents=True)

        # Create versioned prompt
        v10_file = versions_dir / "v1.0.txt"
        v10_file.write_text("Version 1.0 prompt")

        # Test
        version, file_path = detect_prompt_version(
            prompt_version_arg="v1.0",
            prompts_dir=prompts_dir
        )

        assert version == "v1.0"
        assert file_path == v10_file

    def test_detect_version_missing_version_raises_error(self, tmp_path: Path):
        """Test that missing version raises FileNotFoundError."""
        from run_eval import detect_prompt_version

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        with pytest.raises(FileNotFoundError, match="v999.0"):
            detect_prompt_version(
                prompt_version_arg="v999.0",
                prompts_dir=prompts_dir
            )

    def test_detect_version_auto_from_metadata(self, tmp_path: Path):
        """Test auto-detecting version from metadata.yml."""
        from run_eval import detect_prompt_version

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create metadata.yml
        metadata = {
            "current": {
                "version": "v1.0",
                "file": "article_generation.txt"
            }
        }
        (prompts_dir / "metadata.yml").write_text(yaml.dump(metadata))

        # Create prompt file
        prompt_file = prompts_dir / "article_generation.txt"
        prompt_file.write_text("Current prompt")

        # Test with no explicit version
        version, file_path = detect_prompt_version(
            prompt_version_arg=None,
            prompts_dir=prompts_dir
        )

        assert version == "v1.0"
        assert file_path == prompt_file

    def test_detect_version_fallback_to_hash(self, tmp_path: Path):
        """Test fallback to hash when metadata.yml missing."""
        from run_eval import detect_prompt_version

        prompts_dir = tmp_path / "prompts"
        prompts_dir.mkdir()

        # Create prompt file (no metadata.yml)
        prompt_file = prompts_dir / "article_generation.txt"
        prompt_file.write_text("Prompt without metadata")

        # Test
        version, file_path = detect_prompt_version(
            prompt_version_arg=None,
            prompts_dir=prompts_dir
        )

        # Should get hash-based version
        assert version.startswith("hash-")
        assert len(version) == 13  # "hash-" + 8 chars
        assert file_path == prompt_file


class TestGenerateRunId:
    """Tests for generate_run_id function."""

    def test_generate_run_id_format(self):
        """Test that run_id has correct format."""
        from run_eval import generate_run_id

        run_id = generate_run_id()

        # Format: YYYYMMDD_HHMMSS
        assert len(run_id) == 15
        assert run_id[8] == "_"

        # Parse parts
        date_part = run_id[:8]
        time_part = run_id[9:]

        assert date_part.isdigit()
        assert time_part.isdigit()

    def test_generate_run_id_unique(self):
        """Test that consecutive run_ids are unique."""
        from run_eval import generate_run_id
        import time

        run_id1 = generate_run_id()
        time.sleep(1.1)  # Wait > 1 second
        run_id2 = generate_run_id()

        assert run_id1 != run_id2
