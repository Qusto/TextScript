#!/usr/bin/env python3
# AICODE-NOTE: T049 [US1] CLI script implementing cli-dataset-builder.md contract
# AICODE-NOTE: T050 - Argparse with --config and --verbose flags
# AICODE-NOTE: T051 - Config loading with YAML parsing and Pydantic validation
# AICODE-NOTE: T052 - Main function with DatasetBuilder execution
# AICODE-NOTE: T053 - Progress indicators using tqdm (handled by builder)
# AICODE-NOTE: T054 - Final summary output

"""CLI script for generating evaluation dataset from text corpus.

Usage:
    python prepare_dataset.py [--config PATH] [--verbose]

Examples:
    python prepare_dataset.py
    python prepare_dataset.py --config custom_config.yml
    python prepare_dataset.py -v
    python prepare_dataset.py --config my_config.yml -v

Exit Codes:
    0: Success - dataset generated without errors
    1: Configuration error (invalid config file, missing required fields)
    2: Input error (corpus not found, insufficient texts per author)
    3: LLM API error (authentication failed, quota exceeded)
    4: File system error (cannot write to output directory)
"""

import argparse
import sys
from pathlib import Path

import yaml
from loguru import logger

from src.dataset_builder.builder import DatasetBuilder
from src.dataset_builder.config import DatasetConfig
from src.shared.llm_client import LLMClient


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: If True, enable DEBUG level logging

    AICODE-NOTE: Configures loguru for CLI output
    AICODE-NOTE: Normal mode: INFO and above
    AICODE-NOTE: Verbose mode: DEBUG and above
    """
    # AICODE-NOTE: Remove default handler
    logger.remove()

    # AICODE-NOTE: Add console handler with appropriate level
    log_level = "DEBUG" if verbose else "INFO"

    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<level>{message}</level>",
        level=log_level,
        colorize=True
    )

    if verbose:
        logger.debug("Verbose logging enabled")


def load_config(config_path: str) -> DatasetConfig:
    """Load and validate configuration from YAML file.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        Validated DatasetConfig

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config validation fails

    AICODE-NOTE: T051 - YAML parsing and Pydantic validation
    AICODE-NOTE: Exit code 1 on config error
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    logger.info(f"Loading configuration from {config_path}")

    # AICODE-NOTE: Parse YAML
    try:
        with open(config_file) as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e}") from e

    # AICODE-NOTE: Validate with Pydantic
    try:
        config = DatasetConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}") from e

    logger.debug(
        f"Config loaded: corpus={config.corpus_path}, "
        f"output={config.output_path}, "
        f"min_texts={config.min_texts_per_author}, "
        f"m={config.m_style_texts}, k={config.k_test_cases}"
    )

    return config


def main() -> int:
    """Main CLI entry point.

    Returns:
        Exit code (0=success, 1=config error, 2=corpus error, 3=API error, 4=file system error)

    AICODE-NOTE: T052 - Main function with error handling
    AICODE-NOTE: Returns appropriate exit codes per contract
    """
    # AICODE-NOTE: T050 - Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Generate evaluation dataset from text corpus",
        epilog="For more information, see contracts/cli-dataset-builder.md"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="./configs/dataset_config.yml",
        help="Path to YAML configuration file (default: ./configs/dataset_config.yml)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)"
    )

    args = parser.parse_args()

    # AICODE-NOTE: Setup logging
    setup_logging(verbose=args.verbose)

    try:
        # AICODE-NOTE: T051 - Load and validate configuration
        try:
            config = load_config(args.config)
        except FileNotFoundError as e:
            logger.error(f"Configuration error: {e}")
            return 1  # Exit code 1: Configuration error
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            return 1  # Exit code 1: Configuration error

        # AICODE-NOTE: Initialize LLM client
        try:
            llm_client = LLMClient(
                timeout=120,
                max_retries=3
            )
        except ValueError as e:
            logger.error(f"LLM API error: {e}")
            return 3  # Exit code 3: API error

        # AICODE-NOTE: T052 - Create DatasetBuilder and generate dataset
        try:
            builder = DatasetBuilder(config=config, llm_client=llm_client)
        except Exception as e:
            logger.error(f"Builder initialization failed: {e}")
            return 1  # Exit code 1: Configuration error

        # AICODE-NOTE: Generate dataset
        try:
            builder.generate_dataset()
        except FileNotFoundError as e:
            logger.error(f"Input error: {e}")
            return 2  # Exit code 2: Corpus not found
        except ValueError as e:
            logger.error(f"Input error: {e}")
            return 2  # Exit code 2: Insufficient texts
        except OSError as e:
            logger.error(f"File system error: {e}")
            return 4  # Exit code 4: Cannot write to output
        except RuntimeError as e:
            # AICODE-NOTE: LLM API errors from builder
            logger.error(f"LLM API error: {e}")
            return 3  # Exit code 3: API error
        except Exception as e:
            logger.exception(f"Unexpected error during dataset generation: {e}")
            return 1  # Exit code 1: General error

        # AICODE-NOTE: T054 - Success summary already logged by builder
        logger.info("Dataset generation completed successfully")
        return 0  # Exit code 0: Success

    except KeyboardInterrupt:
        logger.warning("Dataset generation interrupted by user")
        return 130  # Standard exit code for SIGINT
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1  # Exit code 1: General error


if __name__ == "__main__":
    sys.exit(main())
