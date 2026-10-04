import math
import secrets
import threading
from datetime import datetime, timedelta

MIN_START_MIN = 1            
MAX_START_MIN = 60

MIN_DURATION_MIN = 5         
MAX_DURATION_MIN = 240

MIN_CAPACITY = 2             
MAX_CAPACITY = 12

EXPIRY_GRACE_SECONDS = 10
CATEGORIES = ["Lunch", "Study", "Work", "Discussion", "Tuwaiq Talk", "Other"]


class Plan:
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
        self.host_key = host_key   # secret: only the host's browser has it, cancel_plan checks it
        self.created_at = datetime.now()
        self.attendees = [host]

    def start_time(self):
        return self.created_at + timedelta(minutes=self.starts_in_min)

    def ends_at(self):
        return self.start_time() + timedelta(minutes=self.duration_min)

    def phase(self, now):
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
        return math.ceil(self.seconds_to_start(now) / 60)

    def has_joined(self, name):
        for person in self.attendees:
            if person.lower() == name.strip().lower():
                return True
        return False

    def count(self):
        return len(self.attendees)

    def is_full(self):
        return self.count() >= self.capacity


class PlanBoard:
    def __init__(self):
        self.plans = {}
        self.next_id = 1
        self.lock = threading.Lock()

    # Only call this inside "with self.lock". It does not take the lock itself,
    # and taking the same lock twice freezes the app.
    def find_alive(self, plan_id):
        plan = self.plans.get(plan_id)
        if plan is None or plan.phase(datetime.now()) == "ended":
            return None
        return plan

    def validate_input(self, title, place, host, starts_in_min, duration_min=60, capacity=10):
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
        errors = self.validate_input(title, place, host, starts_in_min, duration_min, capacity)
        if errors:
            return (False, errors[0], None, "")

        if category not in CATEGORIES:
            category = "Other"
        host_key = secrets.token_hex(4)

        with self.lock:
            plan_id = self.next_id
            self.plans[plan_id] = Plan(plan_id, title.strip(), category, place.strip(),
                                       description.strip(), host.strip(), starts_in_min,
                                       duration_min, capacity, host_key)
            self.next_id += 1
        return (True, "Plan posted", plan_id, host_key)

    def get_active_plans(self):
        now = datetime.now()
        grace = timedelta(seconds=EXPIRY_GRACE_SECONDS)
        with self.lock:
            visible = [p for p in self.plans.values() if now < p.start_time() + grace]
        return sorted(visible, key=lambda plan: plan.start_time())

    def search_plans(self, keyword):
        keyword = keyword.strip().lower()
        matches = []
        for plan in self.get_active_plans():
            text = f"{plan.title} {plan.place} {plan.category}".lower()
            if keyword in text:
                matches.append(plan)
        return matches

    def get_plan_for_participant(self, plan_id, name):
        with self.lock:
            plan = self.find_alive(plan_id)
            if plan is not None and plan.has_joined(name):
                return plan
            return None

    def join_plan(self, plan_id, name):
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
        now = datetime.now()
        with self.lock:
            ended = []
            for plan_id, plan in self.plans.items():
                if plan.phase(now) == "ended":
                    ended.append(plan_id)
            for plan_id in ended:   # delete after the loop: changing a dict while looping over it crashes
                del self.plans[plan_id]

    def rename_person(self, old, new):
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

    # For the tests only. The app never calls this.
    def demo_fast_forward(self, minutes):
        with self.lock:
            for plan in self.plans.values():
                plan.created_at -= timedelta(minutes=minutes)
