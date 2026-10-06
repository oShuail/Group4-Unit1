from datetime import datetime

import streamlit as st

from ui.components import CAT_ICON, LOGO, cover, time_window
from ui.dialogs import confirm_cancel_dialog, confirm_leave_dialog
from ui.state import S, flash, me, open_feed_view, show_name
from ui.strings import CAT_AR, T, ar, fmt_clock, fmt_duration


@st.fragment(run_every=1)
def countdown(board, plan_id, phase):
    now = datetime.now()
    plan = board.get_plan_for_participant(plan_id, me())
    if plan is None or plan.phase(now) != phase:
        st.rerun()
        return
    S["last_phase"] = phase
    S["last_secs"] = plan.seconds_to_end(now)
    if phase == "waiting":
        seconds, total, label = plan.seconds_to_start(now), plan.starts_in_min * 60, T["wait_left"]
    else:
        seconds, total, label = plan.seconds_to_end(now), plan.duration_min * 60, T["plan_left"]
    with st.container(border=True):
        st.metric(label, fmt_clock(seconds), icon=":material/timer:")
        st.progress(1 - seconds / total)


@st.fragment(run_every=2)
def participants_panel(board, plan_id):
    plan = board.get_plan_for_participant(plan_id, me())
    if plan is None:
        return
    with st.container(border=True, key="people_panel"):
        st.markdown(f"#### {T['participants']} ({ar(plan.count())} / {ar(plan.capacity)})")
        st.progress(plan.count() / plan.capacity)
        for person in plan.attendees:
            with st.container(horizontal=True, vertical_alignment="center"):
                # Green when the person pressed "I arrived", so everyone knows they are there
                if plan.has_arrived(person):
                    st.markdown(f":green[:material/check_circle:] {show_name(person)}", width="content")
                    st.badge(T["arrived_tag"], icon=":material/where_to_vote:", color="green")
                else:
                    st.markdown(f":violet[:material/account_circle:] {show_name(person)}", width="content")
                if person == plan.host:
                    st.badge(T["host_tag"], color="violet")
                if person == me():
                    st.badge(T["you"], color="gray")
        seats = plan.capacity - plan.count()
        if seats > 0:
            st.caption(T["seats_left"].format(n=ar(seats)))


def render_arrived_button(board, plan):
    done = plan.has_arrived(me())
    label = T["arrived_done"] if done else T["arrive"]
    if st.button(label, key="arrived_btn", icon=":material/where_to_vote:", disabled=done, width="stretch"):
        ok, msg = board.mark_arrived(plan.id, me())
        flash(msg)
        st.rerun()


def render_plan_page(board, plan):
    role = "host" if plan.host == me() else "join"
    phase = plan.phase(datetime.now())
    key = f"hero_{role}_" + ("wait" if phase == "waiting" else "run")

    with st.container(horizontal=True, vertical_alignment="center"):
        st.image(LOGO, width=130)
        st.space("stretch")
        st.button(T["back"], icon=":material/arrow_forward:", on_click=open_feed_view)

    main, side = st.columns([3, 2], gap="large")
    with main:
        with st.container(border=True, key="plan_card"):
            st.image(cover(plan.category, ratio=2.2), width="stretch")
            with st.container(horizontal=True, gap="xsmall"):
                if phase == "waiting":
                    st.badge(T[key], icon=":material/hourglass_top:", color="violet")
                else:
                    st.badge(T[key], icon=":material/play_circle:", color="green")
                st.badge(CAT_AR[plan.category], icon=CAT_ICON[plan.category], color="gray")
            st.markdown(f"## {plan.title}")
            st.caption(T[key + "_sub"])
            with st.container(horizontal=True, gap="large"):
                st.markdown(f":violet[:material/location_on:] {plan.place}", width="content")
                st.markdown(f":violet[:material/schedule:] {time_window(plan)}", width="content")
                st.markdown(f":violet[:material/timelapse:] {fmt_duration(plan.duration_min)}", width="content")
                st.markdown(f":violet[:material/person:] {T['hosted_by'].format(name=show_name(plan.host))}",
                            width="content")
            if plan.description:
                st.write(plan.description)
            countdown(board, plan.id, phase)

        render_arrived_button(board, plan)
        if role == "host":
            if st.button(T["cancel"], key="danger_plan_cancel", icon=":material/close:", width="stretch"):
                confirm_cancel_dialog(board, plan.id)
        elif st.button(T["leave_plan"], key="plan_leave", icon=":material/logout:", width="stretch"):
            confirm_leave_dialog(board, plan.id)

    with side:
        participants_panel(board, plan.id)
