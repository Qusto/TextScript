#!/usr/bin/env python3
# AICODE-NOTE: T091 - CLI entry point for evaluator
# AICODE-NOTE: Implements cli-evaluator.md contract with argparse
# AICODE-NOTE: T093 - Exit codes: 0=success, 1=config, 2=dataset, 3=API, 4=filesystem, 5=integration

"""CLI entry point for StyleGuard evaluator.

Usage:
    python run_eval.py [--config PATH] [--author NAME] [--verbose]
"""

import sys
import argparse
import yaml
import hashlib
from pathlib import Path
from datetime import datetime

from loguru import logger

# AICODE-NOTE: Import evaluator components
from src.evaluator.config import EvalConfig, TestRunMetadata
from src.evaluator.runner import EvaluationRunner
from src.evaluator.aggregator import (
    ResultAggregator,
    generate_run_metadata_md,
    update_runs_comparison_md
)
from src.evaluator.integration import UglyScriptAdapter
from src.evaluator.metrics.numeric import NumericMetrics
from src.evaluator.metrics.judge import JudgeEvaluator
from src.shared.llm_client import LLMClient


# AICODE-NOTE: Exit codes from cli-evaluator.md
EXIT_SUCCESS = 0
EXIT_CONFIG_ERROR = 1
EXIT_DATASET_ERROR = 2
EXIT_API_ERROR = 3
EXIT_FILESYSTEM_ERROR = 4
EXIT_INTEGRATION_ERROR = 5


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity.

    AICODE-NOTE: Loguru configuration for normal vs verbose mode
    """
    # AICODE-NOTE: Remove default handler
    logger.remove()

    # AICODE-NOTE: Add handler with appropriate level
    log_level = "DEBUG" if verbose else "INFO"
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<level>{message}</level>",
        level=log_level,
        colorize=True
    )


def load_config(config_path: Path) -> EvalConfig:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to eval_config.yml

    Returns:
        Validated EvalConfig object

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config validation fails

    AICODE-NOTE: Loads YAML and validates with Pydantic
    """
    logger.info(f"Loading configuration from {config_path}")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # AICODE-NOTE: Validate with Pydantic EvalConfig
    try:
        config = EvalConfig(**config_data)
        logger.success("Configuration loaded and validated")
        return config
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}") from e


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file for version tracking.

    Args:
        file_path: Path to file

    Returns:
        Hex string of SHA256 hash (64 characters)

    AICODE-NOTE: Used to detect prompt changes even without versioning
    """
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def generate_run_id() -> str:
    """Generate unique run identifier based on current timestamp.

    Returns:
        Run ID in format YYYYMMDD_HHMMSS

    AICODE-NOTE: Used as directory name for results
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def detect_prompt_version(
    prompt_version_arg: str | None = None,
    prompts_dir: Path | None = None
) -> tuple[str, Path]:
    """Detect prompt version from argument or metadata.yml.

    Args:
        prompt_version_arg: Explicit version (e.g., 'v1.0', 'current') or None for auto-detect
        prompts_dir: Path to prompts directory (default: ../../TextScript/prompts)

    Returns:
        Tuple of (version_string, prompt_file_path)

    Raises:
        FileNotFoundError: If specified version not found

    AICODE-NOTE: Priority: explicit arg > metadata.yml > hash fallback
    AICODE-NOTE: prompts_dir param is for testing (dependency injection)
    """
    if prompts_dir is None:
        prompts_dir = Path(__file__).parent.parent / "TextScript" / "prompts"

    metadata_file = prompts_dir / "metadata.yml"

    # Case 1: Explicit version specified
    if prompt_version_arg:
        if prompt_version_arg == "current":
            # Use main file
            prompt_file = prompts_dir / "article_generation.txt"
            # Read version from metadata
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = yaml.safe_load(f)
                version = metadata.get("current", {}).get("version", "v1.0")
            else:
                version = "v1.0"  # Default
        else:
            # Use specific version from versions/
            prompt_file = prompts_dir / "versions" / f"{prompt_version_arg}.txt"
            if not prompt_file.exists():
                raise FileNotFoundError(
                    f"Prompt version not found: {prompt_version_arg}\n"
                    f"  Expected file: {prompt_file}"
                )
            version = prompt_version_arg

    # Case 2: Auto-detect from metadata.yml
    else:
        prompt_file = prompts_dir / "article_generation.txt"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)
            version = metadata.get("current", {}).get("version", "v1.0")
        else:
            # Case 3: Fallback to hash
            version = f"hash-{compute_file_hash(prompt_file)[:8]}"

    return version, prompt_file


def initialize_components(config: EvalConfig, perfect_test: bool = False) -> tuple:
    """Initialize all evaluation components.

    Args:
        config: Validated EvalConfig
        perfect_test: Skip adapter if True (perfect test mode)

    Returns:
        Tuple of (runner, aggregator) ready for evaluation

    Raises:
        ImportError: If Ugly Script cannot be imported
        RuntimeError: If model initialization fails

    AICODE-NOTE: Creates all components based on config
    AICODE-NOTE: Conditionally creates metric computers based on enabled flags
    AICODE-NOTE: T117 - Skip adapter in perfect test (no generation needed)
    """
    logger.info("Initializing evaluation components...")

    try:
        # AICODE-NOTE: Initialize LLM client
        llm_client = LLMClient()
        logger.success("LLM client initialized")

        # AICODE-NOTE: Initialize UglyScriptAdapter for article generation
        # AICODE-NOTE: T117 - Skip in perfect test mode (not needed)
        adapter = None
        if not perfect_test:
            adapter = UglyScriptAdapter(
                llm_client=llm_client,
                generation_model_id=config.generation_model_id
            )
            logger.success(f"Generation adapter initialized (model={config.generation_model_id})")
        else:
            logger.info("⚠️  Skipping adapter (perfect test mode - no generation)")

        # AICODE-NOTE: Initialize numeric metrics if any enabled
        numeric_metrics = None
        if any(config.metrics_numeric.values()):
            logger.info("Initializing numeric metrics...")
            numeric_metrics = NumericMetrics(
                embedding_model=config.embedding_model,
                bert_model="bert-base-uncased"
            )
            logger.success("Numeric metrics initialized")

        # AICODE-NOTE: Initialize judge evaluator if any enabled
        judge_evaluator = None
        if any(config.metrics_judge.values()):
            logger.info("Initializing judge evaluator...")
            judge_evaluator = JudgeEvaluator(
                llm_client=llm_client,
                judge_model_id=config.judge_model_id
            )
            logger.success(f"Judge evaluator initialized (model={config.judge_model_id})")

        # AICODE-NOTE: Create evaluation runner
        runner = EvaluationRunner(
            config=config,
            adapter=adapter,
            numeric_metrics=numeric_metrics,
            judge_evaluator=judge_evaluator
        )
        logger.success("Evaluation runner initialized")

        # AICODE-NOTE: Create result aggregator
        aggregator = ResultAggregator()
        logger.success("Result aggregator initialized")

        return runner, aggregator

    except ImportError as e:
        logger.exception(f"Failed to import required module: {e}")
        raise ImportError(f"Integration error: {e}") from e


def main() -> None:
    """Main entry point for evaluator CLI.

    AICODE-NOTE: T092 - Implements argparse with all flags
    AICODE-NOTE: T093 - Implements exit codes and error handling
    AICODE-NOTE: NEW - Supports --test-mode and --prompt-version for experiment tracking
    """
    # AICODE-NOTE: Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run StyleGuard evaluation on test dataset",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test 1: Perfect test (author baseline)
  python run_eval.py --test-mode perfect -v

  # Test 2: Generation test with current prompt
  python run_eval.py --test-mode generation

  # Test 2: Generation test with specific prompt version
  python run_eval.py --test-mode generation --prompt-version v1.0

  # Legacy syntax (still works)
  python run_eval.py --perfect-test -v
        """
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path("./configs/eval_config.yml"),
        help="Path to YAML configuration file (default: ./configs/eval_config.yml)"
    )

    parser.add_argument(
        "--test-mode",
        choices=["perfect", "generation"],
        default=None,
        help="Test mode: 'perfect' for author baseline, 'generation' for LLM generation (default: generation)"
    )

    parser.add_argument(
        "--prompt-version",
        type=str,
        default=None,
        help="Prompt version (e.g., 'v1.0', 'v1.1', 'current'). Auto-detected from metadata.yml if not specified."
    )

    parser.add_argument(
        "--author",
        type=str,
        default=None,
        help="Filter evaluation to specific author only"
    )

    parser.add_argument(
        "--perfect-test",
        action="store_true",
        help="(Deprecated: use --test-mode=perfect) Enable perfect test mode for baseline calibration"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging output"
    )

    args = parser.parse_args()

    # AICODE-NOTE: Setup logging
    setup_logging(verbose=args.verbose)

    # AICODE-NOTE: Handle backward compatibility for --perfect-test
    if args.perfect_test and not args.test_mode:
        args.test_mode = "perfect"
        logger.warning(
            "⚠️  --perfect-test is deprecated, use --test-mode=perfect instead"
        )

    # AICODE-NOTE: Default to generation mode if not specified
    if not args.test_mode:
        args.test_mode = "generation"

    try:
        # AICODE-NOTE: Step 1 - Load configuration
        try:
            config = load_config(args.config)
        except FileNotFoundError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(EXIT_CONFIG_ERROR)
        except ValueError as e:
            logger.error(f"Configuration validation error: {e}")
            sys.exit(EXIT_CONFIG_ERROR)

        # AICODE-NOTE: Step 2 - Verify dataset exists
        dataset_path = Path(config.dataset_path)
        if not dataset_path.exists() or not dataset_path.is_dir():
            logger.error(f"Dataset directory not found: {dataset_path}")
            sys.exit(EXIT_DATASET_ERROR)

        # AICODE-NOTE: Verify dataset has valid structure
        author_dirs = [d for d in dataset_path.iterdir() if d.is_dir()]
        if not author_dirs:
            logger.error(f"No author directories found in dataset: {dataset_path}")
            sys.exit(EXIT_DATASET_ERROR)

        logger.info(f"Found {len(author_dirs)} authors in dataset")

        # AICODE-NOTE: Step 2.5 - Detect prompt version (only for generation mode)
        prompt_version = None
        prompt_hash = None

        if args.test_mode == "generation":
            try:
                prompt_version, prompt_file = detect_prompt_version(args.prompt_version)
                prompt_hash = compute_file_hash(prompt_file)[:12]
                logger.info(f"📝 Using prompt version: {prompt_version}")
                logger.info(f"   Prompt file: {prompt_file}")
                logger.debug(f"   Prompt hash: {prompt_hash}")
            except FileNotFoundError as e:
                logger.error(f"Prompt version error: {e}")
                sys.exit(EXIT_CONFIG_ERROR)

        # AICODE-NOTE: Step 3 - Initialize components
        perfect_test = (args.test_mode == "perfect")
        try:
            runner, aggregator = initialize_components(config, perfect_test=perfect_test)
        except ImportError as e:
            logger.error(f"Integration error: {e}")
            sys.exit(EXIT_INTEGRATION_ERROR)
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            sys.exit(EXIT_CONFIG_ERROR)

        # AICODE-NOTE: Step 4 - Run evaluation
        logger.info("Starting evaluation run...")
        print("\nRunning evaluation...")
        print(f"Dataset: {config.dataset_path}")
        print(f"Output: {config.output_path}")

        if args.author:
            print(f"Filtering by author: {args.author}")

        # AICODE-NOTE: T116 - Perfect test mode warning
        if args.test_mode == "perfect":
            print("\n⚠️  PERFECT TEST MODE ENABLED - Using source texts as generated output")
            print("This mode establishes author style baseline. Expected metrics:")
            print("  - Char N-grams: ~0.99 (same author style)")
            print("  - Cosine similarity: 0.40-0.60 (different content, same style)")
        else:
            print(f"\n📝 GENERATION MODE - Testing prompt version: {prompt_version}")
            if prompt_hash:
                print(f"   Prompt hash: {prompt_hash}")

        print()

        try:
            results = runner.run_evaluation(
                author_filter=args.author,
                perfect_test=perfect_test  # AICODE-NOTE: T117 - Pass perfect test flag
            )
        except FileNotFoundError as e:
            logger.error(f"Dataset error: {e}")
            sys.exit(EXIT_DATASET_ERROR)
        except Exception as e:
            logger.exception(f"Evaluation error: {e}")

            # AICODE-NOTE: Check if all cases failed due to API errors
            if "authentication" in str(e).lower() or "api" in str(e).lower():
                logger.error("All test cases failed due to API errors")
                sys.exit(EXIT_API_ERROR)
            else:
                logger.error("Evaluation failed")
                sys.exit(EXIT_CONFIG_ERROR)

        # AICODE-NOTE: Step 5 - Generate summary reports
        logger.info("Generating summary reports...")
        output_dir = Path(results["output_path"])

        try:
            aggregator.generate_summary_csv(output_dir)
            aggregator.generate_summary_md(output_dir)

            # AICODE-NOTE: NEW - Generate run metadata
            metadata = TestRunMetadata(
                test_mode=args.test_mode,
                prompt_version=prompt_version,
                prompt_hash=prompt_hash,
                generation_model_id=config.generation_model_id,
                judge_model_id=config.judge_model_id,
                embedding_model=config.embedding_model,
                timestamp=datetime.now(),
                run_id=output_dir.name  # Use directory name as run_id
            )

            generate_run_metadata_md(output_dir, metadata, results)
            update_runs_comparison_md(Path("eval_results"), metadata, results)

        except OSError as e:
            logger.error(f"Filesystem error writing summary: {e}")
            sys.exit(EXIT_FILESYSTEM_ERROR)
        except Exception as e:
            logger.exception(f"Error generating summary: {e}")
            sys.exit(EXIT_CONFIG_ERROR)

        # AICODE-NOTE: Step 6 - Print final summary
        print("\n" + "=" * 60)
        print("Evaluation complete!")
        print("=" * 60)
        print(f"  Test cases processed: {results['successful_cases']}/{results['total_cases']}")

        # AICODE-NOTE: Load and display aggregate metrics
        try:
            summary = aggregator.aggregate_results(output_dir)

            if "cosine_similarity" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["cosine_similarity"]
                print(f"  Mean cosine similarity: {val:.3f}")

            if "bert_f1" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["bert_f1"]
                print(f"  Mean BERTScore F1: {val:.3f}")

            if "content_score" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["content_score"]
                print(f"  Mean content score: {val:.1f}/5.0")

            if "style_score" in summary["mean_metrics"]:
                val = summary["mean_metrics"]["style_score"]
                print(f"  Mean style score: {val:.1f}/5.0")

        except Exception as e:
            logger.warning(f"Could not compute aggregate metrics: {e}")

        print()
        print(f"Results saved to: {output_dir}")
        print(f"Summary CSV: {output_dir / '_SUMMARY.csv'}")
        print(f"Summary MD: {output_dir / '_SUMMARY.md'}")
        print("=" * 60)

        # AICODE-NOTE: Check if any cases failed
        if results["failed_cases"] > 0:
            logger.warning(f"{results['failed_cases']} cases failed (see logs)")
            # AICODE-NOTE: Don't exit with error if only some cases failed
            # Exit with success if at least some cases succeeded

        logger.success("Evaluation completed successfully")
        sys.exit(EXIT_SUCCESS)

    except KeyboardInterrupt:
        logger.warning("Evaluation interrupted by user")
        sys.exit(EXIT_CONFIG_ERROR)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(EXIT_CONFIG_ERROR)


if __name__ == "__main__":
    main()
