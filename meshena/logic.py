"""logic.py - the rules of Join Me. No Streamlit in this file."""

import math
import secrets
import threading
from datetime import datetime, timedelta

MIN_START_MIN = 1            # a plan starts 1 to 60 minutes from now
MAX_START_MIN = 60
MIN_DURATION_MIN = 5         # and lasts 5 to 240 minutes
MAX_DURATION_MIN = 240
MIN_CAPACITY = 2             # 2 to 50 people, host included
MAX_CAPACITY = 50
EXPIRY_GRACE_SECONDS = 15    # a card stays visible this long after its wait ends
CATEGORIES = ["Lunch", "Study", "Work", "Discussion", "Tuwaiq Talk", "Other"]


class Plan:
    """One plan. Phases: waiting (before start), running, ended."""

    def __init__(self, plan_id, title, category, place, description, host,
                 starts_in_min, duration_min, capacity, host_key):
        self.id = plan_id
        self.title = title
        self.category = category
        self.place = place
        self.description = description
        self.host = host
        self.starts_in_min = starts_in_min
        self.duration_min = duration_min
        self.capacity = capacity
        self.host_key = host_key              # secret code only the host's browser keeps
        self.created_at = datetime.now()
        self.attendees = [host]               # the host is always first

    def start_time(self):
        return self.created_at + timedelta(minutes=self.starts_in_min)

    def ends_at(self):
        return self.start_time() + timedelta(minutes=self.duration_min)

    def phase(self, now):
        """Return "waiting", "running" or "ended"."""
        if now < self.start_time():
            return "waiting"
        elif now < self.ends_at():
            return "running"
        else:
            return "ended"

    def seconds_to_start(self, now):
        return max(0, int((self.start_time() - now).total_seconds()))

    def seconds_to_end(self, now):
        return max(0, int((self.ends_at() - now).total_seconds()))

    def minutes_left(self, now):
        """Minutes until the start, rounded up."""
        return math.ceil(self.seconds_to_start(now) / 60)

    def has_joined(self, name):
        """True if this name is already in the plan (any letter case)."""
        for person in self.attendees:
            if person.lower() == name.strip().lower():
                return True
        return False

    def count(self):
        return len(self.attendees)

    def is_full(self):
        return self.count() >= self.capacity


class PlanBoard:
    """All the plans, shared by every browser.

    Each public method takes the lock once. find_alive does not take it,
    so only call it inside "with self.lock" (a Lock can't be taken twice)."""

    def __init__(self):
        self.plans = {}                 # plan id -> Plan
        self.next_id = 1
        self.lock = threading.Lock()

    def find_alive(self, plan_id):
        """The plan if it is waiting or running, otherwise None."""
        plan = self.plans.get(plan_id)
        if plan is None or plan.phase(datetime.now()) == "ended":
            return None
        return plan

    def validate_input(self, title, place, host, starts_in_min, duration_min=60, capacity=10):
        """Return a list of every error (empty list = all good)."""
        errors = []
        if host.strip() == "":
            errors.append("Enter your name first")
        if title.strip() == "":
            errors.append("Title is required")
        if place.strip() == "":
            errors.append("Place is required")
        if starts_in_min < MIN_START_MIN or starts_in_min > MAX_START_MIN:
            errors.append("Start must be between 1 and 60 minutes")
        if duration_min < MIN_DURATION_MIN or duration_min > MAX_DURATION_MIN:
            errors.append("Duration must be between 5 and 240 minutes")
        if capacity < MIN_CAPACITY or capacity > MAX_CAPACITY:
            errors.append("Capacity must be between 2 and 50")
        return errors

    def create_plan(self, title, category, place, starts_in_min, description, host,
                    duration_min=60, capacity=10):
        """Return (ok, message, plan_id, host_key). On failure: first error, None, "".
        Keep the host_key: it is the only proof of being the host."""
        errors = self.validate_input(title, place, host, starts_in_min, duration_min, capacity)
        if errors:
            return (False, errors[0], None, "")

        if category not in CATEGORIES:
            category = "Other"
        host_key = secrets.token_hex(4)          # random code like "a3f9c21e"

        with self.lock:
            plan_id = self.next_id
            self.plans[plan_id] = Plan(plan_id, title.strip(), category, place.strip(),
                                       description.strip(), host.strip(), starts_in_min,
                                       duration_min, capacity, host_key)
            self.next_id += 1
        return (True, "Plan posted", plan_id, host_key)

    def get_active_plans(self):
        """Plans that are waiting (or started less than 15 s ago), soonest first."""
        now = datetime.now()
        grace = timedelta(seconds=EXPIRY_GRACE_SECONDS)
        with self.lock:
            visible = [p for p in self.plans.values() if now < p.start_time() + grace]
        return sorted(visible, key=lambda plan: plan.start_time())

    def search_plans(self, keyword):
        """Visible plans with the keyword in the title, place or category."""
        keyword = keyword.strip().lower()
        matches = []
        for plan in self.get_active_plans():
            text = f"{plan.title} {plan.place} {plan.category}".lower()
            if keyword in text:                  # an empty keyword matches everything
                matches.append(plan)
        return matches

    def get_plan_for_participant(self, plan_id, name):
        """The plan (waiting or running) if this name is in it, otherwise None."""
        with self.lock:
            plan = self.find_alive(plan_id)
            if plan is not None and plan.has_joined(name):
                return plan
            return None

    def join_plan(self, plan_id, name):
        """Join a plan. Only while it is waiting. Return (ok, message)."""
        name = name.strip()
        with self.lock:
            plan = self.find_alive(plan_id)
            if name == "":
                return (False, "Enter your name first")
            elif plan is None or plan.phase(datetime.now()) != "waiting":
                return (False, "Plan not found or expired")
            elif plan.has_joined(name):
                return (False, "You already joined")
            elif plan.is_full():
                return (False, "Plan is full")
            else:
                plan.attendees.append(name)
                return (True, "You joined")

    def leave_plan(self, plan_id, name):
        """Leave a plan (waiting or running). Return (ok, message)."""
        name = name.strip()
        with self.lock:
            plan = self.find_alive(plan_id)
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

    def cancel_plan(self, plan_id, name, host_key):
        """Delete the plan if name is the host AND host_key matches. Return (ok, message)."""
        with self.lock:
            plan = self.find_alive(plan_id)
            if plan is None:
                return (False, "Plan not found or expired")
            elif plan.host.lower() != name.strip().lower() or host_key != plan.host_key:
                return (False, "Only the host can cancel")
            else:
                del self.plans[plan_id]
                return (True, "Plan cancelled")

    def prune_ended_plans(self):
        """Delete every plan that has ended."""
        now = datetime.now()
        with self.lock:
            ended = []
            for plan_id, plan in self.plans.items():
                if plan.phase(now) == "ended":
                    ended.append(plan_id)
            for plan_id in ended:                # delete after the loop, not inside it
                del self.plans[plan_id]

    def rename_person(self, old, new):
        """Change a name in every plan. Return (ok, message)."""
        old = old.strip().lower()
        new = new.strip()
        if new == "":
            return (False, "Enter your name first")
        with self.lock:
            for plan in self.plans.values():
                if plan.host.lower() == old:
                    plan.host = new
                for i in range(len(plan.attendees)):
                    if plan.attendees[i].lower() == old:
                        plan.attendees[i] = new
        return (True, "Name updated")

    def demo_fast_forward(self, minutes):
        """FOR TESTS ONLY: move every plan back in time. The app never calls this."""
        with self.lock:
            for plan in self.plans.values():
                plan.created_at -= timedelta(minutes=minutes)
