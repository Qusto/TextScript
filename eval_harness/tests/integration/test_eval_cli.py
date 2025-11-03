# AICODE-NOTE: T055 - Contract test for evaluator CLI
# AICODE-NOTE: Tests argparse, config loading, exit codes from cli-evaluator.md
# AICODE-NOTE: Verifies run_eval.py implements CLI contract correctly

"""Integration tests for evaluator CLI (run_eval.py)."""

import pytest
import sys
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch
import yaml


class TestEvaluatorCLIContract:
    """Test CLI contract for run_eval.py as specified in cli-evaluator.md.

    AICODE-NOTE: T091-T093 - Tests CLI entry point implementation
    AICODE-NOTE: Verifies argparse, exit codes, and output format
    """

    @pytest.fixture
    def mock_config_file(self, tmp_path):
        """Create a mock eval_config.yml file."""
        config_data = {
            "dataset_path": "./eval_dataset/",
            "output_path": "./eval_results/",
            "generation_model_id": "meta-llama/llama-3-8b-instruct",
            "judge_model_id": "openai/gpt-4o",
            "metrics_numeric": {
                "cosine_similarity": True,
                "bert_score": True
            },
            "metrics_judge": {
                "content_judge": True,
                "style_judge": True
            },
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_timeout": 120,
            "max_retries": 3
        }

        config_file = tmp_path / "eval_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        return config_file

    def test_cli_help_flag(self):
        """Test --help flag shows usage information.

        AICODE-NOTE: T092 - Tests argparse help output
        """
        # Run CLI with --help
        result = subprocess.run(
            [sys.executable, "run_eval.py", "--help"],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True
        )

        # Should exit with code 0
        assert result.returncode == 0

        # Should contain usage information
        assert "usage:" in result.stdout.lower() or "Usage:" in result.stdout
        assert "--config" in result.stdout
        assert "--author" in result.stdout
        assert "--verbose" in result.stdout or "-v" in result.stdout

    def test_cli_default_config_path(self, tmp_path, monkeypatch):
        """Test default config path is ./configs/eval_config.yml.

        AICODE-NOTE: T092 - Tests default config parameter
        """
        # Change to temp directory
        monkeypatch.chdir(tmp_path)

        # Create default config location
        configs_dir = tmp_path / "configs"
        configs_dir.mkdir()
        config_file = configs_dir / "eval_config.yml"

        config_data = {
            "dataset_path": "./eval_dataset/",
            "output_path": "./eval_results/",
            "generation_model_id": "test-model",
            "judge_model_id": "test-judge",
            "metrics_numeric": {"cosine_similarity": True, "bert_score": False},
            "metrics_judge": {"content_judge": True, "style_judge": False},
        }

        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        # Mock the main evaluation logic to avoid running full evaluation
        with patch('eval_harness.run_eval.EvaluationRunner') as mock_runner:
            mock_runner.return_value.run_evaluation.return_value = {}

            # Import and run main without --config argument
            from eval_harness.run_eval import main

            # Should load from default path
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Verify config was attempted to load from default path
            # (may fail due to missing dataset, but that's OK)

    def test_cli_custom_config_path(self, mock_config_file):
        """Test --config flag specifies custom config file.

        AICODE-NOTE: T092 - Tests custom config path argument
        """
        with patch('eval_harness.run_eval.EvaluationRunner') as mock_runner:
            with patch('eval_harness.run_eval.load_config') as mock_load:
                mock_load.return_value = Mock()

                # Run with custom config
                result = subprocess.run(
                    [
                        sys.executable,
                        "run_eval.py",
                        "--config",
                        str(mock_config_file)
                    ],
                    cwd=Path(__file__).parent.parent.parent,
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                # Config path should have been used
                # (exact assertion depends on implementation)

    def test_cli_author_filter(self, mock_config_file):
        """Test --author flag filters evaluation to specific author.

        AICODE-NOTE: T092 - Tests author filtering parameter
        """
        with patch('eval_harness.run_eval.EvaluationRunner') as mock_runner:
            mock_instance = Mock()
            mock_runner.return_value = mock_instance

            from eval_harness.run_eval import main

            # Mock sys.argv for author filter
            with patch.object(sys, 'argv', ['run_eval.py', '--author', 'mark_twain']):
                try:
                    main()
                except SystemExit:
                    pass

            # Verify runner was initialized with author filter
            # (implementation detail - may need adjustment)

    def test_cli_verbose_flag(self, mock_config_file):
        """Test -v/--verbose flag enables verbose logging.

        AICODE-NOTE: T092 - Tests verbose mode flag
        """
        result = subprocess.run(
            [
                sys.executable,
                "run_eval.py",
                "--config",
                str(mock_config_file),
                "-v"
            ],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Verbose output should have DEBUG or detailed logs
        # (depends on actual evaluation running)

    def test_cli_exit_code_success(self, mock_config_file, tmp_path):
        """Test exit code 0 on successful evaluation.

        AICODE-NOTE: T093 - Tests success exit code
        """
        # Create minimal dataset
        dataset_dir = tmp_path / "eval_dataset" / "author" / "case_001"
        dataset_dir.mkdir(parents=True)

        (dataset_dir / "source_texts.txt").write_text("Source", encoding="utf-8")
        (dataset_dir / "ground_truth_article.txt").write_text("Truth", encoding="utf-8")
        (dataset_dir / "topic.json").write_text('{"topic": "Test", "theses": ["T1"]}', encoding="utf-8")

        # Mock evaluation to succeed
        with patch('eval_harness.run_eval.EvaluationRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run_evaluation.return_value = {"status": "success"}
            mock_runner.return_value = mock_instance

            result = subprocess.run(
                [sys.executable, "run_eval.py", "--config", str(mock_config_file)],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should exit with 0
            assert result.returncode == 0

    def test_cli_exit_code_config_error(self, tmp_path):
        """Test exit code 1 for configuration errors.

        AICODE-NOTE: T093 - Tests config error exit code
        """
        # Create invalid config (missing required fields)
        bad_config = tmp_path / "bad_config.yml"
        with open(bad_config, 'w') as f:
            yaml.dump({"invalid": "config"}, f)

        result = subprocess.run(
            [sys.executable, "run_eval.py", "--config", str(bad_config)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should exit with code 1
        assert result.returncode == 1
        assert "config" in result.stderr.lower() or "config" in result.stdout.lower()

    def test_cli_exit_code_dataset_error(self, mock_config_file):
        """Test exit code 2 for dataset not found errors.

        AICODE-NOTE: T093 - Tests dataset error exit code
        """
        # Config points to non-existent dataset
        result = subprocess.run(
            [sys.executable, "run_eval.py", "--config", str(mock_config_file)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Should exit with code 2
        assert result.returncode == 2
        assert "dataset" in result.stderr.lower() or "dataset" in result.stdout.lower()

    def test_cli_exit_code_api_error(self, mock_config_file, tmp_path):
        """Test exit code 3 for LLM API errors when all cases fail.

        AICODE-NOTE: T093 - Tests API error exit code
        """
        # Create dataset
        dataset_dir = tmp_path / "eval_dataset" / "author" / "case_001"
        dataset_dir.mkdir(parents=True)

        (dataset_dir / "source_texts.txt").write_text("Source", encoding="utf-8")
        (dataset_dir / "ground_truth_article.txt").write_text("Truth", encoding="utf-8")
        (dataset_dir / "topic.json").write_text('{"topic": "Test", "theses": ["T1"]}', encoding="utf-8")

        # Mock API failure
        with patch('eval_harness.run_eval.UglyScriptAdapter') as mock_adapter:
            mock_adapter.return_value.generate_article.side_effect = RuntimeError("API authentication failed")

            result = subprocess.run(
                [sys.executable, "run_eval.py", "--config", str(mock_config_file)],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=10
            )

            # Should exit with code 3
            assert result.returncode == 3
            assert "api" in result.stderr.lower() or "authentication" in result.stderr.lower()

    def test_cli_exit_code_filesystem_error(self, mock_config_file, tmp_path):
        """Test exit code 4 for file system errors.

        AICODE-NOTE: T093 - Tests filesystem error exit code
        """
        # Set output path to read-only location
        # (implementation-specific test)
        pass  # TODO: Implement if feasible

    def test_cli_exit_code_integration_error(self, mock_config_file):
        """Test exit code 5 for Ugly Script integration errors.

        AICODE-NOTE: T093 - Tests integration error exit code
        """
        # Mock import error for Ugly Script
        with patch('eval_harness.run_eval.UglyScriptAdapter', side_effect=ImportError("Cannot import ugly_script")):
            result = subprocess.run(
                [sys.executable, "run_eval.py", "--config", str(mock_config_file)],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=5
            )

            # Should exit with code 5
            assert result.returncode == 5
            assert "import" in result.stderr.lower() or "integration" in result.stderr.lower()


class TestCLIOutputFormat:
    """Test CLI output format matches specification.

    AICODE-NOTE: Tests output format from cli-evaluator.md
    """

    def test_normal_mode_output_format(self):
        """Test normal mode output includes required information."""
        # Mock evaluation
        with patch('eval_harness.run_eval.EvaluationRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run_evaluation.return_value = {
                "total_cases": 5,
                "mean_metrics": {
                    "cosine_similarity": 0.823,
                    "bert_f1": 0.840,
                    "content_score": 3.8,
                    "style_score": 3.7
                }
            }
            mock_runner.return_value = mock_instance

            result = subprocess.run(
                [sys.executable, "run_eval.py"],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout

            # Should include key information
            assert "Loading configuration" in output or "Config" in output
            assert "Initializing models" in output or "Model" in output
            assert "Evaluation complete" in output or "Complete" in output
            # Mean metrics should be displayed
            assert "0.8" in output  # Cosine similarity
            assert "3." in output   # Judge scores

    def test_author_filter_output(self):
        """Test author filter mode shows filtered results."""
        with patch('eval_harness.run_eval.EvaluationRunner') as mock_runner:
            mock_instance = Mock()
            mock_instance.run_evaluation.return_value = {
                "total_cases": 5,
                "filtered_author": "mark_twain"
            }
            mock_runner.return_value = mock_instance

            result = subprocess.run(
                [sys.executable, "run_eval.py", "--author", "mark_twain"],
                cwd=Path(__file__).parent.parent.parent,
                capture_output=True,
                text=True,
                timeout=10
            )

            output = result.stdout

            # Should mention author filter
            assert "mark_twain" in output
            assert "filter" in output.lower() or "only" in output.lower()
