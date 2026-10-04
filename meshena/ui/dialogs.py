import streamlit as st

from ui.components import category_label
from ui.contract import CATEGORIES, MAX_CAPACITY, MAX_START_MIN, MIN_CAPACITY, MIN_START_MIN
from ui.state import S, enter_plan, flash, leave_plan_state, viewer
from ui.strings import MSG, T, fmt_duration

DURATIONS = [15, 30, 45, 60, 90, 120, 180, 240]
POST_KEYS = ["dlg_title", "dlg_category", "dlg_place", "dlg_description", "dlg_wait", "dlg_duration",
             "dlg_capacity"]


@st.dialog(T["dlg_post"], width="medium", icon=":material/edit_calendar:")
def post_dialog(board):
    st.caption(f":material/person: {T['f_name']} **{viewer()}** · {T['f_name_hint']}")
    title = st.text_input(T["f_title"], key="dlg_title", max_chars=40, placeholder=T["f_title_hint"])
    category = st.pills(T["f_category"], CATEGORIES, key="dlg_category", default="Lunch", required=True,
                        format_func=category_label)
    place = st.text_input(T["f_place"], key="dlg_place", max_chars=40, placeholder=T["f_place_hint"],
                          icon=":material/location_on:")
    description = st.text_area(T["f_description"], key="dlg_description", max_chars=140, height=80,
                               placeholder=T["f_description_hint"])

    wait_col, duration_col, capacity_col = st.columns(3)
    wait = wait_col.number_input(T["f_wait"], MIN_START_MIN, MAX_START_MIN, value=5, key="dlg_wait",
                                 icon=":material/schedule:")
    duration = duration_col.selectbox(T["f_duration"], DURATIONS, index=3, key="dlg_duration",
                                      format_func=fmt_duration)
    capacity = capacity_col.number_input(T["f_capacity"], MIN_CAPACITY, MAX_CAPACITY, value=4,
                                         key="dlg_capacity", icon=":material/group:")

    if st.button(T["f_post"], type="primary", icon=":material/send:", width="stretch"):
        errors = board.validate_input(title, place, viewer(), wait, duration, capacity)
        for error in errors:
            st.error(MSG.get(error, error))
        if not errors:
            ok, msg, plan_id, host_key = board.create_plan(title, category, place, wait, description,
                                                           viewer(), duration, capacity)
            flash(msg)
            if ok:
                for key in POST_KEYS:
                    S.pop(key, None)
                enter_plan(plan_id, host_key)
            st.rerun()


def plan_title(board, plan_id):
    plan = board.get_plan_for_participant(plan_id, viewer())
    return plan.title if plan else ""


@st.dialog(T["dlg_leave"], icon=":material/logout:")
def confirm_leave_dialog(board, plan_id):
    st.write(T["dlg_leave_q"])
    st.markdown(f"**{plan_title(board, plan_id)}**")
    stay, leave = st.columns(2)
    if stay.button(T["stay"], type="primary", width="stretch"):
        st.rerun()
    if leave.button(T["leave"], icon=":material/logout:", width="stretch"):
        ok, msg = board.leave_plan(plan_id, viewer())
        flash(msg)
        if ok:
            leave_plan_state()
        st.rerun()


@st.dialog(T["dlg_cancel"], icon=":material/event_busy:")
def confirm_cancel_dialog(board, plan_id):
    st.write(T["dlg_cancel_q"])
    st.markdown(f"**{plan_title(board, plan_id)}**")
    back, cancel = st.columns(2)
    if back.button(T["go_back"], type="primary", width="stretch"):
        st.rerun()
    if cancel.button(T["cancel"], key="danger_dlg_cancel", icon=":material/close:", width="stretch"):
        ok, msg = board.cancel_plan(plan_id, viewer(), S.get("my_host_key", ""))
        flash(msg)
        if ok:
            leave_plan_state()
        st.rerun()
