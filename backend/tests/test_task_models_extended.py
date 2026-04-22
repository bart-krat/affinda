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

    def test_minimum_duration_is_one(self):
        """Should require minimum 1 minute duration."""
        with pytest.raises(ValidationError, match="at least 1 minute"):
            TaskWithConstraints(
                id="1",
                description="Test",
                category="Work",
                duration_minutes=0,
            )

    def test_negative_duration_raises(self):
        """Should raise error for negative duration."""
        with pytest.raises(ValidationError, match="at least 1 minute"):
            TaskWithConstraints(
                id="1",
                description="Test",
                category="Work",
                duration_minutes=-10,
            )

    def test_max_duration_is_480(self):
        """Should reject duration over 480 minutes."""
        with pytest.raises(ValidationError, match="cannot exceed 480"):
            TaskWithConstraints(
                id="1",
                description="Test",
                category="Work",
                duration_minutes=481,
            )

    def test_valid_duration_at_boundaries(self):
        """Should accept durations at boundaries."""
        task_min = TaskWithConstraints(
            id="1", description="Test", category="Work", duration_minutes=1
        )
        task_max = TaskWithConstraints(
            id="2", description="Test", category="Work", duration_minutes=480
        )
        assert task_min.duration_minutes == 1
        assert task_max.duration_minutes == 480

    def test_time_format_validation(self):
        """Should validate HH:MM time format."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            TaskWithConstraints(
                id="1",
                description="Test",
                category="Work",
                duration_minutes=30,
                fixed_start_time="8am",
            )

    def test_time_normalization(self):
        """Should normalize time to HH:MM format."""
        task = TaskWithConstraints(
            id="1",
            description="Test",
            category="Work",
            duration_minutes=30,
            fixed_start_time="9:00",
        )
        assert task.fixed_start_time == "09:00"


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

    def test_invalid_time_format_raises(self):
        """Should reject invalid time format."""
        with pytest.raises(ValidationError, match="Invalid time format"):
            DayConstraints(window_start="8am", window_end="6pm")

    def test_end_must_be_after_start(self):
        """Should reject window where end is before or equal to start."""
        with pytest.raises(ValidationError, match="after window start"):
            DayConstraints(window_start="18:00", window_end="08:00")

    def test_minimum_window_duration(self):
        """Should require at least 30 minute window."""
        with pytest.raises(ValidationError, match="at least 30 minutes"):
            DayConstraints(window_start="08:00", window_end="08:15")

    def test_time_normalization(self):
        """Should normalize times."""
        constraints = DayConstraints(window_start="8:00", window_end="18:00")
        assert constraints.window_start == "08:00"


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

    def test_negative_weights_rejected(self):
        """Should reject negative weights."""
        with pytest.raises(ValidationError, match="cannot be negative"):
            UtilityWeights(personal=-1.0)

    def test_max_weight_is_10(self):
        """Should reject weights over 10."""
        with pytest.raises(ValidationError, match="cannot exceed 10"):
            UtilityWeights(personal=11.0)

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
            tasks=[
                TaskWithConstraints(
                    id="1",
                    description="Task",
                    category="Work",
                    duration_minutes=30,
                )
            ],
            constraints=DayConstraints(window_start="08:00", window_end="18:00"),
            weights=UtilityWeights(),
        )
        assert request.algorithm == "greedy"

    def test_valid_algorithm_values(self):
        """Should accept valid algorithm values."""
        for algo in ["greedy", "knapsack", "permutation"]:
            request = ScheduleRequest(
                tasks=[
                    TaskWithConstraints(
                        id="1",
                        description="Task",
                        category="Work",
                        duration_minutes=30,
                    )
                ],
                constraints=DayConstraints(window_start="08:00", window_end="18:00"),
                weights=UtilityWeights(),
                algorithm=algo,
            )
            assert request.algorithm == algo

    def test_invalid_algorithm_rejected(self):
        """Should reject invalid algorithm values."""
        with pytest.raises(ValidationError):
            ScheduleRequest(
                tasks=[
                    TaskWithConstraints(
                        id="1",
                        description="Task",
                        category="Work",
                        duration_minutes=30,
                    )
                ],
                constraints=DayConstraints(window_start="08:00", window_end="18:00"),
                weights=UtilityWeights(),
                algorithm="invalid",
            )


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
        assert response.warnings == []

    def test_empty_schedule(self):
        """Should allow empty schedule."""
        response = ScheduleResponse(schedule=[])
        assert response.schedule == []

    def test_warnings_field(self):
        """Should accept warnings."""
        response = ScheduleResponse(schedule=[], warnings=["Some tasks were skipped"])
        assert len(response.warnings) == 1
