"""Integration tests for API endpoints."""

import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import shutil
from pathlib import Path


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_ok(self, client):
        """Should return status ok."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_method_not_allowed(self, client):
        """Should return 405 for POST request."""
        response = client.post("/health")

        assert response.status_code == 405


class TestWorkflowStartEndpoint:
    """Tests for the /workflow/start endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_workflow(self, client):
        """Should start a new workflow session."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            response = client.post("/workflow/start?session_id=test-123")

            assert response.status_code == 200
            data = response.json()
            assert "state" in data
            assert data["state"]["session_id"] == "test-123"
            assert data["state"]["phase"] == "weights"


class TestWorkflowStateEndpoint:
    """Tests for the /workflow/state endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_get_existing_state(self, client):
        """Should return state for existing session."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Create session first
            client.post("/workflow/start?session_id=test-123")

            # Get state
            response = client.get("/workflow/state/test-123")

            assert response.status_code == 200
            assert response.json()["state"]["session_id"] == "test-123"

    def test_get_nonexistent_state(self, client):
        """Should return 404 for nonexistent session."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            response = client.get("/workflow/state/nonexistent")

            assert response.status_code == 404


class TestWorkflowResetEndpoint:
    """Tests for the /workflow/reset endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_reset_workflow(self, client):
        """Should reset workflow to initial state."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Create session
            client.post("/workflow/start?session_id=test-123")

            # Reset
            response = client.post("/workflow/reset/test-123")

            assert response.status_code == 200
            assert response.json()["state"]["phase"] == "weights"


class TestPhase1WeightsEndpoint:
    """Tests for the /workflow/phase1/weights endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_weights(self, client):
        """Should set weights and advance to tasks phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            response = client.post(
                "/workflow/phase1/weights",
                json={
                    "session_id": "test-123",
                    "weights": {"personal": 1.0, "health": 2.0, "work": 1.5},
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["state"]["phase"] == "tasks"
            assert data["state"]["weights"]["health"] == 2.0

    def test_set_weights_creates_session(self, client):
        """Should create session if it doesn't exist."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            response = client.post(
                "/workflow/phase1/weights",
                json={
                    "session_id": "new-session",
                    "weights": {"personal": 1.0, "health": 1.0, "work": 1.0},
                },
            )

            assert response.status_code == 200
            assert response.json()["state"]["session_id"] == "new-session"

    def test_set_weights_missing_fields(self, client):
        """Should return 422 for missing fields."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            response = client.post(
                "/workflow/phase1/weights",
                json={"session_id": "test"},
            )

            assert response.status_code == 422


class TestPhase2TasksEndpoint:
    """Tests for the /workflow/phase2/tasks endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_submit_tasks(self, client):
        """Should categorize tasks and advance to constraints phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Setup: advance to TASKS phase
            client.post(
                "/workflow/phase1/weights",
                json={
                    "session_id": "test",
                    "weights": {"personal": 1.0, "health": 1.0, "work": 1.0},
                },
            )

            # Mock categoriser
            with patch(
                "src.orchestrator.categorise_tasks",
                new_callable=AsyncMock,
                return_value=[{"description": "Go to gym", "category": "Health"}],
            ):
                response = client.post(
                    "/workflow/phase2/tasks",
                    json={"session_id": "test", "tasks": ["Go to gym"]},
                )

            assert response.status_code == 200
            assert response.json()["state"]["phase"] == "constraints"

    def test_submit_tasks_wrong_phase(self, client):
        """Should return 400 if not in TASKS phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Create session but don't advance
            client.post("/workflow/start?session_id=test")

            response = client.post(
                "/workflow/phase2/tasks",
                json={"session_id": "test", "tasks": ["Task"]},
            )

            assert response.status_code == 400


class TestPhase3ConstraintsEndpoint:
    """Tests for the /workflow/phase3/constraints endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_set_constraints(self, client):
        """Should set constraints and advance to schedule phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Setup: advance to CONSTRAINTS phase
            client.post(
                "/workflow/phase1/weights",
                json={
                    "session_id": "test",
                    "weights": {"personal": 1.0, "health": 1.0, "work": 1.0},
                },
            )
            with patch(
                "src.orchestrator.categorise_tasks",
                new_callable=AsyncMock,
                return_value=[],
            ):
                client.post(
                    "/workflow/phase2/tasks",
                    json={"session_id": "test", "tasks": []},
                )

            response = client.post(
                "/workflow/phase3/constraints",
                json={
                    "session_id": "test",
                    "tasks": [
                        {
                            "id": "1",
                            "description": "Task",
                            "category": "Work",
                            "duration_minutes": 30,
                        }
                    ],
                    "window_start": "08:00",
                    "window_end": "18:00",
                },
            )

            assert response.status_code == 200
            assert response.json()["state"]["phase"] == "schedule"


class TestPhase4ScheduleEndpoint:
    """Tests for the /workflow/phase4/schedule endpoint."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_generate_schedule(self, client):
        """Should generate schedule and complete workflow."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Setup: advance to SCHEDULE phase
            client.post(
                "/workflow/phase1/weights",
                json={
                    "session_id": "test",
                    "weights": {"personal": 1.0, "health": 1.0, "work": 1.0},
                },
            )
            with patch(
                "src.orchestrator.categorise_tasks",
                new_callable=AsyncMock,
                return_value=[],
            ):
                client.post(
                    "/workflow/phase2/tasks",
                    json={"session_id": "test", "tasks": []},
                )
            client.post(
                "/workflow/phase3/constraints",
                json={
                    "session_id": "test",
                    "tasks": [
                        {
                            "id": "1",
                            "description": "Task",
                            "category": "Work",
                            "duration_minutes": 30,
                        }
                    ],
                    "window_start": "08:00",
                    "window_end": "18:00",
                },
            )

            response = client.post(
                "/workflow/phase4/schedule",
                json={"session_id": "test"},
            )

            assert response.status_code == 200
            assert response.json()["state"]["phase"] == "complete"
            assert response.json()["state"]["selected_algorithm"] == "greedy"


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""

    def test_cors_allows_localhost_origin(self, client):
        """Should allow requests from localhost:5173."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )

        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:5173"
        )

    def test_cors_preflight_allows_post(self, client):
        """Should allow POST method in preflight."""
        response = client.options(
            "/workflow/start",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )

        assert "POST" in response.headers.get("access-control-allow-methods", "")
