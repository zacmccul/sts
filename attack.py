"""
attack.py
A class that represents a creature's attack. Contains info on its damage,
target, how many hits, and any statuses it applies.
"""

#########
# Imports
#########

# Builtins

from __future__ import annotations
import math

# Custom

import custom_typing as t


#########
# Classes
#########


class Attack:
    def __init__(
        self,
        damage: int | None = None,
        hits: int = 1,
        statuses: t.Dict[str, t.Any] | None = None,
        target: "Creature" | None = None,
        multi_target: bool = False,
        creature: "Creature" | None = None,
    ) -> None:
        self.damage: int = damage if damage is not None else 0
        self.hits = hits if damage is not None else 0
        self.statuses = statuses
        self.target = target
        self.multi_target = multi_target

        if creature is not None and "weak" in creature.statuses:
            self.damage = math.floor(self.damage * 0.75)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Attack):
            return (
                self.damage == __value.damage
                and self.hits == __value.hits
                and self.statuses == __value.statuses
            )
        elif isinstance(__value, int):
            return self.damage * self.hits == __value
        return False

    def __repr__(self) -> str:
        return f"Attack(damage={self.damage}, hits={self.hits}, statuses={self.statuses}, target={self.target})"


if t.TYPE_CHECKING:
    from creature import Creature
