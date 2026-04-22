"""Unit tests for permutation optimiser."""

import pytest
from src.submodules.optimiser_permutation import optimise_schedule_permutation
from src.models.task import TaskWithConstraints, DayConstraints, UtilityWeights


class TestOptimiseSchedulePermutation:
    """Tests for permutation scheduling algorithm."""

    @pytest.fixture
    def default_weights(self):
        return UtilityWeights(personal=1.0, health=2.0, work=1.5)

    @pytest.fixture
    def default_constraints(self):
        return DayConstraints(window_start="08:00", window_end="18:00")

    @pytest.mark.asyncio
    async def test_empty_tasks(self, default_constraints, default_weights):
        """Should return empty schedule for empty tasks."""
        result = await optimise_schedule_permutation([], default_constraints, default_weights)
        assert result == []

    @pytest.mark.asyncio
    async def test_single_task(self, default_constraints, default_weights):
        """Should schedule single task."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task",
                category="Work",
                duration_minutes=60,
            )
        ]

        result = await optimise_schedule_permutation(tasks, default_constraints, default_weights)

        assert len(result) == 1
        assert result[0].task_id == "1"

    @pytest.mark.asyncio
    async def test_only_fixed_tasks(self, default_constraints, default_weights):
        """Should schedule only fixed tasks correctly."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed 1",
                category="Work",
                duration_minutes=30,
                fixed_start_time="09:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Fixed 2",
                category="Health",
                duration_minutes=30,
                fixed_start_time="10:00",
            ),
        ]

        result = await optimise_schedule_permutation(tasks, default_constraints, default_weights)

        assert len(result) == 2
        # Should be sorted by start time
        assert result[0].start_time == "09:00"
        assert result[1].start_time == "10:00"

    @pytest.mark.asyncio
    async def test_finds_optimal_permutation(self, default_weights):
        """Should find the permutation that maximizes utility."""
        # Tight window where order matters
        constraints = DayConstraints(window_start="08:00", window_end="09:30")  # 90 min

        tasks = [
            TaskWithConstraints(
                id="1",
                description="Long low priority",
                category="Personal",  # 1.0
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="2",
                description="Short high priority",
                category="Health",  # 2.0
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_permutation(tasks, constraints, default_weights)

        # Only one task can fit in 90 min window (each is 60 min)
        # Should pick Health (higher weight) over Personal
        assert len(result) == 1
        assert result[0].task_id == "2"  # Health task

    @pytest.mark.asyncio
    async def test_schedules_around_fixed_tasks(self, default_constraints, default_weights):
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
                description="Flexible",
                category="Health",
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_permutation(tasks, default_constraints, default_weights)

        assert len(result) == 2
        fixed = next(b for b in result if b.task_id == "1")
        flexible = next(b for b in result if b.task_id == "2")
        assert fixed.start_time == "10:00"
        # Flexible should be scheduled before or after fixed
        assert flexible.start_time in ["08:00", "09:00", "11:00"]

    @pytest.mark.asyncio
    async def test_multiple_permutations_small_set(self, default_weights):
        """Should try all permutations for small task sets."""
        constraints = DayConstraints(window_start="08:00", window_end="10:30")  # 150 min

        tasks = [
            TaskWithConstraints(
                id="1",
                description="A",
                category="Personal",  # 1.0 * 30 = 30
                duration_minutes=30,
            ),
            TaskWithConstraints(
                id="2",
                description="B",
                category="Health",  # 2.0 * 60 = 120
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="3",
                description="C",
                category="Work",  # 1.5 * 60 = 90
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_permutation(tasks, constraints, default_weights)

        # Total duration = 150 min, window = 150 min, all fit
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_fallback_for_large_task_sets(self, default_constraints, default_weights):
        """Should fall back to sorted order for >8 tasks."""
        # Create 10 tasks (> MAX_PERMUTATION_TASKS)
        tasks = [
            TaskWithConstraints(
                id=str(i),
                description=f"Task {i}",
                category=["Personal", "Health", "Work"][i % 3],
                duration_minutes=30,
            )
            for i in range(10)
        ]

        result = await optimise_schedule_permutation(tasks, default_constraints, default_weights)

        # Should still produce valid schedule
        assert len(result) > 0
        # All should fit in 10-hour window
        assert len(result) == 10

    @pytest.mark.asyncio
    async def test_result_sorted_by_start_time(self, default_constraints, default_weights):
        """Should return schedule sorted by start time."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task 1",
                category="Work",
                duration_minutes=30,
            ),
            TaskWithConstraints(
                id="2",
                description="Task 2",
                category="Health",
                duration_minutes=30,
            ),
            TaskWithConstraints(
                id="3",
                description="Task 3",
                category="Personal",
                duration_minutes=30,
            ),
        ]

        result = await optimise_schedule_permutation(tasks, default_constraints, default_weights)

        for i in range(len(result) - 1):
            assert result[i].start_time <= result[i + 1].start_time

    @pytest.mark.asyncio
    async def test_utility_calculation(self, default_weights):
        """Should maximize utility = weight * duration."""
        constraints = DayConstraints(window_start="08:00", window_end="09:00")  # 60 min

        tasks = [
            TaskWithConstraints(
                id="1",
                description="Short high priority",
                category="Health",  # 2.0 * 30 = 60
                duration_minutes=30,
            ),
            TaskWithConstraints(
                id="2",
                description="Long low priority",
                category="Personal",  # 1.0 * 60 = 60
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_permutation(tasks, constraints, default_weights)

        # Both give same utility (60), but task 2 takes full window
        # If task 1 is scheduled, task 2 won't fit
        # Algorithm should pick the one that maximizes total utility
        # Either solution is valid since utilities are equal
        assert len(result) >= 1

    @pytest.mark.asyncio
    async def test_no_flexible_tasks(self, default_constraints, default_weights):
        """Should handle case with only fixed tasks."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed",
                category="Work",
                duration_minutes=60,
                fixed_start_time="09:00",
            ),
        ]

        result = await optimise_schedule_permutation(tasks, default_constraints, default_weights)

        assert len(result) == 1
        assert result[0].task_id == "1"
        assert result[0].start_time == "09:00"
