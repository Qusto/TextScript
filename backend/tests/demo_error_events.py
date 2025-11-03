#!/usr/bin/env python3
"""
Demonstration of error event formats (T047).

AICODE-NOTE: This script shows example error events following DM-4 data model.
Run this to see what frontend will receive when errors occur.
"""

import json

# AICODE-NOTE: Example 1 - Process error (script failure)
process_error = {
    "error_type": "process",  # Script execution failed
    "message": "Script failed with exit code 1",
    "details": "ValueError: All style URLs failed to fetch"
}

# AICODE-NOTE: Example 2 - Validation error (invalid input)
validation_error = {
    "error_type": "validation",
    "message": "Invalid URL format",
    "details": "URLs cannot contain shell metacharacters: `, $, |, <, >, \\, {, }"
}

# AICODE-NOTE: Example 3 - Timeout error (generation too long)
timeout_error = {
    "error_type": "timeout",
    "message": "Generation exceeded maximum time limit",
    "details": "Process timed out after 300 seconds"
}

# AICODE-NOTE: Example 4 - Unknown error (unexpected exception)
unknown_error = {
    "error_type": "unknown",
    "message": "Unexpected error during generation",
    "details": "KeyError: 'missing_config_key'"
}

# AICODE-NOTE: Print SSE format for each error type
print("=== Error Event Examples (SSE Format) ===\n")

for i, error in enumerate([process_error, validation_error, timeout_error, unknown_error], 1):
    print(f"Example {i}: {error['error_type']} error")
    print(f"event: error")
    print(f"data: {json.dumps(error)}")
    print()  # SSE requires double newline
    print()

# AICODE-NOTE: Show complete SSE stream with error
print("=== Complete SSE Stream Example (with error) ===\n")
print("data: [INFO] Starting article generation...")
print()
print("data: [INFO] Fetching style URLs...")
print()
print("data: [ERROR] Failed to fetch all URLs")
print()
print("event: error")
print(f"data: {json.dumps(process_error)}")
print()
print("event: close")
print("data: done")
print()
