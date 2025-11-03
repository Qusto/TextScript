#!/usr/bin/env python3
"""
Mock article generation script that writes to output.txt.

AICODE-NOTE: This is a test script for T030 that simulates the real article generator
by writing the final article to output.txt while printing logs to stdout.
"""

import sys
import time
import signal
from pathlib import Path


def handle_sigterm(signum, frame):
    """Handle SIGTERM gracefully."""
    # AICODE-NOTE: Print to stderr to avoid polluting stdout stream
    print("[INFO] Received SIGTERM, shutting down gracefully...", file=sys.stderr)
    sys.exit(0)


def main():
    """Simulate article generation with progressive log output and file output."""
    # AICODE-NOTE: Register SIGTERM handler for graceful shutdown testing
    signal.signal(signal.SIGTERM, handle_sigterm)

    print("[INFO] Starting article generation...")
    time.sleep(0.1)

    print("[INFO] Fetching style URLs...")
    time.sleep(0.1)

    print("[INFO] Successfully fetched: https://example.com/article1")
    time.sleep(0.1)

    print("[INFO] Analyzing style patterns...")
    time.sleep(0.1)

    print("[INFO] Generating article...")
    time.sleep(0.1)

    # AICODE-NOTE: Write final article to output.txt (T030 requirement)
    output_file = Path("output.txt")
    article_content = """# The Future of AI in Software Development

## Introduction

Artificial Intelligence is transforming how we write and maintain code.

## Key Developments

- Automated code generation
- Intelligent code review
- Predictive bug detection

## Conclusion

The future is bright for AI-assisted development."""

    output_file.write_text(article_content)
    print("[INFO] Article written to output.txt")

    print("[INFO] Article generation complete!")
    time.sleep(0.1)


if __name__ == "__main__":
    main()
