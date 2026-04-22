"""Unit tests for greedy optimiser."""

import pytest
from src.submodules.optimiser_greedy import (
    optimise_schedule_greedy,
    parse_time,
    format_time,
)
from src.models.task import TaskWithConstraints, DayConstraints, UtilityWeights


class TestParseTime:
    """Tests for parse_time helper function."""

    def test_parse_morning_time(self):
        """Should parse morning time correctly."""
        dt = parse_time("08:00")
        assert dt.hour == 8
        assert dt.minute == 0

    def test_parse_afternoon_time(self):
        """Should parse afternoon time correctly."""
        dt = parse_time("14:30")
        assert dt.hour == 14
        assert dt.minute == 30

    def test_parse_midnight(self):
        """Should parse midnight correctly."""
        dt = parse_time("00:00")
        assert dt.hour == 0
        assert dt.minute == 0

    def test_invalid_format_raises(self):
        """Should raise error for invalid format."""
        with pytest.raises(ValueError):
            parse_time("8am")


class TestFormatTime:
    """Tests for format_time helper function."""

    def test_format_morning_time(self):
        """Should format morning time correctly."""
        dt = parse_time("08:00")
        assert format_time(dt) == "08:00"

    def test_format_preserves_time(self):
        """Should preserve time through parse/format cycle."""
        original = "14:30"
        assert format_time(parse_time(original)) == original


class TestOptimiseScheduleGreedy:
    """Tests for greedy scheduling algorithm."""

    @pytest.fixture
    def default_weights(self):
        return UtilityWeights(personal=1.0, health=2.0, work=1.5)

    @pytest.fixture
    def default_constraints(self):
        return DayConstraints(window_start="08:00", window_end="18:00")

    @pytest.mark.asyncio
    async def test_empty_tasks(self, default_constraints, default_weights):
        """Should return empty schedule for empty tasks."""
        result = await optimise_schedule_greedy([], default_constraints, default_weights)
        assert result == []

    @pytest.mark.asyncio
    async def test_single_flexible_task(self, default_constraints, default_weights):
        """Should schedule single task at window start."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task 1",
                category="Work",
                duration_minutes=60,
            )
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert len(result) == 1
        assert result[0].task_id == "1"
        assert result[0].start_time == "08:00"
        assert result[0].end_time == "09:00"

    @pytest.mark.asyncio
    async def test_single_fixed_task(self, default_constraints, default_weights):
        """Should schedule fixed task at its specified time."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Meeting",
                category="Work",
                duration_minutes=60,
                fixed_start_time="14:00",
            )
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert len(result) == 1
        assert result[0].start_time == "14:00"
        assert result[0].end_time == "15:00"

    @pytest.mark.asyncio
    async def test_multiple_tasks_sorted_by_weight(self, default_constraints, default_weights):
        """Should schedule higher-weight tasks first."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Work task",
                category="Work",  # weight 1.5
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="2",
                description="Health task",
                category="Health",  # weight 2.0 (highest)
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="3",
                description="Personal task",
                category="Personal",  # weight 1.0
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert len(result) == 3
        # Health (highest weight) should be scheduled first
        assert result[0].category == "Health"
        assert result[0].start_time == "08:00"
        # Work (second highest) next
        assert result[1].category == "Work"
        # Personal (lowest) last
        assert result[2].category == "Personal"

    @pytest.mark.asyncio
    async def test_fixed_task_takes_priority(self, default_constraints, default_weights):
        """Should place fixed tasks before scheduling flexible ones."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Flexible",
                category="Health",
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="2",
                description="Fixed",
                category="Work",
                duration_minutes=60,
                fixed_start_time="08:00",
            ),
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert len(result) == 2
        # Fixed task at 08:00
        fixed_task = next(b for b in result if b.task_id == "2")
        assert fixed_task.start_time == "08:00"
        # Flexible task should start after fixed task
        flexible_task = next(b for b in result if b.task_id == "1")
        assert flexible_task.start_time == "09:00"

    @pytest.mark.asyncio
    async def test_task_too_long_for_window(self, default_weights):
        """Should not schedule task that doesn't fit."""
        constraints = DayConstraints(window_start="08:00", window_end="09:00")
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Long task",
                category="Work",
                duration_minutes=120,  # 2 hours, window is only 1 hour
            )
        ]

        result = await optimise_schedule_greedy(tasks, constraints, default_weights)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_schedules_around_fixed_task(self, default_constraints, default_weights):
        """Should schedule flexible tasks around fixed tasks."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed",
                category="Work",
                duration_minutes=60,
                fixed_start_time="10:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Flexible 1",
                category="Health",
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="3",
                description="Flexible 2",
                category="Personal",
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert len(result) == 3
        # Should schedule flexible tasks before and after fixed task
        times = [(b.start_time, b.task_id) for b in result]
        assert ("10:00", "1") in times  # Fixed task at 10:00

    @pytest.mark.asyncio
    async def test_result_sorted_by_start_time(self, default_constraints, default_weights):
        """Should return schedule sorted by start time."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Late fixed",
                category="Work",
                duration_minutes=30,
                fixed_start_time="15:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Early fixed",
                category="Work",
                duration_minutes=30,
                fixed_start_time="09:00",
            ),
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert result[0].start_time < result[1].start_time

    @pytest.mark.asyncio
    async def test_unknown_category_uses_default_weight(self, default_constraints, default_weights):
        """Should use weight 1.0 for unknown categories."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Unknown category",
                category="Unknown",
                duration_minutes=30,
            )
        ]

        result = await optimise_schedule_greedy(tasks, default_constraints, default_weights)

        assert len(result) == 1
