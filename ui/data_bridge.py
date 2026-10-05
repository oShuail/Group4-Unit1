"""Compatibility bridge between the preserved Mashina UI and the project core.

The visual layer from the original UI expects dictionary-shaped plans and
function calls. The current core exposes Plan / PlanBoard objects. This file
translates between them without changing the visual markup or CSS.
"""
from __future__ import annotations

from datetime import datetime, timedelta
import math
import inspect
import streamlit as st

from ui.contract import (
    CATEGORIES, MIN_START_MIN, MAX_START_MIN, EXPIRY_GRACE_SECONDS as CORE_EXPIRY_GRACE_SECONDS
)
from ui.strings import CAT_AR

# ADDED: the new core does not provide visual theme/image metadata.
# If the old dummy_data.py is still present, reuse it so the design is exactly
# the same. Otherwise use a visual-only fallback; no business logic comes from it.
try:
    from dummy_data import CATS as _OLD_CATS, CAT_NAMES as _OLD_CAT_NAMES, IMAGES as _OLD_IMAGES
except Exception:
    _OLD_CATS = _OLD_CAT_NAMES = _OLD_IMAGES = None

# ADDED: restore the original blue/green Mashina palette instead of the temporary purple fallback.
# The current core has different category names, so each one is mapped to the closest old UI color.
_FALLBACK_COLORS = {
    "Lunch": ("#F3ECF8", "#8056A0"),
    "Study": ("#EEE7F6", "#6C4A8B"),
    "Work": ("#F6EFF9", "#8A63A6"),
    "Discussion": ("#F1EAF7", "#76548F"),
    "Tuwaiq Talk": ("#E9DFF2", "#5E3C78"),
    "Other": ("#F5F0F8", "#9270A8"),
}

CATS = _OLD_CATS or {
    cat: {"bg": _FALLBACK_COLORS.get(cat, ("#F4EFF7", "#5E3C78"))[0],
          "deep": _FALLBACK_COLORS.get(cat, ("#F4EFF7", "#5E3C78"))[1],
          "mat": ":material/category:"}
    for cat in CATEGORIES
}
# ADDED: Tuwaiq Talk visual-only override; no business-logic change.
if "Tuwaiq Talk" in CATS:
    CATS["Tuwaiq Talk"] = {**CATS["Tuwaiq Talk"], "bg": "#E9DFF2", "deep": "#5E3C78", "mat": ":material/record_voice_over:"}

CAT_NAMES = _OLD_CAT_NAMES or {cat: CAT_AR.get(cat, cat) for cat in CATEGORIES}
IMAGES = _OLD_IMAGES or {
    "Lunch": [{"id": "ic_food"}],
    "Study": [{"id": "ic_study"}],
    "Work": [{"id": "ic_work"}],
    "Discussion": [{"id": "ic_meet"}],
    "Tuwaiq Talk": [{"id": "ic_talk"}],  # ADDED: dedicated talk icon
    "Other": [{"id": "ic_walk"}],
}
EXPIRY_GRACE_SECONDS = CORE_EXPIRY_GRACE_SECONDS  # ADDED: use the real core grace period.

_BOARD = None
_PLAN_CACHE = {}
# UI-only cancellation registry. Kept outside logic.py so the project core stays untouched.
_CANCELLED_PLAN_NOTICES = {}

# UI-only participant identity. The core still receives a plain string, but the
# string carries a session UID so two people with the same display name remain
# distinct. All UI rendering decodes it back to the original display name.
_USER_TOKEN_PREFIX = "__mashina_user__::"
_USER_TOKEN_SEP = "::"


def participant_identity(name=None, uid=None):
    display = (name if name is not None else st.session_state.get("name", "")).strip()
    session_uid = (uid if uid is not None else st.session_state.get("uid", "")).strip()
    if not display or not session_uid:
        return display
    return f"{_USER_TOKEN_PREFIX}{session_uid}{_USER_TOKEN_SEP}{display}"


def participant_display(value):
    text = str(value or "")
    if not text.startswith(_USER_TOKEN_PREFIX):
        return text
    payload = text[len(_USER_TOKEN_PREFIX):]
    _uid, sep, display = payload.partition(_USER_TOKEN_SEP)
    return display if sep else text


def participant_uid(value):
    text = str(value or "")
    if not text.startswith(_USER_TOKEN_PREFIX):
        return ""
    payload = text[len(_USER_TOKEN_PREFIX):]
    uid, sep, _display = payload.partition(_USER_TOKEN_SEP)
    return uid if sep else ""


def _same_current_participant(raw_value, display_name=None):
    current = participant_identity(display_name)
    raw = str(raw_value or "")
    if raw.startswith(_USER_TOKEN_PREFIX):
        return bool(current and raw.lower() == current.lower())
    # Legacy plans created before this UI-only identity layer stored the visible
    # name directly. Keep them readable, while all new plans use the UID token.
    legacy_name = (display_name if display_name is not None else st.session_state.get("name", "")).strip()
    return bool(legacy_name and raw.strip().lower() == legacy_name.lower())


def set_board(board):
    global _BOARD
    _BOARD = board
    return board


def board():
    if _BOARD is None:
        raise RuntimeError("UI board was not bound. Call set_board(board) before rendering.")
    return _BOARD


def _board_plans():
    """Return a stable snapshot whether PlanBoard.plans is a dict or a list."""
    b = board()
    raw = getattr(b, "plans", {})
    lock = getattr(b, "lock", None)

    # ADDED: real logic.py stores plans in a dict; the older dummy used a list.
    if lock is not None:
        with lock:
            raw = getattr(b, "plans", {})
            return list(raw.values()) if isinstance(raw, dict) else list(raw or [])
    return list(raw.values()) if isinstance(raw, dict) else list(raw or [])


def _remember(plans):
    for plan in plans or []:
        _PLAN_CACHE[getattr(plan, "id", None)] = plan
    return plans


def _plan_obj(plan_id):
    if plan_id is None:
        return None
    b = board()
    # ADDED: always verify against the real board so a cancelled/pruned plan is not
    # accidentally returned from the UI cache.
    for plan in _board_plans():
        if getattr(plan, "id", None) == plan_id:
            _PLAN_CACHE[plan_id] = plan
            return plan
    _PLAN_CACHE.pop(plan_id, None)
    try:
        p = b.get_plan_for_participant(plan_id, participant_identity())
    except Exception:
        p = None
    if p is not None:
        _PLAN_CACHE[plan_id] = p
    return p


def _start_dt(plan):
    fn = getattr(plan, "start_time", None)
    if callable(fn):
        return fn()
    return getattr(plan, "created_at", datetime.now()) + timedelta(minutes=getattr(plan, "starts_in_min", 0))


def _end_dt(plan):
    fn = getattr(plan, "ends_at", None)
    if callable(fn):
        return fn()
    return _start_dt(plan) + timedelta(minutes=getattr(plan, "duration_min", 60))


def _minute_of_day(dt):
    return int(dt.hour * 60 + dt.minute)


def _owner_uid(plan):
    # Ownership follows the UID embedded in the UI-only participant token.
    # ui_owner_uid is retained for compatibility with plans already in memory.
    explicit = getattr(plan, "ui_owner_uid", None)
    if explicit:
        return explicit

    raw_host = getattr(plan, "host", "")
    encoded_uid = participant_uid(raw_host)
    if encoded_uid:
        return encoded_uid

    plan_id = getattr(plan, "id", None)
    core_key = getattr(plan, "host_key", "")
    session_key = st.session_state.get("_host_keys", {}).get(plan_id, "")
    if not session_key and st.session_state.get("my_plan_id") == plan_id:
        session_key = st.session_state.get("my_host_key", "")
    if core_key and session_key == core_key:
        return st.session_state.get("uid", "")
    return f"core-host:{participant_display(raw_host)}:{plan_id}"


def _as_dict(plan):
    if plan is None:
        return None
    _PLAN_CACHE[getattr(plan, "id", None)] = plan
    start_dt = _start_dt(plan)
    end_dt = _end_dt(plan)
    category = getattr(plan, "category", CATEGORIES[0] if CATEGORIES else "Other")
    default_img = IMAGES.get(category, [{}])[0].get("id")
    raw_host = getattr(plan, "host", "")
    raw_attendees = list(getattr(plan, "attendees", []))
    return {
        "id": getattr(plan, "id", None),
        "owner": _owner_uid(plan),
        "host": participant_display(raw_host),
        "_host_identity": raw_host,
        "title": getattr(plan, "title", ""),
        "category": category,
        "start": getattr(plan, "ui_start_min", _minute_of_day(start_dt)),
        "end": getattr(plan, "ui_end_min", _minute_of_day(end_dt)),
        "place": getattr(plan, "place", ""),
        "description": getattr(plan, "description", ""),
        "starts_in_min": int(getattr(plan, "starts_in_min", 0)),
        "image": getattr(plan, "ui_image", default_img),
        "building": getattr(plan, "ui_building", ""),
        "attendees": [participant_display(person) for person in raw_attendees],
        "_attendee_identities": raw_attendees,
        "capacity": int(getattr(plan, "capacity", 10)),
    }


def store():
    b = board()
    plans = _board_plans()
    if not plans:
        try:
            plans = list(b.get_active_plans())
        except Exception:
            plans = []
    _remember(plans)
    return {"plans": [_as_dict(p) for p in plans], "ver": st.session_state.get("_bridge_ver", 0)}


def _store():
    return store()


def bump():
    st.session_state["_bridge_ver"] = st.session_state.get("_bridge_ver", 0) + 1


def get_plan(plan_id):
    return _as_dict(_plan_obj(plan_id))


def wait_end_at(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    return _start_dt(obj) if obj is not None else datetime.now()


def plan_end_at(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    return _end_dt(obj) if obj is not None else datetime.now()


def remaining(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    if obj is None:
        return 0
    now = datetime.now()
    fn = getattr(obj, "seconds_to_start", None)
    if callable(fn):
        return max(0, int(fn(now)))
    return max(0, math.ceil((_start_dt(obj) - now).total_seconds()))


def plan_seconds_left(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    if obj is None:
        return 0
    now = datetime.now()
    fn = getattr(obj, "seconds_to_end", None)
    if callable(fn):
        return max(0, int(fn(now)))
    return max(0, math.ceil((_end_dt(obj) - now).total_seconds()))


def minutes_left(p):
    return math.ceil(remaining(p) / 60)


def start_time(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    return _start_dt(obj) if obj is not None else datetime.now()


def is_active(p):
    return remaining(p) > 0


def expired_card_visible(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    if obj is None:
        return False
    now = datetime.now()
    return _start_dt(obj) <= now < _start_dt(obj) + timedelta(seconds=EXPIRY_GRACE_SECONDS)


def show_public_card(p):
    obj = _plan_obj(p["id"] if isinstance(p, dict) else getattr(p, "id", p))
    if obj is None:
        return False
    return datetime.now() < _start_dt(obj) + timedelta(seconds=EXPIRY_GRACE_SECONDS)


def has_joined(p, name):
    if isinstance(p, dict):
        raw_attendees = p.get("_attendee_identities")
        if raw_attendees is not None:
            return any(_same_current_participant(person, name) for person in raw_attendees)
        attendees = p.get("attendees", [])
    else:
        attendees = list(getattr(p, "attendees", []))
    return any(_same_current_participant(person, name) for person in attendees)


def get_active_membership(name):
    identity = participant_identity(name)
    fn = getattr(board(), "get_active_membership", None)
    if callable(fn):
        return _as_dict(fn(identity))
    if not identity:
        return None
    for plan in _board_plans():
        if getattr(plan, "phase", lambda _now: "waiting")(datetime.now()) == "ended":
            continue
        attendees = list(getattr(plan, "attendees", []))
        if any(_same_current_participant(person, name) for person in attendees):
            return _as_dict(plan)
    return None


def get_cancelled_plan_notice(plan_id, name):
    # UI-only fallback: logic.py is intentionally left unchanged.
    info = _CANCELLED_PLAN_NOTICES.get(plan_id)
    if not info:
        return None
    if any(_same_current_participant(person, name) for person in info.get("attendees", [])):
        return {"id": plan_id, "title": info.get("title", "الخطة")}
    return None


def count(p):
    return len(p.get("attendees", []) if isinstance(p, dict) else getattr(p, "attendees", []))


def valid_img(category, image_id):
    valid = {item.get("id") for item in IMAGES.get(category, [])}
    return image_id if image_id in valid else (next(iter(valid), None))


def to_min(value):
    return value


def seed_plans():
    # ADDED: demo seeding belongs to the core now, not the UI.
    return None


def validate_input(*args, **kwargs):
    return board().validate_input(*args, **kwargs)


def _unpack_create(result):
    if not isinstance(result, tuple):
        return bool(result), "", None, ""
    if len(result) >= 4:
        return result[0], result[1], result[2], result[3]
    if len(result) == 3:
        return result[0], result[1], result[2], ""
    raise ValueError("Unsupported create_plan return value")


def create_plan(title, category, place, starts_in_min, description, host, start=None, end=None, capacity=10, **_):
    # ADDED: old UI has explicit start/end clock fields; current core stores wait + duration.
    # Keep those values as UI-only metadata and translate them to duration_min for the core.
    duration = 60
    if start is not None and end is not None and end > start:
        duration = max(5, int(end - start))
    core_host = participant_identity(host)
    result = board().create_plan(title, category, place, int(starts_in_min), description, core_host,
                                 duration, capacity)
    ok, msg, plan_id, host_key = _unpack_create(result)
    if ok and plan_id is not None:
        plan = _plan_obj(plan_id)
        if plan is None:
            try:
                _remember(board().get_active_plans())
                plan = _plan_obj(plan_id)
            except Exception:
                pass
        if plan is not None:
            # ADDED: compatibility-only metadata; does not alter core calculations.
            plan.ui_start_min = start
            plan.ui_end_min = end
            plan.ui_owner_uid = st.session_state.get("uid", "")
            plan.ui_image = valid_img(category, IMAGES.get(category, [{}])[0].get("id"))
        st.session_state.setdefault("_host_keys", {})[plan_id] = host_key
        # ADDED: keep the modular state API in sync while preserving the original page flow.
        st.session_state["my_host_key"] = host_key
        bump()
    return ok, msg, plan_id


def get_active_plans(include_grace=False):
    plans = list(board().get_active_plans())
    _remember(plans)
    if include_grace:
        # Core get_active_plans normally already includes its grace period.
        return [_as_dict(p) for p in plans]
    return [_as_dict(p) for p in plans if remaining(_as_dict(p)) > 0]


def search_plans(keyword, include_grace=False):
    plans = list(board().search_plans(keyword))
    _remember(plans)
    if include_grace:
        return [_as_dict(p) for p in plans]
    return [_as_dict(p) for p in plans if remaining(_as_dict(p)) > 0]


def join_plan(plan_id, name):
    result = board().join_plan(plan_id, participant_identity(name))
    if result and result[0]:
        bump()
    return result


def leave_plan(plan_id, name):
    result = board().leave_plan(plan_id, participant_identity(name))
    if result and result[0]:
        bump()
        if st.session_state.get("my_plan_id") == plan_id:
            st.session_state["my_plan_id"] = None
            st.session_state["view"] = "feed"
        st.session_state["joined"] = None
    return result


def cancel_plan(plan_id, name):
    b = board()
    # Capture what the UI needs before the core deletes the plan. This is UI state only.
    plan_before_cancel = _plan_obj(plan_id)
    cancel_snapshot = None
    if plan_before_cancel is not None:
        cancel_snapshot = {
            "title": getattr(plan_before_cancel, "title", "الخطة"),
            "attendees": list(getattr(plan_before_cancel, "attendees", [])),
            "cancelled_at": datetime.now(),
        }
    host_key = st.session_state.get("_host_keys", {}).get(plan_id, st.session_state.get("my_host_key", ""))
    # ADDED: the target core may require host_key; older dummy core does not.
    try:
        result = b.cancel_plan(plan_id, participant_identity(name), host_key)
    except TypeError:
        result = b.cancel_plan(plan_id, participant_identity(name))
    if result and result[0]:
        if cancel_snapshot is not None:
            _CANCELLED_PLAN_NOTICES[plan_id] = cancel_snapshot
        bump()
        st.session_state.get("_host_keys", {}).pop(plan_id, None)
        if st.session_state.get("my_plan_id") == plan_id:
            st.session_state["my_plan_id"] = None
            st.session_state["my_host_key"] = ""
            st.session_state["view"] = "feed"
        if st.session_state.get("owner_active_plan") == plan_id:
            st.session_state["owner_active_plan"] = None
    return result


def rename_person(old, new):
    # Keep the same UID while changing only the visible portion of the core token.
    result = board().rename_person(participant_identity(old), participant_identity(new))
    if result and result[0]:
        bump()
    return result


def prune_expired_plans():
    # Keep method naming expected by the old UI, call the new core method.
    fn = getattr(board(), "prune_ended_plans", None)
    if callable(fn):
        fn()
