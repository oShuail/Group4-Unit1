"""
logic.py - the core logic of Join Me.

Holds the data and the rules. No Streamlit imports here, so the same
code can run in app.py (web), cli_demo.py (console) and test_logic.py.
"""

import math
from datetime import datetime, timedelta

# ---------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------
MIN_START_MIN = 1          # int: earliest a plan can start (minutes from now)
MAX_START_MIN = 60         # int: latest a plan can start
CATEGORIES = ["Lunch", "Study", "Work", "Discussion", "Other"]   # list[str]


# ---------------------------------------------------------------
# Plan: one post on the board
# ---------------------------------------------------------------
class Plan:
    """One short plan that people can join."""

    def __init__(self, plan_id, title, category, place, description,
                 host, starts_in_min, created_at):
        self.id = plan_id                    # int
        self.title = title                   # str
        self.category = category             # str
        self.place = place                   # str
        self.description = description       # str (can be empty)
        self.host = host                     # str
        self.starts_in_min = starts_in_min   # int, 1 to 60
        self.created_at = created_at         # datetime
        self.attendees = [host]              # list[str], host is always first

    def start_time(self):
        """Return the datetime when the plan starts (and disappears)."""
        return self.created_at + timedelta(minutes=self.starts_in_min)

    def minutes_left(self, now):
        """Return whole minutes until the start, rounded up. Never below 0."""
        seconds = (self.start_time() - now).total_seconds()
        if seconds <= 0:
            return 0
        return math.ceil(seconds / 60)

    def is_active(self, now):
        """Return True while the plan has not started yet."""
        return now < self.start_time()

    def has_joined(self, name):
        """Return True if this name is already in the attendee list (any case)."""
        name = name.strip().lower()
        for person in self.attendees:
            if person.lower() == name:
                return True
        return False

    def count(self):
        """Return how many people are coming, host included."""
        return len(self.attendees)


# ---------------------------------------------------------------
# Quick manual check: run "python logic.py"
# (test_logic.py will replace this with real tests later)
# ---------------------------------------------------------------
if __name__ == "__main__":
    created = datetime(2026, 10, 2, 13, 0)          # a fixed, fake clock
    lunch = Plan(1, "Lunch at the cafeteria", "Lunch", "Building 4",
                 "Quick lunch", "Lama", 5, created)

    print("Starts at:      ", lunch.start_time())                                # 13:05
    print("Left at 13:00:  ", lunch.minutes_left(created))                       # 5
    print("Left at 13:04:30", lunch.minutes_left(created + timedelta(minutes=4.5)))  # 1
    print("Active at 13:04:", lunch.is_active(created + timedelta(minutes=4)))   # True
    print("Active at 13:05:", lunch.is_active(created + timedelta(minutes=5)))   # False
    print("Lama joined?    ", lunch.has_joined("lama"))                          # True
    print("Sara joined?    ", lunch.has_joined("Sara"))                          # False
    print("Count:          ", lunch.count())                                     # 1