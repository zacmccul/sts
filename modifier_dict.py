from collections import UserDict
import custom_typing as t


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
        if attr == "data":
            return super().__getattribute__(attr)
        try:
            return self.data[attr]
        except KeyError:
            raise AttributeError

    def __setattr__(self, __name: str, __value: t.Any) -> None:
        if __name in ("data", "default_val"):
            return super().__setattr__(__name, __value)
        return super().__setattr__(__name, __value)

    def __getitem__(self, key: str) -> t.Any:
        if key not in self.data:
            self.data[key] = self.default_val
        return super().__getitem__(key)


class Statuses(ModifierDict):
    def __init__(self, initial_dict: dict[str, t.Any], /, default_val: t.Any = None):
        super().__init__(
            initial_dict, default_val=0 if default_val is None else default_val
        )

    def __setitem__(self, key: str, item: t.Any) -> None:
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


class Permanents(ModifierDict):
    def __init__(self, initial_dict: dict[str, t.Any], /) -> None:
        super().__init__(initial_dict, default_val=None)
