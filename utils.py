import typing as t
import random

def safe_add(obj: t.Any, attr_name: str, default: t.Any=None) -> bool:
    """A safe function to add an attribute to an object. Returns False if 
    the attribute already exists and nothing happens, True if the attribute
    is set with the default value.

    Args:
        obj (t.Any): Some object to set the attribute on
        attr_name (str): The name of the attribute
        default (t.Any, optional): The value to set the attribute to. 
            Defaults to None.

    Returns:
        bool: _description_
    """
    if hasattr(obj, attr_name):
        return False
    setattr(obj, attr_name, default)
    return True


def increment_status(obj: t.Any, status_name: str, increment_amount=-1):
    """On a creature like Jaw Worm, change a particular status by an amount.
    If the status doesn't exist, set it to the increment_amount if positive.
    Defaults to decrementing one like at the start of a turn.

    Args:
        obj (t.Any): The creature
        status_name (_type_): The status name, like vulnerable, weak, etc.
        increment_amount (int, optional): The amount to modify the status by. 
        Defaults to -1.
    """
    
    # ensure the obj has a statuses attribute
    safe_add(obj, 'statuses', {})
    

class RandomChooser:
    def __init__(self, elements: t.List[str], weights: t.List[float]) -> None:
        """
        Initializes the RandomChooser object with a list of elements and a corresponding list of weights.

        Args:
            elements (List[str]): List of elements to choose from.
            weights (List[float]): Corresponding weights for each element. Must sum up to 1.

        Raises:
            ValueError: If the lists elements and weights do not have the same length, or if weights do not sum to 1.
        """
        if len(elements) != len(weights):
            raise ValueError("The lists elements and weights must have the same length")

        if not sum(weights) == 1:
            raise ValueError("The weights must sum up to 1")

        self.elements = elements
        self.weights = weights

    def choose(self) -> str:
        """
        Chooses a random element from the list of elements, based on their weights.

        Returns:
            str: Chosen element.

        Raises:
            Exception: If all elements have been chosen and removed.
        """
        if not self.elements:
            raise Exception("All elements have been chosen")

        chosen = random.choices(self.elements, self.weights, k=1)[0]

        index = self.elements.index(chosen)

        self.elements.pop(index)
        self.weights.pop(index)

        if self.weights:
            total = sum(self.weights)
            self.weights = [w / total for w in self.weights]

        return chosen
