#!/usr/bin/env python3
"""
Mock failing script for testing error event emission.

AICODE-NOTE: T047 - This script exits with non-zero code to test error handling.
"""

import sys

print("[INFO] Starting article generation...")
print("[ERROR] Critical error: All source URLs failed to fetch")
sys.exit(1)  # Non-zero exit code indicates failure
