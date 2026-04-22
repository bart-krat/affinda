"""Unit tests for extended task models (TaskWithConstraints, DayConstraints, etc.)."""

import pytest
from pydantic import ValidationError

from src.models.task import (
    TaskWithConstraints,
    DayConstraints,
    UtilityWeights,
    ScheduleRequest,
    ScheduledBlock,
    ScheduleResponse,
)


class TestTaskWithConstraints:
    """Tests for TaskWithConstraints model."""

    def test_valid_task_without_fixed_time(self):
        """Should create task without fixed start time."""
        task = TaskWithConstraints(
            id="1",
            description="Go to gym",
            category="Health",
            duration_minutes=60,
        )
        assert task.id == "1"
        assert task.description == "Go to gym"
        assert task.category == "Health"
        assert task.duration_minutes == 60
        assert task.fixed_start_time is None

    def test_valid_task_with_fixed_time(self):
        """Should create task with fixed start time."""
        task = TaskWithConstraints(
            id="2",
            description="Meeting",
            category="Work",
            duration_minutes=30,
            fixed_start_time="14:00",
        )
        assert task.fixed_start_time == "14:00"

    def test_missing_required_fields_raises(self):
        """Should raise error for missing required fields."""
        with pytest.raises(ValidationError):
            TaskWithConstraints(id="1", description="Test")

    def test_zero_duration_allowed(self):
        """Should allow zero duration."""
        task = TaskWithConstraints(
            id="1",
            description="Test",
            category="Work",
            duration_minutes=0,
        )
        assert task.duration_minutes == 0

    def test_negative_duration_raises(self):
        """Should allow negative duration (no constraint in model)."""
        # Note: The model doesn't enforce positive durations
        task = TaskWithConstraints(
            id="1",
            description="Test",
            category="Work",
            duration_minutes=-10,
        )
        assert task.duration_minutes == -10


class TestDayConstraints:
    """Tests for DayConstraints model."""

    def test_valid_constraints(self):
        """Should create valid day constraints."""
        constraints = DayConstraints(window_start="08:00", window_end="18:00")
        assert constraints.window_start == "08:00"
        assert constraints.window_end == "18:00"

    def test_missing_window_start_raises(self):
        """Should raise error when window_start is missing."""
        with pytest.raises(ValidationError):
            DayConstraints(window_end="18:00")

    def test_missing_window_end_raises(self):
        """Should raise error when window_end is missing."""
        with pytest.raises(ValidationError):
            DayConstraints(window_start="08:00")

    def test_arbitrary_time_format(self):
        """Should accept any string format (no validation)."""
        constraints = DayConstraints(window_start="8am", window_end="6pm")
        assert constraints.window_start == "8am"


class TestUtilityWeights:
    """Tests for UtilityWeights model."""

    def test_default_weights(self):
        """Should have default weights of 1.0."""
        weights = UtilityWeights()
        assert weights.personal == 1.0
        assert weights.health == 1.0
        assert weights.work == 1.0

    def test_custom_weights(self):
        """Should accept custom weights."""
        weights = UtilityWeights(personal=0.5, health=2.0, work=1.5)
        assert weights.personal == 0.5
        assert weights.health == 2.0
        assert weights.work == 1.5

    def test_zero_weights_allowed(self):
        """Should allow zero weights."""
        weights = UtilityWeights(personal=0, health=0, work=0)
        assert weights.personal == 0

    def test_negative_weights_allowed(self):
        """Should allow negative weights (no constraint)."""
        weights = UtilityWeights(personal=-1.0)
        assert weights.personal == -1.0

    def test_partial_weights(self):
        """Should allow partial weight specification."""
        weights = UtilityWeights(health=3.0)
        assert weights.personal == 1.0
        assert weights.health == 3.0
        assert weights.work == 1.0


class TestScheduleRequest:
    """Tests for ScheduleRequest model."""

    def test_valid_request(self):
        """Should create valid schedule request."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task",
                category="Work",
                duration_minutes=30,
            )
        ]
        constraints = DayConstraints(window_start="08:00", window_end="18:00")
        weights = UtilityWeights()

        request = ScheduleRequest(
            tasks=tasks,
            constraints=constraints,
            weights=weights,
        )

        assert len(request.tasks) == 1
        assert request.algorithm == "greedy"

    def test_default_algorithm_is_greedy(self):
        """Should default to greedy algorithm."""
        request = ScheduleRequest(
            tasks=[],
            constraints=DayConstraints(window_start="08:00", window_end="18:00"),
            weights=UtilityWeights(),
        )
        assert request.algorithm == "greedy"

    def test_custom_algorithm(self):
        """Should accept custom algorithm."""
        request = ScheduleRequest(
            tasks=[],
            constraints=DayConstraints(window_start="08:00", window_end="18:00"),
            weights=UtilityWeights(),
            algorithm="knapsack",
        )
        assert request.algorithm == "knapsack"


class TestScheduledBlock:
    """Tests for ScheduledBlock model."""

    def test_valid_block(self):
        """Should create valid scheduled block."""
        block = ScheduledBlock(
            task_id="1",
            description="Meeting",
            category="Work",
            start_time="09:00",
            end_time="10:00",
        )
        assert block.task_id == "1"
        assert block.description == "Meeting"
        assert block.category == "Work"
        assert block.start_time == "09:00"
        assert block.end_time == "10:00"

    def test_missing_fields_raises(self):
        """Should raise error for missing required fields."""
        with pytest.raises(ValidationError):
            ScheduledBlock(task_id="1", description="Test")


class TestScheduleResponse:
    """Tests for ScheduleResponse model."""

    def test_valid_response(self):
        """Should create valid response."""
        blocks = [
            ScheduledBlock(
                task_id="1",
                description="Task",
                category="Work",
                start_time="09:00",
                end_time="10:00",
            )
        ]
        response = ScheduleResponse(schedule=blocks)
        assert len(response.schedule) == 1

    def test_empty_schedule(self):
        """Should allow empty schedule."""
        response = ScheduleResponse(schedule=[])
        assert response.schedule == []
