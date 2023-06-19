"""

This module is for keeping track of run wide items that do not change in a run.
Ascension primarily.

"""



import logging

class Settings:
    
    def __init__(self) -> None:
        self.ascension = 20




settings = Settings()
logging.basicConfig(level=logging.DEBUG)