from datetime import datetime

import streamlit as st

from ui.components import LOGO
from ui.contract import CATEGORIES, MAX_CAPACITY, MAX_START_MIN, MIN_CAPACITY, MIN_START_MIN, Plan
from ui.state import S, enter_plan, flash, me, open_feed_view, viewer
from ui.strings import CAT_AR, MSG, T, fmt_duration
from ui.views_feed import render_card

DURATIONS = [15, 30, 45, 60, 90, 120, 180, 240]
FORM_KEYS = ["c_title", "c_category", "c_place", "c_description", "c_wait", "c_duration", "c_capacity"]


def post_plan(board, title, category, place, wait, description, duration, capacity):
    errors = board.validate_input(title, place, viewer(), wait, duration, capacity)
    for error in errors:
        st.error(MSG.get(error, error))
    if not errors:
        ok, msg, plan_id, host_key = board.create_plan(title, category, place, wait, description,
                                                       me(), duration, capacity)
        flash(msg)
        if ok:
            for key in FORM_KEYS:   # empty the form for next time
                S.pop(key, None)
            enter_plan(plan_id, host_key)
        st.rerun()


def render_create_page(board):
    with st.container(horizontal=True, vertical_alignment="center"):
        st.image(LOGO, width=130)
        st.space("stretch")
        st.button(T["back"], icon=":material/arrow_forward:", on_click=open_feed_view)

    st.markdown(f"## {T['dlg_post']}")
    form_col, preview_col = st.columns([1.15, 1], gap="large")

    with form_col:
        with st.container(border=True, key="form_card"):
            st.caption(f":material/person: {T['f_name']} **{viewer()}** · {T['f_name_hint']}")
            category = st.selectbox(T["f_category"], CATEGORIES, key="c_category",
                                    format_func=lambda c: CAT_AR[c])
            title = st.text_input(T["f_title"], key="c_title", max_chars=40, placeholder=T["f_title_hint"])
            place = st.text_input(T["f_place"], key="c_place", max_chars=40, placeholder=T["f_place_hint"],
                                  icon=":material/location_on:")
            description = st.text_area(T["f_description"], key="c_description", max_chars=140, height=80,
                                       placeholder=T["f_description_hint"])

            wait_col, duration_col, capacity_col = st.columns(3)
            wait = wait_col.number_input(T["f_wait"], MIN_START_MIN, MAX_START_MIN, value=5, key="c_wait",
                                         icon=":material/schedule:")
            duration = duration_col.selectbox(T["f_duration"], DURATIONS, index=3, key="c_duration",
                                              format_func=fmt_duration)
            capacity = capacity_col.number_input(T["f_capacity"], MIN_CAPACITY, MAX_CAPACITY, value=4,
                                                 key="c_capacity", icon=":material/group:")

            if st.button(T["f_post"], type="primary", icon=":material/send:", width="stretch"):
                post_plan(board, title, category, place, wait, description, duration, capacity)

    with preview_col:
        # A plan that is only drawn on screen, it is not added to the board
        st.caption(T["preview"])
        preview = Plan(0, title.strip() or T["preview_title"], category, place.strip() or T["preview_place"],
                       description.strip(), me(), wait, duration, capacity, "")
        render_card(preview, board, datetime.now(), preview=True)
