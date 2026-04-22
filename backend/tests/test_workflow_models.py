"""Unit tests for workflow models."""

import pytest
from pydantic import ValidationError

from src.models.workflow import (
    WorkflowPhase,
    WorkflowState,
    SetWeightsRequest,
    SubmitTasksRequest,
    SetConstraintsRequest,
    GenerateScheduleRequest,
    WorkflowResponse,
)
from src.models.task import UtilityWeights, TaskWithConstraints, ScheduledBlock


class TestWorkflowPhase:
    """Tests for WorkflowPhase enum."""

    def test_all_phases_exist(self):
        """Should have all required workflow phases."""
        assert WorkflowPhase.WEIGHTS == "weights"
        assert WorkflowPhase.TASKS == "tasks"
        assert WorkflowPhase.CONSTRAINTS == "constraints"
        assert WorkflowPhase.SCHEDULE == "schedule"
        assert WorkflowPhase.COMPLETE == "complete"

    def test_phase_count(self):
        """Should have exactly 5 phases."""
        assert len(WorkflowPhase) == 5


class TestWorkflowState:
    """Tests for WorkflowState model."""

    def test_minimal_state(self):
        """Should create state with just session_id."""
        state = WorkflowState(session_id="test-123")
        assert state.session_id == "test-123"
        assert state.phase == WorkflowPhase.WEIGHTS

    def test_default_phase_is_weights(self):
        """Should default to WEIGHTS phase."""
        state = WorkflowState(session_id="test")
        assert state.phase == WorkflowPhase.WEIGHTS

    def test_all_optional_fields_default_to_none(self):
        """Should have all optional fields default to None."""
        state = WorkflowState(session_id="test")
        assert state.weights is None
        assert state.raw_tasks is None
        assert state.categorised_tasks is None
        assert state.tasks_with_constraints is None
        assert state.window_start is None
        assert state.window_end is None
        assert state.selected_algorithm is None
        assert state.schedule is None

    def test_full_state(self):
        """Should create state with all fields populated."""
        weights = UtilityWeights(personal=1.0, health=2.0, work=1.5)
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Test",
                category="Work",
                duration_minutes=30,
            )
        ]
        schedule = [
            ScheduledBlock(
                task_id="1",
                description="Test",
                category="Work",
                start_time="09:00",
                end_time="09:30",
            )
        ]

        state = WorkflowState(
            session_id="test",
            phase=WorkflowPhase.COMPLETE,
            weights=weights,
            raw_tasks=["Test task"],
            categorised_tasks=[{"description": "Test", "category": "Work"}],
            tasks_with_constraints=tasks,
            window_start="08:00",
            window_end="18:00",
            selected_algorithm="greedy",
            schedule=schedule,
        )

        assert state.phase == WorkflowPhase.COMPLETE
        assert state.weights.health == 2.0
        assert state.raw_tasks == ["Test task"]
        assert state.selected_algorithm == "greedy"
        assert len(state.schedule) == 1

    def test_missing_session_id_raises(self):
        """Should raise error when session_id is missing."""
        with pytest.raises(ValidationError):
            WorkflowState()


class TestSetWeightsRequest:
    """Tests for SetWeightsRequest model."""

    def test_valid_request(self):
        """Should create valid request."""
        weights = UtilityWeights(personal=1.0, health=2.0, work=1.5)
        request = SetWeightsRequest(session_id="test", weights=weights)
        assert request.session_id == "test"
        assert request.weights.health == 2.0

    def test_missing_session_id_raises(self):
        """Should raise error when session_id is missing."""
        with pytest.raises(ValidationError):
            SetWeightsRequest(weights=UtilityWeights())

    def test_missing_weights_raises(self):
        """Should raise error when weights is missing."""
        with pytest.raises(ValidationError):
            SetWeightsRequest(session_id="test")


class TestSubmitTasksRequest:
    """Tests for SubmitTasksRequest model."""

    def test_valid_request(self):
        """Should create valid request."""
        request = SubmitTasksRequest(session_id="test", tasks=["Task 1", "Task 2"])
        assert request.session_id == "test"
        assert len(request.tasks) == 2

    def test_empty_tasks_allowed(self):
        """Should allow empty tasks list."""
        request = SubmitTasksRequest(session_id="test", tasks=[])
        assert request.tasks == []


class TestSetConstraintsRequest:
    """Tests for SetConstraintsRequest model."""

    def test_valid_request(self):
        """Should create valid request."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Test",
                category="Work",
                duration_minutes=30,
            )
        ]
        request = SetConstraintsRequest(
            session_id="test",
            tasks=tasks,
            window_start="08:00",
            window_end="18:00",
        )
        assert request.session_id == "test"
        assert request.window_start == "08:00"
        assert request.window_end == "18:00"


class TestGenerateScheduleRequest:
    """Tests for GenerateScheduleRequest model."""

    def test_valid_request(self):
        """Should create valid request."""
        request = GenerateScheduleRequest(session_id="test")
        assert request.session_id == "test"


class TestWorkflowResponse:
    """Tests for WorkflowResponse model."""

    def test_valid_response(self):
        """Should create valid response."""
        state = WorkflowState(session_id="test")
        response = WorkflowResponse(state=state, message="Success")
        assert response.message == "Success"
        assert response.state.session_id == "test"
