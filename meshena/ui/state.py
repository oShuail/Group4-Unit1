import uuid

import streamlit as st

from ui.strings import MSG

S = st.session_state


def viewer():
    # The name the person typed (what we show on screen)
    return S.get("name", "").strip()


def me():
    # Two people can have the same name, so every browser gets its own random id.
    # The logic gets "name#id", and the screen only shows the name part.
    if "uid" not in S:
        S["uid"] = uuid.uuid4().hex[:8]
    return f"{viewer()}#{S['uid']}"


def show_name(person):
    # "عمر#a1b2c3d4" -> "عمر"
    return person.split("#")[0]


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


def open_plan_view():
    S["view"] = "plan"
    S["need_rerun"] = True


def open_feed_view():
    S["view"] = "feed"


def open_create_view():
    S["view"] = "create"
    S["need_rerun"] = True   # the Post button in the empty feed is inside the feed fragment
