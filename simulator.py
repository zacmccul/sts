import custom_typing as t
from creature import Creature

from concurrent.futures import ProcessPoolExecutor
import random
import logging
import copy


class Simulator:
    def __init__(
        self, left_creatures: t.List[Creature], right_creatures: t.List[Creature]
    ) -> None:
        self.left_creatures = left_creatures
        self.right_creatures = right_creatures
        self.current_turn = 0

    def __get_beat_of_death(self) -> t.Tuple[int, int]:
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
        if not creature.start_turn_resolution():
            return  # creature died

        left_beat, right_beat = self.__get_beat_of_death()

        attack = creature.take_action()

        enemy_creatures = self.right_creatures if is_left else self.left_creatures
        logging.debug(
            f"Acting Creature: {creature}. Enemy creatures: {enemy_creatures}"
        )
        targets = enemy_creatures
        if not attack.multi_target:
            targets = random.choices(enemy_creatures, k=1)

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

    def get_state(self) -> t.Dict[str, t.Dict[str, t.List[str]]]:
        """Returns a dictionary of the current state of the simulation.

        Returns:
            t.Dict[str, t.Dict[str, t.List[str]]]: The state of the simulation.
        """
        state_dict: t.Dict[str, t.Dict[str, t.List[str]]] = {}

        def get_side_state(
            creatures: t.List[Creature],
        ) -> t.Dict[str, t.List[t.Tuple[str]] | str]:
            """Gets the state of a set of creatures, e.g. left creatures.

            Args:
                creatures (t.List[Creature]): The creatures to get the state of.

            Returns:
                t.Dict[str, t.List[str]]: The state of the creatures.
            """
            creature_dict: t.Dict[str, t.List[str]] = {"alive": [], "dead": []}
            for creature in creatures:
                if creature.alive:
                    creature_dict["alive"].append((creature.name, creature.hp))
                else:
                    creature_dict["dead"].append(f"{creature.name}")
            return creature_dict

        state_dict["left_creatures"] = get_side_state(self.left_creatures)
        state_dict["right_creatures"] = get_side_state(self.right_creatures)
        return state_dict

    def one_battle(self) -> bool:  # | None:
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
        self, seed: None | int | float | str | bytes | bytearray = None
    ) -> t.Tuple[bool, t.Dict[str, t.Dict[str, t.List[str]]]]:
        if seed is None:
            random.seed()
        else:
            random.seed(seed)
        new_sim = copy.deepcopy(self)
        result = new_sim.one_battle()
        result_state = new_sim.get_state()
        return result, result_state

    @staticmethod
    def merge_results(results, result_state):
        for side in result_state:
            result_name = side.split("_")[0]  # get left or right
            for alive_or_dead in result_state[side]:
                for creature in result_state[side][alive_or_dead]:
                    name = creature[0]
                    if alive_or_dead == "dead":
                        name = creature
                    if name not in results[result_name]:
                        results[result_name][name] = {
                            "total_hp": creature[1] if alive_or_dead == "alive" else 0,
                            "count": 1,
                        }
                    else:
                        name = creature[0]
                        if alive_or_dead != "alive":
                            name = creature
                        hp = creature[1] if alive_or_dead == "alive" else 0
                        results[result_name][name]["total_hp"] += hp
                        results[result_name][name]["count"] += 1

    # TODO: FIX THIS
    def simulate(self, num_battles: int = 10_000, num_cores: int = 4) -> None:
        """Simulates a number of battles between the two teams.

        Args:
            num_battles (int): Number of battles to simulate.

        Returns:
            t.Tuple[int, int]: (left_wins, right_wins)
        """
        results = {"left": {}, "right": {}}
        num_left_wins = 0
        if num_cores > 1:
            with ProcessPoolExecutor(max_workers=num_cores) as executor:
                running_tasks = [
                    executor.submit(self._simulate_mp) for _ in range(num_battles)
                ]
                for i, task in enumerate(running_tasks):
                    left_won, result_state = task.result()
                    num_left_wins += 1 if left_won else 0
                    self.merge_results(results, result_state)
                    if i % 1000 == 0 and i != 0:
                        logging.info(
                            f"Simulated {i} battles. Left win rate: {num_left_wins / i}"
                        )
        for i in range(num_battles):
            left_won, result_state = self._simulate_mp(seed=i)
            num_left_wins += 1 if left_won else 0
            self.merge_results(results, result_state)
            if i % 1000 == 0 and i != 0:
                logging.info(
                    f"Simulated {i} battles. Left win rate: {num_left_wins / i}"
                )
        print(f"Left win rate: {num_left_wins / num_battles}")
        print(results)
