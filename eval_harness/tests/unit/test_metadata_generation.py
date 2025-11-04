"""Unit tests for metadata generation functions.

AICODE-NOTE: Tests _RUN_METADATA.md and RUNS_COMPARISON.md generation
AICODE-NOTE: Tests metadata extraction and formatting
"""

import pytest
from datetime import datetime
from pathlib import Path
import json

from src.evaluator.config import TestRunMetadata
from src.evaluator.aggregator import (
    generate_run_metadata_md,
    update_runs_comparison_md,
    load_run_metadata_from_dir
)


class TestGenerateRunMetadataMd:
    """Tests for generate_run_metadata_md function."""

    def test_generate_metadata_for_generation_mode(self, tmp_path: Path):
        """Test generating metadata for generation mode run."""
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

        results = {
            "total_cases": 6,
            "successful_cases": 6,
            "failed_cases": 0
        }

        # Create mock summary JSON
        summary_json = tmp_path / "summary.json"
        summary_json.write_text(json.dumps({
            "mean_metrics": {
                "cosine_similarity": 0.527,
                "char_ngrams": 0.990
            }
        }))

        # Generate metadata
        generate_run_metadata_md(tmp_path, metadata, results)

        # Check file was created
        metadata_file = tmp_path / "_RUN_METADATA.md"
        assert metadata_file.exists()

        content = metadata_file.read_text()

        # Verify content
        assert "# Test Run Metadata" in content
        assert "20251104_123000" in content
        assert "generation" in content
        assert "v1.0" in content
        assert "abc123def456" in content
        assert "gpt-4o-mini" in content
        assert "0.527" in content
        assert "0.990" in content

    def test_generate_metadata_for_perfect_mode(self, tmp_path: Path):
        """Test generating metadata for perfect test mode."""
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

        results = {
            "total_cases": 6,
            "successful_cases": 6,
            "failed_cases": 0
        }

        # Create mock summary JSON
        summary_json = tmp_path / "summary.json"
        summary_json.write_text(json.dumps({
            "mean_metrics": {
                "cosine_similarity": 0.527
            }
        }))

        # Generate metadata
        generate_run_metadata_md(tmp_path, metadata, results)

        # Check file was created
        metadata_file = tmp_path / "_RUN_METADATA.md"
        assert metadata_file.exists()

        content = metadata_file.read_text()

        # Verify content shows N/A for prompt fields
        assert "perfect" in content
        assert "N/A" in content or "None" in content


class TestUpdateRunsComparisonMd:
    """Tests for update_runs_comparison_md function."""

    def test_create_new_comparison_file(self, tmp_path: Path):
        """Test creating new RUNS_COMPARISON.md file."""
        metadata = TestRunMetadata(
            test_mode="generation",
            prompt_version="v1.0",
            prompt_hash="abc123",
            generation_model_id="gpt-4o-mini",
            judge_model_id="gpt-4o",
            embedding_model="all-roberta-large-v1",
            timestamp=datetime(2025, 11, 4, 12, 30, 0),
            run_id="20251104_123000"
        )

        results = {
            "output_path": str(tmp_path / "20251104_123000")
        }

        # Create mock results directory with summary
        results_dir = tmp_path / "20251104_123000"
        results_dir.mkdir()
        summary_json = results_dir / "summary.json"
        summary_json.write_text(json.dumps({
            "mean_metrics": {
                "cosine_similarity": 0.527,
                "char_ngrams": 0.990
            }
        }))

        # Update comparison
        update_runs_comparison_md(tmp_path, metadata, results)

        # Check file was created
        comparison_file = tmp_path / "RUNS_COMPARISON.md"
        assert comparison_file.exists()

        content = comparison_file.read_text()

        # Verify table exists
        assert "# Test Runs Comparison" in content
        assert "Run ID" in content
        assert "20251104_123000" in content
        assert "v1.0" in content
        assert "0.527" in content

    def test_append_to_existing_comparison_file(self, tmp_path: Path):
        """Test appending to existing RUNS_COMPARISON.md file."""
        # Create first run
        metadata1 = TestRunMetadata(
            test_mode="perfect",
            prompt_version=None,
            prompt_hash=None,
            generation_model_id="gpt-4o-mini",
            judge_model_id="gpt-4o",
            embedding_model="all-roberta-large-v1",
            timestamp=datetime(2025, 11, 4, 12, 0, 0),
            run_id="20251104_120000"
        )

        results1_dir = tmp_path / "20251104_120000"
        results1_dir.mkdir()
        (results1_dir / "summary.json").write_text(json.dumps({
            "mean_metrics": {"cosine_similarity": 0.520}
        }))

        update_runs_comparison_md(tmp_path, metadata1, {"output_path": str(results1_dir)})

        # Create second run
        metadata2 = TestRunMetadata(
            test_mode="generation",
            prompt_version="v1.0",
            prompt_hash="abc123",
            generation_model_id="gpt-4o-mini",
            judge_model_id="gpt-4o",
            embedding_model="all-roberta-large-v1",
            timestamp=datetime(2025, 11, 4, 12, 30, 0),
            run_id="20251104_123000"
        )

        results2_dir = tmp_path / "20251104_123000"
        results2_dir.mkdir()
        (results2_dir / "summary.json").write_text(json.dumps({
            "mean_metrics": {"cosine_similarity": 0.450}
        }))

        update_runs_comparison_md(tmp_path, metadata2, {"output_path": str(results2_dir)})

        # Check both runs are in file
        comparison_file = tmp_path / "RUNS_COMPARISON.md"
        content = comparison_file.read_text()

        assert "20251104_120000" in content
        assert "20251104_123000" in content
        assert "0.520" in content
        assert "0.450" in content


class TestLoadRunMetadataFromDir:
    """Tests for load_run_metadata_from_dir helper."""

    def test_load_metadata_from_json(self, tmp_path: Path):
        """Test loading metadata from _RUN_METADATA.json."""
        metadata_file = tmp_path / "_RUN_METADATA.json"
        metadata_file.write_text(json.dumps({
            "test_mode": "generation",
            "prompt_version": "v1.0",
            "prompt_hash": "abc123",
            "generation_model_id": "gpt-4o-mini",
            "judge_model_id": "gpt-4o",
            "embedding_model": "all-roberta-large-v1",
            "timestamp": "2025-11-04T12:30:00",
            "run_id": "20251104_123000"
        }))

        metadata = load_run_metadata_from_dir(tmp_path)

        assert metadata.test_mode == "generation"
        assert metadata.prompt_version == "v1.0"
        assert metadata.run_id == "20251104_123000"

    def test_load_metadata_missing_file_returns_none(self, tmp_path: Path):
        """Test that missing metadata file returns None."""
        metadata = load_run_metadata_from_dir(tmp_path)
        assert metadata is None
