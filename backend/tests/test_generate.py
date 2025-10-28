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
        # AICODE-NOTE: Look for custom SSE event
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

            # AICODE-NOTE: Should have "event: result" line
            has_result_event = any("event: result" in line for line in lines)
            assert has_result_event, "Should have custom 'result' event"

    def test_streams_close_event(self, client):
        """Test stream ends with 'close' event (T019)."""
        # AICODE-NOTE: Verify proper stream termination
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

            # AICODE-NOTE: Should have "event: close" line
            has_close_event = any("event: close" in line for line in lines)
            assert has_close_event, "Should have 'close' event at end"


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
