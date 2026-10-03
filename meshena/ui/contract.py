"""contract.py - the ONE place that decides which logic we use.

When the real logic arrives, change only the module name on the next line
(ui.dummy_logic -> logic, the file in the project root). Every other file imports from here.
"""
from ui.dummy_logic import (PlanBoard, CATEGORIES, MIN_START_MIN, MAX_START_MIN,   # noqa: F401
                         MIN_CAPACITY, MAX_CAPACITY)
