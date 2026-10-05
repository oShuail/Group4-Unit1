import streamlit as st
from ui.strings import MSG

S = st.session_state


def viewer():
    return S.get("name", "").strip()


def flash(msg):
    S["flash"] = msg


def show_flash():
    msg = S.pop("flash", None)
    if msg:
        st.toast(MSG.get(msg, msg))


def enter_plan(plan_id, host_key=""):
    S["my_plan_id"] = plan_id
    S["my_host_key"] = host_key
    S["view"] = "plan"
    S["last_phase"] = None
    S["last_secs"] = None


def leave_plan_state():
    S["my_plan_id"] = None
    S["my_host_key"] = ""
    S["view"] = "feed"
    # ADDED: legacy design keeps these two view markers as well.
    S["joined"] = None
    S["owner_active_plan"] = None


def open_plan_view():
    S["view"] = "plan"
    S["need_rerun"] = True


def open_feed_view():
    S["view"] = "feed"
    # ADDED: make the legacy back button and the new router agree.
    S["joined"] = None
    S["owner_active_plan"] = None
    S["my_plan_id"] = None
