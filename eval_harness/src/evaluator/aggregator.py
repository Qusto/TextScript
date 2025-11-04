# AICODE-NOTE: T087 - ResultAggregator class - Aggregates metrics across test cases
# AICODE-NOTE: Generates _SUMMARY.csv with per-case metrics and aggregate statistics
# AICODE-NOTE: Generates _SUMMARY.md with human-readable report

"""Result aggregation and summary report generation."""

import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from statistics import mean, median, stdev
from datetime import datetime

from loguru import logger

from src.evaluator.config import TestRunMetadata


class ResultAggregator:
    """Aggregates evaluation results and generates summary reports.

    AICODE-NOTE: T087-T090 - Computes statistics and generates CSV/MD reports
    AICODE-NOTE: Uses pandas-style aggregation for mean, median, std
    """

    def __init__(self):
        """Initialize result aggregator.

        AICODE-NOTE: T087 - Simple initialization, no dependencies
        """
        logger.info("ResultAggregator initialized")

    def aggregate_results(self, results_dir: Path) -> Dict[str, Any]:
        """Aggregate metrics across all test cases.

        Args:
            results_dir: Directory containing evaluation results

        Returns:
            Dict with total_cases, mean_metrics, median_metrics, std_metrics

        Raises:
            ValueError: If no results found

        AICODE-NOTE: T088 - Computes mean, median, std across all cases
        AICODE-NOTE: Handles missing metrics gracefully (None values)
        """
        logger.info(f"Aggregating results from {results_dir}")

        # AICODE-NOTE: Find all case directories
        all_cases = []
        for author_dir in results_dir.iterdir():
            if not author_dir.is_dir() or author_dir.name.startswith("_"):
                continue

            for case_dir in author_dir.iterdir():
                if case_dir.is_dir() and case_dir.name.startswith("case_"):
                    all_cases.append((author_dir.name, case_dir.name, case_dir))

        if not all_cases:
            raise ValueError(f"No evaluation results found in {results_dir}")

        logger.info(f"Found {len(all_cases)} test cases")

        # AICODE-NOTE: Collect all metrics from each case
        metrics_data = {
            "cosine_similarity": [],
            "bert_f1": [],
            "char_ngrams": [],
            "content_score": [],
            "style_score": []
        }

        for author, case_name, case_path in all_cases:
            # AICODE-NOTE: Load numeric metrics
            numeric_file = case_path / "metrics_numeric.json"
            if numeric_file.exists():
                with open(numeric_file, 'r') as f:
                    numeric_data = json.load(f)

                # AICODE-NOTE: Extract cosine similarity
                if numeric_data.get("cosine_similarity"):
                    metrics_data["cosine_similarity"].append(
                        numeric_data["cosine_similarity"]["score"]
                    )

                # AICODE-NOTE: Extract BERTScore F1
                if numeric_data.get("bert_score"):
                    metrics_data["bert_f1"].append(
                        numeric_data["bert_score"]["f1"]
                    )

                # AICODE-NOTE: Extract character n-grams
                if numeric_data.get("char_ngrams"):
                    metrics_data["char_ngrams"].append(
                        numeric_data["char_ngrams"]["score"]
                    )

            # AICODE-NOTE: Load content judge
            content_file = case_path / "metrics_judge_content.json"
            if content_file.exists():
                with open(content_file, 'r') as f:
                    content_data = json.load(f)
                    metrics_data["content_score"].append(content_data["score"])

            # AICODE-NOTE: Load style judge
            style_file = case_path / "metrics_judge_style.json"
            if style_file.exists():
                with open(style_file, 'r') as f:
                    style_data = json.load(f)
                    metrics_data["style_score"].append(style_data["score"])

        # AICODE-NOTE: Compute aggregate statistics
        summary = {
            "total_cases": len(all_cases),
            "mean_metrics": {},
            "median_metrics": {},
            "std_metrics": {}
        }

        for metric_name, values in metrics_data.items():
            if not values:
                logger.warning(f"No data for {metric_name}")
                continue

            # AICODE-NOTE: Compute mean, median, std
            summary["mean_metrics"][metric_name] = mean(values)
            summary["median_metrics"][metric_name] = median(values)

            # AICODE-NOTE: Std requires at least 2 values
            if len(values) >= 2:
                summary["std_metrics"][metric_name] = stdev(values)
            else:
                summary["std_metrics"][metric_name] = 0.0

            logger.debug(
                f"{metric_name}: mean={summary['mean_metrics'][metric_name]:.3f}, "
                f"median={summary['median_metrics'][metric_name]:.3f}, "
                f"std={summary['std_metrics'][metric_name]:.3f}"
            )

        logger.success(f"Aggregation complete: {len(all_cases)} cases")
        return summary

    def generate_summary_csv(self, results_dir: Path) -> None:
        """Generate _SUMMARY.csv with per-case metrics and aggregates.

        Args:
            results_dir: Directory containing evaluation results

        AICODE-NOTE: T089 - Creates CSV with one row per case + aggregate rows
        AICODE-NOTE: Format: author, case, cosine_sim, bert_f1, content_score, style_score
        """
        logger.info("Generating _SUMMARY.csv")

        # AICODE-NOTE: Collect all case data
        case_rows = []
        for author_dir in sorted(results_dir.iterdir()):
            if not author_dir.is_dir() or author_dir.name.startswith("_"):
                continue

            for case_dir in sorted(author_dir.iterdir()):
                if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
                    continue

                row = {
                    "author": author_dir.name,
                    "case": case_dir.name,
                    "cosine_sim": "",
                    "bert_f1": "",
                    "char_ngrams": "",
                    "content_score": "",
                    "style_score": ""
                }

                # AICODE-NOTE: Load metrics from files
                numeric_file = case_dir / "metrics_numeric.json"
                if numeric_file.exists():
                    with open(numeric_file, 'r') as f:
                        numeric_data = json.load(f)

                    if numeric_data.get("cosine_similarity"):
                        row["cosine_sim"] = f"{numeric_data['cosine_similarity']['score']:.4f}"

                    if numeric_data.get("bert_score"):
                        row["bert_f1"] = f"{numeric_data['bert_score']['f1']:.4f}"

                    if numeric_data.get("char_ngrams"):
                        row["char_ngrams"] = f"{numeric_data['char_ngrams']['score']:.4f}"

                content_file = case_dir / "metrics_judge_content.json"
                if content_file.exists():
                    with open(content_file, 'r') as f:
                        content_data = json.load(f)
                        row["content_score"] = str(content_data["score"])

                style_file = case_dir / "metrics_judge_style.json"
                if style_file.exists():
                    with open(style_file, 'r') as f:
                        style_data = json.load(f)
                        row["style_score"] = str(style_data["score"])

                case_rows.append(row)

        if not case_rows:
            logger.warning("No case data to write to CSV")
            return

        # AICODE-NOTE: Compute aggregate statistics
        summary = self.aggregate_results(results_dir)

        # AICODE-NOTE: Add aggregate rows (MEAN, MEDIAN, STD)
        mean_row = {
            "author": "MEAN",
            "case": "",
            "cosine_sim": f"{summary['mean_metrics'].get('cosine_similarity', 0):.4f}" if summary['mean_metrics'].get('cosine_similarity') else "",
            "bert_f1": f"{summary['mean_metrics'].get('bert_f1', 0):.4f}" if summary['mean_metrics'].get('bert_f1') else "",
            "char_ngrams": f"{summary['mean_metrics'].get('char_ngrams', 0):.4f}" if summary['mean_metrics'].get('char_ngrams') else "",
            "content_score": f"{summary['mean_metrics'].get('content_score', 0):.2f}" if summary['mean_metrics'].get('content_score') else "",
            "style_score": f"{summary['mean_metrics'].get('style_score', 0):.2f}" if summary['mean_metrics'].get('style_score') else ""
        }

        median_row = {
            "author": "MEDIAN",
            "case": "",
            "cosine_sim": f"{summary['median_metrics'].get('cosine_similarity', 0):.4f}" if summary['median_metrics'].get('cosine_similarity') else "",
            "bert_f1": f"{summary['median_metrics'].get('bert_f1', 0):.4f}" if summary['median_metrics'].get('bert_f1') else "",
            "char_ngrams": f"{summary['median_metrics'].get('char_ngrams', 0):.4f}" if summary['median_metrics'].get('char_ngrams') else "",
            "content_score": f"{summary['median_metrics'].get('content_score', 0):.2f}" if summary['median_metrics'].get('content_score') else "",
            "style_score": f"{summary['median_metrics'].get('style_score', 0):.2f}" if summary['median_metrics'].get('style_score') else ""
        }

        std_row = {
            "author": "STD",
            "case": "",
            "cosine_sim": f"{summary['std_metrics'].get('cosine_similarity', 0):.4f}" if summary['std_metrics'].get('cosine_similarity') else "",
            "bert_f1": f"{summary['std_metrics'].get('bert_f1', 0):.4f}" if summary['std_metrics'].get('bert_f1') else "",
            "char_ngrams": f"{summary['std_metrics'].get('char_ngrams', 0):.4f}" if summary['std_metrics'].get('char_ngrams') else "",
            "content_score": f"{summary['std_metrics'].get('content_score', 0):.2f}" if summary['std_metrics'].get('content_score') else "",
            "style_score": f"{summary['std_metrics'].get('style_score', 0):.2f}" if summary['std_metrics'].get('style_score') else ""
        }

        # AICODE-NOTE: Write CSV file
        csv_file = results_dir / "_SUMMARY.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["author", "case", "cosine_sim", "bert_f1", "char_ngrams", "content_score", "style_score"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(case_rows)
            writer.writerow(mean_row)
            writer.writerow(median_row)
            writer.writerow(std_row)

        logger.success(f"Saved _SUMMARY.csv: {csv_file}")

    def generate_summary_md(self, results_dir: Path) -> None:
        """Generate _SUMMARY.md human-readable report.

        Args:
            results_dir: Directory containing evaluation results

        AICODE-NOTE: T090 - Creates markdown report with statistics and interpretation
        AICODE-NOTE: Includes per-author breakdown and overall metrics
        """
        logger.info("Generating _SUMMARY.md")

        # AICODE-NOTE: Compute aggregate statistics
        summary = self.aggregate_results(results_dir)

        # AICODE-NOTE: Build markdown content
        md_lines = []
        md_lines.append("# Evaluation Summary Report")
        md_lines.append("")
        md_lines.append(f"**Total Test Cases**: {summary['total_cases']}")
        md_lines.append("")

        md_lines.append("## Overall Metrics")
        md_lines.append("")

        # AICODE-NOTE: Format mean metrics
        if summary["mean_metrics"]:
            md_lines.append("### Mean Values")
            md_lines.append("")

            if "cosine_similarity" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["cosine_similarity"]
                md_lines.append(f"- **Cosine Similarity**: {val:.3f}")

            if "bert_f1" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["bert_f1"]
                md_lines.append(f"- **BERTScore F1**: {val:.3f}")

            if "content_score" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["content_score"]
                md_lines.append(f"- **Content Score**: {val:.1f}/5.0")

            if "style_score" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["style_score"]
                md_lines.append(f"- **Style Score**: {val:.1f}/5.0")

            md_lines.append("")

        # AICODE-NOTE: Format median metrics
        if summary["median_metrics"]:
            md_lines.append("### Median Values")
            md_lines.append("")

            if "cosine_similarity" in summary["median_metrics"]:
                val = summary["median_metrics"]["cosine_similarity"]
                md_lines.append(f"- **Cosine Similarity**: {val:.3f}")

            if "bert_f1" in summary["median_metrics"]:
                val = summary["median_metrics"]["bert_f1"]
                md_lines.append(f"- **BERTScore F1**: {val:.3f}")

            if "content_score" in summary["median_metrics"]:
                val = summary["median_metrics"]["content_score"]
                md_lines.append(f"- **Content Score**: {val:.1f}/5.0")

            if "style_score" in summary["median_metrics"]:
                val = summary["median_metrics"]["style_score"]
                md_lines.append(f"- **Style Score**: {val:.1f}/5.0")

            md_lines.append("")

        # AICODE-NOTE: Format std metrics
        if summary["std_metrics"]:
            md_lines.append("### Standard Deviation")
            md_lines.append("")

            if "cosine_similarity" in summary["std_metrics"]:
                val = summary["std_metrics"]["cosine_similarity"]
                md_lines.append(f"- **Cosine Similarity**: {val:.3f}")

            if "bert_f1" in summary["std_metrics"]:
                val = summary["std_metrics"]["bert_f1"]
                md_lines.append(f"- **BERTScore F1**: {val:.3f}")

            if "content_score" in summary["std_metrics"]:
                val = summary["std_metrics"]["content_score"]
                md_lines.append(f"- **Content Score**: {val:.2f}")

            if "style_score" in summary["std_metrics"]:
                val = summary["std_metrics"]["style_score"]
                md_lines.append(f"- **Style Score**: {val:.2f}")

            md_lines.append("")

        # AICODE-NOTE: Per-author breakdown
        md_lines.append("## Per-Author Breakdown")
        md_lines.append("")

        # AICODE-NOTE: Collect results by author
        author_data = {}
        for author_dir in sorted(results_dir.iterdir()):
            if not author_dir.is_dir() or author_dir.name.startswith("_"):
                continue

            author_name = author_dir.name
            author_data[author_name] = {
                "total_cases": 0,
                "metrics": {
                    "cosine_similarity": [],
                    "bert_f1": [],
                    "char_ngrams": [],
                    "content_score": [],
                    "style_score": []
                }
            }

            for case_dir in author_dir.iterdir():
                if not case_dir.is_dir() or not case_dir.name.startswith("case_"):
                    continue

                author_data[author_name]["total_cases"] += 1

                # AICODE-NOTE: Load metrics
                numeric_file = case_dir / "metrics_numeric.json"
                if numeric_file.exists():
                    with open(numeric_file, 'r') as f:
                        numeric = json.load(f)

                    if numeric.get("cosine_similarity"):
                        author_data[author_name]["metrics"]["cosine_similarity"].append(
                            numeric["cosine_similarity"]["score"]
                        )

                    if numeric.get("bert_score"):
                        author_data[author_name]["metrics"]["bert_f1"].append(
                            numeric["bert_score"]["f1"]
                        )

                    if numeric.get("char_ngrams"):
                        author_data[author_name]["metrics"]["char_ngrams"].append(
                            numeric["char_ngrams"]["score"]
                        )

                content_file = case_dir / "metrics_judge_content.json"
                if content_file.exists():
                    with open(content_file, 'r') as f:
                        content = json.load(f)
                        author_data[author_name]["metrics"]["content_score"].append(content["score"])

                style_file = case_dir / "metrics_judge_style.json"
                if style_file.exists():
                    with open(style_file, 'r') as f:
                        style = json.load(f)
                        author_data[author_name]["metrics"]["style_score"].append(style["score"])

        # AICODE-NOTE: Format per-author statistics
        for author_name in sorted(author_data.keys()):
            data = author_data[author_name]
            md_lines.append(f"### {author_name}")
            md_lines.append("")
            md_lines.append(f"**Cases**: {data['total_cases']}")
            md_lines.append("")

            # AICODE-NOTE: Compute and format author means
            for metric_name, values in data["metrics"].items():
                if values:
                    avg = mean(values)
                    if metric_name in ["cosine_similarity", "bert_f1", "char_ngrams"]:
                        md_lines.append(f"- **{metric_name.replace('_', ' ').title()}**: {avg:.3f}")
                    else:
                        md_lines.append(f"- **{metric_name.replace('_', ' ').title()}**: {avg:.1f}/5.0")

            md_lines.append("")

        # AICODE-NOTE: Write markdown file
        md_file = results_dir / "_SUMMARY.md"
        md_file.write_text("\n".join(md_lines), encoding="utf-8")

        logger.success(f"Saved _SUMMARY.md: {md_file}")


# AICODE-NOTE: Standalone functions for test run metadata generation
# AICODE-NOTE: These are not part of ResultAggregator class for easier testing


def load_run_metadata_from_dir(results_dir: Path) -> Optional[TestRunMetadata]:
    """Load test run metadata from results directory.

    Args:
        results_dir: Path to results directory

    Returns:
        TestRunMetadata object or None if not found

    AICODE-NOTE: Helper for loading metadata from _RUN_METADATA.json
    """
    metadata_file = results_dir / "_RUN_METADATA.json"
    if not metadata_file.exists():
        return None

    try:
        with open(metadata_file, 'r') as f:
            data = json.load(f)

        # Convert timestamp string back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])

        return TestRunMetadata(**data)
    except Exception as e:
        logger.warning(f"Failed to load metadata from {metadata_file}: {e}")
        return None


def generate_run_metadata_md(
    output_dir: Path,
    metadata: TestRunMetadata,
    results: Dict[str, Any]
) -> None:
    """Generate _RUN_METADATA.md in results directory.

    Args:
        output_dir: Path to results directory
        metadata: Test run metadata
        results: Evaluation results dict with total_cases, successful_cases, failed_cases

    AICODE-NOTE: Generates human-readable metadata report
    AICODE-NOTE: Also saves JSON version for programmatic access
    """
    lines = [
        "# Test Run Metadata",
        "",
        f"**Run ID**: {metadata.run_id}",
        f"**Test Mode**: {metadata.test_mode}",
        f"**Timestamp**: {metadata.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Prompt Configuration",
        ""
    ]

    if metadata.test_mode == "generation":
        lines.extend([
            f"- **Prompt Version**: {metadata.prompt_version}",
            f"- **Prompt Hash**: {metadata.prompt_hash}",
        ])
    else:
        lines.append("- **Prompt Version**: N/A (perfect test mode)")

    lines.extend([
        "",
        "## Model Configuration",
        "",
        f"- **Generation Model**: {metadata.generation_model_id}",
        f"- **Judge Model**: {metadata.judge_model_id}",
        f"- **Embedding Model**: {metadata.embedding_model}",
        "",
        "## Results Summary",
        "",
        f"- **Total Cases**: {results['total_cases']}",
        f"- **Successful**: {results['successful_cases']}",
        f"- **Failed**: {results['failed_cases']}",
        "",
        "## Metrics",
        ""
    ])

    # Load summary and add metrics
    summary_json = output_dir / "summary.json"
    if summary_json.exists():
        try:
            with open(summary_json, 'r') as f:
                summary = json.load(f)

            for metric_name, value in summary.get("mean_metrics", {}).items():
                formatted_name = metric_name.replace('_', ' ').title()
                if isinstance(value, float):
                    lines.append(f"- **Mean {formatted_name}**: {value:.3f}")
                else:
                    lines.append(f"- **Mean {formatted_name}**: {value}")
        except Exception as e:
            logger.warning(f"Failed to load summary metrics: {e}")

    # Write markdown file
    md_file = output_dir / "_RUN_METADATA.md"
    md_file.write_text("\n".join(lines), encoding="utf-8")
    logger.success(f"Generated run metadata: {md_file}")

    # Also save JSON version for programmatic access
    json_file = output_dir / "_RUN_METADATA.json"
    metadata_dict = metadata.model_dump(mode="json")
    # Convert datetime to ISO format string
    if isinstance(metadata_dict.get("timestamp"), datetime):
        metadata_dict["timestamp"] = metadata_dict["timestamp"].isoformat()

    with open(json_file, 'w') as f:
        json.dump(metadata_dict, f, indent=2)
    logger.debug(f"Saved metadata JSON: {json_file}")


def update_runs_comparison_md(
    eval_results_dir: Path,
    metadata: TestRunMetadata,
    results: Dict[str, Any]
) -> None:
    """Update RUNS_COMPARISON.md with new run data.

    Args:
        eval_results_dir: Path to eval_results/ directory
        metadata: Test run metadata
        results: Evaluation results dict with output_path

    AICODE-NOTE: Maintains comparison table of all test runs
    AICODE-NOTE: Shows last 20 runs sorted by timestamp (newest first)
    """
    comparison_file = eval_results_dir / "RUNS_COMPARISON.md"

    # Load existing runs
    runs_data = []
    if comparison_file.exists():
        runs_data = _parse_existing_comparison(comparison_file)

    # Add new run
    output_path = Path(results["output_path"])
    metrics = _extract_metrics_from_summary(output_path)

    runs_data.append({
        "run_id": metadata.run_id,
        "test_mode": metadata.test_mode,
        "prompt_version": metadata.prompt_version or "-",
        "generation_model": metadata.generation_model_id if metadata.test_mode == "generation" else "-",
        "timestamp": metadata.timestamp,
        "metrics": metrics
    })

    # Sort by timestamp (newest first) and limit to last 20
    runs_data.sort(key=lambda x: x["timestamp"], reverse=True)
    runs_data = runs_data[:20]

    # Generate markdown content
    md_content = _generate_comparison_table(runs_data)

    # Write file
    comparison_file.write_text(md_content, encoding="utf-8")
    logger.success(f"Updated runs comparison: {comparison_file}")


def _parse_existing_comparison(comparison_file: Path) -> List[Dict[str, Any]]:
    """Parse existing RUNS_COMPARISON.md file.

    Args:
        comparison_file: Path to RUNS_COMPARISON.md

    Returns:
        List of run data dicts

    AICODE-NOTE: Helper for update_runs_comparison_md
    """
    runs_data = []
    content = comparison_file.read_text(encoding="utf-8")

    # Simple parsing: find table rows (lines starting with |)
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("|") and not line.startswith("| Run ID"):
            # Skip header and separator rows
            if "---" in line or "Run ID" in line:
                continue

            # Parse table row
            cells = [c.strip() for c in line.split("|")[1:-1]]  # Skip first and last empty
            if len(cells) >= 5:
                try:
                    # Try to parse timestamp from run_id
                    run_id = cells[0]
                    timestamp = datetime.strptime(run_id, "%Y%m%d_%H%M%S")

                    # Extract metrics from correct columns
                    cos_sim = cells[4] if len(cells) > 4 else "-"
                    char_ngrams = cells[5] if len(cells) > 5 else "-"

                    runs_data.append({
                        "run_id": run_id,
                        "test_mode": cells[1],
                        "prompt_version": cells[2],
                        "generation_model": cells[3],
                        "timestamp": timestamp,
                        "metrics": {
                            "cosine_similarity": cos_sim,
                            "char_ngrams": char_ngrams
                        }
                    })
                except Exception:
                    # Skip malformed rows
                    continue

    return runs_data


def _extract_metrics_from_summary(output_dir: Path) -> Dict[str, str]:
    """Extract metrics from summary.json for comparison table.

    Args:
        output_dir: Path to results directory

    Returns:
        Dict with metric name -> formatted value

    AICODE-NOTE: Helper for update_runs_comparison_md
    """
    summary_json = output_dir / "summary.json"
    if not summary_json.exists():
        return {}

    try:
        with open(summary_json, 'r') as f:
            summary = json.load(f)

        metrics = {}
        for name, value in summary.get("mean_metrics", {}).items():
            if isinstance(value, float):
                metrics[name] = f"{value:.3f}"
            else:
                metrics[name] = str(value)

        return metrics
    except Exception as e:
        logger.warning(f"Failed to extract metrics from {summary_json}: {e}")
        return {}


def _generate_comparison_table(runs_data: List[Dict[str, Any]]) -> str:
    """Generate markdown comparison table from runs data.

    Args:
        runs_data: List of run data dicts

    Returns:
        Markdown table content

    AICODE-NOTE: Helper for update_runs_comparison_md
    """
    lines = [
        "# Test Runs Comparison",
        "",
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Recent Runs",
        "",
        "| Run ID | Mode | Prompt Ver | Gen Model | Cos Sim | Char N-grams |",
        "|--------|------|------------|-----------|---------|--------------|"
    ]

    for run in runs_data:
        metrics = run.get("metrics", {})
        cos_sim = metrics.get("cosine_similarity", "-")
        char_ngrams = metrics.get("char_ngrams", "-")

        # Truncate model name if too long
        model = run["generation_model"]
        if len(model) > 15:
            model = model[:12] + "..."

        lines.append(
            f"| {run['run_id']} | {run['test_mode'][:4]} | "
            f"{run['prompt_version'][:10]} | {model} | {cos_sim} | {char_ngrams} |"
        )

    return "\n".join(lines)
