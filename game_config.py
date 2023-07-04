"""

This module is for keeping track of run wide items that do not change in a run.
Ascension primarily.

"""



import logging
import os

class Settings:
    
    def __init__(self) -> None:
        self.ascension = 20
        self.simulator_log_dir = './simulator'
        if not os.path.exists(self.simulator_log_dir):
            os.makedirs(self.simulator_log_dir)




settings = Settings()
logging.basicConfig(level=logging.DEBUG)