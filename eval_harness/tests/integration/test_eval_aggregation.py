# AICODE-NOTE: T060 - Integration test for result aggregation
# AICODE-NOTE: Tests _SUMMARY.csv generation with mean values across cases
# AICODE-NOTE: Tests _SUMMARY.md human-readable report generation

"""Integration tests for evaluation result aggregation and summary generation."""

import pytest
import json
import csv
from pathlib import Path
from datetime import datetime


class TestResultAggregation:
    """Test aggregation of evaluation results across test cases.

    AICODE-NOTE: T087-T090 - Tests ResultAggregator class
    AICODE-NOTE: Aggregates metrics and generates summary CSV/MD files
    """

    @pytest.fixture
    def eval_results_dir(self, tmp_path):
        """Create evaluation results directory with multiple test cases."""
        results_dir = tmp_path / "eval_results" / "20250103_120000"
        results_dir.mkdir(parents=True)

        # Create results for mark_twain (3 cases)
        for i in range(1, 4):
            case_dir = results_dir / "mark_twain" / f"case_{i:03d}"
            case_dir.mkdir(parents=True)

            # Generated article
            (case_dir / "generated_article.txt").write_text(
                f"Generated article {i}",
                encoding="utf-8"
            )

            # Numeric metrics
            numeric_data = {
                "cosine_similarity": {
                    "score": 0.80 + i * 0.02,  # 0.82, 0.84, 0.86
                    "model": "all-MiniLM-L6-v2",
                    "computed_at": datetime.now().isoformat()
                },
                "bert_score": {
                    "precision": 0.85 + i * 0.01,
                    "recall": 0.83 + i * 0.01,
                    "f1": 0.84 + i * 0.01,  # 0.85, 0.86, 0.87
                    "model": "bert-base-uncased",
                    "computed_at": datetime.now().isoformat()
                }
            }
            (case_dir / "metrics_numeric.json").write_text(
                json.dumps(numeric_data, indent=2),
                encoding="utf-8"
            )

            # Content judge
            content_judge = {
                "score": 3 + (i % 2),  # 4, 3, 4
                "reasoning": f"Content evaluation reasoning for case {i}.",
                "model": "openai/gpt-4o",
                "prompt_version": "content_judge_v1",
                "computed_at": datetime.now().isoformat()
            }
            (case_dir / "metrics_judge_content.json").write_text(
                json.dumps(content_judge, indent=2),
                encoding="utf-8"
            )

            # Style judge
            style_judge = {
                "score": 2 + i,  # 3, 4, 5
                "reasoning": f"Style evaluation reasoning for case {i}.",
                "model": "openai/gpt-4o",
                "prompt_version": "style_judge_v1",
                "computed_at": datetime.now().isoformat()
            }
            (case_dir / "metrics_judge_style.json").write_text(
                json.dumps(style_judge, indent=2),
                encoding="utf-8"
            )

        # Create results for charles_dickens (2 cases)
        for i in range(1, 3):
            case_dir = results_dir / "charles_dickens" / f"case_{i:03d}"
            case_dir.mkdir(parents=True)

            (case_dir / "generated_article.txt").write_text(
                f"Generated article {i}",
                encoding="utf-8"
            )

            numeric_data = {
                "cosine_similarity": {
                    "score": 0.75 + i * 0.02,  # 0.77, 0.79
                    "model": "all-MiniLM-L6-v2",
                    "computed_at": datetime.now().isoformat()
                },
                "bert_score": {
                    "precision": 0.80 + i * 0.01,
                    "recall": 0.78 + i * 0.01,
                    "f1": 0.79 + i * 0.01,  # 0.80, 0.81
                    "model": "bert-base-uncased",
                    "computed_at": datetime.now().isoformat()
                }
            }
            (case_dir / "metrics_numeric.json").write_text(
                json.dumps(numeric_data, indent=2),
                encoding="utf-8"
            )

            content_judge = {
                "score": 3,
                "reasoning": f"Content evaluation for Dickens case {i}.",
                "model": "openai/gpt-4o",
                "prompt_version": "content_judge_v1",
                "computed_at": datetime.now().isoformat()
            }
            (case_dir / "metrics_judge_content.json").write_text(
                json.dumps(content_judge, indent=2),
                encoding="utf-8"
            )

            style_judge = {
                "score": 3,
                "reasoning": f"Style evaluation for Dickens case {i}.",
                "model": "openai/gpt-4o",
                "prompt_version": "style_judge_v1",
                "computed_at": datetime.now().isoformat()
            }
            (case_dir / "metrics_judge_style.json").write_text(
                json.dumps(style_judge, indent=2),
                encoding="utf-8"
            )

        return results_dir

    def test_aggregate_results_computes_means(self, eval_results_dir):
        """Test that aggregate_results() computes correct mean values.

        AICODE-NOTE: T088 - Tests mean computation across all test cases
        """
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        aggregator = ResultAggregator()
        summary = aggregator.aggregate_results(eval_results_dir)

        # Verify summary structure
        assert "total_cases" in summary
        assert "mean_metrics" in summary

        # Total cases: 3 (twain) + 2 (dickens) = 5
        assert summary["total_cases"] == 5

        # Mean cosine: (0.82 + 0.84 + 0.86 + 0.77 + 0.79) / 5 = 0.816
        assert summary["mean_metrics"]["cosine_similarity"] == pytest.approx(0.816, abs=0.01)

        # Mean BERTScore F1: (0.85 + 0.86 + 0.87 + 0.80 + 0.81) / 5 = 0.838
        assert summary["mean_metrics"]["bert_f1"] == pytest.approx(0.838, abs=0.01)

        # Mean content score: (4 + 3 + 4 + 3 + 3) / 5 = 3.4
        assert summary["mean_metrics"]["content_score"] == pytest.approx(3.4, abs=0.1)

        # Mean style score: (3 + 4 + 5 + 3 + 3) / 5 = 3.6
        assert summary["mean_metrics"]["style_score"] == pytest.approx(3.6, abs=0.1)

    def test_generate_summary_csv(self, eval_results_dir):
        """Test generation of _SUMMARY.csv file.

        AICODE-NOTE: T089 - Tests CSV generation with per-case metrics
        """
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        aggregator = ResultAggregator()
        aggregator.generate_summary_csv(eval_results_dir)

        # Verify CSV file exists
        csv_file = eval_results_dir / "_SUMMARY.csv"
        assert csv_file.exists()

        # Read and validate CSV content
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should have 5 data rows + 3 aggregate rows (MEAN, MEDIAN, STD)
        assert len(rows) == 8

        # Check first data row (mark_twain/case_001)
        row = rows[0]
        assert row["author"] == "mark_twain"
        assert row["case"] == "case_001"
        assert float(row["cosine_sim"]) == pytest.approx(0.82, abs=0.01)
        assert int(row["content_score"]) == 4
        assert int(row["style_score"]) == 3

        # Check aggregate rows
        mean_row = rows[5]  # After 5 data rows
        assert mean_row["author"] == "MEAN"
        assert float(mean_row["cosine_sim"]) == pytest.approx(0.816, abs=0.01)

        median_row = rows[6]
        assert median_row["author"] == "MEDIAN"

        std_row = rows[7]
        assert std_row["author"] == "STD"

    def test_generate_summary_md(self, eval_results_dir):
        """Test generation of _SUMMARY.md human-readable report.

        AICODE-NOTE: T090 - Tests markdown report generation
        """
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        aggregator = ResultAggregator()
        aggregator.generate_summary_md(eval_results_dir)

        # Verify MD file exists
        md_file = eval_results_dir / "_SUMMARY.md"
        assert md_file.exists()

        # Read and validate markdown content
        content = md_file.read_text(encoding="utf-8")

        # Should contain evaluation summary header
        assert "Evaluation Summary" in content or "Summary Report" in content

        # Should contain mean metrics
        assert "Mean" in content or "Average" in content
        assert "0.8" in content  # Cosine similarity mean
        assert "3." in content   # Judge scores

        # Should contain per-author breakdown
        assert "mark_twain" in content
        assert "charles_dickens" in content

        # Should contain total cases
        assert "5" in content

    def test_aggregation_handles_missing_metrics(self, eval_results_dir):
        """Test aggregation when some test cases have missing metrics.

        AICODE-NOTE: T088 - Tests handling of None values in aggregation
        """
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        # Remove one metric file to simulate failure
        case_dir = eval_results_dir / "mark_twain" / "case_001"
        (case_dir / "metrics_numeric.json").unlink()

        aggregator = ResultAggregator()
        summary = aggregator.aggregate_results(eval_results_dir)

        # Should still complete, but with reduced sample size
        assert summary["total_cases"] == 5

        # Mean should be computed from available metrics (4 cases instead of 5)
        # Mean cosine: (0.84 + 0.86 + 0.77 + 0.79) / 4 = 0.815
        assert "cosine_similarity" in summary["mean_metrics"]

    def test_aggregation_empty_results_dir(self, tmp_path):
        """Test aggregation with no evaluation results."""
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        empty_dir = tmp_path / "empty_results"
        empty_dir.mkdir()

        aggregator = ResultAggregator()

        # Should handle gracefully
        with pytest.raises(ValueError, match="No evaluation results found"):
            aggregator.aggregate_results(empty_dir)

    def test_summary_csv_format(self, eval_results_dir):
        """Test CSV format matches data-model.md specification."""
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        aggregator = ResultAggregator()
        aggregator.generate_summary_csv(eval_results_dir)

        csv_file = eval_results_dir / "_SUMMARY.csv"

        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        # Verify required columns
        required_columns = [
            "author",
            "case",
            "cosine_sim",
            "bert_f1",
            "content_score",
            "style_score"
        ]

        for col in required_columns:
            assert col in headers, f"Missing required column: {col}"

    def test_aggregation_computes_median_and_std(self, eval_results_dir):
        """Test that aggregation includes median and standard deviation."""
        from eval_harness.src.evaluator.aggregator import ResultAggregator

        aggregator = ResultAggregator()
        summary = aggregator.aggregate_results(eval_results_dir)

        # Should include statistics beyond just mean
        assert "median_metrics" in summary or "statistics" in summary
        assert "std_metrics" in summary or "statistics" in summary
