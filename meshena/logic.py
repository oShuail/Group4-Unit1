"""
logic.py - the core logic of Join Me.

Holds the data and the rules. No Streamlit imports here, so the same
code can run in app.py (web), cli_demo.py (console) and test_logic.py.
"""

import math
import secrets
import threading
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
                 host, starts_in_min, created_at, host_key=""):
        self.id = plan_id                    # int
        self.title = title                   # str
        self.category = category             # str
        self.place = place                   # str
        self.description = description       # str (can be empty)
        self.host = host                     # str
        self.starts_in_min = starts_in_min   # int, 1 to 60
        self.created_at = created_at         # datetime
        self.attendees = [host]              # list[str], host is always first
        self.host_key = host_key             # str, secret code only the poster's browser keeps

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
# PlanBoard: the one shared board that holds every plan
# ---------------------------------------------------------------
class PlanBoard:
    """Stores all plans and applies the rules for creating and listing them."""

    def __init__(self):
        self.plans = {}                 # dict[int, Plan], key is the plan id
        self.next_id = 1                # int, the id the next plan will get
        self.lock = threading.Lock()    # lets only one change happen at a time

    # ---------- L3: validate and create ----------
    def validate_input(self, title, place, host, starts_in_min):
        """Check the form. Return a list of every error (empty list = all good)."""
        errors = []
        if host.strip() == "":
            errors.append("Enter your name first")
        if title.strip() == "":
            errors.append("Title is required")
        if place.strip() == "":
            errors.append("Place is required")
        if starts_in_min < MIN_START_MIN or starts_in_min > MAX_START_MIN:
            errors.append(f"Start must be between {MIN_START_MIN} and {MAX_START_MIN} minutes")
        return errors

    def create_plan(self, title, category, place, starts_in_min, description, host):
        """Add a new plan. Return (ok, message, plan_id, host_key).
        On failure plan_id is 0 and host_key is "".
        The caller must keep host_key private: it is the only proof of being the host."""
        errors = self.validate_input(title, place, host, starts_in_min)
        if errors:
            return (False, "\n".join(errors), 0, "")

        if category not in CATEGORIES:
            category = "Other"

        host_key = secrets.token_hex(4)      # random code like "a3f9c21e"

        with self.lock:
            plan_id = self.next_id
            self.plans[plan_id] = Plan(plan_id, title.strip(), category, place.strip(),
                                       description.strip(), host.strip(),
                                       starts_in_min, datetime.now(), host_key)
            self.next_id += 1
        return (True, "Plan posted", plan_id, host_key)

    # ---------- L2: listing and search ----------
    def get_active_plans(self, now=None):
        """Return the plans that have not started yet, soonest first."""
        if now is None:
            now = datetime.now()
        with self.lock:
            all_plans = list(self.plans.values())

        active = []
        for plan in all_plans:
            if plan.is_active(now):
                active.append(plan)
        return sorted(active, key=lambda plan: plan.start_time())

    def search_plans(self, keyword, now=None):
        """Return active plans whose title, place or category contain the keyword."""
        keyword = keyword.strip().lower()
        active = self.get_active_plans(now)
        if keyword == "":
            return active

        matches = []
        for plan in active:
            text = f"{plan.title} {plan.place} {plan.category}".lower()
            if keyword in text:
                matches.append(plan)
        return matches


    # ---------- L4: join, leave, cancel ----------
    def _find_active(self, plan_id, now):
        """Helper: return the plan if it exists and is still active, else None.
        Call it only while holding self.lock."""
        plan = self.plans.get(plan_id)
        if plan is None or not plan.is_active(now):
            return None
        return plan

    def join_plan(self, plan_id, name, now=None):
        """Add name to the plan's attendees. Return (ok, message)."""
        if now is None:
            now = datetime.now()
        name = name.strip()

        with self.lock:
            plan = self._find_active(plan_id, now)
            if name == "":
                return (False, "Enter your name first")
            elif plan is None:
                return (False, "Plan not found or expired")
            elif plan.has_joined(name):
                return (False, "You already joined")
            else:
                plan.attendees.append(name)
                return (True, f"You joined: {plan.title}")

    def leave_plan(self, plan_id, name, now=None):
        """Remove name from the plan's attendees. Return (ok, message)."""
        if now is None:
            now = datetime.now()
        name = name.strip()

        with self.lock:
            plan = self._find_active(plan_id, now)
            if plan is None:
                return (False, "Plan not found or expired")
            elif plan.host.lower() == name.lower():
                return (False, "The host cannot leave, cancel instead")
            elif not plan.has_joined(name):
                return (False, "You are not in this plan")
            else:
                for person in plan.attendees:
                    if person.lower() == name.lower():
                        plan.attendees.remove(person)
                        break
                return (True, "You left the plan")

    def cancel_plan(self, plan_id, name, host_key, now=None):
        """Delete the plan if name is its host AND host_key matches. Return (ok, message)."""
        if now is None:
            now = datetime.now()
        name = name.strip()

        with self.lock:
            plan = self._find_active(plan_id, now)
            if plan is None:
                return (False, "Plan not found or expired")
            elif plan.host.lower() != name.lower() or host_key != plan.host_key:
                return (False, "Only the host can cancel")
            else:
                del self.plans[plan_id]
                return (True, "Plan cancelled")



# ---------------------------------------------------------------
# Quick manual check: run "python logic.py"
# (test_logic.py will replace this with real tests later)
# ---------------------------------------------------------------
if __name__ == "__main__":
    board = PlanBoard()
    ok, msg, lunch_id, lama_key = board.create_plan("Lunch at the cafeteria", "Lunch",
                                                    "Building 4", 5, "Quick lunch", "Lama")
    print("Posted:", msg, "| id =", lunch_id, "| Lama's key =", lama_key)
    print("Bad form:", board.create_plan("", "Lunch", "", 5, "", "Sara"))

    print("\n--- Join ---")
    print(board.join_plan(lunch_id, "Sara"))      # (True, 'You joined: ...')
    print(board.join_plan(lunch_id, "sara"))      # (False, 'You already joined')
    print(board.join_plan(lunch_id, ""))          # (False, 'Enter your name first')
    print(board.join_plan(99, "Reem"))            # (False, 'Plan not found or expired')
    print(board.join_plan(lunch_id, "Reem"))      # (True, ...)
    print("Attendees:", board.plans[lunch_id].attendees, "| count =", board.plans[lunch_id].count())

    print("\n--- Leave ---")
    print(board.leave_plan(lunch_id, "Lama"))     # host cannot leave
    print(board.leave_plan(lunch_id, "Huda"))     # not in this plan
    print(board.leave_plan(lunch_id, "Reem"))     # (True, 'You left the plan')
    print("Attendees:", board.plans[lunch_id].attendees)

    print("\n--- Cancel ---")
    print(board.cancel_plan(lunch_id, "Sara", lama_key))      # wrong name
    print(board.cancel_plan(lunch_id, "Lama", "wrongkey"))    # impostor typed "Lama"
    print(board.cancel_plan(lunch_id, "Lama", ""))            # impostor, no key
    print(board.cancel_plan(lunch_id, "Lama", lama_key))      # (True, 'Plan cancelled')
    print("Plans left:", len(board.get_active_plans()))

    print("\n--- Late click ---")
    ok, msg, quick_id, noura_key = board.create_plan("Coffee", "Other", "Cafe", 1, "", "Noura")
    one_min_later = datetime.now() + timedelta(minutes=1)
    print(board.join_plan(quick_id, "Sara", now=one_min_later))  # expired
