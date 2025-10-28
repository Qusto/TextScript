#!/usr/bin/env python3
"""
Mock article generation script for testing SSE streaming.

AICODE-NOTE: This is a DUMMY script that simulates the real article generator
for testing purposes. It prints log lines with delays to simulate real processing.
"""

import sys
import time
import signal


def handle_sigterm(signum, frame):
    """Handle SIGTERM gracefully."""
    # AICODE-NOTE: Print to stderr to avoid polluting stdout stream
    print("[INFO] Received SIGTERM, shutting down gracefully...", file=sys.stderr)
    sys.exit(0)


def main():
    """Simulate article generation with progressive log output."""
    # AICODE-NOTE: Register SIGTERM handler for graceful shutdown testing
    signal.signal(signal.SIGTERM, handle_sigterm)

    print("[INFO] Starting article generation...")
    time.sleep(0.1)

    print("[INFO] Fetching style URLs...")
    time.sleep(0.1)

    print("[INFO] Successfully fetched: https://example.com/article1")
    time.sleep(0.1)

    print("[WARN] Не удалось получить URL: https://example.com/article2 (Ошибка: Таймаут)")
    time.sleep(0.1)

    print("[INFO] Analyzing style patterns...")
    time.sleep(0.1)

    print("[INFO] Generating article...")
    time.sleep(0.1)

    print("[INFO] Article generation complete!")
    time.sleep(0.1)

    # AICODE-NOTE: Final result on stdout (backend will capture this as result)
    print("This is the generated article content.")


if __name__ == "__main__":
    main()
