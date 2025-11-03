# AICODE-NOTE: T005 - StyleGuard Eval Harness package initialization
# AICODE-NOTE: This is the root package for the evaluation system
# AICODE-NOTE: Provides version metadata and top-level exports

"""
StyleGuard Eval Harness - Automated evaluation system for article generation quality.

This package provides two main CLI tools:
1. prepare_dataset.py - Generates test datasets from text corpora
2. run_eval.py - Evaluates article generation quality with multiple metrics

Key Components:
- dataset_builder: Dataset generation with LLM-based topic neutralization
- evaluator: Quality evaluation with numeric metrics and LLM judges
- shared: Common utilities (LLM client, file I/O helpers)
"""

__version__ = "1.0.0"
__author__ = "TextScript Team"
__description__ = "Automated evaluation harness for testing article generation quality"
