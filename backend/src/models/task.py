from pydantic import BaseModel


class CategoriseRequest(BaseModel):
    tasks: list[str]


class CategorisedTask(BaseModel):
    description: str
    category: str


class CategoriseResponse(BaseModel):
    categorised: list[CategorisedTask]


class TaskWithConstraints(BaseModel):
    id: str
    description: str
    category: str
    duration_minutes: int
    fixed_start_time: str | None = None


class DayConstraints(BaseModel):
    window_start: str
    window_end: str


class UtilityWeights(BaseModel):
    personal: float = 1.0
    health: float = 1.0
    work: float = 1.0


class ScheduleRequest(BaseModel):
    tasks: list[TaskWithConstraints]
    constraints: DayConstraints
    weights: UtilityWeights
    algorithm: str = "greedy"  # Options: greedy, knapsack, permutation


class ScheduledBlock(BaseModel):
    task_id: str
    description: str
    category: str
    start_time: str
    end_time: str


class ScheduleResponse(BaseModel):
    schedule: list[ScheduledBlock]
