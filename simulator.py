import custom_typing as t
from creature import Creature

import random
import logging

class Simulator:
    
    def __init__(self, left_creatures: t.List[Creature], right_creatures: t.List[Creature]) -> None:
        self.left_creatures = left_creatures
        self.right_creatures = right_creatures
        self.current_turn = 0
    
    def __get_beat_of_death(self) -> t.Tuple[int, int]:
        left_beat_total = 0
        for creature in self.left_creatures:
            if 'beat_of_death' in creature.permanents:
                left_beat_total += creature.permanents['beat_of_death']
        right_beat_total = 0
        for creature in self.right_creatures:
            if 'beat_of_death' in creature.permanents:
                right_beat_total += creature.permanents['beat_of_death']
        return left_beat_total, right_beat_total
        

    
    def resolve_one_creature_turn(self, creature: Creature, is_left: bool) -> None:
        
        if not creature.start_turn_resolution():
            return  # creature died

        left_beat, right_beat = self.__get_beat_of_death()
        
        attack = creature.take_action()
        
        enemy_creatures = self.right_creatures if is_left else self.left_creatures
        logging.info(f'Acting Creature: {creature}. Enemy creatures: {enemy_creatures}')
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
    
    def one_battle(self) -> bool | None:
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
        output = f'{0} side won with the following creatures: {1}'
        side_won = 'left' if left_won else 'right'
        winning_creatures = self.left_creatures if left_won else self.right_creatures
        creatures = '\n'.join(str(creature) for creature in winning_creatures if creature.alive)
        logging.info(output.format(side_won, creatures))
        return left_won
    
