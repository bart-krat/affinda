"""Unit tests for knapsack optimiser."""

import pytest
from src.submodules.optimiser_knapsack import optimise_schedule_knapsack
from src.models.task import TaskWithConstraints, DayConstraints, UtilityWeights


class TestOptimiseScheduleKnapsack:
    """Tests for knapsack scheduling algorithm."""

    @pytest.fixture
    def default_weights(self):
        return UtilityWeights(personal=1.0, health=2.0, work=1.5)

    @pytest.fixture
    def default_constraints(self):
        return DayConstraints(window_start="08:00", window_end="18:00")

    @pytest.mark.asyncio
    async def test_empty_tasks(self, default_constraints, default_weights):
        """Should return empty schedule for empty tasks."""
        result = await optimise_schedule_knapsack([], default_constraints, default_weights)
        assert result == []

    @pytest.mark.asyncio
    async def test_single_task_fits(self, default_constraints, default_weights):
        """Should schedule single task when it fits."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task",
                category="Work",
                duration_minutes=60,
            )
        ]

        result = await optimise_schedule_knapsack(tasks, default_constraints, default_weights)

        assert len(result) == 1
        assert result[0].task_id == "1"

    @pytest.mark.asyncio
    async def test_selects_higher_value_tasks(self, default_weights):
        """Should select tasks that maximize utility when constrained."""
        # 2-hour window, 3 tasks totaling 3 hours
        constraints = DayConstraints(window_start="08:00", window_end="10:00")
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Personal task",
                category="Personal",  # weight 1.0
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
                description="Work task",
                category="Work",  # weight 1.5
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_knapsack(tasks, constraints, default_weights)

        # Should select Health (2.0) and Work (1.5) over Personal (1.0)
        assert len(result) == 2
        task_ids = {b.task_id for b in result}
        assert "2" in task_ids  # Health
        assert "3" in task_ids  # Work
        assert "1" not in task_ids  # Personal excluded

    @pytest.mark.asyncio
    async def test_fixed_tasks_always_scheduled(self, default_weights):
        """Should always schedule fixed tasks regardless of utility."""
        constraints = DayConstraints(window_start="08:00", window_end="09:00")
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed low priority",
                category="Personal",  # weight 1.0
                duration_minutes=60,
                fixed_start_time="08:00",
            ),
            TaskWithConstraints(
                id="2",
                description="High priority flexible",
                category="Health",  # weight 2.0
                duration_minutes=60,
            ),
        ]

        result = await optimise_schedule_knapsack(tasks, constraints, default_weights)

        # Fixed task should be scheduled even though it has lower utility
        assert len(result) == 1
        assert result[0].task_id == "1"

    @pytest.mark.asyncio
    async def test_respects_capacity_after_fixed_tasks(self, default_weights):
        """Should calculate remaining capacity after fixed tasks."""
        constraints = DayConstraints(window_start="08:00", window_end="10:00")
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed",
                category="Work",
                duration_minutes=60,
                fixed_start_time="08:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Flexible 1",
                category="Health",
                duration_minutes=30,
            ),
            TaskWithConstraints(
                id="3",
                description="Flexible 2",
                category="Personal",
                duration_minutes=90,  # Won't fit
            ),
        ]

        result = await optimise_schedule_knapsack(tasks, constraints, default_weights)

        # Fixed task (60 min) + Flexible 1 (30 min) = 90 min, fits in 120 min window
        # Flexible 2 (90 min) won't fit in remaining 60 min
        task_ids = {b.task_id for b in result}
        assert "1" in task_ids
        assert "2" in task_ids
        assert "3" not in task_ids

    @pytest.mark.asyncio
    async def test_no_capacity_returns_only_fixed(self, default_weights):
        """Should return only fixed tasks when no capacity for flexible."""
        constraints = DayConstraints(window_start="08:00", window_end="09:00")
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed",
                category="Work",
                duration_minutes=60,  # Takes entire window
                fixed_start_time="08:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Flexible",
                category="Health",
                duration_minutes=30,
            ),
        ]

        result = await optimise_schedule_knapsack(tasks, constraints, default_weights)

        assert len(result) == 1
        assert result[0].task_id == "1"

    @pytest.mark.asyncio
    async def test_knapsack_optimal_selection(self, default_weights):
        """Should make optimal selection using dynamic programming."""
        # Classic knapsack: choose items to maximize value
        # Value calculation: weight * 100 (scaled for DP)
        constraints = DayConstraints(window_start="08:00", window_end="09:30")  # 90 min
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task A",
                category="Health",  # 2.0 * 100 = 200 value
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="2",
                description="Task B",
                category="Work",  # 1.5 * 100 = 150 value
                duration_minutes=40,
            ),
            TaskWithConstraints(
                id="3",
                description="Task C",
                category="Personal",  # 1.0 * 100 = 100 value
                duration_minutes=40,
            ),
        ]

        result = await optimise_schedule_knapsack(tasks, constraints, default_weights)

        # With 90 min capacity:
        # - A alone: 60 min, value 200
        # - B + C: 80 min, value 250 (optimal!)
        # Knapsack should select B + C over A
        task_ids = {b.task_id for b in result}
        assert len(result) == 2
        assert "2" in task_ids  # Work task
        assert "3" in task_ids  # Personal task

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
        ]

        result = await optimise_schedule_knapsack(tasks, default_constraints, default_weights)

        if len(result) > 1:
            for i in range(len(result) - 1):
                assert result[i].start_time <= result[i + 1].start_time

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

        result = await optimise_schedule_knapsack(tasks, default_constraints, default_weights)

        assert len(result) == 2
        assert result[0].start_time == "09:00"
        assert result[1].start_time == "10:00"
