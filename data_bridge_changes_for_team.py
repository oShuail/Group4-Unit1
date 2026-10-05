"""
Mashina - data_bridge.py changes for team review
=================================================

IMPORTANT:
- data_bridge.py is a BRIDGE / ADAPTER (وسيط) between the UI and logic.py.
- It receives data from the UI, prepares/converts it, calls the original logic.py methods,
  then returns data in a form the UI can use.
- It is NOT a replacement for logic.py and does not replace the core business rules.
- logic.py was NOT modified.
- These additions live in the UI bridge only.
- Purpose: keep the original PlanBoard logic untouched while supporting:
    1) users with the same visible name,
    2) UI detection of the user's active plan,
    3) cancellation notice for joined users,
    4) conversion between Plan objects and UI dictionaries.

This file is for REVIEW/EXPLANATION of the added bridge logic.
It is not a replacement for logic.py.
"""

from datetime import datetime
import streamlit as st


# ============================================================================
# 1) UNIQUE USER IDENTITY - UI ONLY
# ============================================================================
# Problem:
# logic.py identifies participants by a string name. If two users are both
# called "Rand", the core could treat them as the same participant.
#
# Solution:
# Keep the visible name unchanged in the UI, but send a unique string to the
# existing logic.py using the Streamlit session UID.
#
# Visible to user:   Rand
# Sent to logic.py:  __mashina_user__::<uid>::Rand
#
# No change is required inside logic.py because it already accepts strings.

_USER_TOKEN_PREFIX = "__mashina_user__::"
_USER_TOKEN_SEP = "::"


def participant_identity(name=None, uid=None):
    """Return the unique internal participant string sent to logic.py."""
    display = (name if name is not None else st.session_state.get("name", "")).strip()
    session_uid = (uid if uid is not None else st.session_state.get("uid", "")).strip()

    if not display or not session_uid:
        return display

    return f"{_USER_TOKEN_PREFIX}{session_uid}{_USER_TOKEN_SEP}{display}"


def participant_display(value):
    """Convert the internal identity back to the normal visible name."""
    text = str(value or "")

    if not text.startswith(_USER_TOKEN_PREFIX):
        return text

    payload = text[len(_USER_TOKEN_PREFIX):]
    _uid, separator, display = payload.partition(_USER_TOKEN_SEP)

    return display if separator else text


def participant_uid(value):
    """Extract the UID from an internal participant identity."""
    text = str(value or "")

    if not text.startswith(_USER_TOKEN_PREFIX):
        return ""

    payload = text[len(_USER_TOKEN_PREFIX):]
    uid, separator, _display = payload.partition(_USER_TOKEN_SEP)

    return uid if separator else ""


def _same_current_participant(raw_value, display_name=None):
    """Check whether a stored participant is the current browser user."""
    current = participant_identity(display_name)
    raw = str(raw_value or "")

    if raw.startswith(_USER_TOKEN_PREFIX):
        return bool(current and raw.lower() == current.lower())

    # Backward compatibility for plans created before UID identities existed.
    legacy_name = (
        display_name
        if display_name is not None
        else st.session_state.get("name", "")
    ).strip()

    return bool(legacy_name and raw.strip().lower() == legacy_name.lower())


# ============================================================================
# 2) PLAN -> UI DICTIONARY CONVERSION
# ============================================================================
# The core uses Plan objects, while the preserved UI reads dictionary fields.
# data_bridge.py converts the Plan object without changing the Plan class.
#
# Important additions:
# - "host" and "attendees" contain clean DISPLAY names.
# - "_host_identity" and "_attendee_identities" keep the internal identities
#   so the UI can distinguish two people who have the same name.


def example_as_dict(plan, owner_uid):
    """Simplified example of the identity-related part of _as_dict()."""
    raw_host = getattr(plan, "host", "")
    raw_attendees = list(getattr(plan, "attendees", []))

    return {
        "id": getattr(plan, "id", None),
        "owner": owner_uid,

        # DISPLAY VALUES - safe to show in the interface
        "host": participant_display(raw_host),
        "attendees": [participant_display(person) for person in raw_attendees],

        # INTERNAL VALUES - only for correct user matching
        "_host_identity": raw_host,
        "_attendee_identities": raw_attendees,
    }


# ============================================================================
# 3) CHECK WHETHER CURRENT USER JOINED A PLAN
# ============================================================================
# We do NOT compare only the visible name anymore.
# We compare the internal UID identity whenever it exists.


def has_joined(plan_dict, name):
    """UI-side membership check that supports duplicate display names."""
    identities = plan_dict.get("_attendee_identities")

    if identities is not None:
        return any(
            _same_current_participant(person, name)
            for person in identities
        )

    # Compatibility fallback for older plan dictionaries.
    attendees = plan_dict.get("attendees", [])
    return any(
        _same_current_participant(person, name)
        for person in attendees
    )


# ============================================================================
# 4) FIND CURRENT USER'S ACTIVE PLAN - UI FEATURE
# ============================================================================
# This supports the UI behavior:
#
#   "الخطة الي منضم اليها"
#   -----------------------
#   [current joined plan]
#
#   "باقي الخطط"
#   ------------
#   [other plans]
#
# The original logic.py does not need to know about this screen grouping.


def get_active_membership_from_plans(plans, name):
    """Return the first non-ended plan containing the current participant."""
    identity = participant_identity(name)

    if not identity:
        return None

    for plan in plans:
        phase_fn = getattr(plan, "phase", None)

        if callable(phase_fn) and phase_fn(datetime.now()) == "ended":
            continue

        attendees = list(getattr(plan, "attendees", []))

        if any(_same_current_participant(person, name) for person in attendees):
            return plan

    return None


# ============================================================================
# 5) WRAPPERS AROUND THE ORIGINAL logic.py METHODS
# ============================================================================
# These functions do NOT re-implement create/join/leave/cancel rules.
# They only convert the visible user name into the unique internal identity,
# then call the ORIGINAL PlanBoard methods.


def create_plan_bridge(board, title, category, place, starts_in_min,
                       description, host, duration, capacity):
    """Pass a UID-safe host string to the original create_plan()."""
    core_host = participant_identity(host)

    return board.create_plan(
        title,
        category,
        place,
        int(starts_in_min),
        description,
        core_host,
        duration,
        capacity,
    )


def join_plan_bridge(board, plan_id, name):
    """Use the original join_plan() with the current user's unique identity."""
    return board.join_plan(
        plan_id,
        participant_identity(name),
    )


def leave_plan_bridge(board, plan_id, name):
    """Use the original leave_plan() with the current user's unique identity."""
    return board.leave_plan(
        plan_id,
        participant_identity(name),
    )


def rename_person_bridge(board, old_name, new_name):
    """Keep the same UID while changing only the visible name."""
    return board.rename_person(
        participant_identity(old_name),
        participant_identity(new_name),
    )


# ============================================================================
# 6) HOST CANCELLATION NOTICE - UI ONLY
# ============================================================================
# Problem:
# The original logic.py deletes the plan immediately when the host cancels it.
# After deletion, the UI no longer has the plan title/attendee list needed to
# tell joined users: "صاحب الخطة ألغى الخطة".
#
# Solution:
# Before calling the ORIGINAL cancel_plan(), data_bridge.py stores a temporary
# UI snapshot. The core cancellation behavior itself is unchanged.

_CANCELLED_PLAN_NOTICES = {}


def cancel_plan_bridge(board, plan_id, name, host_key, plan_before_cancel):
    """Save UI notice data, then call the original cancel_plan()."""
    snapshot = None

    if plan_before_cancel is not None:
        snapshot = {
            "title": getattr(plan_before_cancel, "title", "الخطة"),
            "attendees": list(getattr(plan_before_cancel, "attendees", [])),
            "cancelled_at": datetime.now(),
        }

    # ORIGINAL core method - no cancellation rule was rewritten here.
    result = board.cancel_plan(
        plan_id,
        participant_identity(name),
        host_key,
    )

    if result and result[0] and snapshot is not None:
        _CANCELLED_PLAN_NOTICES[plan_id] = snapshot

    return result


def get_cancelled_plan_notice(plan_id, name):
    """Return the cancellation notice only to a user who was in that plan."""
    info = _CANCELLED_PLAN_NOTICES.get(plan_id)

    if not info:
        return None

    was_member = any(
        _same_current_participant(person, name)
        for person in info.get("attendees", [])
    )

    if not was_member:
        return None

    return {
        "id": plan_id,
        "title": info.get("title", "الخطة"),
    }


# ============================================================================
# TEAM SUMMARY
# ============================================================================
# What stays in logic.py:
# - input validation
# - plan creation rules
# - capacity/full checks
# - join rules
# - leave rules
# - host cancellation authorization
# - timing / waiting / running / ended phases
# - pruning ended plans
#
# Main role of data_bridge.py:
# - acts as a Bridge / Adapter (وسيط) between the UI and logic.py
# - prepares UI data before sending it to the core
# - converts core Plan data back into the format expected by the UI
#
# What data_bridge.py adds:
# - UI <-> core data conversion
# - per-session UID identity for duplicate visible names
# - UI membership detection
# - UI grouping of the current joined plan vs other plans
# - temporary cancellation-notice data for joined users
#
# Therefore:
# UI -> data_bridge.py -> logic.py
# logic.py -> data_bridge.py -> UI
#
# data_bridge.py is mainly a mediator/adapter layer. It contains application/UI
# compatibility helpers, but the project's original business rules remain in logic.py.
