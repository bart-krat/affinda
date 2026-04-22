"""Greedy Scheduler: Schedules tasks in order of priority weight, fitting each into the earliest available slot."""

from datetime import datetime, timedelta
from ..models.task import TaskWithConstraints, DayConstraints, UtilityWeights, ScheduledBlock


def parse_time(time_str: str) -> datetime:
    today = datetime.now().date()
    time_part = datetime.strptime(time_str, "%H:%M").time()
    return datetime.combine(today, time_part)


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


async def optimise_schedule_greedy(
    tasks: list[TaskWithConstraints],
    constraints: DayConstraints,
    weights: UtilityWeights,
) -> list[ScheduledBlock]:
    """
    Greedy algorithm:
    1. Place all fixed-time tasks first
    2. Sort remaining tasks by category weight (descending)
    3. For each task, find the earliest available slot that fits
    """
    window_start = parse_time(constraints.window_start)
    window_end = parse_time(constraints.window_end)

    fixed_tasks = [t for t in tasks if t.fixed_start_time]
    flexible_tasks = [t for t in tasks if not t.fixed_start_time]

    schedule: list[ScheduledBlock] = []
    occupied_slots: list[tuple[datetime, datetime]] = []

    # Step 1: Place fixed tasks
    for task in fixed_tasks:
        start = parse_time(task.fixed_start_time)
        end = start + timedelta(minutes=task.duration_minutes)
        schedule.append(
            ScheduledBlock(
                task_id=task.id,
                description=task.description,
                category=task.category,
                start_time=format_time(start),
                end_time=format_time(end),
            )
        )
        occupied_slots.append((start, end))

    # Step 2: Sort flexible tasks by weight (greedy choice)
    def get_weight(category: str) -> float:
        category_lower = category.lower()
        if category_lower == "personal":
            return weights.personal
        elif category_lower == "health":
            return weights.health
        elif category_lower == "work":
            return weights.work
        return 1.0

    flexible_tasks.sort(key=lambda t: -get_weight(t.category))

    # Step 3: Greedy placement - earliest available slot
    def find_earliest_slot(duration_minutes: int) -> datetime | None:
        candidate = window_start
        while candidate + timedelta(minutes=duration_minutes) <= window_end:
            candidate_end = candidate + timedelta(minutes=duration_minutes)
            conflict = False
            next_candidate = candidate_end
            for occ_start, occ_end in sorted(occupied_slots):
                if not (candidate_end <= occ_start or candidate >= occ_end):
                    conflict = True
                    next_candidate = occ_end
                    break
            if not conflict:
                return candidate
            candidate = next_candidate
        return None

    for task in flexible_tasks:
        slot_start = find_earliest_slot(task.duration_minutes)
        if slot_start is not None:
            slot_end = slot_start + timedelta(minutes=task.duration_minutes)
            schedule.append(
                ScheduledBlock(
                    task_id=task.id,
                    description=task.description,
                    category=task.category,
                    start_time=format_time(slot_start),
                    end_time=format_time(slot_end),
                )
            )
            occupied_slots.append((slot_start, slot_end))

    schedule.sort(key=lambda b: parse_time(b.start_time))
    return schedule
