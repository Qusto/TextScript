# AICODE-NOTE: T018 - Dataset builder package
# AICODE-NOTE: Responsible for generating evaluation datasets from text corpora
# AICODE-NOTE: Main components: builder.py (orchestrator), neutralizer.py (LLM topic extraction)

"""Dataset builder for StyleGuard Eval Harness.

This module generates structured test datasets from raw text corpora by:
1. Scanning corpus directories for author texts
2. Splitting texts into style references and test cases
3. Extracting neutralized topics from test cases using LLM
4. Saving structured dataset for evaluation
"""

__version__ = "1.0.0"
