# pyright: reportWildcardImportFromLibrary=false
from typing import * 
CreatureModifiers = Literal['artifact', 'buffer', 'beat_of_death', 'block', 'dexterity', 'frail', 'hp', 'painful_stabs', 'regeneration', 'strength', 'turns_taken', 'vulnerable', 'weak']

class Attack:
    pass

class Creature:
    statuses: Dict[CreatureModifiers, Any]
    
