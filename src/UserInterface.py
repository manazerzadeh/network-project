import threading
import time
from typing import *


class UserInterface(threading.Thread):
    buffer: List[str] = []


def run(self):
    """
    Which the user or client sees and works with.
    This method runs every time to see whether there are new messages or not.
    """
    while True:
        message = input("Write your command:\n")
        self.buffer.append(message)
