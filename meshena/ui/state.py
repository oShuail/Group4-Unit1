"""state.py - the few things we keep in st.session_state (never the plans themselves)."""
import streamlit as st

from ui.strings import MSG

S = st.session_state


def viewer():
    """The display name typed on the name page, without extra spaces."""
    return S.get("name", "").strip()


def flash(msg):
    """Remember a board message to show as a toast on the next run."""
    S["flash"] = msg


def show_flash():
    """Show the saved board message (Arabic text) once, then forget it."""
    msg = S.pop("flash", None)
    if msg:
        st.toast(MSG.get(msg, msg))


def enter_plan(plan_id, host_key=""):
    """Remember which plan I am in (hosting or joined) and open its page."""
    S["my_plan_id"] = plan_id
    S["my_host_key"] = host_key
    S["view"] = "plan"
    S["last_phase"] = None   # filled in by the countdown on the plan page
    S["last_secs"] = None


def leave_plan_state():
    """Forget my plan and go back to the feed."""
    S["my_plan_id"] = None
    S["my_host_key"] = ""
    S["view"] = "feed"


def open_plan_view():
    """Button callback: open my plan's page. Needs a full rerun to switch pages."""
    S["view"] = "plan"
    S["need_rerun"] = True


def open_feed_view():
    """Button callback: go back to the feed."""
    S["view"] = "feed"
