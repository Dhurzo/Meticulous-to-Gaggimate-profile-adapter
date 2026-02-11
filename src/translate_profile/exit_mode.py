"""
Exit trigger conversion module for Meticulous to Gaggimate profile translation.

Handles conversion of Meticulous exit triggers to Gaggimate exit targets:
- Type mapping: weight→volumetric, time→time, pressure→pressure, flow→flow
- Operator mapping: >=→gte, <=→lte, >→gt, <→lt
- Relative time conversion using phase start time
- Unsupported trigger type warnings
- Deduplication of duplicate trigger types
"""

from typing import TYPE_CHECKING

from .models.gaggimate import ExitTarget
from .models.meticulous import ExitTrigger

if TYPE_CHECKING:
    from .models.gaggimate import ExitTarget as ExitTargetType
    from .models.meticulous import ExitTrigger as ExitTriggerType

# Type mapping: Meticulous trigger types to Gaggimate target types
TRIGGER_TO_TARGET_TYPE = {
    "weight": "volumetric",
    "time": "time",
    "pressure": "pressure",
    "flow": "flow",
}

# Operator mapping: Meticulous comparison operators to Gaggimate operators
OPERATOR_MAP = {
    ">=": "gte",
    "<=": "lte",
    ">": "gt",
    "<": "lt",
}

# Unsupported trigger types that will generate warnings
UNSUPPORTED_TYPES = {"piston_position", "power", "user_interaction"}


def detect_conflicting_triggers(triggers: list[ExitTrigger]) -> list[str]:
    """
    Detect contradictory exit trigger conditions.

    Looks for triggers of the same type with conditions that can never
    both be true (e.g., pressure >= 4 AND pressure <= 2).

    Args:
        triggers: List of ExitTrigger objects to check for conflicts

    Returns:
        List of conflict warning messages
    """
    warnings: list[str] = []

    # Group triggers by type
    triggers_by_type: dict[str, list[ExitTrigger]] = {}
    for trigger in triggers:
        if trigger.type not in triggers_by_type:
            triggers_by_type[trigger.type] = []
        triggers_by_type[trigger.type].append(trigger)

    # Check each type for conflicts
    for trigger_type, type_triggers in triggers_by_type.items():
        if len(type_triggers) < 2:
            continue  # No conflicts possible with single trigger

        # Check all pairs for conflicts
        for i, trigger_a in enumerate(type_triggers):
            for trigger_b in type_triggers[i + 1:]:
                conflict = _check_trigger_pair_conflict(trigger_a, trigger_b)
                if conflict:
                    warnings.append(conflict)

    return warnings


def _check_trigger_pair_conflict(trigger_a: ExitTrigger, trigger_b: ExitTrigger) -> str | None:
    """
    Check if two triggers of the same type have conflicting conditions.

    Args:
        trigger_a: First ExitTrigger
        trigger_b: Second ExitTrigger (same type as trigger_a)

    Returns:
        Conflict warning message if conflicting, None otherwise
    """
    trigger_type = trigger_a.type  # Both triggers have same type

    # Handle >= and <= conflicts (opposite bounds)
    # >= X AND <= Y is only a conflict if X > Y (impossible range)
    if trigger_a.comparison == ">=" and trigger_b.comparison == "<=":
        if trigger_a.value > trigger_b.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} >= {trigger_a.value} AND {trigger_type} <= {trigger_b.value} - conditions can never both be true"
    elif trigger_a.comparison == "<=" and trigger_b.comparison == ">=":
        if trigger_b.value > trigger_a.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} <= {trigger_a.value} AND {trigger_type} >= {trigger_b.value} - conditions can never both be true"

    # Handle > and < conflicts
    # > X AND < Y is only a conflict if X >= Y (impossible range)
    if trigger_a.comparison == ">" and trigger_b.comparison == "<":
        if trigger_a.value >= trigger_b.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} > {trigger_a.value} AND {trigger_type} < {trigger_b.value} - conditions can never both be true"
    elif trigger_a.comparison == "<" and trigger_b.comparison == ">":
        if trigger_b.value >= trigger_a.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} < {trigger_a.value} AND {trigger_type} > {trigger_b.value} - conditions can never both be true"

    # Handle >= and < conflicts (edge case)
    # >= X AND < Y is only a conflict if X >= Y (impossible range)
    if trigger_a.comparison == ">=" and trigger_b.comparison == "<":
        if trigger_a.value >= trigger_b.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} >= {trigger_a.value} AND {trigger_type} < {trigger_b.value} - conditions can never both be true"
    elif trigger_a.comparison == "<" and trigger_b.comparison == ">=":
        if trigger_b.value >= trigger_a.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} < {trigger_a.value} AND {trigger_type} >= {trigger_b.value} - conditions can never both be true"

    # Handle <= and > conflicts
    # <= X AND > Y is only a conflict if X <= Y (impossible range)
    if trigger_a.comparison == "<=" and trigger_b.comparison == ">":
        if trigger_a.value < trigger_b.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} <= {trigger_a.value} AND {trigger_type} > {trigger_b.value} - conditions can never both be true"
    elif trigger_a.comparison == ">" and trigger_b.comparison == "<=":
        if trigger_b.value < trigger_a.value:
            return f"Conflicting {trigger_type} triggers: {trigger_type} > {trigger_a.value} AND {trigger_type} <= {trigger_b.value} - conditions can never both be true"

    return None


def convert_exit_triggers(
    triggers: list[ExitTrigger],
    phase_start_time: float = 0.0
) -> tuple[list[ExitTarget], list[str]]:
    """
    Convert Meticulous exit triggers to Gaggimate exit targets.

    Args:
        triggers: List of Meticulous ExitTrigger objects
        phase_start_time: Accumulated time before this phase starts (for relative conversion)

    Returns:
        Tuple of (targets list, warnings list)
    """
    targets: list[ExitTarget] = []
    seen_types: dict[str, tuple[str, float]] = {}  # type -> (comparison, value) for deduplication
    duplicates: list[str] = []  # Track specific duplicate warnings
    warnings: list[str] = []

    # First, detect conflicting triggers
    conflict_warnings = detect_conflicting_triggers(triggers)
    for conflict in conflict_warnings:
        warnings.append(f"[Validation] {conflict}. Only the first trigger will be used.")

    for trigger in triggers:
        # Skip unsupported types with warning
        if trigger.type in UNSUPPORTED_TYPES:
            warnings.append(f"[Unsupported] {trigger.type} exit trigger is not supported by Gaggimate machines. This trigger will be ignored.")
            continue

        # Handle deduplication - skip duplicate trigger types with specific details
        if trigger.type in seen_types:
            prev_comparison, prev_value = seen_types[trigger.type]
            duplicates.append(f"[Validation] Duplicate {trigger.type} trigger: {trigger.type} {trigger.comparison} {trigger.value} (already have {trigger.type} {prev_comparison} {prev_value}). Only the first trigger will be used.")
            continue
        seen_types[trigger.type] = (trigger.comparison, trigger.value)

        # Calculate value for time triggers with relative flag
        calculated_value = trigger.value
        if trigger.type == "time" and trigger.relative:
            calculated_value = float(phase_start_time) + float(trigger.value)
        value = calculated_value

        # Create ExitTarget
        target_type = TRIGGER_TO_TARGET_TYPE.get(trigger.type, trigger.type)
        operator = OPERATOR_MAP.get(trigger.comparison, "gte")

        target = ExitTarget(
            type=target_type,
            operator=operator,
            value=value,
        )
        targets.append(target)

    # Add specific duplicate warnings
    warnings.extend(duplicates)

    return targets, warnings


# Re-export ExitTarget for convenience
__all__ = ["convert_exit_triggers", "detect_conflicting_triggers", "ExitTarget"]
