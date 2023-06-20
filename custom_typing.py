# pyright: reportWildcardImportFromLibrary=false
from typing import * 
CreatureModifiers = Literal['artifact', 'buffer', 'beat_of_death', 'block', 'dexterity', 'frail', 'hp', 'painful_stabs', 'regeneration', 'strength', 'turns_taken', 'vulnerable', 'weak']



# Forward declaring classes
class Attack:
    pass

class Creature:
    statuses: Dict[CreatureModifiers, Any]
    permanents: Dict[CreatureModifiers, Any]

class JawWorm(Creature):
    pass

# custom types

# SubCreature = TypeVar('SubCreature', bound=Creature)
    
