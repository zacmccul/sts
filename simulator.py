"""
simulator.py
Contains a class Simulator to provide the simulator code. This allows for a
consumer to create a simulation between the supported creatures, run in single
or multiprocessing, and get printed to console results.

Zachary McCullough
"""

#########
# Imports
#########

# Builtins

from concurrent.futures import ProcessPoolExecutor

import copy
import logging
import random
import time

# Customs

from creature import Creature
import custom_typing as t


#########
# Classes
#########


class Simulator:
    def __init__(
        self, left_creatures: t.List[Creature], right_creatures: t.List[Creature]
    ) -> None:
        """Initializes the simulator with the two teams.

        Args:
            left_creatures (t.List[Creature]): The side that goes first
            right_creatures (t.List[Creature]): The side that goes second
        """
        self.left_creatures = left_creatures
        self.right_creatures = right_creatures
        self.current_turn = 0

    def __get_beat_of_death(self) -> t.Tuple[int, int]:
        """Gets the beat of death damage for each side.

        Returns:
            t.Tuple[int, int]: (left_beat_total, right_beat_total)
        """
        left_beat_total = 0
        for creature in self.left_creatures:
            if "beat_of_death" in creature.permanents:
                left_beat_total += creature.permanents["beat_of_death"]
        right_beat_total = 0
        for creature in self.right_creatures:
            if "beat_of_death" in creature.permanents:
                right_beat_total += creature.permanents["beat_of_death"]
        return left_beat_total, right_beat_total

    def resolve_one_creature_turn(self, creature: Creature, is_left: bool) -> None:
        """Resolves one creature's turn.

        Args:
            creature (Creature): The creature to resolve
            is_left (bool): If they go first or not
        """
        if not creature.start_turn_resolution():
            return  # creature died

        left_beat, right_beat = self.__get_beat_of_death()

        attack = creature.take_action()

        enemy_creatures = self.right_creatures if is_left else self.left_creatures
        logging.debug(
            f"Acting Creature: {creature}. Enemy creatures: {enemy_creatures}"
        )
        targets = [enemy for enemy in enemy_creatures if enemy.alive]

        if len(targets) == 0:
            logging.info("No targets for attack")
            return
        if not attack.multi_target:
            targets = random.choices(targets, k=1)

        for target in targets:
            # for each hit in the attack
            for _ in range(attack.hits):
                # handle thorns/retaliation damage
                receiving_damage = target.take_hit(attack)
                if receiving_damage > 0:
                    creature.take_damage(receiving_damage)
                # interrupt attacks if target dies mid combo
                if not target.alive:
                    break

            # apply statuses
            if attack.statuses:
                for status in attack.statuses:
                    value = attack.statuses[status]
                    if isinstance(value, int):
                        target.statuses[status] += attack.statuses[status]
                    else:
                        target.statuses[status] = None

        if is_left and right_beat > 0:
            creature.take_damage(right_beat)
        elif not is_left and left_beat > 0:
            creature.take_damage(right_beat)

        creature.end_turn_resolution()

    def _keep_simulating(self) -> t.Tuple[bool, bool | None]:
        """Checks if the simulation should continue. If not, returns the winner.

        Returns:
            t.Tuple[bool, bool | None]: (keep_simulating, winner)
        """
        if all(not creature.alive for creature in self.right_creatures):
            return False, True
        if all(not creature.alive for creature in self.left_creatures):
            return False, False
        return True, None

    def get_state(self) -> t.Dict[str, t.Dict[str, t.List[str | t.Tuple[str, int]]]]:
        """Returns a dictionary of the current state of the simulation.

        Returns:
            t.Dict[str, t.Dict[str, t.List[str]]]: The state of the simulation.
        """
        state_dict: t.Dict[str, t.Dict[str, t.List[str | t.Tuple[str, int]]]] = {}

        def get_side_state(
            creatures: t.List[Creature],
        ) -> t.Dict[str, t.List[str | t.Tuple[str, int]]]:
            """Gets the state of a set of creatures, e.g. left creatures.

            Args:
                creatures (t.List[Creature]): The creatures to get the state of.

            Returns:
                t.Dict[str, t.List[str]]: The state of the creatures.
            """
            creature_dict: t.Dict[str, t.List[str | t.Tuple[str, int]]] = {
                "alive": [],
                "dead": [],
            }
            for creature in creatures:
                if creature.alive:
                    creature_dict["alive"].append((creature.name, creature.hp))
                else:
                    creature_dict["dead"].append(f"{creature.name}")
            return creature_dict

        state_dict["left_creatures"] = get_side_state(self.left_creatures)
        state_dict["right_creatures"] = get_side_state(self.right_creatures)
        return state_dict

    def one_battle(self) -> bool:
        """Simulates one battle between the two teams.
        Returns:
            bool: True if left team won, False if right team won.
        """
        left_won = True
        keep_simulating = True
        while keep_simulating:
            # left team turn
            for creature in self.left_creatures:
                if creature.alive:
                    self.resolve_one_creature_turn(creature, True)
                keep_simulating, left_won = self._keep_simulating()
                if not keep_simulating:
                    break
            # right team turn
            for creature in self.right_creatures:
                if creature.alive:
                    self.resolve_one_creature_turn(creature, False)
                keep_simulating, left_won = self._keep_simulating()
                if not keep_simulating:
                    break
            self.current_turn += 1
        output = f"{0} side won with the following creatures: {1}"
        side_won = "left" if left_won else "right"
        winning_creatures = self.left_creatures if left_won else self.right_creatures
        creatures = "\n".join(
            str(creature) for creature in winning_creatures if creature.alive
        )
        logging.info(output.format(side_won, creatures))
        return left_won  # type: ignore

    def _simulate_mp(
        self,
        seed: None | int | float | str | bytes | bytearray = None,
        num_iters: int = 1,
    ) -> t.Tuple[int, t.ResultDict]:
        """A helper method to simulate single threaded the battles. Used for
        multiprocessing or single process.

        Args:
            seed (None | int | float | str | bytes | bytearray, optional): The
                random seed to use, if None doens't pass any argument.
                Defaults to None.
            num_iters (int, optional): Number of iterations to run. Defaults to 1.

        Returns:
            t.Tuple[int, t.ResultDict]: (number of wins by left side,
                results dictionary)
        """
        if seed is None:
            random.seed()
        else:
            random.seed(seed)
        results: t.Dict[str, t.Dict[str, t.Dict[str, int]]] = {"left": {}, "right": {}}

        num_left_wins = 0
        # Do the simulation
        for _ in range(num_iters):
            new_sim = copy.deepcopy(self)
            result = new_sim.one_battle()
            result_state = new_sim.get_state()
            self.merge_results(results, result_state)
            num_left_wins += 1 if result else 0
        return num_left_wins, results

    @staticmethod
    def merge_results(
        results: t.ResultDict,
        result_state: t.Dict[str, t.Dict[str, t.List[str | t.Tuple[str, int]]]],
    ) -> None:
        """Merges the results of a battle into the results dictionary. Example:
        results = {'left': {'creature1': {'total_hp': 100, 'count': 1}},
                    'right': {'creature2': {'total_hp': 100, 'count': 1}}}

        Args:
            results (t.Dict[str, t.Dict[str, t.Dict[str, int]]]): The core
                results dicitonary to merge data into
            result_state (t.Dict[str,t.Dict[str, t.List[str  |  t.Tuple[str, int]]]]):
                The results of a single battle
        """
        for side in result_state:
            result_name = side.split("_")[0]  # get left or right
            for alive_or_dead in result_state[side]:
                for creature in result_state[side][alive_or_dead]:
                    name = creature[0]
                    if alive_or_dead == "dead":
                        name = creature
                    if name not in results[result_name]:
                        results[result_name][name] = {  # type: ignore
                            "total_hp": creature[1] if alive_or_dead == "alive" else 0,
                            "count": 1,
                        }
                    else:
                        name = creature[0]
                        if alive_or_dead != "alive":
                            name = creature
                        hp = creature[1] if alive_or_dead == "alive" else 0
                        results[result_name][name]["total_hp"] += hp  # type: ignore
                        results[result_name][name]["count"] += 1  # type: ignore

    @staticmethod
    def update_results(base_dict: t.ResultDict, additional_dict: t.ResultDict) -> None:
        """Updates the base_dict with the values from additional_dict

        Args:
            base_dict (t.ResultDict): The base dictionary to update
            additional_dict (t.ResultDict): The dictionary to update base_dict with
        """
        for side in additional_dict:
            for creature in additional_dict[side]:
                if creature not in base_dict[side]:
                    base_dict[side][creature] = additional_dict[side][creature]
                else:
                    base_dict[side][creature]["total_hp"] += additional_dict[side][
                        creature
                    ]["total_hp"]
                    base_dict[side][creature]["count"] += additional_dict[side][
                        creature
                    ]["count"]
        del additional_dict

    def simulate(
        self, num_battles: int = 100_000, num_cores: int = 4, seed: None | int = None
    ) -> None:
        """Simulates a number of battles between the two teams.

        Args:
            num_battles (int): Number of battles to simulate.

        Returns:
            t.Tuple[int, int]: (left_wins, right_wins)
        """
        results: t.ResultDict = {"left": {}, "right": {}}
        num_left_wins = 0
        if num_cores > 1:
            with ProcessPoolExecutor(max_workers=num_cores) as executor:
                running_tasks = [
                    executor.submit(
                        self._simulate_mp,
                        time.time_ns() if seed is not None else seed,
                        num_battles // num_cores,
                    )
                    for _ in range(num_cores)
                ]
                for i, task in enumerate(running_tasks):
                    left_wins, result_dict = task.result()
                    num_left_wins += left_wins
                    self.update_results(results, result_dict)
                    logging.info(
                        f"Simulated {i*num_cores} battles. Left win rate: "
                        f"{num_left_wins / ((i+1) * num_battles // num_cores)}"
                    )
        else:
            for i in range(num_battles):
                left_won, result_state = self._simulate_mp(
                    seed=i if seed is not None else seed
                )
                num_left_wins += left_won
                self.update_results(results, result_state)
                if i % 1000 == 0 and i != 0:
                    logging.info(
                        f"Simulated {i} battles. Left win rate: {num_left_wins / i}"
                    )
        print(f"Left win rate: {num_left_wins / num_battles}")
        print(results)

    def _simulate_search_mp(
        self, num_battles: int, base_seed: int, args: t.Dict[str, t.Any]
    ) -> t.Any:
        """_summary_

        Args:
            base_seed (int): Seeds are iterated upon by adding 1 each iter, this is the first seed.

        Returns:
            t.Any: _description_
        """

        one_side_search = None
        if "a_left_win" in args and "a_right_win" in args:
            if bool(args["a_left_win"]) ^ bool(args["a_right_win"]):
                one_side_search = bool(args["a_left_win"])
            else:
                raise ValueError(
                    f"Cannot search for both/neither a left win and a right win."
                    f'Got a_left_win: {args["a_left_win"]}, a_right_win: {args["a_right_win"]}'
                )
        elif "a_left_win" not in args and "a_right_win" not in args:
            raise ValueError(
                "Must provide a search criteria. Options: a_left_win, a_right_win"
            )
        else:
            one_side_search = (
                bool(args["a_left_win"]) if "a_left_win" in args else False
            )

        # In future expand this to check for more conditions
        if one_side_search is None:  # type: ignore
            raise ValueError(
                "Must provide a search criteria. Options: a_left_win, a_right_win"
            )

        cur_seed = base_seed
        # Do the simulation
        for _ in range(num_battles):
            new_sim = copy.deepcopy(self)
            random.seed(cur_seed)
            result = new_sim.one_battle()
            # we got a left win and want a left win, or we got a right win and want a right win
            if result == one_side_search:
                return cur_seed
            cur_seed += 1
        return None

    def simulation_search(self, /, **kwargs: t.Any) -> t.Any:
        """Performs a search over the simulation space.

        Args:
            **kwargs (t.Dict[str, t.Any]): The search criteria. Options:
                'a_left_win': Returns (true, seed) if a left win is found.
                    Return's the seed used for random for this. Cannot be used with 'a_right_win'.
                'a_right_win': Returns (true, seed) if a right win is found.
                    Return's the seed used for random for this. Cannot be used with 'a_left_win'.
                'max_battles': The maximum number of battles to run. Defaults to 1_000.
                    Set to -1 for infinite.
                'num_cores': The number of cores to use. Defaults to 4.
                    Set to 1 for single threaded. If logging is desired, MUST be set to 1.

        Returns:
            t.Any: The relevant value of the search criteria.
        """

        max_battles = 1_000
        num_cores = 4
        search_for_win = None

        print(f"kwargs: {kwargs}")

        if "num_cores" in kwargs:
            num_cores = t.cast(int, kwargs["num_cores"])
        if "max_battles" in kwargs:
            max_battles = t.cast(int, kwargs["max_battles"])
        if "a_left_win" in kwargs:
            search_for_win = True
        elif "a_right_win" in kwargs:
            search_for_win = False

        # In future we'll accept more options. For now if search_for_win is None,
        # we don't have a valid search criteria.
        if search_for_win is None:
            raise ValueError("No valid search criteria provided.")

        # this should work?
        if True:  # num_cores > 1:
            with ProcessPoolExecutor(max_workers=num_cores) as executor:
                running_tasks = [
                    executor.submit(
                        self._simulate_search_mp,
                        seed * max_battles // num_cores,
                        max_battles // num_cores,
                        kwargs,
                    )
                    for seed in range(num_cores)
                ]
                for _, task in enumerate(running_tasks):
                    winning_seed = task.result()
                    if winning_seed is not None:
                        return winning_seed
