"""Knapsack Scheduler: Maximizes total utility value within the time window constraint."""

from datetime import datetime, timedelta
from ..models.task import TaskWithConstraints, DayConstraints, UtilityWeights, ScheduledBlock


def parse_time(time_str: str) -> datetime:
    today = datetime.now().date()
    time_part = datetime.strptime(time_str, "%H:%M").time()
    return datetime.combine(today, time_part)


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


async def optimise_schedule_knapsack(
    tasks: list[TaskWithConstraints],
    constraints: DayConstraints,
    weights: UtilityWeights,
) -> list[ScheduledBlock]:
    """
    Knapsack algorithm:
    1. Place all fixed-time tasks first (must be scheduled)
    2. Calculate remaining capacity
    3. Use 0/1 knapsack DP to select flexible tasks that maximize utility
    4. Schedule selected tasks in priority order
    """
    window_start = parse_time(constraints.window_start)
    window_end = parse_time(constraints.window_end)
    total_minutes = int((window_end - window_start).total_seconds() / 60)

    fixed_tasks = [t for t in tasks if t.fixed_start_time]
    flexible_tasks = [t for t in tasks if not t.fixed_start_time]

    schedule: list[ScheduledBlock] = []
    occupied_slots: list[tuple[datetime, datetime]] = []

    # Step 1: Place fixed tasks
    fixed_time_used = 0
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
        fixed_time_used += task.duration_minutes

    # Step 2: Calculate available capacity
    capacity = total_minutes - fixed_time_used

    if capacity <= 0 or not flexible_tasks:
        schedule.sort(key=lambda b: parse_time(b.start_time))
        return schedule

    # Step 3: Get weights for utility calculation
    def get_weight(category: str) -> float:
        category_lower = category.lower()
        if category_lower == "personal":
            return weights.personal
        elif category_lower == "health":
            return weights.health
        elif category_lower == "work":
            return weights.work
        return 1.0

    # Convert to integer values for DP (scale by 100 for precision)
    n = len(flexible_tasks)
    values = [int(get_weight(t.category) * 100) for t in flexible_tasks]
    durations = [t.duration_minutes for t in flexible_tasks]

    # Step 4: 0/1 Knapsack DP
    # dp[i][w] = max value using first i items with capacity w
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        for w in range(capacity + 1):
            if durations[i - 1] <= w:
                dp[i][w] = max(
                    dp[i - 1][w],
                    dp[i - 1][w - durations[i - 1]] + values[i - 1]
                )
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtrack to find selected tasks
    selected_indices = []
    w = capacity
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected_indices.append(i - 1)
            w -= durations[i - 1]

    selected_tasks = [flexible_tasks[i] for i in selected_indices]
    selected_tasks.sort(key=lambda t: -get_weight(t.category))

    # Step 5: Schedule selected tasks
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

    for task in selected_tasks:
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
