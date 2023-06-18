import custom_typing as t
from creature import Creature

import random

class Simulator:
    
    def __init__(self, left_creatures: t.List[Creature], right_creatures: t.List[Creature]) -> None:
        self.left_creatures = left_creatures
        self.right_creatures = right_creatures

    
    def resolve_one_creature_turn(self, creature: Creature, is_left: bool) -> None:
        
        if not creature.start_turn_resolution():
            return  # creature died
        action = creature.pick_action()
        attack = creature.action_dict[action]()
        
        enemy_creatures = self.right_creatures if is_left else self.left_creatures
        targets = enemy_creatures
        if not attack.multi_target:
            targets = random.choices(enemy_creatures, k=1)
        
        for target in targets:
            # for each hit in the attack
            for _ in range(attack.hits):
                # handle thorns/retaliation damage
                receiving_damage = target.take_hit(attack)
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
        
        creature.end_turn_resolution()

    
