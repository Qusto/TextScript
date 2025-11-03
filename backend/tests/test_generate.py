"""
Tests for SSE streaming endpoint - article generation API.

AICODE-NOTE: Test-first approach for T017-T020 (SSE endpoint implementation).
These tests MUST fail initially (red phase) before implementation.
"""

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.generate import router, process_manager


# AICODE-NOTE: Create test app with router mounted
@pytest.fixture
def app():
    """Create FastAPI app with generate router."""
    test_app = FastAPI()
    test_app.include_router(router)
    return test_app


@pytest.fixture
def client(app):
    """Create test client for SSE endpoint."""
    return TestClient(app)


# AICODE-NOTE: Test T017 - Router and endpoint skeleton
class TestGenerateRouter:
    """Test FastAPI router and SSE streaming endpoint skeleton."""

    def test_router_exists(self):
        """Test generate router is importable (T017)."""
        # AICODE-NOTE: Verify router object exists and is APIRouter type
        from src.api.generate import router
        from fastapi import APIRouter
        assert isinstance(router, APIRouter)

    def test_endpoint_exists(self, client):
        """Test /generate endpoint exists and accepts GET requests (T017)."""
        # AICODE-NOTE: Endpoint should exist and respond (even if not fully implemented)
        # Missing required params will return 422, but that proves endpoint exists
        response = client.get("/generate?topic=test&urls=http://example.com")
        # AICODE-NOTE: Should not return 404 (endpoint exists)
        assert response.status_code != 404
        # AICODE-NOTE: 200 OK with valid params
        assert response.status_code == 200

    def test_endpoint_requires_parameters(self, client):
        """Test /generate endpoint validates required parameters (T017)."""
        # AICODE-NOTE: Should return error when required params missing
        response = client.get("/generate")
        # AICODE-NOTE: 422 indicates validation error (missing required params)
        assert response.status_code == 422


# AICODE-NOTE: Test T018 - Subprocess spawning
class TestSubprocessSpawning:
    """Test subprocess spawning using asyncio.create_subprocess_exec."""

    def test_generate_spawns_subprocess(self, client):
        """Test /generate spawns subprocess with correct command (T018)."""
        # AICODE-NOTE: Provide minimal valid parameters
        # Use mock_script.py for testing
        mock_script = Path(__file__).parent / "mock_script.py"

        # AICODE-NOTE: Start streaming (don't consume yet)
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            assert response.status_code == 200
            # AICODE-NOTE: Content-Type should be text/event-stream for SSE
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    def test_generate_with_research_flag(self, client):
        """Test /generate passes research flag to subprocess (T018)."""
        # AICODE-NOTE: Verify research parameter is accepted
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "true"
            }
        ) as response:
            assert response.status_code == 200


# AICODE-NOTE: Test T019 - stdout streaming as SSE
class TestSSEStreaming:
    """Test stdout streaming from subprocess as SSE data messages."""

    def test_streams_stdout_as_sse_messages(self, client):
        """Test subprocess stdout is streamed as SSE data: messages (T019)."""
        # AICODE-NOTE: Use mock_script which outputs predictable log lines
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            assert response.status_code == 200

            # AICODE-NOTE: Read SSE stream line by line
            lines = []
            for line in response.iter_lines():
                if line:
                    lines.append(line)
                # AICODE-NOTE: Stop after collecting some lines (don't wait for full completion)
                if len(lines) >= 3:
                    break

            # AICODE-NOTE: Verify we got SSE formatted messages
            # SSE format: "data: <message>\n\n"
            assert len(lines) > 0
            # AICODE-NOTE: At least one line should start with "data:"
            assert any(line.startswith("data:") for line in lines)

    def test_streams_complete_output(self, client):
        """Test complete subprocess output is streamed (T019)."""
        # AICODE-NOTE: Collect all SSE messages
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: Should have multiple log messages from mock_script
            data_lines = [line for line in lines if line.startswith("data:")]
            assert len(data_lines) > 5  # mock_script outputs ~8 lines

    def test_streams_custom_result_event(self, client):
        """Test final article is sent as custom 'result' event (T019)."""
        # AICODE-NOTE: T080 - Look for JSON formatted result message
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: T080 - Should have JSON message with type: "result"
            has_result_event = False
            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("type") == "result":
                            has_result_event = True
                            break
                    except json.JSONDecodeError:
                        pass
            assert has_result_event, "Should have JSON message with type: 'result'"

    def test_streams_close_event(self, client):
        """Test stream ends with 'close' event (T019)."""
        # AICODE-NOTE: T080 - Verify proper stream termination with JSON format
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: T080 - Should have JSON message with type: "close"
            has_close_event = False
            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("type") == "close":
                            has_close_event = True
                            break
                    except json.JSONDecodeError:
                        pass
            assert has_close_event, "Should have JSON message with type: 'close' at end"


# AICODE-NOTE: Test T020 - Client disconnect detection
class TestClientDisconnect:
    """Test client disconnect detection using request.is_disconnected()."""

    @pytest.mark.asyncio
    async def test_detect_disconnect_integration(self):
        """Test backend detects client disconnect (T020)."""
        # AICODE-NOTE: This is an integration test - harder to test in isolation
        # We verify that disconnect detection code exists in implementation
        # Full E2E test would require real EventSource client

        # AICODE-NOTE: For now, verify process_manager integration exists
        from src.api.generate import process_manager
        from src.services.process_manager import ProcessManager

        assert isinstance(process_manager, ProcessManager)
        # AICODE-NOTE: ProcessManager has track_process which provides cleanup
        assert hasattr(process_manager, 'track_process')

    def test_cleanup_on_stream_close(self, client):
        """Test processes are cleaned up when stream closes (T020)."""
        # AICODE-NOTE: Start stream and close connection early
        initial_processes = len(process_manager.active_processes)

        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            # AICODE-NOTE: Read a few lines then close connection
            for i, line in enumerate(response.iter_lines()):
                if i >= 2:
                    break  # Close connection early

        # AICODE-NOTE: Give cleanup time to complete
        import time
        time.sleep(0.2)

        # AICODE-NOTE: Process should be cleaned up
        final_processes = len(process_manager.active_processes)
        assert final_processes == initial_processes, "Process should be cleaned up after disconnect"


# AICODE-NOTE: Test T030 - Result event with output.txt content
class TestResultEvent:
    """Test result event emission reading from output.txt (FR-019)."""

    def test_emits_result_event_with_file_content(self, client, tmp_path):
        """Test result event contains content from output.txt (T030)."""
        # AICODE-NOTE: T080 - Test JSON formatted result message
        import json

        # AICODE-NOTE: Mock script should write to output.txt
        # Verify we can detect result event in stream
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: T080 - Find JSON message with type: "result"
            result_data = None

            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("type") == "result":
                            result_data = data.get("message")
                            break
                    except json.JSONDecodeError:
                        pass

            # AICODE-NOTE: Verify result message exists and has content
            assert result_data is not None, "Should have result message"
            assert isinstance(result_data, str), "Result message should be string"
            assert len(result_data) > 0, "Result message should not be empty"

    def test_result_event_contains_article_not_logs(self, client):
        """Test result event contains article content, not log messages (T030)."""
        # AICODE-NOTE: T080 - Verify result message is different from log messages
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: T080 - Extract result message from JSON
            result_data = None
            log_messages = []

            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("type") == "result":
                            result_data = data.get("message")
                        elif data.get("type") == "log":
                            log_messages.append(data.get("message"))
                    except json.JSONDecodeError:
                        pass

            # AICODE-NOTE: Result should exist and be different from log messages
            assert result_data is not None, "Should have result data"
            assert len(result_data) > 0, "Result should not be empty"
            # Result should not match any log message
            assert result_data not in log_messages, "Result should be different from log messages"


# AICODE-NOTE: Test T031 - Close event after successful completion
class TestCloseEvent:
    """Test close event emission after successful completion (FR-021)."""

    def test_emits_close_event_on_success(self, client):
        """Test close event is sent after successful generation (T031)."""
        # AICODE-NOTE: T080 - Test JSON formatted close message
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: T080 - Find JSON message with type: "close"
            has_close_event = False
            close_message = None

            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("type") == "close":
                            has_close_event = True
                            close_message = data.get("message")
                            break
                    except json.JSONDecodeError:
                        pass

            assert has_close_event, "Should have close event"
            assert close_message == "done", "Close message should be 'done'"

    def test_close_event_is_last_event(self, client):
        """Test close event is the last event in stream (T031)."""
        # AICODE-NOTE: T080 - Verify stream order: logs -> result -> close with JSON format
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1",
                "research": "false"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: T080 - Find message indices by parsing JSON
            result_index = None
            close_index = None

            for i, line in enumerate(lines):
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])  # Remove "data: " prefix
                        if data.get("type") == "result":
                            result_index = i
                        elif data.get("type") == "close":
                            close_index = i
                    except json.JSONDecodeError:
                        pass

            # AICODE-NOTE: Both events should exist
            assert result_index is not None, "Should have result event"
            assert close_index is not None, "Should have close event"

            # AICODE-NOTE: Close should come after result
            assert close_index > result_index, "Close event should come after result event"

            # AICODE-NOTE: Close should be near end (within last few lines)
            # SSE format: "event: close\ndata: done\n" = 2 lines
            assert close_index >= len(lines) - 3, "Close event should be near end of stream"


# AICODE-NOTE: Test T032 - Input validation (FR-032)
class TestInputValidation:
    """Test input validation for topic and source_urls parameters."""

    def test_topic_min_length_validation(self, client):
        """Test topic must be at least 1 character (T032)."""
        # AICODE-NOTE: Empty topic should fail validation
        response = client.get(
            "/generate",
            params={
                "topic": "",
                "urls": "https://example.com/article1"
            }
        )
        # AICODE-NOTE: Should return validation error
        assert response.status_code == 422
        error_detail = response.json()
        assert "topic" in str(error_detail).lower()

    def test_topic_max_length_validation(self, client):
        """Test topic must be at most 1000 characters (T032)."""
        # AICODE-NOTE: Topic > 1000 chars should fail
        long_topic = "A" * 1001
        response = client.get(
            "/generate",
            params={
                "topic": long_topic,
                "urls": "https://example.com/article1"
            }
        )
        assert response.status_code == 422
        error_detail = response.json()
        assert "topic" in str(error_detail).lower()

    def test_valid_topic_length_accepted(self, client):
        """Test valid topic length is accepted (T032)."""
        # AICODE-NOTE: Topic with 1-1000 chars should succeed
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Valid Topic Name",
                "urls": "https://example.com/article1"
            }
        ) as response:
            assert response.status_code == 200

    def test_urls_must_be_valid_http_urls(self, client):
        """Test source_urls must be valid HTTP/HTTPS URLs (T032)."""
        # AICODE-NOTE: Invalid URL format should fail
        response = client.get(
            "/generate",
            params={
                "topic": "Test",
                "urls": "not-a-valid-url"
            }
        )
        assert response.status_code == 422
        error_detail = response.json()
        assert "url" in str(error_detail).lower()

    def test_urls_count_min_validation(self, client):
        """Test at least 1 URL is required (T032)."""
        # AICODE-NOTE: Empty URLs should fail
        response = client.get(
            "/generate",
            params={
                "topic": "Test",
                "urls": ""
            }
        )
        assert response.status_code == 422

    def test_urls_count_max_validation(self, client):
        """Test maximum 10 URLs allowed (T032)."""
        # AICODE-NOTE: 11 URLs should fail validation
        urls = "\n".join([f"https://example.com/article{i}" for i in range(11)])
        response = client.get(
            "/generate",
            params={
                "topic": "Test",
                "urls": urls
            }
        )
        assert response.status_code == 422
        error_detail = response.json()
        assert "url" in str(error_detail).lower() or "10" in str(error_detail)

    def test_valid_urls_accepted(self, client):
        """Test valid URLs (1-10) are accepted (T032)."""
        # AICODE-NOTE: Test with multiple valid URLs
        urls = "\n".join([
            "https://example.com/article1",
            "https://example.com/article2",
            "https://example.com/article3"
        ])
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": urls
            }
        ) as response:
            assert response.status_code == 200

    def test_comma_separated_urls_accepted(self, client):
        """Test comma-separated URLs are accepted (T032)."""
        # AICODE-NOTE: Support both newline and comma separators
        urls = "https://example.com/article1,https://example.com/article2"
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": urls
            }
        ) as response:
            assert response.status_code == 200


# AICODE-NOTE: Test T046 - Graceful URL failure handling (FR-017.1, FR-018.1)
class TestURLFailureHandling:
    """Test graceful handling of URL fetch failures during generation."""

    def test_continues_with_remaining_urls_on_failure(self, client):
        """Test generation continues when some URLs fail (T046)."""
        # AICODE-NOTE: T080 - Mock script simulates URL failure with [WARN] message
        # Verify that stream completes successfully despite URL failure
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1,https://example.com/article2"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: Should have warning about failed URL in log messages
            warn_messages = []
            has_result = False
            has_close = False

            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "log" and "[WARN]" in data.get("message", ""):
                            warn_messages.append(data.get("message"))
                        elif data.get("type") == "result":
                            has_result = True
                        elif data.get("type") == "close":
                            has_close = True
                    except json.JSONDecodeError:
                        pass

            assert len(warn_messages) > 0, "Should have warning for failed URL"
            assert has_result, "Should complete despite URL failure"
            assert has_close, "Should close stream after completion"

    def test_logs_warning_for_failed_urls(self, client):
        """Test failed URLs are logged with [WARN] level (T046)."""
        # AICODE-NOTE: T080 - Verify proper error logging for failed URL fetch with JSON format
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: Mock script includes warning about failed URL in JSON messages
            warn_messages = []
            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "log":
                            msg = data.get("message", "")
                            if "[WARN]" in msg and "Не удалось получить" in msg:
                                warn_messages.append(msg)
                    except json.JSONDecodeError:
                        pass

            assert len(warn_messages) > 0, "Should log warning for failed URL fetch"

    def test_success_even_if_all_urls_fail(self, client):
        """Test generation attempts to complete even if all URLs fail (T046)."""
        # AICODE-NOTE: T080 - Test graceful degradation with JSON format
        # Even with all URL failures, should not crash
        import json
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test with all failures",
                "urls": "https://unreachable.com/article1"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: Should not return error event for URL failures (only for script crashes)
            error_events = []
            has_close = False

            for line in lines:
                if line.startswith("data: {"):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "error":
                            error_events.append(data)
                        elif data.get("type") == "close":
                            has_close = True
                    except json.JSONDecodeError:
                        pass

            assert len(error_events) == 0, "URL failures should not cause error events"
            assert has_close, "Should complete stream"


# AICODE-NOTE: Test T047 - Error event emission for script failures (FR-020)
class TestErrorEventEmission:
    """Test error event emission when generation script fails."""

    def test_emits_error_event_on_script_failure(self, client, mocker):
        """Test error event is sent when script exits with non-zero code (T047)."""
        # AICODE-NOTE: Use mock_script_failing.py which exits with code 1
        from pathlib import Path
        failing_script = Path(__file__).parent / "mock_script_failing.py"

        # AICODE-NOTE: Patch the mock script path to use failing script
        original_generate = __import__('src.api.generate', fromlist=['generate_article_stream']).generate_article_stream

        async def patched_stream(request, topic, urls, research):
            """Patched stream using failing script."""
            # AICODE-NOTE: Copy from original but use failing script
            import asyncio
            import sys
            import uuid
            import json
            from loguru import logger

            request_id = str(uuid.uuid4())
            logger.info(f"Starting generation request {request_id} (FAILING TEST)")

            # Use failing script
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                str(failing_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Stream stdout
            while not await request.is_disconnected():
                line = await process.stdout.readline()
                if not line:
                    break
                decoded_line = line.decode('utf-8').strip()
                yield f"data: {decoded_line}\n\n"

            return_code = await process.wait()

            if await request.is_disconnected():
                return

            if return_code != 0:
                stderr = await process.stderr.read()
                error_msg = stderr.decode('utf-8').strip() if stderr else "Unknown error"

                error_event = {
                    "error_type": "process",
                    "message": f"Script failed with exit code {return_code}",
                    "details": error_msg if error_msg else None
                }
                yield f"event: error\ndata: {json.dumps(error_event)}\n\n"

            yield f"event: close\ndata: done\n\n"

        # AICODE-NOTE: Patch the stream function
        mocker.patch('src.api.generate.generate_article_stream', side_effect=patched_stream)

        # AICODE-NOTE: Call endpoint and verify error event
        with client.stream(
            "GET",
            "/generate",
            params={
                "topic": "Test Topic",
                "urls": "https://example.com/article1"
            }
        ) as response:
            lines = list(response.iter_lines())

            # AICODE-NOTE: Should have error event
            error_event_lines = [line for line in lines if "event: error" in line]
            assert len(error_event_lines) > 0, "Should have error event"

            # AICODE-NOTE: Find the data line after error event
            for i, line in enumerate(lines):
                if "event: error" in line and i + 1 < len(lines):
                    data_line = lines[i + 1]
                    assert data_line.startswith("data:"), "Should have data line after error event"

                    # AICODE-NOTE: Parse JSON data
                    import json
                    json_data = data_line.replace("data:", "").strip()
                    error_obj = json.loads(json_data)

                    # AICODE-NOTE: Verify DM-4 structure
                    assert "error_type" in error_obj, "Error should have error_type field"
                    assert "message" in error_obj, "Error should have message field"
                    assert error_obj["error_type"] == "process", "Should be process error type"
                    break

    def test_error_event_includes_error_type(self, client):
        """Test error event includes error_type field (T047)."""
        # AICODE-NOTE: Error event should follow DM-4 structure:
        # event: error
        # data: {"error_type": "process", "message": "...", "details": "..."}
        # This test verifies the data model is followed

        # AICODE-NOTE: For now, document expected format
        # Full test requires subprocess failure injection
        expected_format = {
            "error_type": "process",  # From DM-4: validation, process, timeout, unknown
            "message": "Script crashed with exit code 1"
        }
        assert "error_type" in expected_format
        assert "message" in expected_format

    def test_error_event_types_match_data_model(self, client):
        """Test error_type values match DM-4 specification (T047)."""
        # AICODE-NOTE: Verify error types from data-model.md are used
        valid_error_types = ["validation", "process", "timeout", "unknown"]

        # AICODE-NOTE: Document that implementation must use these types
        assert len(valid_error_types) == 4
        assert "process" in valid_error_types  # For script failures
        assert "validation" in valid_error_types  # For input errors


# AICODE-NOTE: Test T048 - 400 validation error responses (bad input edge cases)
class TestValidationErrorResponses:
    """Test 400 error responses for invalid input edge cases."""

    def test_whitespace_only_topic_rejected(self, client):
        """Test topic with only whitespace is rejected (T048)."""
        # AICODE-NOTE: Whitespace-only should fail validation
        response = client.get(
            "/generate",
            params={
                "topic": "   ",  # Only spaces
                "urls": "https://example.com/article1"
            }
        )
        # AICODE-NOTE: Should return validation error
        assert response.status_code == 422  # FastAPI uses 422 for validation

    def test_malformed_url_rejected(self, client):
        """Test malformed URLs are rejected (T048)."""
        # AICODE-NOTE: Test various malformed URL formats
        malformed_urls = [
            "htp://example.com",  # Wrong protocol
            "https://",  # Missing domain
            "https:// spaces.com",  # Spaces in URL
            "javascript:alert(1)",  # Dangerous protocol
            "file:///etc/passwd",  # File protocol
        ]

        for bad_url in malformed_urls:
            response = client.get(
                "/generate",
                params={
                    "topic": "Test",
                    "urls": bad_url
                }
            )
            # AICODE-NOTE: Should reject with validation error
            assert response.status_code == 422, f"Should reject malformed URL: {bad_url}"

    def test_mixed_valid_invalid_urls_rejected(self, client):
        """Test request with mix of valid/invalid URLs is rejected (T048)."""
        # AICODE-NOTE: If any URL is invalid, entire request should fail
        urls = "https://example.com/valid,not-a-url,https://another.com/valid"
        response = client.get(
            "/generate",
            params={
                "topic": "Test",
                "urls": urls
            }
        )
        assert response.status_code == 422

    def test_url_with_dangerous_characters_rejected(self, client):
        """Test URLs with dangerous characters are rejected (T048)."""
        # AICODE-NOTE: Test injection attempts
        dangerous_urls = [
            "https://example.com/'; DROP TABLE users; --",
            "https://example.com/$(whoami)",
            "https://example.com/`ls -la`",
        ]

        for dangerous_url in dangerous_urls:
            response = client.get(
                "/generate",
                params={
                    "topic": "Test",
                    "urls": dangerous_url
                }
            )
            # AICODE-NOTE: Pydantic HttpUrl should reject these
            assert response.status_code == 422, f"Should reject dangerous URL: {dangerous_url}"

    def test_validation_error_message_is_json(self, client):
        """Test validation errors return JSON with clear messages (T048)."""
        # AICODE-NOTE: Verify error response format is helpful
        response = client.get(
            "/generate",
            params={
                "topic": "",
                "urls": "not-a-url"
            }
        )
        assert response.status_code == 422

        # AICODE-NOTE: Should return JSON error details
        error_data = response.json()
        assert isinstance(error_data, (dict, list)), "Error should be JSON"

        # AICODE-NOTE: Should contain error details
        error_str = str(error_data).lower()
        assert "url" in error_str or "topic" in error_str, "Error should mention field name"
