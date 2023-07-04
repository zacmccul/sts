from typing import Any

import custom_typing as t
import custom_typing as t
from collections import UserDict


import copy
import math
import logging
import game_constants

#####
# TODO:
#    Impelment statuses class to provide @properties automatically to anything in that dic
#   do similar for anything in permanents so we can do .permanents.strength without needing to manually code it. Make defalts
#   maybe make abstract class as they should work similarly
#   the reason for this is I want to say weakenss += 2 without worrying about does it exist yada yada yada. or if weakness in statuses. dict like but fancy
#   maybe that's the difference. Permanents are permanent anything in permanents is true, statuses will be removed if they hit 0 or w/e. Maybe need a singular status
#       to have its own logic on decay e.g. how to support poison? Some statuses don't decay off like choke/corpse explosion.
#  FIX TYPING ON SHTUFF
####


class ModifierDict(UserDict[str, t.Any]):
    def __init__(self, initial_dict: dict[str, t.Any], /, default_val: t.Any = None):
        super().__init__()
        self.update(initial_dict)
        self.default_val = default_val

        # defaults
        for key in ("strength", "dexterity"):
            if key not in self.data:
                self.data[key] = 0

    def __getattr__(self, attr: str) -> t.Any:
        if attr == 'data':
            return super().__getattribute__(attr)
        try:
            return self.data[attr]
        except KeyError:
            raise AttributeError

    def __setattr__(self, __name: str, __value: Any) -> None:
        if __name in ("data", "default_val"):
            return super().__setattr__(__name, __value)
        return super().__setattr__(__name, __value)

    def __getitem__(self, key: str) -> Any:
        if key not in self.data:
            self.data[key] = self.default_val
        return super().__getitem__(key)


class StatusesTest(ModifierDict):
    def __init__(self, initial_dict: dict[str, Any], /, default_val: Any = None):
        super().__init__(
            initial_dict, default_val=0 if default_val is None else default_val
        )

    def __setitem__(self, key: str, item: Any) -> None:
        super().__setitem__(key, item)
        if isinstance(item, int) and self.data[key] <= 0:
            del self.data[key]

    def turn_start(self) -> None:
        for kv_tup in list(self.data.items()):
            if kv_tup[1] is None:
                continue
            new_val = kv_tup[1] - 1
            if new_val <= 0:
                del self.data[kv_tup[0]]
            else:
                self.data[kv_tup[0]] = new_val


class PermanentsTest(ModifierDict):
    def __init__(self, initial_dict: dict[str, t.Any], /) -> None:
        super().__init__(initial_dict, default_val=None)


class AbstractModifier:
    """Provides the abstract class for permanents and statuses among others,
    enabling a JavaScript-esque interface to a dictionary, allowing you to call
    a = AbstractModifer()
    a.foo = 3, which will just work.
    """

    def __init__(
        self, initial_dict: dict[str, t.Any], /, default_val: t.Any = None
    ) -> None:
        self.dict = initial_dict
        self.default_val = default_val
        self.__iter__()

    def __getattr__(self, attr: str) -> t.Any:
        """Modification so that on get attribute if it doesn't start with _ it
            instead creates it in dict and assigns it to 0 to represent # of turns
            before it wears off. This supports now .unknown_attr = 3 now too.
            If it does have a _ at the beginning, revert to default behavior

        Args:
            attr (str): The attribute we're trying.
            default_val (Any): The value to populate the dict with. Defaults to None.

        Returns:
            _type_: The corresponding value.
        """

        if attr in self.dict:
            return object.__getattribute__(self, "dict")[attr]
        elif len(attr) and attr[0] != "_":
            self.dict[attr] = self.default_val
            return self.dict[attr]
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr: str, value: t.Any) -> None:
        if attr in ("dict", "_keys", "default_val"):
            super().__setattr__(attr, value)
            return
        self.dict[attr] = value

    def __contains__(self, item: t.Any) -> bool:
        return item in self.dict

    def __getitem__(self, item: str) -> t.Any:
        try:
            return self.dict[item]
        except KeyError:
            self.dict[item] = self.default_val
            return self.dict[item]

    def __iter__(self) -> t.Iterator[t.Any]:
        super().__setattr__("_keys", iter(self.dict.keys()))
        return self._keys

    def __next__(self) -> t.Any:
        key = next(self._keys)
        return self.dict[key]

    def __setitem__(self, item: str, value: t.Any) -> None:
        self.dict[item] = value
        if isinstance(value, int) and self.dict[item] <= 0:
            del self.dict[item]

    def __delitem__(self, item: str) -> None:
        del self.dict[item]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.dict})"

    def keys(self) -> t.KeysView[str]:
        return self.dict.keys()


class Statuses(AbstractModifier):
    """Tracks the Status effects and # of turns remaining for status.

    Args:
        AbstractModifier (_type_): _description_
    """

    def __init__(self, initial_dict: dict[str, t.Any], /) -> None:
        super().__init__(initial_dict, default_val=0)

    # def __getattr__(self, attr: str) -> t.Any:
    #     return super().__getattr__(attr)

    def turn_start(self) -> None:
        """Decrements each status by one, representing the # of turns it has.

        Returns:
            None
        """
        for kv_tup in list(self.dict.items()):
            if kv_tup[1] is None:
                # if the value is None, it is a permanent Status which ignores
                # turns
                continue
            new_val = kv_tup[1] - 1
            if new_val <= 0:
                del self.dict[kv_tup[0]]
            else:
                self.dict[kv_tup[0]] = new_val


class Permanents(AbstractModifier):
    def __init__(self, initial_dict: dict[str, t.Any], /) -> None:
        super().__init__(initial_dict, default_val=None)


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
        self.statuses = StatusesTest(statuses)
        self.permanents = PermanentsTest(permanents)
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

    def __setattr__(self, __name: str, __value: Any) -> None:
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

        def __setattr__(self, __name: str, __value: Any) -> None:
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
        # def __check_cond(action: str) -> bool:
        #     last_action = self.prev_actions[-1]
        #     bellow_cond = (action == 'bellow' and last_action != 'bellow') or action != 'bellow'
        #     thrash_cond = (action == 'thrash' and self.prev_actions.count('thrash') < 2) or action != 'thrash'
        #     chomp_cond = (action == 'chomp' and last_action != 'chomp') or action != 'chomp'
        #     cond = action != '' and bellow_cond and thrash_cond and chomp_cond
        #     return cond

        # TODO:
        # For actions and picking actions, maybe just make internal_pick_action an abstract method that has to be created
        # by each subclass, and each creature just has its own implementatino with some shared tools in like util.
        # that's probably the best approach :( they're just too random by creature like jaw worm or the act 4 elites.

        # # get random list of actions
        # list_of_possible_actions = list(self.action_dict.keys())
        # random.shuffle(list_of_possible_actions)

        # # initial to ensure we always go into loop
        # is_cond_met = False
        # action = ''

        # # while our action is bad, iterate over each action and check if that's
        # # valid.
        # while not is_cond_met:
        #     if len(list_of_possible_actions) == 0:
        #         logging.error('While iterating actions no action was valid!')
        #         # just pick one at random
        #         action = random.choice(list(self.action_dict.keys()))
        #         break
        #     action = list_of_possible_actions[-1]
        #     is_cond_met = cond(action)
        #     list_of_possible_actions.pop()

        # return self.action_dict[action]
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

    # def take_turn(self, **kw: dict[str, t.Any]) -> None:
    #     action = self.pick_action()
    #     self.prev_actions.append(action)
    #     if len(self.prev_actions) > 3:
    #         self.prev_actions.pop(0)
    #     self.turns_taken += 1
    #     attack = self.action_dict[action](**kw)
    #     # fill in the rest


if t.TYPE_CHECKING:
    from attack import Attack
