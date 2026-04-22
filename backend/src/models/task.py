import re
from pydantic import BaseModel, field_validator, model_validator
from typing import Literal


class CategoriseRequest(BaseModel):
    tasks: list[str]

    @field_validator("tasks")
    @classmethod
    def validate_tasks(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("Task list cannot be empty")
        if len(v) > 50:
            raise ValueError("Maximum 50 tasks allowed")
        cleaned = []
        for task in v:
            task = task.strip()
            if not task:
                continue
            if len(task) > 500:
                raise ValueError(f"Task description too long (max 500 chars): {task[:50]}...")
            cleaned.append(task)
        if not cleaned:
            raise ValueError("No valid tasks provided")
        return cleaned


class CategorisedTask(BaseModel):
    description: str
    category: Literal["Personal", "Health", "Work"]


class CategoriseResponse(BaseModel):
    categorised: list[CategorisedTask]


TIME_PATTERN = re.compile(r"^([01]?[0-9]|2[0-3]):([0-5][0-9])$")


def validate_time_format(time_str: str) -> str:
    """Validate HH:MM format and normalize to HH:MM."""
    if not TIME_PATTERN.match(time_str):
        raise ValueError(f"Invalid time format '{time_str}'. Use HH:MM (e.g., 09:00)")
    # Normalize to ensure leading zero
    parts = time_str.split(":")
    return f"{int(parts[0]):02d}:{parts[1]}"


class TaskWithConstraints(BaseModel):
    id: str
    description: str
    category: str
    duration_minutes: int
    fixed_start_time: str | None = None

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Duration must be at least 1 minute")
        if v > 480:  # 8 hours max per task
            raise ValueError("Duration cannot exceed 480 minutes (8 hours)")
        return v

    @field_validator("fixed_start_time")
    @classmethod
    def validate_fixed_time(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        return validate_time_format(v)

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Task description cannot be empty")
        if len(v) > 500:
            raise ValueError("Task description too long (max 500 chars)")
        return v


class DayConstraints(BaseModel):
    window_start: str
    window_end: str

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
            raise ValueError("Window end must be after window start")
        if end_minutes - start_minutes < 30:
            raise ValueError("Window must be at least 30 minutes")
        return self


class UtilityWeights(BaseModel):
    personal: float = 1.0
    health: float = 1.0
    work: float = 1.0

    @field_validator("personal", "health", "work")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Weight cannot be negative")
        if v > 10:
            raise ValueError("Weight cannot exceed 10")
        return v


class ScheduleRequest(BaseModel):
    tasks: list[TaskWithConstraints]
    constraints: DayConstraints
    weights: UtilityWeights
    algorithm: Literal["greedy", "knapsack", "permutation"] = "greedy"


class ScheduledBlock(BaseModel):
    task_id: str
    description: str
    category: str
    start_time: str
    end_time: str


class ScheduleResponse(BaseModel):
    schedule: list[ScheduledBlock]
    warnings: list[str] = []  # For edge case warnings
