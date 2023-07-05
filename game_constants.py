"""
game_constants.py
This provides for dynamic set of what attributes can be keyed upon.
Zachary McCullough
"""

ALL_STATUSES = set(
    (
        "frail",
        "regeneration",
        "weak",
        "vulnerable",
    )
)

ALL_PERMANENTS = set(
    (
        "artifact",
        "beat_of_death",
        "buffer",
        "dexterity",
        "strength",
    )
)

ALL_BASE_ATTRIBUTES = set(("block", "hp", "turns_taken"))

ALL_ATTRIBUTES = ALL_BASE_ATTRIBUTES.union(ALL_STATUSES).union(ALL_PERMANENTS)
