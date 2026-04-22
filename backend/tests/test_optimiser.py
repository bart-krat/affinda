"""Unit tests for main optimiser module."""

import pytest
from src.submodules.optimiser import optimise_schedule, DEFAULT_ALGORITHM
from src.models.task import TaskWithConstraints, DayConstraints, UtilityWeights


class TestOptimiseSchedule:
    """Tests for main optimise_schedule entry point."""

    @pytest.fixture
    def default_weights(self):
        return UtilityWeights(personal=1.0, health=2.0, work=1.5)

    @pytest.fixture
    def default_constraints(self):
        return DayConstraints(window_start="08:00", window_end="18:00")

    @pytest.fixture
    def sample_tasks(self):
        return [
            TaskWithConstraints(
                id="1",
                description="Task 1",
                category="Work",
                duration_minutes=60,
            ),
            TaskWithConstraints(
                id="2",
                description="Task 2",
                category="Health",
                duration_minutes=30,
            ),
        ]

    def test_default_algorithm_is_greedy(self):
        """Should default to greedy algorithm."""
        assert DEFAULT_ALGORITHM == "greedy"

    @pytest.mark.asyncio
    async def test_uses_greedy_by_default(
        self, sample_tasks, default_constraints, default_weights
    ):
        """Should use greedy algorithm when no algorithm specified."""
        result = await optimise_schedule(
            sample_tasks, default_constraints, default_weights
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_explicit_greedy_algorithm(
        self, sample_tasks, default_constraints, default_weights
    ):
        """Should use greedy algorithm when explicitly specified."""
        result = await optimise_schedule(
            sample_tasks, default_constraints, default_weights, algorithm="greedy"
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_knapsack_algorithm(
        self, sample_tasks, default_constraints, default_weights
    ):
        """Should use knapsack algorithm when specified."""
        result = await optimise_schedule(
            sample_tasks, default_constraints, default_weights, algorithm="knapsack"
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_permutation_algorithm(
        self, sample_tasks, default_constraints, default_weights
    ):
        """Should use permutation algorithm when specified."""
        result = await optimise_schedule(
            sample_tasks, default_constraints, default_weights, algorithm="permutation"
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_unknown_algorithm_falls_back_to_greedy(
        self, sample_tasks, default_constraints, default_weights
    ):
        """Should fall back to greedy for unknown algorithm."""
        result = await optimise_schedule(
            sample_tasks, default_constraints, default_weights, algorithm="unknown"
        )

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_empty_tasks_all_algorithms(self, default_constraints, default_weights):
        """Should handle empty tasks for all algorithms."""
        for algorithm in ["greedy", "knapsack", "permutation"]:
            result = await optimise_schedule(
                [], default_constraints, default_weights, algorithm=algorithm
            )
            assert result == []

    @pytest.mark.asyncio
    async def test_algorithms_produce_valid_schedules(
        self, sample_tasks, default_constraints, default_weights
    ):
        """All algorithms should produce valid scheduled blocks."""
        for algorithm in ["greedy", "knapsack", "permutation"]:
            result = await optimise_schedule(
                sample_tasks, default_constraints, default_weights, algorithm=algorithm
            )

            for block in result:
                assert block.task_id in ["1", "2"]
                assert block.start_time is not None
                assert block.end_time is not None
                assert block.description in ["Task 1", "Task 2"]
