#!/usr/bin/env python3
# AICODE-NOTE: T095 - Example script for comparing two evaluation runs
# AICODE-NOTE: Demonstrates how to load and analyze differences between _SUMMARY.csv files
# AICODE-NOTE: Shows improvements/regressions in metrics between runs

"""Compare two evaluation runs and identify improvements/regressions.

Usage:
    python examples/compare_runs.py run1/_SUMMARY.csv run2/_SUMMARY.csv

Example:
    python examples/compare_runs.py \
        eval_results/20251103_100000/_SUMMARY.csv \
        eval_results/20251103_120000/_SUMMARY.csv
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from loguru import logger


# AICODE-NOTE: Thresholds for interpreting metric changes
SIGNIFICANCE_THRESHOLDS = {
    "cosine_similarity": 0.02,  # ±2% is meaningful
    "bert_f1": 0.02,            # ±2% is meaningful
    "content_score": 0.2,       # ±0.2 points (on 1-5 scale)
    "style_score": 0.2          # ±0.2 points (on 1-5 scale)
}


def load_summary(csv_path: Path) -> pd.DataFrame:
    """Load _SUMMARY.csv file.

    Args:
        csv_path: Path to _SUMMARY.csv file

    Returns:
        DataFrame with evaluation results

    Raises:
        FileNotFoundError: If CSV file not found

    AICODE-NOTE: Loads CSV and handles missing values
    """
    logger.info(f"Loading summary from {csv_path}")

    if not csv_path.exists():
        raise FileNotFoundError(f"Summary file not found: {csv_path}")

    df = pd.read_csv(csv_path)
    logger.success(f"Loaded {len(df)} test cases from {csv_path}")

    return df


def compute_aggregate_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Compute mean metrics across all test cases.

    Args:
        df: DataFrame with individual case metrics

    Returns:
        Dict with mean values for all metrics

    AICODE-NOTE: Computes means, ignoring NaN values (failed metrics)
    """
    metrics = {}

    # AICODE-NOTE: List of metric columns to aggregate
    metric_columns = [
        "cosine_similarity",
        "bert_precision",
        "bert_recall",
        "bert_f1",
        "content_score",
        "style_score"
    ]

    for col in metric_columns:
        if col in df.columns:
            # AICODE-NOTE: Use nanmean to ignore NaN values
            mean_val = df[col].mean()
            if pd.notna(mean_val):
                metrics[col] = mean_val

    return metrics


def compare_metrics(
    metrics1: Dict[str, float],
    metrics2: Dict[str, float]
) -> Dict[str, Dict[str, Any]]:
    """Compare metrics between two runs.

    Args:
        metrics1: Metrics from run 1
        metrics2: Metrics from run 2

    Returns:
        Dict with metric name -> {run1, run2, delta, change_type}

    AICODE-NOTE: Categorizes changes as improvement/regression/neutral
    """
    comparison = {}

    # AICODE-NOTE: Find all metrics present in both runs
    common_metrics = set(metrics1.keys()) & set(metrics2.keys())

    for metric in common_metrics:
        val1 = metrics1[metric]
        val2 = metrics2[metric]
        delta = val2 - val1

        # AICODE-NOTE: Determine significance based on threshold
        threshold = SIGNIFICANCE_THRESHOLDS.get(metric, 0.01)

        if abs(delta) < threshold:
            change_type = "neutral"
        elif delta > 0:
            change_type = "improvement"
        else:
            change_type = "regression"

        comparison[metric] = {
            "run1": val1,
            "run2": val2,
            "delta": delta,
            "percent_change": (delta / val1 * 100) if val1 != 0 else 0,
            "change_type": change_type
        }

    return comparison


def print_comparison_report(comparison: Dict[str, Dict[str, Any]]) -> None:
    """Print human-readable comparison report.

    Args:
        comparison: Comparison results from compare_metrics()

    AICODE-NOTE: Uses color coding for improvements/regressions
    """
    print("\n" + "=" * 80)
    print("EVALUATION RUN COMPARISON")
    print("=" * 80)
    print()

    # AICODE-NOTE: Group metrics by change type
    improvements = []
    regressions = []
    neutral = []

    for metric, data in comparison.items():
        if data["change_type"] == "improvement":
            improvements.append((metric, data))
        elif data["change_type"] == "regression":
            regressions.append((metric, data))
        else:
            neutral.append((metric, data))

    # AICODE-NOTE: Print improvements first (positive news)
    if improvements:
        print("✅ IMPROVEMENTS:")
        print("-" * 80)
        for metric, data in improvements:
            print(f"  {metric:20s}: {data['run1']:.4f} → {data['run2']:.4f} "
                  f"(+{data['delta']:.4f}, +{data['percent_change']:.1f}%)")
        print()

    # AICODE-NOTE: Print regressions (red flags)
    if regressions:
        print("❌ REGRESSIONS:")
        print("-" * 80)
        for metric, data in regressions:
            print(f"  {metric:20s}: {data['run1']:.4f} → {data['run2']:.4f} "
                  f"({data['delta']:.4f}, {data['percent_change']:.1f}%)")
        print()

    # AICODE-NOTE: Print neutral changes (within noise threshold)
    if neutral:
        print("➖ NO SIGNIFICANT CHANGE:")
        print("-" * 80)
        for metric, data in neutral:
            print(f"  {metric:20s}: {data['run1']:.4f} → {data['run2']:.4f} "
                  f"({data['delta']:+.4f})")
        print()

    # AICODE-NOTE: Print overall verdict
    print("=" * 80)
    if improvements and not regressions:
        print("🎉 VERDICT: Run 2 shows clear improvements!")
    elif regressions and not improvements:
        print("⚠️  VERDICT: Run 2 shows regressions - investigate!")
    elif improvements and regressions:
        print("⚖️  VERDICT: Mixed results - trade-offs detected")
    else:
        print("🔄 VERDICT: No significant changes between runs")
    print("=" * 80)
    print()


def main() -> None:
    """Main entry point for comparison script.

    AICODE-NOTE: T095 - Implements CLI for comparing two evaluation runs
    """
    parser = argparse.ArgumentParser(
        description="Compare two evaluation runs and identify improvements/regressions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two runs
  python compare_runs.py eval_results/run1/_SUMMARY.csv eval_results/run2/_SUMMARY.csv

  # Compare with verbose logging
  python compare_runs.py run1/_SUMMARY.csv run2/_SUMMARY.csv -v
        """
    )

    parser.add_argument(
        "run1_csv",
        type=Path,
        help="Path to first run's _SUMMARY.csv"
    )

    parser.add_argument(
        "run2_csv",
        type=Path,
        help="Path to second run's _SUMMARY.csv"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # AICODE-NOTE: Setup logging
    if not args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="WARNING")

    try:
        # AICODE-NOTE: Load both summaries
        df1 = load_summary(args.run1_csv)
        df2 = load_summary(args.run2_csv)

        # AICODE-NOTE: Compute aggregate metrics
        metrics1 = compute_aggregate_metrics(df1)
        metrics2 = compute_aggregate_metrics(df2)

        logger.info(f"Run 1: {len(metrics1)} metrics")
        logger.info(f"Run 2: {len(metrics2)} metrics")

        # AICODE-NOTE: Compare metrics
        comparison = compare_metrics(metrics1, metrics2)

        # AICODE-NOTE: Print report
        print_comparison_report(comparison)

        # AICODE-NOTE: Exit with appropriate code
        regressions = [m for m, d in comparison.items() if d["change_type"] == "regression"]
        if regressions:
            logger.warning(f"Found {len(regressions)} regressions")
            sys.exit(1)
        else:
            logger.success("Comparison complete - no regressions detected")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(2)
    except Exception as e:
        logger.exception(f"Comparison failed: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
