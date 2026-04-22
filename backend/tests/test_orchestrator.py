"""Unit tests for orchestrator module."""

import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, AsyncMock
import tempfile
import shutil

from src.orchestrator import (
    create_session,
    save_state,
    load_state,
    get_state,
    reset_session,
    phase1_set_weights,
    phase2_submit_tasks,
    phase3_set_constraints,
    phase4_generate_schedule,
    _select_algorithm,
    _parse_time,
    STATE_DIR,
)
from src.models.workflow import WorkflowState, WorkflowPhase
from src.models.task import UtilityWeights, TaskWithConstraints


class TestStateFileHelpers:
    """Tests for state file management helpers."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.original_state_dir = STATE_DIR
        self.temp_dir = Path(tempfile.mkdtemp())
        # Patch STATE_DIR for tests
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_parse_time_morning(self):
        """Should parse morning time."""
        dt = _parse_time("08:30")
        assert dt.hour == 8
        assert dt.minute == 30

    def test_parse_time_afternoon(self):
        """Should parse afternoon time."""
        dt = _parse_time("14:00")
        assert dt.hour == 14


class TestSelectAlgorithm:
    """Tests for algorithm selection logic."""

    @pytest.fixture
    def default_window(self):
        return ("08:00", "18:00")  # 10 hours = 600 minutes

    def test_greedy_when_all_tasks_fit(self, default_window):
        """Should select greedy when all tasks fit in window."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Task",
                category="Work",
                duration_minutes=60,
            )
        ]

        algorithm = _select_algorithm(tasks, *default_window)

        assert algorithm == "greedy"

    def test_knapsack_when_tasks_dont_fit(self, default_window):
        """Should select knapsack when total duration exceeds window."""
        # Create tasks totaling more than 600 minutes
        tasks = [
            TaskWithConstraints(
                id=str(i),
                description=f"Task {i}",
                category="Work",
                duration_minutes=100,
            )
            for i in range(7)  # 700 minutes > 600
        ]

        algorithm = _select_algorithm(tasks, *default_window)

        assert algorithm == "knapsack"

    def test_permutation_when_multiple_fixed_times(self, default_window):
        """Should select permutation when 2+ fixed time constraints."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed 1",
                category="Work",
                duration_minutes=60,
                fixed_start_time="09:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Fixed 2",
                category="Work",
                duration_minutes=60,
                fixed_start_time="14:00",
            ),
        ]

        algorithm = _select_algorithm(tasks, *default_window)

        assert algorithm == "permutation"

    def test_greedy_with_single_fixed_time(self, default_window):
        """Should select greedy with only one fixed time task."""
        tasks = [
            TaskWithConstraints(
                id="1",
                description="Fixed",
                category="Work",
                duration_minutes=60,
                fixed_start_time="09:00",
            ),
            TaskWithConstraints(
                id="2",
                description="Flexible",
                category="Work",
                duration_minutes=60,
            ),
        ]

        algorithm = _select_algorithm(tasks, *default_window)

        assert algorithm == "greedy"

    def test_empty_tasks_returns_greedy(self, default_window):
        """Should return greedy for empty task list."""
        algorithm = _select_algorithm([], *default_window)
        assert algorithm == "greedy"


class TestSessionManagement:
    """Tests for session creation and management."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_session(self):
        """Should create new session in WEIGHTS phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            state = create_session("test-session")

            assert state.session_id == "test-session"
            assert state.phase == WorkflowPhase.WEIGHTS

    def test_save_and_load_state(self):
        """Should persist and retrieve state."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            state = WorkflowState(session_id="test", phase=WorkflowPhase.TASKS)
            save_state(state)

            loaded = load_state("test")

            assert loaded is not None
            assert loaded.session_id == "test"
            assert loaded.phase == WorkflowPhase.TASKS

    def test_load_nonexistent_session(self):
        """Should return None for nonexistent session."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            result = load_state("nonexistent")
            assert result is None

    def test_get_state(self):
        """Should get current state."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            create_session("test")
            state = get_state("test")

            assert state is not None
            assert state.session_id == "test"

    def test_reset_session(self):
        """Should reset session to initial state."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Create and advance session
            state = create_session("test")
            state.phase = WorkflowPhase.COMPLETE
            save_state(state)

            # Reset
            reset_state = reset_session("test")

            assert reset_state.phase == WorkflowPhase.WEIGHTS


class TestWorkflowPhases:
    """Tests for workflow phase transitions."""

    @pytest.fixture(autouse=True)
    def setup_temp_state_dir(self):
        """Use temporary directory for state files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            yield
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_phase1_set_weights(self):
        """Should set weights and advance to TASKS phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            weights = UtilityWeights(personal=1.0, health=2.0, work=1.5)

            state = await phase1_set_weights("test", weights)

            assert state.phase == WorkflowPhase.TASKS
            assert state.weights.health == 2.0

    @pytest.mark.asyncio
    async def test_phase1_creates_session_if_needed(self):
        """Should create session if it doesn't exist."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            weights = UtilityWeights()

            state = await phase1_set_weights("new-session", weights)

            assert state.session_id == "new-session"

    @pytest.mark.asyncio
    async def test_phase2_submit_tasks(self):
        """Should categorize tasks and advance to CONSTRAINTS phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Setup: create session in TASKS phase
            await phase1_set_weights("test", UtilityWeights())

            # Mock categoriser
            mock_result = [
                {"description": "Go to gym", "category": "Health"},
            ]
            with patch(
                "src.orchestrator.categorise_tasks",
                new_callable=AsyncMock,
                return_value=mock_result,
            ):
                state = await phase2_submit_tasks("test", ["Go to gym"])

            assert state.phase == WorkflowPhase.CONSTRAINTS
            assert state.raw_tasks == ["Go to gym"]
            assert state.categorised_tasks == mock_result

    @pytest.mark.asyncio
    async def test_phase2_wrong_phase_raises(self):
        """Should raise error if not in TASKS phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            create_session("test")  # Creates in WEIGHTS phase

            with pytest.raises(ValueError, match="Invalid phase"):
                await phase2_submit_tasks("test", ["Task"])

    @pytest.mark.asyncio
    async def test_phase2_missing_session_raises(self):
        """Should raise error for missing session."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            with pytest.raises(ValueError, match="not found"):
                await phase2_submit_tasks("nonexistent", ["Task"])

    @pytest.mark.asyncio
    async def test_phase3_set_constraints(self):
        """Should set constraints and advance to SCHEDULE phase."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Setup: advance to CONSTRAINTS phase
            await phase1_set_weights("test", UtilityWeights())
            with patch(
                "src.orchestrator.categorise_tasks",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await phase2_submit_tasks("test", [])

            tasks = [
                TaskWithConstraints(
                    id="1",
                    description="Task",
                    category="Work",
                    duration_minutes=30,
                )
            ]

            state = await phase3_set_constraints(
                "test", tasks, "08:00", "18:00"
            )

            assert state.phase == WorkflowPhase.SCHEDULE
            assert state.window_start == "08:00"
            assert state.window_end == "18:00"

    @pytest.mark.asyncio
    async def test_phase4_generate_schedule(self):
        """Should generate schedule and complete workflow."""
        with patch("src.orchestrator.STATE_DIR", self.temp_dir):
            # Setup: advance to SCHEDULE phase
            await phase1_set_weights("test", UtilityWeights())
            with patch(
                "src.orchestrator.categorise_tasks",
                new_callable=AsyncMock,
                return_value=[],
            ):
                await phase2_submit_tasks("test", [])

            tasks = [
                TaskWithConstraints(
                    id="1",
                    description="Task",
                    category="Work",
                    duration_minutes=30,
                )
            ]
            await phase3_set_constraints("test", tasks, "08:00", "18:00")

            # Mock optimisers
            mock_schedule = []
            with patch(
                "src.orchestrator.optimise_schedule_greedy",
                new_callable=AsyncMock,
                return_value=mock_schedule,
            ):
                state = await phase4_generate_schedule("test")

            assert state.phase == WorkflowPhase.COMPLETE
            assert state.selected_algorithm == "greedy"
