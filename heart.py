import typing as t
import random
from game_config import settings
from creature import Creature
from attack import Attack


class Heart(Creature):
    def __init__(self, hp: int = 800, block: int = 0):
        action_dict: dict[str, t.Callable[[], Attack]] = {
            "debilitate": self.debilitate,
            "blood_shots": self.blood_shots,
            "echo": self.echo,
            "buff": self.buff,
        }

        if settings.ascension < 9:
            hp = 750

        super().__init__(hp=hp, cur_block=block, action_dict=action_dict)

        self.__num_times_buffed = 0
        if settings.ascension < 19:
            self.permanents["beat_of_death"] = 1
            self.permanents["invincible"] = 300
        else:
            self.permanents["beat_of_death"] = 2
            self.permanents["invincible"] = 200

    def pick_action(self) -> str:
        action = ""
        if self.turns_taken == 0:
            action = "debilitate"
        elif (self.turns_taken) % 3 == 0 and self.turns_taken >= 3:
            action = "buff"
        elif self.prev_actions[-1] == "blood_shots":
            action = "echo"
        elif self.prev_actions[-1] == "echo":
            action = "blood_shots"
        else:
            # 50/50
            action = "echo" if random.random() >= 0.5 else "blood_shots"
        return action

    def debilitate(self, **kw: dict[str, t.Any]) -> Attack:
        # if "enemies" in kw:
        #     for enemy in kw["enemies"]:
        #         safe_add(enemy, "statuses", {})
        #         for status in ("weak", "vulnerable", "frail"):
        #             if isinstance(enemy, Creature):
        #                 enemy.statuses[status] += 2
        return Attack(
            statuses={"weak": 2, "vulnerable": 2, "frail": 2}, multi_target=True
        )

    def blood_shots(self, **kw: dict[str, t.Any]) -> Attack:
        if settings.ascension < 4:
            return Attack(damage=2 + self.strength, hits=12)
        return Attack(damage=2 + self.strength, hits=15)

    def echo(self, **kw: dict[str, t.Any]) -> Attack:
        if settings.ascension < 4:
            return Attack(damage=40 + self.strength)
        return Attack(damage=45 + self.strength)

    def buff(self, **kw: dict[str, t.Any]) -> Attack:
        if "strength_down" in self.statuses:
            del self.statuses["strength_down"]
        self.strength += 2

        if self.__num_times_buffed == 0:
            self.permanents["artifact"] = 2
        elif self.__num_times_buffed == 1:
            self.permanents["beat_of_death"] += 1
        elif self.__num_times_buffed == 2:
            self.permanents["painful_stabs"] = None
        elif self.__num_times_buffed == 3:
            self.strength += 10
        elif self.__num_times_buffed > 3:
            self.strength += 50

        self.__num_times_buffed += 1
        return Attack()
