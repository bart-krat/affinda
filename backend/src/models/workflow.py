from pydantic import BaseModel
from enum import Enum
from typing import Optional
from .task import TaskWithConstraints, UtilityWeights, ScheduledBlock


class WorkflowPhase(str, Enum):
    WEIGHTS = "weights"
    TASKS = "tasks"
    CONSTRAINTS = "constraints"
    SCHEDULE = "schedule"
    COMPLETE = "complete"


class WorkflowState(BaseModel):
    session_id: str
    phase: WorkflowPhase = WorkflowPhase.WEIGHTS

    # Phase 1: Utility weights
    weights: Optional[UtilityWeights] = None

    # Phase 2: Tasks with categories
    raw_tasks: Optional[list[str]] = None
    categorised_tasks: Optional[list[dict]] = None  # {description, category}

    # Phase 3: Constraints
    tasks_with_constraints: Optional[list[TaskWithConstraints]] = None
    window_start: Optional[str] = None
    window_end: Optional[str] = None

    # Phase 4: Schedule result
    selected_algorithm: Optional[str] = None
    schedule: Optional[list[ScheduledBlock]] = None


class SetWeightsRequest(BaseModel):
    session_id: str
    weights: UtilityWeights


class SubmitTasksRequest(BaseModel):
    session_id: str
    tasks: list[str]


class SetConstraintsRequest(BaseModel):
    session_id: str
    tasks: list[TaskWithConstraints]
    window_start: str
    window_end: str


class GenerateScheduleRequest(BaseModel):
    session_id: str


class WorkflowResponse(BaseModel):
    state: WorkflowState
    message: str
