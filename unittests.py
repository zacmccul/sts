import unittest
import creature
import jaw_worm
import heart
import random
import simulator
import game_constants
import game_status
import attack
import logging
import copy
class TestAbstractStatus(unittest.TestCase):
    
    def setUp(self):
        self.abs = creature.AbstractModifier({'frail': 2}, default_val=-1)

    def test_access(self):
        self.assertEqual(self.abs.newAttr, -1)
        self.assertEqual(self.abs.frail, 2)
    
    def test_contains(self):
        self.assertTrue('frail' in self.abs)
        self.assertFalse('newAttr' in self.abs)
        self.abs.newAttr
        self.assertTrue('newAttr' in self.abs)
        self.assertFalse('newAttr2' in self.abs)
        self.assertFalse('newAttr2' in self.abs)
    
    def test_getitem(self):
        self.assertEqual(self.abs['frail'], 2)
        self.assertEqual(self.abs['newAttr'], -1)
    
    def test_setitem(self):
        self.abs['newAttr'] = 3
        self.assertEqual(self.abs['newAttr'], 3)
    
    def test_delitems(self):
        self.abs['newAttr'] = 3
        del self.abs['newAttr']
        self.assertTrue('newAttr' not in self.abs)


class TestAbstractDerived(unittest.TestCase):
    
    def setUp(self):
        self.abs = creature.Statuses({'frail': 2})
        self.p = creature.Permanents({'artifact': 2})
    
    def test_access(self):
        self.assertEqual(self.abs.newAttr, 0)
        self.assertEqual(self.abs.frail, 2)
    
    def test_contains(self):
        self.assertTrue('frail' in self.abs)
        self.assertFalse('newAttr' in self.abs)
        self.abs.newAttr
        self.assertTrue('newAttr' in self.abs)
        self.assertTrue('artifact' in self.p)
        self.assertFalse('newAttr' in self.p)
        self.assertFalse('blur' in self.abs)
        self.assertFalse('barricade' in self.p)
        self.assertEqual(sorted(list(key for key in self.abs)), sorted(['frail', 'newAttr']))


class TestGameConstants(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()
    
    def test_constants(self) -> None:
        self.assertEqual(len(game_constants.ALL_STATUSES), 4)


class TestGameStatus(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()
    
    def test_act(self) -> None:
        self.assertEqual(game_status.state.act, 3)

class TestCreature(unittest.TestCase):
    
    def setUp(self):
        self.creature = creature.Creature(100, 10, {'frail': 2}, {'strength': 4})
        
    def test_copy(self):
        copied_creature = copy.deepcopy(self.creature)
        self.assertFalse(copied_creature is self.creature)
        self.assertFalse(copied_creature.statuses is self.creature.statuses)
        self.assertFalse(copied_creature.permanents is self.creature.permanents)
        self.assertTrue(isinstance(copied_creature.permanents, creature.PermanentsTest))
        self.assertTrue(isinstance(copied_creature.statuses, creature.StatusesTest))

    def test_access(self):
        self.assertEqual(100, self.creature.hp)
        self.assertEqual(10, self.creature.block)
        self.assertEqual(2, self.creature.frail)
        self.assertEqual(4, self.creature.strength)
        self.assertFalse('newAttr2' in self.creature.statuses)
        self.assertFalse('newAttr2' in self.creature.statuses)
        self.assertFalse('weak' in self.creature.statuses)
        self.assertFalse('weak' in self.creature.statuses)
        
        self.assertEqual(4, self.creature.permanents['strength'])
        self.creature.strength += 3
        
        self.assertEqual(7, self.creature.permanents['strength'])
        self.creature.permanents['strength'] += 3
        self.assertEqual(10, self.creature.permanents['strength'])
    
    def test_take_hit(self):
        self.creature.start_turn_resolution()
        self.assertEqual(self.creature.frail, 2)
        self.assertEqual(self.creature.strength, 4)
        self.creature.end_turn_resolution()
        
        self.creature.turns_taken = 1
        self.creature.start_turn_resolution()
        self.assertEqual(self.creature.frail, 1)
        self.creature.end_turn_resolution()
        
        self.creature.start_turn_resolution()
        self.assertTrue('frail' not in self.creature.statuses)
        
        self.creature.take_hit(attack.Attack(damage=10))
        self.assertEqual(self.creature.hp, 90)
        self.creature.statuses['vulnerable'] = 2
        self.creature.take_hit(attack.Attack(damage=10))
        self.assertEqual(self.creature.hp, 75)
        
        self.creature.permanents['thorns'] = 5
        self.assertEqual(self.creature.take_hit(attack.Attack(damage=10)), 5)
        self.assertEqual(self.creature.hp, 60)
        self.creature.permanents['flame_barrier'] = 10
        self.assertEqual(self.creature.take_hit(attack.Attack(damage=1)), 15)
        self.assertEqual(self.creature.hp, 59)
        
        self.creature.statuses['intangible'] = 1
        self.assertEqual(self.creature.take_hit(attack.Attack(damage=10)), 15)
        self.assertEqual(self.creature.hp, 58)
        
        self.creature.take_hit(attack.Attack(damage=0))
        self.assertEqual(self.creature.hp, 58)

    def test_take_damage(self):
        self.creature.take_damage(0)
        self.assertEqual(self.creature.hp, 100)
        self.assertEqual(self.creature.block, 10)
        self.creature.take_damage(5)
        self.assertEqual(self.creature.hp, 100)
        self.assertEqual(self.creature.block, 5)
        self.creature.take_damage(10)
        self.assertEqual(self.creature.hp, 95)
        self.assertEqual(self.creature.block, 0)
        self.creature.block = 10
        self.creature.take_damage(10)
        self.assertEqual(self.creature.hp, 95)
        self.assertEqual(self.creature.block, 0)
        self.creature.take_damage(1)
        self.assertEqual(self.creature.hp, 94)
        self.assertEqual(self.creature.block, 0)
    
    def test_start_turn_resolution(self):
        self.creature.turns_taken = 1
        self.creature.start_turn_resolution()
        self.creature.end_turn_resolution()
        self.assertEqual(self.creature.frail, 1)
        self.assertEqual(self.creature.strength, 4)
        self.creature.start_turn_resolution()
        self.creature.end_turn_resolution()
        self.assertTrue('frail' not in self.creature.statuses)
        
        self.creature.block = 10
        self.creature.statuses['blur'] = 1
        self.creature.start_turn_resolution()
        self.creature.end_turn_resolution()
        self.assertEqual(self.creature.block, 10)
        self.assertTrue('blur' not in self.creature.statuses)
        self.creature.start_turn_resolution()
        self.assertEqual(self.creature.block, 0)
    
    def test_end_turn_resolution(self):
        self.creature.end_turn_resolution()
        self.assertEqual(self.creature.turns_taken, 1)
        self.creature.statuses['regeneration'] = 5
        self.creature.end_turn_resolution()
        self.assertEqual(self.creature.hp, 100)
        self.assertEqual(self.creature.regeneration, 4)
        self.creature.hp = 96
        self.creature.end_turn_resolution()
        self.assertEqual(self.creature.hp, 100)

class TestHeart(unittest.TestCase):
    
    def setUp(self) -> None:
        self.h = heart.Heart()
    
    def test_contains(self):
        self.assertTrue('beat_of_death' in self.h.permanents)
        self.assertFalse('beat_of_death' in self.h.statuses)
        self.assertEqual(self.h.permanents['beat_of_death'], 2)
        self.assertTrue('beat_of_death' in self.h)
        self.assertFalse('beat_of_death' in self.h.statuses)
        self.assertTrue('beat_of_death' in self.h.permanents)
    
    def test_copy(self):
        copied_heart = copy.deepcopy(self.h)
        self.assertFalse(copied_heart is self.h)
        self.assertFalse(copied_heart.statuses is self.h.statuses)
        self.assertFalse(copied_heart.permanents is self.h.permanents)
    
    def test_moves(self):
        self.assertEqual(self.h.strength, 0)
        self.assertEqual(self.h.block, 0)
        self.assertEqual(self.h.debilitate(), 0)
        self.assertEqual(self.h.blood_shots(), 2*15)
        self.assertEqual(self.h.echo(), 45)
        self.assertEqual(self.h.buff(), 0)
    
    def test_pick_action(self):
        random.seed(0)
        self.assertEqual(self.h.pick_action(), 'debilitate')
        self.h.turns_taken += 1
        self.h.prev_actions.append('debilitate')
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 45)
        
        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 2*15)
        
        self.assertEqual(self.h.pick_action(), 'buff')
        self.h.turns_taken += 1
        self.h.prev_actions.append('buff')
        self.assertEqual(self.h.buff(), 0)
        self.assertEqual(self.h.artifact, 2)
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 47)
        
        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 4*15)
        
        self.assertEqual(self.h.pick_action(), 'buff')
        self.h.turns_taken += 1
        self.h.prev_actions.append('buff')
        self.assertEqual(self.h.buff(), 0)
        self.assertEqual(self.h.beat_of_death, 3)
        
        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 6*15)
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 49)
        
        self.assertEqual(self.h.pick_action(), 'buff')
        self.h.turns_taken += 1
        self.h.prev_actions.append('buff')
        self.assertEqual(self.h.buff(), 0)
        self.assertTrue('painful_stabs' in self.h.permanents)
        
        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 8*15)
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 51)
        
        self.assertEqual(self.h.pick_action(), 'buff')
        self.h.turns_taken += 1
        self.h.prev_actions.append('buff')
        self.assertEqual(self.h.buff(), 0)
        self.assertEqual(self.h.strength, 18)
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 45+18)
        
        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 20*15)
    
        self.assertEqual(self.h.pick_action(), 'buff')
        self.h.turns_taken += 1
        self.h.prev_actions.append('buff')
        self.assertEqual(self.h.buff(), 0)
        self.assertEqual(self.h.strength, 70)

        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 72*15)
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 45+70)

        self.assertEqual(self.h.pick_action(), 'buff')
        self.h.turns_taken += 1
        self.h.prev_actions.append('buff')
        self.assertEqual(self.h.buff(), 0)
        self.assertEqual(self.h.strength, 122)
        
        self.assertEqual(self.h.pick_action(), 'echo')
        self.h.turns_taken += 1
        self.h.prev_actions.append('echo')
        self.assertEqual(self.h.echo(), 45+122)
        
        self.assertEqual(self.h.pick_action(), 'blood_shots')
        self.h.turns_taken += 1
        self.h.prev_actions.append('blood_shots')
        self.assertEqual(self.h.blood_shots(), 124*15)
        

class TestJawWorm(unittest.TestCase):
    def setUp(self) -> None:
        self.worm = jaw_worm.JawWorm(hp=100)
    
    def test_moves(self):
        self.assertEqual(self.worm.strength, 5)
        self.assertEqual(self.worm.block, 9)
        self.assertEqual(self.worm.chomp(), 17)
        self.assertEqual(self.worm.thrash(), 12)
        self.assertEqual(self.worm.block, 14)
        self.assertEqual(self.worm.bellow(), 0)
        self.assertEqual(self.worm.block, 23)
        self.assertEqual(self.worm.strength, 10)
    
    def test_pick_action(self):
        random.seed(0)
        self.assertEqual(self.worm.pick_action(), 'chomp')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('chomp')
        self.assertEqual(self.worm.pick_action(), 'thrash')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('thrash')
        self.assertEqual(self.worm.pick_action(), 'thrash')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('thrash')
        self.assertEqual(self.worm.pick_action(), 'bellow')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('bellow')
        self.assertEqual(self.worm.pick_action(), 'chomp')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('chomp')
        self.assertEqual(self.worm.pick_action(), 'bellow')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('bellow')
        self.assertEqual(self.worm.pick_action(), 'chomp')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('chomp')
        self.assertEqual(self.worm.pick_action(), 'thrash')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('thrash')
        self.assertEqual(self.worm.pick_action(), 'bellow')
        self.worm.turns_taken += 1
        self.worm.prev_actions.append('bellow')
        
class TestUtils(unittest.TestCase):
    
    def test_random_chooser(self) -> None:
        """
        Tests the RandomChooser class.
        """
        
        from utils import RandomChooser
        chooser = RandomChooser(['a', 'b', 'c'], [0.1, 0.2, 0.7])
        chosen = chooser.choose()
        assert chosen in ['a', 'b', 'c']

        remaining_elements = chooser.elements
        remaining_weights = chooser.weights

        assert len(remaining_elements) == 2
        assert sum(remaining_weights) == 1

        for i in range(len(remaining_elements)):
            assert remaining_elements[i] != chosen

        chooser.choose()  # Second call
        assert len(chooser.elements) == 1
        assert chooser.weights[0] == 1

        chooser.choose()  # Third call
        assert len(chooser.elements) == 0

        try:
            chooser.choose()  # Fourth call, should raise an exception
            assert False, "Should have raised an exception"
        except Exception as e:
            assert str(e) == "All elements have been chosen"


class TestSimulator(unittest.TestCase):
    
    def setUp(self) -> None:
        self.s = simulator.Simulator([jaw_worm.JawWorm(hp=100)], [heart.Heart(hp=100)])
        return super().setUp()
    
    def test_resolve_one_creature_turn(self):
        random.seed(0)
        worm = self.s.left_creatures[0]
        heart = self.s.right_creatures[0]
        self.assertFalse('frail' in heart.statuses)
        self.assertFalse('weak' in heart.statuses)
        self.assertFalse('vulnerable' in heart.statuses)
        self.assertFalse('frail' in worm.statuses)
        self.assertFalse('weak' in worm.statuses)
        self.assertFalse('vulnerable' in worm.statuses)
        
        self.assertEqual(worm.strength, 5)
        
        # worm chomp attack
        self.s.resolve_one_creature_turn(worm, True)
        self.assertEqual(worm.hp, 100)
        self.assertEqual(worm.block, 7)
        self.assertEqual(heart.hp, 83)
        
        # heart debuff
        self.s.resolve_one_creature_turn(heart, False)
        self.assertEqual(worm.hp, 100)
        self.assertEqual(worm.block, 7)
        self.assertEqual(heart.hp, 83)
        self.assertTrue('frail' in worm.statuses)
        self.assertTrue('vulnerable' in worm.statuses)
        self.assertTrue('weak' in worm.statuses)

        # worm turn 2 thrash: 
        self.s.resolve_one_creature_turn(worm, True)
        self.assertEqual(worm.hp, 100)
        self.assertEqual(worm.block, 3)
        self.assertEqual(heart.hp, 74)
        self.assertEqual(worm.frail, 1)
        self.assertEqual(worm.vulnerable, 1)
        self.assertEqual(worm.weak, 1)
        
        # heart turn 2 blood_shots
        self.s.resolve_one_creature_turn(heart, False)
        self.assertEqual(worm.hp, 58)
        self.assertEqual(worm.block, 0)
        self.assertEqual(heart.hp, 74)
        
        # worm turn 3 bellow
        self.s.resolve_one_creature_turn(worm, True)
        self.assertTrue('frail' not in worm)
        self.assertTrue('vulnerable' not in worm)
        self.assertTrue('weak' not in worm)
        self.assertEqual(heart.hp, 74)
        self.assertEqual(worm.hp, 58)
        self.assertEqual(worm.block, 7)
        self.assertEqual(worm.strength, 10)
        
        # heart turn 3 echo
        self.s.resolve_one_creature_turn(heart, False)
        self.assertEqual(worm.hp, 20)
        self.assertEqual(worm.block, 0)
        self.assertEqual(heart.hp, 74)
        
        # worm turn 4 thrash
        self.s.resolve_one_creature_turn(worm, True)
        self.assertEqual(heart.hp, 57)
        self.assertEqual(worm.hp, 20)
        self.assertEqual(worm.block, 3)
        self.assertEqual(worm.strength, 10)
        
        # heart turn 4 buff
        self.s.resolve_one_creature_turn(heart, False)
        self.assertEqual(heart.strength, 2)
        self.assertEqual(heart.artifact, 2)
        
        # worm turn 5 chomp
        self.s.resolve_one_creature_turn(worm, True)
        self.assertEqual(worm.hp, 18)
        self.assertEqual(heart.hp, 35)
        
        # heart turn 5 blood shots
        self.s.resolve_one_creature_turn(heart, False)
        self.assertEqual(heart.hp, 35)
        self.assertEqual(heart.artifact, 2)
        self.assertEqual(heart.strength, 2)
        self.assertEqual(worm.hp, 0)
        self.assertTrue(not worm.alive)
    
    def test_copy(self):
        clone_sim = copy.deepcopy(self.s)
        self.assertFalse(clone_sim is self.s)
        self.assertFalse(clone_sim.left_creatures is self.s.left_creatures)
        self.assertFalse(clone_sim.right_creatures is self.s.right_creatures)
        for creature in self.s.left_creatures:
            self.assertFalse(creature is clone_sim.left_creatures[self.s.left_creatures.index(creature)])
        for creature in self.s.right_creatures:
            self.assertFalse(creature is clone_sim.right_creatures[self.s.right_creatures.index(creature)])
    
    def test_one_battle(self) -> None:
        self.assertFalse(self.s.one_battle())
    
    def test_simulate(self) -> None:
        logging.disable(logging.CRITICAL)
        self.s = simulator.Simulator([jaw_worm.JawWorm(), 
                                      jaw_worm.JawWorm(), 
                                      jaw_worm.JawWorm(), 
                                      jaw_worm.JawWorm(),
                                      jaw_worm.JawWorm(),
                                      jaw_worm.JawWorm(),], [heart.Heart()])
        self.s.simulate(num_cores=1)
        