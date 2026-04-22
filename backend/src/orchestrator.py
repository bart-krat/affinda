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
import logging
from pathlib import Path
from datetime import datetime, timedelta

from .models.task import TaskWithConstraints, UtilityWeights, ScheduledBlock, DayConstraints
from .models.workflow import WorkflowState, WorkflowPhase
from .submodules.categoriser import categorise_tasks
from .submodules.optimiser_greedy import optimise_schedule_greedy
from .submodules.optimiser_knapsack import optimise_schedule_knapsack
from .submodules.optimiser_permutation import optimise_schedule_permutation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State storage directory
STATE_DIR = Path(__file__).parent.parent.parent / "workflow_states"


class WorkflowError(Exception):
    """Custom exception for workflow errors."""
    pass


class ValidationError(WorkflowError):
    """Validation-specific errors."""
    pass


class APIError(WorkflowError):
    """External API errors (e.g., OpenAI)."""
    pass


def _ensure_state_dir():
    STATE_DIR.mkdir(exist_ok=True)


def _state_file(session_id: str) -> Path:
    return STATE_DIR / f"{session_id}.json"


def save_state(state: WorkflowState) -> None:
    """Persist workflow state to JSON file."""
    _ensure_state_dir()
    try:
        with open(_state_file(state.session_id), "w") as f:
            json.dump(state.model_dump(), f, indent=2, default=str)
        logger.info(f"State saved for session {state.session_id}, phase: {state.phase}")
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        raise WorkflowError(f"Failed to save workflow state: {e}")


def load_state(session_id: str) -> WorkflowState | None:
    """Load workflow state from JSON file."""
    state_file = _state_file(session_id)
    if not state_file.exists():
        return None
    try:
        with open(state_file, "r") as f:
            data = json.load(f)
            return WorkflowState(**data)
    except Exception as e:
        logger.error(f"Failed to load state for {session_id}: {e}")
        return None


def create_session(session_id: str) -> WorkflowState:
    """Create a new workflow session."""
    logger.info(f"Creating new session: {session_id}")
    state = WorkflowState(session_id=session_id, phase=WorkflowPhase.WEIGHTS)
    save_state(state)
    return state


async def phase1_set_weights(session_id: str, weights: UtilityWeights) -> WorkflowState:
    """Phase 1: Set utility weights and advance to tasks phase."""
    logger.info(f"Phase 1: Setting weights for session {session_id}")
    state = load_state(session_id)
    if state is None:
        state = create_session(session_id)

    state.weights = weights
    state.phase = WorkflowPhase.TASKS
    state.error = None
    save_state(state)
    return state


async def phase2_submit_tasks(session_id: str, tasks: list[str]) -> tuple[WorkflowState, list[str]]:
    """Phase 2: Submit tasks, categorize with LLM, advance to constraints phase."""
    logger.info(f"Phase 2: Submitting {len(tasks)} tasks for session {session_id}")
    warnings = []

    state = load_state(session_id)
    if state is None:
        raise ValidationError(f"Session {session_id} not found")

    if state.phase != WorkflowPhase.TASKS:
        raise ValidationError(f"Invalid phase: expected TASKS, got {state.phase}")

    # Validate tasks
    if not tasks:
        raise ValidationError("No tasks provided")

    # Filter and validate
    valid_tasks = []
    for task in tasks:
        task = task.strip()
        if not task:
            continue
        if len(task) > 500:
            warnings.append(f"Task truncated (max 500 chars): {task[:30]}...")
            task = task[:500]
        valid_tasks.append(task)

    if not valid_tasks:
        raise ValidationError("No valid tasks after filtering")

    if len(valid_tasks) > 50:
        warnings.append(f"Too many tasks ({len(valid_tasks)}), limiting to first 50")
        valid_tasks = valid_tasks[:50]

    state.raw_tasks = valid_tasks

    # Call LLM for categorization with error handling
    try:
        categorised = await categorise_tasks(valid_tasks)
        state.categorised_tasks = categorised
    except Exception as e:
        logger.error(f"OpenAI categorization failed: {e}")
        state.error = f"Failed to categorize tasks: {str(e)}"
        save_state(state)
        raise APIError(f"Task categorization failed: {str(e)}")

    state.phase = WorkflowPhase.CONSTRAINTS
    state.error = None
    save_state(state)
    return state, warnings


async def phase3_set_constraints(
    session_id: str,
    tasks: list[TaskWithConstraints],
    window_start: str,
    window_end: str,
) -> tuple[WorkflowState, list[str]]:
    """Phase 3: Set time constraints, validate, advance to schedule phase."""
    logger.info(f"Phase 3: Setting constraints for session {session_id}")
    warnings = []

    state = load_state(session_id)
    if state is None:
        raise ValidationError(f"Session {session_id} not found")

    if state.phase != WorkflowPhase.CONSTRAINTS:
        raise ValidationError(f"Invalid phase: expected CONSTRAINTS, got {state.phase}")

    # Validate window
    window_warnings = _validate_time_window(window_start, window_end)
    warnings.extend(window_warnings)

    # Validate and check for edge cases in constraints
    constraint_warnings = _validate_constraints(tasks, window_start, window_end)
    warnings.extend(constraint_warnings)

    state.tasks_with_constraints = tasks
    state.window_start = window_start
    state.window_end = window_end
    state.phase = WorkflowPhase.SCHEDULE
    state.error = None
    save_state(state)
    return state, warnings


def _parse_time(time_str: str) -> datetime:
    today = datetime.now().date()
    time_part = datetime.strptime(time_str, "%H:%M").time()
    return datetime.combine(today, time_part)


def _validate_time_window(window_start: str, window_end: str) -> list[str]:
    """Validate time window and return warnings."""
    warnings = []
    try:
        start_dt = _parse_time(window_start)
        end_dt = _parse_time(window_end)
        duration = (end_dt - start_dt).total_seconds() / 60

        if duration < 60:
            warnings.append("Very short time window (less than 1 hour)")
        if duration > 720:  # 12 hours
            warnings.append("Very long time window (over 12 hours)")
    except Exception:
        pass
    return warnings


def _validate_constraints(
    tasks: list[TaskWithConstraints],
    window_start: str,
    window_end: str,
) -> list[str]:
    """Validate task constraints and detect edge cases."""
    warnings = []

    window_start_dt = _parse_time(window_start)
    window_end_dt = _parse_time(window_end)
    window_minutes = int((window_end_dt - window_start_dt).total_seconds() / 60)

    # Check total duration
    total_duration = sum(t.duration_minutes for t in tasks)
    if total_duration > window_minutes:
        excess = total_duration - window_minutes
        warnings.append(f"Tasks exceed window by {excess} minutes. Some tasks may be omitted.")

    # Check for fixed time conflicts
    fixed_tasks = [t for t in tasks if t.fixed_start_time]
    if len(fixed_tasks) >= 2:
        fixed_tasks_sorted = sorted(fixed_tasks, key=lambda t: t.fixed_start_time)
        for i in range(len(fixed_tasks_sorted) - 1):
            t1 = fixed_tasks_sorted[i]
            t2 = fixed_tasks_sorted[i + 1]
            t1_end = _parse_time(t1.fixed_start_time) + timedelta(minutes=t1.duration_minutes)
            t2_start = _parse_time(t2.fixed_start_time)
            if t1_end > t2_start:
                warnings.append(
                    f"Overlapping fixed times: '{t1.description}' ends at {t1_end.strftime('%H:%M')}, "
                    f"but '{t2.description}' starts at {t2.fixed_start_time}"
                )

    # Check fixed times within window
    for task in fixed_tasks:
        task_start = _parse_time(task.fixed_start_time)
        task_end = task_start + timedelta(minutes=task.duration_minutes)
        if task_start < window_start_dt:
            warnings.append(f"'{task.description}' starts before window opens")
        if task_end > window_end_dt:
            warnings.append(f"'{task.description}' extends past window close")

    return warnings


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
    total_duration = sum(t.duration_minutes for t in tasks)

    # Rule 1: Multiple fixed time constraints -> permutation
    if len(fixed_time_tasks) >= 2:
        logger.info("Selected algorithm: permutation (multiple fixed times)")
        return "permutation"

    # Rule 2: Tasks don't fit in window -> knapsack
    if total_duration > total_window_minutes:
        logger.info("Selected algorithm: knapsack (tasks exceed window)")
        return "knapsack"

    # Rule 3: All tasks fit -> greedy
    logger.info("Selected algorithm: greedy (all tasks fit)")
    return "greedy"


async def phase4_generate_schedule(session_id: str) -> tuple[WorkflowState, list[str]]:
    """Phase 4: Select algorithm, generate schedule, complete workflow."""
    logger.info(f"Phase 4: Generating schedule for session {session_id}")
    warnings = []

    state = load_state(session_id)
    if state is None:
        raise ValidationError(f"Session {session_id} not found")

    if state.phase != WorkflowPhase.SCHEDULE:
        raise ValidationError(f"Invalid phase: expected SCHEDULE, got {state.phase}")

    tasks = state.tasks_with_constraints
    window_start = state.window_start
    window_end = state.window_end
    weights = state.weights

    if not tasks:
        raise ValidationError("No tasks to schedule")

    # Select algorithm based on constraints
    algorithm = _select_algorithm(tasks, window_start, window_end)
    state.selected_algorithm = algorithm

    # Create constraints objects
    constraints = DayConstraints(window_start=window_start, window_end=window_end)

    # Run selected algorithm with error handling
    try:
        if algorithm == "greedy":
            schedule = await optimise_schedule_greedy(tasks, constraints, weights)
        elif algorithm == "knapsack":
            schedule = await optimise_schedule_knapsack(tasks, constraints, weights)
        elif algorithm == "permutation":
            schedule = await optimise_schedule_permutation(tasks, constraints, weights)
        else:
            schedule = await optimise_schedule_greedy(tasks, constraints, weights)
    except Exception as e:
        logger.error(f"Schedule generation failed: {e}")
        state.error = f"Failed to generate schedule: {str(e)}"
        save_state(state)
        raise WorkflowError(f"Schedule generation failed: {str(e)}")

    # Check for unscheduled tasks
    scheduled_ids = {b.task_id for b in schedule}
    unscheduled = [t for t in tasks if t.id not in scheduled_ids]
    if unscheduled:
        warnings.append(
            f"{len(unscheduled)} task(s) could not be scheduled: "
            f"{', '.join(t.description[:30] for t in unscheduled[:3])}"
            f"{'...' if len(unscheduled) > 3 else ''}"
        )

    state.schedule = schedule
    state.schedule_warnings = warnings
    state.phase = WorkflowPhase.COMPLETE
    state.error = None
    save_state(state)

    logger.info(f"Schedule generated: {len(schedule)} tasks scheduled, {len(unscheduled)} omitted")
    return state, warnings


def get_state(session_id: str) -> WorkflowState | None:
    """Get current workflow state."""
    return load_state(session_id)


def reset_session(session_id: str) -> WorkflowState:
    """Reset a session to the beginning."""
    logger.info(f"Resetting session: {session_id}")
    state = create_session(session_id)
    return state
