"""
Orchestrator module - manages workflow phases and state persistence.

Workflow phases:
1. WEIGHTS: User sets utility weights for categories
2. TASKS: User inputs task list, LLM categorizes them
3. CONSTRAINTS: User sets durations, fixed times, day window
4. SCHEDULE: System selects algorithm and generates schedule
5. COMPLETE: Workflow finished
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta

from .models.task import TaskWithConstraints, UtilityWeights, ScheduledBlock
from .models.workflow import WorkflowState, WorkflowPhase
from .submodules.categoriser import categorise_tasks
from .submodules.optimiser_greedy import optimise_schedule_greedy
from .submodules.optimiser_knapsack import optimise_schedule_knapsack
from .submodules.optimiser_permutation import optimise_schedule_permutation

# State storage directory
STATE_DIR = Path(__file__).parent.parent.parent / "workflow_states"


def _ensure_state_dir():
    STATE_DIR.mkdir(exist_ok=True)


def _state_file(session_id: str) -> Path:
    return STATE_DIR / f"{session_id}.json"


def save_state(state: WorkflowState) -> None:
    """Persist workflow state to JSON file."""
    _ensure_state_dir()
    with open(_state_file(state.session_id), "w") as f:
        json.dump(state.model_dump(), f, indent=2, default=str)


def load_state(session_id: str) -> WorkflowState | None:
    """Load workflow state from JSON file."""
    state_file = _state_file(session_id)
    if not state_file.exists():
        return None
    with open(state_file, "r") as f:
        data = json.load(f)
        return WorkflowState(**data)


def create_session(session_id: str) -> WorkflowState:
    """Create a new workflow session."""
    state = WorkflowState(session_id=session_id, phase=WorkflowPhase.WEIGHTS)
    save_state(state)
    return state


async def phase1_set_weights(session_id: str, weights: UtilityWeights) -> WorkflowState:
    """Phase 1: Set utility weights and advance to tasks phase."""
    state = load_state(session_id)
    if state is None:
        state = create_session(session_id)

    state.weights = weights
    state.phase = WorkflowPhase.TASKS
    save_state(state)
    return state


async def phase2_submit_tasks(session_id: str, tasks: list[str]) -> WorkflowState:
    """Phase 2: Submit tasks, categorize with LLM, advance to constraints phase."""
    state = load_state(session_id)
    if state is None:
        raise ValueError(f"Session {session_id} not found")

    if state.phase != WorkflowPhase.TASKS:
        raise ValueError(f"Invalid phase: expected TASKS, got {state.phase}")

    state.raw_tasks = tasks
    categorised = await categorise_tasks(tasks)
    state.categorised_tasks = categorised
    state.phase = WorkflowPhase.CONSTRAINTS
    save_state(state)
    return state


async def phase3_set_constraints(
    session_id: str,
    tasks: list[TaskWithConstraints],
    window_start: str,
    window_end: str,
) -> WorkflowState:
    """Phase 3: Set time constraints, advance to schedule phase."""
    state = load_state(session_id)
    if state is None:
        raise ValueError(f"Session {session_id} not found")

    if state.phase != WorkflowPhase.CONSTRAINTS:
        raise ValueError(f"Invalid phase: expected CONSTRAINTS, got {state.phase}")

    state.tasks_with_constraints = tasks
    state.window_start = window_start
    state.window_end = window_end
    state.phase = WorkflowPhase.SCHEDULE
    save_state(state)
    return state


def _parse_time(time_str: str) -> datetime:
    today = datetime.now().date()
    time_part = datetime.strptime(time_str, "%H:%M").time()
    return datetime.combine(today, time_part)


def _select_algorithm(
    tasks: list[TaskWithConstraints],
    window_start: str,
    window_end: str,
) -> str:
    """
    Select the optimal algorithm based on constraints:
    - If all tasks fit in window: greedy (fast)
    - If tasks don't fit without fixed times: knapsack (maximize utility)
    - If multiple fixed time constraints: permutation (find best ordering)
    """
    window_start_dt = _parse_time(window_start)
    window_end_dt = _parse_time(window_end)
    total_window_minutes = int((window_end_dt - window_start_dt).total_seconds() / 60)

    fixed_time_tasks = [t for t in tasks if t.fixed_start_time]
    flexible_tasks = [t for t in tasks if not t.fixed_start_time]

    total_duration = sum(t.duration_minutes for t in tasks)
    flexible_duration = sum(t.duration_minutes for t in flexible_tasks)
    fixed_duration = sum(t.duration_minutes for t in fixed_time_tasks)

    # Rule 1: Multiple fixed time constraints -> permutation
    # (need to find optimal ordering around fixed blocks)
    if len(fixed_time_tasks) >= 2:
        return "permutation"

    # Rule 2: Tasks don't fit in window -> knapsack
    # (need to maximize utility by selecting subset)
    if total_duration > total_window_minutes:
        return "knapsack"

    # Rule 3: All tasks fit -> greedy
    # (simple priority-based scheduling is sufficient)
    return "greedy"


async def phase4_generate_schedule(session_id: str) -> WorkflowState:
    """Phase 4: Select algorithm, generate schedule, complete workflow."""
    state = load_state(session_id)
    if state is None:
        raise ValueError(f"Session {session_id} not found")

    if state.phase != WorkflowPhase.SCHEDULE:
        raise ValueError(f"Invalid phase: expected SCHEDULE, got {state.phase}")

    tasks = state.tasks_with_constraints
    window_start = state.window_start
    window_end = state.window_end
    weights = state.weights

    # Select algorithm based on constraints
    algorithm = _select_algorithm(tasks, window_start, window_end)
    state.selected_algorithm = algorithm

    # Create constraints objects
    from .models.task import DayConstraints
    constraints = DayConstraints(window_start=window_start, window_end=window_end)

    # Run selected algorithm
    if algorithm == "greedy":
        schedule = await optimise_schedule_greedy(tasks, constraints, weights)
    elif algorithm == "knapsack":
        schedule = await optimise_schedule_knapsack(tasks, constraints, weights)
    elif algorithm == "permutation":
        schedule = await optimise_schedule_permutation(tasks, constraints, weights)
    else:
        schedule = await optimise_schedule_greedy(tasks, constraints, weights)

    state.schedule = schedule
    state.phase = WorkflowPhase.COMPLETE
    save_state(state)
    return state


def get_state(session_id: str) -> WorkflowState | None:
    """Get current workflow state."""
    return load_state(session_id)


def reset_session(session_id: str) -> WorkflowState:
    """Reset a session to the beginning."""
    state = create_session(session_id)
    return state
