"""
custom_typing.py
Provides a place to store custom types and forward declare classes, supplementing
the default typing module.

Zachary McCullough
"""


#########
# Imports
#########

# pyright: reportWildcardImportFromLibrary=false
from typing import *

# Literal type definitoins
CreatureModifiers = Literal[
    "artifact",
    "buffer",
    "beat_of_death",
    "block",
    "dexterity",
    "frail",
    "hp",
    "painful_stabs",
    "regeneration",
    "strength",
    "turns_taken",
    "vulnerable",
    "weak",
]
ResultDict = Dict[str, Dict[str, Dict[str, int]]]


# Forward declaring classes
class Attack:
    pass


class Creature:
    statuses: Dict[CreatureModifiers, Any]
    permanents: Dict[CreatureModifiers, Any]


class JawWorm(Creature):
    pass
