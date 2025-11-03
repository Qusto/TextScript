# AICODE-NOTE: T021 - Evaluator package
# AICODE-NOTE: Responsible for running article generation and computing quality metrics
# AICODE-NOTE: Main components: runner.py (orchestrator), metrics/ (numeric + judge)

"""Evaluator for StyleGuard Eval Harness.

This module evaluates article generation quality by:
1. Loading test cases from dataset
2. Generating articles using Ugly Script
3. Computing numeric metrics (cosine similarity, BERTScore)
4. Computing LLM-as-Judge metrics (content, style)
5. Aggregating results into summary reports
"""

__version__ = "1.0.0"
