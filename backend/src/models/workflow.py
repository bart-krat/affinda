import re
from pydantic import BaseModel, field_validator, model_validator
from enum import Enum
from typing import Optional
from .task import TaskWithConstraints, UtilityWeights, ScheduledBlock, validate_time_format


class WorkflowPhase(str, Enum):
    WEIGHTS = "weights"
    TASKS = "tasks"
    CONSTRAINTS = "constraints"
    SCHEDULE = "schedule"
    COMPLETE = "complete"


class WorkflowState(BaseModel):
    session_id: str
    phase: WorkflowPhase = WorkflowPhase.WEIGHTS
    error: Optional[str] = None  # Store error messages

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
    schedule_warnings: Optional[list[str]] = None  # Warnings about edge cases


SESSION_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,100}$")


class SetWeightsRequest(BaseModel):
    session_id: str
    weights: UtilityWeights

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("Invalid session ID format")
        return v


class SubmitTasksRequest(BaseModel):
    session_id: str
    tasks: list[str]

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("Invalid session ID format")
        return v

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Task list cannot be empty")
        if len(v) > 50:
            raise ValueError("Maximum 50 tasks allowed")
        cleaned = [t.strip() for t in v if t.strip()]
        if not cleaned:
            raise ValueError("No valid tasks provided")
        return cleaned


class SetConstraintsRequest(BaseModel):
    session_id: str
    tasks: list[TaskWithConstraints]
    window_start: str
    window_end: str

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("Invalid session ID format")
        return v

    @field_validator("window_start", "window_end")
    @classmethod
    def validate_window_time(cls, v: str) -> str:
        return validate_time_format(v)

    @model_validator(mode="after")
    def validate_window_order(self):
        start_parts = self.window_start.split(":")
        end_parts = self.window_end.split(":")
        start_minutes = int(start_parts[0]) * 60 + int(start_parts[1])
        end_minutes = int(end_parts[0]) * 60 + int(end_parts[1])
        if end_minutes <= start_minutes:
            raise ValueError("Window end time must be after start time")
        if end_minutes - start_minutes < 30:
            raise ValueError("Window must be at least 30 minutes")
        return self

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, v: list[TaskWithConstraints]) -> list[TaskWithConstraints]:
        if not v:
            raise ValueError("Task list cannot be empty")
        return v


class GenerateScheduleRequest(BaseModel):
    session_id: str

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        if not SESSION_ID_PATTERN.match(v):
            raise ValueError("Invalid session ID format")
        return v


class WorkflowResponse(BaseModel):
    state: WorkflowState
    message: str
    warnings: list[str] = []  # Any warnings to display to user
