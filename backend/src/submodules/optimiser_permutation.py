"""Permutation Scheduler: Tries all permutations to find the optimal ordering that maximizes utility."""

from datetime import datetime, timedelta
from itertools import permutations
from ..models.task import TaskWithConstraints, DayConstraints, UtilityWeights, ScheduledBlock


def parse_time(time_str: str) -> datetime:
    today = datetime.now().date()
    time_part = datetime.strptime(time_str, "%H:%M").time()
    return datetime.combine(today, time_part)


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


async def optimise_schedule_permutation(
    tasks: list[TaskWithConstraints],
    constraints: DayConstraints,
    weights: UtilityWeights,
) -> list[ScheduledBlock]:
    """
    Permutation algorithm (brute force):
    1. Place all fixed-time tasks first
    2. Try all permutations of flexible tasks
    3. For each permutation, calculate total utility achieved
    4. Return the schedule with maximum utility

    Note: Only practical for small numbers of tasks (<=8) due to O(n!) complexity
    """
    window_start = parse_time(constraints.window_start)
    window_end = parse_time(constraints.window_end)

    fixed_tasks = [t for t in tasks if t.fixed_start_time]
    flexible_tasks = [t for t in tasks if not t.fixed_start_time]

    # Build fixed schedule first
    fixed_schedule: list[ScheduledBlock] = []
    fixed_slots: list[tuple[datetime, datetime]] = []

    for task in fixed_tasks:
        start = parse_time(task.fixed_start_time)
        end = start + timedelta(minutes=task.duration_minutes)
        fixed_schedule.append(
            ScheduledBlock(
                task_id=task.id,
                description=task.description,
                category=task.category,
                start_time=format_time(start),
                end_time=format_time(end),
            )
        )
        fixed_slots.append((start, end))

    if not flexible_tasks:
        fixed_schedule.sort(key=lambda b: parse_time(b.start_time))
        return fixed_schedule

    def get_weight(category: str) -> float:
        category_lower = category.lower()
        if category_lower == "personal":
            return weights.personal
        elif category_lower == "health":
            return weights.health
        elif category_lower == "work":
            return weights.work
        return 1.0

    def find_slot(
        duration_minutes: int,
        occupied: list[tuple[datetime, datetime]]
    ) -> datetime | None:
        candidate = window_start
        while candidate + timedelta(minutes=duration_minutes) <= window_end:
            candidate_end = candidate + timedelta(minutes=duration_minutes)
            conflict = False
            next_candidate = candidate_end
            for occ_start, occ_end in sorted(occupied):
                if not (candidate_end <= occ_start or candidate >= occ_end):
                    conflict = True
                    next_candidate = occ_end
                    break
            if not conflict:
                return candidate
            candidate = next_candidate
        return None

    def evaluate_permutation(
        perm: tuple[TaskWithConstraints, ...]
    ) -> tuple[float, list[ScheduledBlock]]:
        """Try scheduling tasks in given order, return (utility, schedule)."""
        occupied = list(fixed_slots)
        perm_schedule: list[ScheduledBlock] = []
        total_utility = 0.0

        for task in perm:
            slot_start = find_slot(task.duration_minutes, occupied)
            if slot_start is not None:
                slot_end = slot_start + timedelta(minutes=task.duration_minutes)
                perm_schedule.append(
                    ScheduledBlock(
                        task_id=task.id,
                        description=task.description,
                        category=task.category,
                        start_time=format_time(slot_start),
                        end_time=format_time(slot_end),
                    )
                )
                occupied.append((slot_start, slot_end))
                # Utility = weight * duration (reward longer high-priority tasks)
                total_utility += get_weight(task.category) * task.duration_minutes

        return total_utility, perm_schedule

    # Limit permutations for performance (cap at 8 tasks = 40320 permutations)
    MAX_PERMUTATION_TASKS = 8
    if len(flexible_tasks) > MAX_PERMUTATION_TASKS:
        # Fall back to sorting by weight for large task sets
        flexible_tasks.sort(key=lambda t: -get_weight(t.category))
        _, best_schedule = evaluate_permutation(tuple(flexible_tasks))
    else:
        # Try all permutations
        best_utility = -1.0
        best_schedule: list[ScheduledBlock] = []

        for perm in permutations(flexible_tasks):
            utility, perm_schedule = evaluate_permutation(perm)
            if utility > best_utility:
                best_utility = utility
                best_schedule = perm_schedule

    # Combine fixed and best flexible schedule
    final_schedule = fixed_schedule + best_schedule
    final_schedule.sort(key=lambda b: parse_time(b.start_time))
    return final_schedule
