"""
Optimiser module - provides scheduling algorithms for task optimization.

Available algorithms:
- greedy: Fast, schedules highest priority tasks first into earliest slots
- knapsack: Maximizes total utility within time constraints using 0/1 knapsack DP
- permutation: Brute force, tries all orderings (best for small task sets)
"""

from ..models.task import TaskWithConstraints, DayConstraints, UtilityWeights, ScheduledBlock
from .optimiser_greedy import optimise_schedule_greedy
from .optimiser_knapsack import optimise_schedule_knapsack
from .optimiser_permutation import optimise_schedule_permutation

# Default algorithm
DEFAULT_ALGORITHM = "greedy"


async def optimise_schedule(
    tasks: list[TaskWithConstraints],
    constraints: DayConstraints,
    weights: UtilityWeights,
    algorithm: str = DEFAULT_ALGORITHM,
) -> list[ScheduledBlock]:
    """
    Main entry point for schedule optimization.

    Args:
        tasks: List of tasks with constraints
        constraints: Day window constraints
        weights: Category priority weights
        algorithm: One of 'greedy', 'knapsack', 'permutation'

    Returns:
        Optimized schedule as list of scheduled blocks
    """
    if algorithm == "greedy":
        return await optimise_schedule_greedy(tasks, constraints, weights)
    elif algorithm == "knapsack":
        return await optimise_schedule_knapsack(tasks, constraints, weights)
    elif algorithm == "permutation":
        return await optimise_schedule_permutation(tasks, constraints, weights)
    else:
        # Default to greedy for unknown algorithms
        return await optimise_schedule_greedy(tasks, constraints, weights)
