"""
creature.py
Contains the creature class which is the core class to be inherited by specific
creatures, e.g. the Heart and Jaw Worm.
"""

#########
# Imports
#########

# Builtins

import logging

import math

# Customs
import custom_typing as t
import game_constants

from modifier_dict import Statuses, Permanents


#########
# Classes
#########


class Creature:
    def __init__(
        self,
        hp: int | None = None,
        cur_block: int | None = None,
        statuses: dict[str, t.Any] = {},
        permanents: dict[str, t.Any] = {},
        action_dict: dict[str, t.Callable[[], "Attack"]] = {},
    ) -> None:
        self.raw_hp, self.cur_block = hp, cur_block
        self.max_hp = hp
        self.statuses = Statuses(statuses)
        self.permanents = Permanents(permanents)
        self.action_dict = action_dict
        self.turns_taken = 0
        self.alive = True if hp is not None and hp > 0 else False

        self.current_turn_taken_damage = 0

        self.prev_actions: list[t.Any] = []

    def __getattr__(self, attr: str) -> t.Any:  # type: ignore
        """Modified getattr

        Args:
            attr (str): _description_

        Returns:
            t.Any: _description_
        """
        try:
            return getattr(super, attr)
        except AttributeError:
            # Creatively check if they exist, and if they should exist,
            # define them and return. This works because everything in the game
            # should be in game_constants.

            # priority is in subclass, then creature, then permanents,
            # then statuses, so in case of name conflict that's how it's resolved
            # (but ideally should never happen!)
            # if attr in self.permanents:
            #     print('245')
            #     return self.permanents[attr]
            if attr in game_constants.ALL_PERMANENTS:
                # self.permanents.data[attr] = None
                return self.permanents[attr]
            elif attr in game_constants.ALL_STATUSES:
                return self.statuses[attr]
            raise

    def __setattr__(self, __name: str, __value: t.Any) -> None:
        if __name in game_constants.ALL_PERMANENTS:
            self.permanents[__name] = __value
            return
        elif __name in game_constants.ALL_STATUSES:
            self.statuses[__name] = __value
            return
        else:
            super().__setattr__(__name, __value)
            return

    def __contains__(self, item: t.Any) -> bool:
        return item in self.permanents or item in self.statuses

    # exists soley for typechecking to work properly.
    if t.TYPE_CHECKING:

        def __getattr__(self, _prop: t.CreatureModifiers) -> int:
            return 0

        def __setattr__(self, __name: str, __value: t.Any) -> None:
            pass

    def __repr__(self) -> str:
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            return f"{self.__class__.__name__}(hp={self.hp}, block={self.block}, permanents={self.permanents}, statuses={self.statuses})"

        return f"{self.__class__.__name__}(hp={self.hp}, block={self.block})"

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @property
    def hp(self) -> int:
        return self.raw_hp if self.raw_hp is not None else 0

    @hp.setter
    def hp(self, other: int) -> None:
        if "buffer" in self.permanents:
            self.buffer -= 1
            return
        self.raw_hp = other
        if self.raw_hp <= 0:
            self.alive = False
            self.raw_hp = 0

    @property
    def block(self) -> int:
        return self.cur_block if self.cur_block is not None else 0

    @block.setter
    def block(self, other: int) -> None:
        self.cur_block = other

    @staticmethod
    def adjust_possible_actions(
        action_list: t.List[str],
        actions_to_remove: t.List[str],
        weights: None | t.List[float] = None,
    ) -> None:
        if len(actions_to_remove) > 0:
            for action in actions_to_remove:
                action_idx = action_list.index(action)
                action_list.pop(action_idx)
                if weights is not None:
                    weights.pop(action_idx)
                    # redo probabilities
            if weights is not None:
                weights = [x / sum(weights) for x in weights]

    def pick_action(self) -> str:
        return next(iter(self.action_dict))

    def take_hit(self, attack: "Attack") -> int:
        """_summary_

        Args:
            attack (Attack): _description_

        Returns:
            int: _description_
        """
        damage_to_apply = attack.damage
        if "vulnerable" in self.statuses:
            damage_to_apply = math.floor(damage_to_apply * 1.5)

        if "intangible" in self.statuses:
            damage_to_apply = min(damage_to_apply, 1)

        outgoing_damage = 0
        self.take_damage(damage_to_apply)
        if "thorns" in self.permanents:
            outgoing_damage += self.permanents.thorns
        if "flame_barrier" in self.permanents:
            outgoing_damage += self.permanents.flame_barrier

        return outgoing_damage

    def take_damage(self, damage: int) -> None:
        if damage > self.block:
            damage = damage - self.block
            if (
                "invincible" in self.permanents
                and self.current_turn_taken_damage + damage > self.permanents.invincible
            ):
                damage = self.permanents.invincible - self.current_turn_taken_damage
            self.block = 0
            self.hp -= damage
        else:
            self.block -= damage
        logging.debug(f"{self} took {damage} damage. HP={self.hp}, Block={self.block}.")

    def start_turn_resolution(self) -> bool:
        # on first turn don't resolve start of turn effects
        if self.turns_taken == 0:
            return self.alive
        if "blur" not in self.statuses and "barricade" not in self.permanents:
            self.cur_block = 0

        return self.alive

    def end_turn_resolution(self) -> bool:
        """Resolves the end of turn effects for a creature.

        Args:
            creature (Creature): The creature to resolve the end of turn effects for, based upon statuses.

        Returns:
            bool: True if the creature is still alive, False otherwise.
        """
        if "regeneration" in self.statuses:
            self.hp = min(self.hp + self.statuses.regeneration, self.max_hp)

        self.turns_taken += 1

        # make copy of statuses and then iterate over them
        # -1 deletes keys that hit 0.
        for status in list(self.statuses.keys()):
            value = self.statuses[status]
            if status == "poison":
                self.hp -= value
            if isinstance(value, int):
                self.statuses[status] -= 1
        return self.alive

    def take_action(self) -> "Attack":
        action = self.pick_action()
        logging.info(f"{self} took action {action}.")
        attack = self.action_dict[action]()
        self.turns_taken += 1
        self.prev_actions.append(action)
        return attack


if t.TYPE_CHECKING:
    from attack import Attack
