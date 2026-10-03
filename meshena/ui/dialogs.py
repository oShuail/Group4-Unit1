"""dialogs.py - pop-ups: post a plan (D), rename (F), confirm leave (F), confirm cancel (F)."""
import streamlit as st

from ui.components import CLOSE, LOGOUT, PERSON, bdi, dialog_head_html
from ui.state import S, enter_plan, flash, leave_plan_state, viewer
from ui.strings import CAT_AR, MSG, T, ar, fmt_duration
from ui.contract import CATEGORIES, MAX_CAPACITY, MAX_START_MIN, MIN_CAPACITY, MIN_START_MIN

DURATIONS = [15, 30, 45, 60, 90, 120, 180, 240]   # choices for the plan length (minutes)
POST_KEYS = ["dlg_title", "dlg_category", "dlg_place", "dlg_description", "dlg_wait", "dlg_duration", "dlg_capacity"]


def pill_row(label, value_text):
    """A label on one side and the live value in a pill on the other (for the sliders)."""
    st.markdown(f'<div class="wait-row"><span>{label}</span><b class="pill-live">{value_text}</b></div>',
                unsafe_allow_html=True)


@st.dialog(T["dlg_post"])
def post_dialog(board):
    """D: the post form. Validation and saving are done by the board."""
    st.markdown(f'<div class="name-box"><span class="ic">{PERSON}</span><span>{T["f_name"]}</span>'
                f'<b>{bdi(viewer())}</b></div><div class="name-note">{T["f_name_hint"]}</div>',
                unsafe_allow_html=True)
    title = st.text_input(T["f_title"], key="dlg_title")
    category = st.selectbox(T["f_category"], CATEGORIES, key="dlg_category",
                            format_func=lambda c: CAT_AR.get(c, c))
    place = st.text_input(T["f_place"], key="dlg_place")
    description = st.text_input(T["f_description"], key="dlg_description")

    S.setdefault("dlg_wait", 5)
    S.setdefault("dlg_duration", 60)
    with st.container(key="box_wait"):
        pill_row(T["f_wait"], T["minutes"].format(n=ar(S["dlg_wait"])))
        wait = st.slider(T["f_wait"], MIN_START_MIN, MAX_START_MIN, key="dlg_wait",
                         label_visibility="collapsed")
    with st.container(key="box_duration"):
        pill_row(T["f_duration"], fmt_duration(S["dlg_duration"]))
        duration = st.select_slider(T["f_duration"], DURATIONS, key="dlg_duration",
                                    format_func=fmt_duration, label_visibility="collapsed")
    capacity = st.number_input(T["f_capacity"], MIN_CAPACITY, MAX_CAPACITY, value=10, step=1,
                               key="dlg_capacity")

    if st.button(T["f_post"], key="dlg_post_btn", type="primary"):
        errors = board.validate_input(title, place, viewer(), wait, duration, capacity)
        for error in errors:                         # each error gets its own box
            st.error(MSG.get(error, error))
        if not errors:
            ok, msg, plan_id = board.create_plan(title, category, place, wait, description,
                                                 viewer(), duration, capacity)
            flash(msg)
            if ok:
                for key in POST_KEYS:                # empty the form for next time
                    S.pop(key, None)
                enter_plan(plan_id)
            st.rerun()                               # closes the dialog


def plan_title(board, plan_id):
    """The title of my plan (shown inside the confirm dialogs), or an empty text."""
    plan = board.get_plan_for_participant(plan_id, viewer())
    return bdi(plan.title) if plan else ""


@st.dialog(" ")
def rename_dialog(board):
    """F: change the display name (the board also renames it inside plans)."""
    st.markdown(dialog_head_html(PERSON, "soft", T["dlg_rename"]), unsafe_allow_html=True)
    new_name = st.text_input(T["f_new_name"], key="rename_input", max_chars=24,
                             label_visibility="collapsed")
    if st.button(T["save"], key="rename_save", type="primary"):
        ok, msg = board.rename_person(viewer(), new_name)
        if ok:
            S["name"] = new_name.strip()
            flash(msg)
            st.rerun()
        else:
            st.error(MSG.get(msg, msg))


@st.dialog(" ")
def confirm_leave_dialog(board, plan_id):
    """F: ask before leaving a plan. The safe choice comes first."""
    st.markdown(dialog_head_html(LOGOUT, "soft", T["dlg_leave_q"], plan_title(board, plan_id)),
                unsafe_allow_html=True)
    stay, leave = st.columns(2)
    if stay.button(T["stay"], key="dlg_leave_stay", type="primary"):
        st.rerun()
    if leave.button(T["leave"], key="dlg_leave_yes"):
        ok, msg = board.leave_plan(plan_id, viewer())
        flash(msg)
        if ok:
            leave_plan_state()
        st.rerun()


@st.dialog(" ")
def confirm_cancel_dialog(board, plan_id):
    """F: ask before cancelling my plan. The safe choice comes first."""
    st.markdown(dialog_head_html(CLOSE, "danger", T["dlg_cancel_q"], plan_title(board, plan_id)),
                unsafe_allow_html=True)
    back, cancel = st.columns(2)
    if back.button(T["go_back"], key="dlg_cancel_back", type="primary"):
        st.rerun()
    if cancel.button(T["cancel"], key="dlg_cancel_yes"):
        ok, msg = board.cancel_plan(plan_id, viewer())
        flash(msg)
        if ok:
            leave_plan_state()
        st.rerun()
