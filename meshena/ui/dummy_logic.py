"""dummy_logic.py - temporary stand-in for logic.py.

Same names, arguments and return types as the contract, so the UI only needs
to change one import line later. Plans live in memory only.
Messages stay in English (the UI translates them).
"""
from datetime import datetime, timedelta
import math

# ---- Constants (contract) ----
MIN_START_MIN = 1
MAX_START_MIN = 60
MIN_DURATION_MIN = 5
MAX_DURATION_MIN = 240
MIN_CAPACITY = 2
MAX_CAPACITY = 50
EXPIRY_GRACE_SECONDS = 15   # a card stays visible this long after the wait ends
CATEGORIES = ["Lunch", "Study", "Work", "Discussion", "Tuwaiq Talk", "Other"]


def _seconds(delta):
    """Whole seconds in a timedelta, rounded up, never below zero."""
    return max(0, math.ceil(delta.total_seconds()))


class Plan:
    """One post: a short plan that starts in a few minutes and then lasts a while."""

    def __init__(self, plan_id, title, category, place, description, host,
                 starts_in_min, duration_min, capacity=10):
        self.id = plan_id
        self.title = title
        self.category = category
        self.place = place
        self.description = description
        self.host = host
        self.starts_in_min = starts_in_min
        self.duration_min = duration_min
        self.capacity = capacity   # most people allowed (host included)
        self.created_at = datetime.now()
        self.attendees = [host]  # the host is always first

    def start_time(self):
        return self.created_at + timedelta(minutes=self.starts_in_min)

    def ends_at(self):
        return self.start_time() + timedelta(minutes=self.duration_min)

    def phase(self, now):
        """'waiting' (joinable), 'running' (started) or 'ended'."""
        if now < self.start_time():
            return "waiting"
        if now < self.ends_at():
            return "running"
        return "ended"

    def seconds_to_start(self, now):
        return _seconds(self.start_time() - now)

    def seconds_to_end(self, now):
        return _seconds(self.ends_at() - now)

    def minutes_left(self, now):
        """Whole minutes until the start (rounded up)."""
        return math.ceil(self.seconds_to_start(now) / 60)

    def is_active(self, now):
        return self.phase(now) == "waiting"

    def has_joined(self, name):
        return name in self.attendees

    def count(self):
        return len(self.attendees)

    def is_full(self):
        return self.count() >= self.capacity


class PlanBoard:
    """The shared board that holds every plan."""

    def __init__(self):
        self.plans = []
        self.next_id = 1
        self._add_demo_data()

    # ---- helpers ----
    def _add_demo_data(self):
        # title, category, place, host, starts in, duration, capacity, other attendees, description
        demo = [
            ("قهوة سريعة", "Other", "بوابة الكافيه", "Huda", 1, 30, 4, [],
             "نرجع للمحاضرة قريباً."),
            ("غداء في الكافتيريا", "Lunch", "مبنى 4، الدور الأرضي", "Lama", 5, 60, 6, ["Reem"],
             "غداء سريع بين المحاضرات."),
            ("مشي وسوالف", "Other", "حديقة الجامعة", "Dana", 8, 20, 5, ["Joud"],
             "عشر دقايق هوا نقي قبل المحاضرة الجاية."),
            ("مراجعة حلقات بايثون", "Study", "المكتبة، طاولة 3", "Sara", 12, 90, 8, ["Maha"],
             "نتدرب على for و while سوا."),
            ("شرائح بكرة", "Work", "مبنى 2، قاعة 118", "Reem", 15, 120, 6, ["Huda", "Dana"],
             "نخلّص الشرائح لبكرة، جيبوا لابتوباتكم."),
            ("مقاعد لحديث طويق", "Tuwaiq Talk", "القاعة الرئيسية", "Dana", 18, 60, 10, ["Lama"],
             "نحجز مقاعد سوا قرب الأمام."),
            ("نناقش فكرة المشروع", "Discussion", "المعمل 2", "Noura", 20, 60, 6,
             ["Huda", "Reem"], ""),
            ("تدريب على العرض", "Work", "المعمل 1", "Joud", 25, 45, 4, ["Sara"],
             "نجرّب العرض خمس دقايق مرة وحدة."),
            ("مجموعة مذاكرة للميدتيرم", "Study", "المكتبة، الدور الثاني", "Maha", 30, 120, 6,
             ["Lama", "Reem", "Huda", "Dana", "Noura"],
             "نراجع أسئلة الميدتيرم السابقة سوا."),
        ]
        for title, cat, place, host, start, duration, cap, others, desc in demo:
            plan = Plan(self.next_id, title, cat, place, desc, host, start, duration, cap)
            plan.attendees += others
            self.plans.append(plan)
            self.next_id += 1

    def _alive(self, plan_id):
        """Return the plan if it is waiting or running, otherwise None."""
        now = datetime.now()
        for plan in self.plans:
            if plan.id == plan_id and plan.phase(now) != "ended":
                return plan
        return None

    # ---- contract methods ----
    def validate_input(self, title, place, host, starts_in_min, duration_min=60, capacity=10):
        errors = []
        if not host.strip():
            errors.append("Enter your name first")
        if not title.strip():
            errors.append("Title is required")
        if not place.strip():
            errors.append("Place is required")
        if not MIN_START_MIN <= starts_in_min <= MAX_START_MIN:
            errors.append("Start must be between 1 and 60 minutes")
        if not MIN_DURATION_MIN <= duration_min <= MAX_DURATION_MIN:
            errors.append("Duration must be between 5 and 240 minutes")
        if not MIN_CAPACITY <= capacity <= MAX_CAPACITY:
            errors.append("Capacity must be between 2 and 50")
        return errors

    def create_plan(self, title, category, place, starts_in_min, description, host,
                    duration_min=60, capacity=10):
        errors = self.validate_input(title, place, host, starts_in_min, duration_min, capacity)
        if errors:
            return False, errors[0], None
        plan = Plan(self.next_id, title.strip(), category, place.strip(),
                    description.strip(), host.strip(), starts_in_min, duration_min, capacity)
        self.plans.append(plan)
        self.next_id += 1
        return True, "Plan posted", plan.id

    def get_active_plans(self):
        """Waiting plans, plus plans inside the grace window. Soonest first."""
        now = datetime.now()
        grace = timedelta(seconds=EXPIRY_GRACE_SECONDS)
        visible = [p for p in self.plans if now < p.start_time() + grace]
        return sorted(visible, key=lambda p: p.start_time())

    def search_plans(self, keyword):
        word = keyword.strip().lower()
        return [p for p in self.get_active_plans()
                if word in p.title.lower() or word in p.place.lower() or word in p.category.lower()]

    def get_plan_for_participant(self, plan_id, name):
        """The plan (waiting or running) if this name is in it, otherwise None."""
        plan = self._alive(plan_id)
        if plan is not None and plan.has_joined(name):
            return plan
        return None

    def join_plan(self, plan_id, name):
        if not name.strip():
            return False, "Enter your name first"
        plan = self._alive(plan_id)
        if plan is None or plan.phase(datetime.now()) != "waiting":
            return False, "Plan not found or expired"
        if plan.has_joined(name):
            return False, "You already joined"
        if plan.is_full():
            return False, "Plan is full"
        plan.attendees.append(name)
        return True, "You joined"

    def leave_plan(self, plan_id, name):
        plan = self._alive(plan_id)
        if plan is None:
            return False, "Plan not found or expired"
        if plan.host == name:
            return False, "The host cannot leave, cancel instead"
        if not plan.has_joined(name):
            return False, "You are not in this plan"
        plan.attendees.remove(name)
        return True, "You left the plan"

    def cancel_plan(self, plan_id, name):
        plan = self._alive(plan_id)
        if plan is None:
            return False, "Plan not found or expired"
        if plan.host != name:
            return False, "Only the host can cancel"
        self.plans.remove(plan)
        return True, "Plan cancelled"

    def prune_ended_plans(self):
        """Remove plans whose time is over."""
        now = datetime.now()
        self.plans = [p for p in self.plans if p.phase(now) != "ended"]

    def rename_person(self, old, new):
        """Change a person's name everywhere (host name and attendee lists)."""
        new = new.strip()
        if not new:
            return False, "Enter your name first"
        for plan in self.plans:
            if plan.host == old:
                plan.host = new
            plan.attendees = [new if person == old else person for person in plan.attendees]
        return True, "Name updated"

    # ---- dummy only ----
    def demo_fast_forward(self, minutes):
        """Move every plan back in time so phases can be tested quickly."""
        for plan in self.plans:
            plan.created_at -= timedelta(minutes=minutes)
