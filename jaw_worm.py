import typing as t
import random
from creature import Creature
from game_status import state
from attack import Attack
from game_config import settings


class JawWorm(Creature):
    
    def __init__(self, 
                 hp: int=44, 
                 permanents: dict[str, t.Any] | None = None, 
                 block: int=0):
        action_dict: dict[str, t.Callable[[], Attack]] = {
            'chomp': self.chomp,
            'thrash': self.thrash,
            'bellow': self.bellow
        }
        if permanents is None:
            permanents = {}
        super().__init__(
            hp=hp,
            cur_block=block,
            permanents=permanents,
            action_dict=action_dict
        )
        
        if state.act >= 3:
            self.bellow()
            
    
    def pick_action(self) -> str:
        """Rules:
            1. First turn is always chomp.
            2. Cannot repeat bellow or chomp 
            3. Cannot thrash 3 times in a row.
        Weights for each turn:
            45% bellow, 25% chomp, 30% thrash.

        Returns:
            str: Chosen action string.
        """
        if self.turns_taken == 0:
            return 'chomp'
        possible_actions = ['bellow', 'chomp', 'thrash']
        weights = [.45, .25, .3]
        last_action = self.prev_actions[-1]
        action_to_remove = ''
        if last_action == 'bellow' or last_action == 'chomp':
            action_to_remove = last_action
        elif len(self.prev_actions) >= 2 and last_action == 'thrash' and self.prev_actions[-2] == 'thrash':
            action_to_remove = 'thrash'
        
        # if we need to remove an action
        if action_to_remove != '':
            # adjust weights and list of possible actions in place
            self.adjust_possible_actions(possible_actions, [action_to_remove], weights)
        
        return random.choices(possible_actions, weights, k=1)[0]

    
    def chomp(self, **kw: dict[str, t.Any]) -> Attack:
        if settings.ascension < 2:
            return Attack(damage= 11 + self.strength, creature = self)
        return Attack(damage = 12 + self.strength, creature = self)
    
    def thrash(self, **kw: dict[str, t.Any]) -> Attack:
        self.block += 5
        return Attack(damage=7 + self.strength, creature = self)

    def bellow(self, **kw: dict[str, t.Any]) -> Attack:
        if settings.ascension < 2:
            self.block += 6
            self.strength += 3
            return Attack(creature = self)
        elif settings.ascension < 17:
            self.block += 6
            self.strength += 4
            return Attack(creature = self)
        else:
            self.block += 9
            self.strength += 5
            return Attack(creature = self)
