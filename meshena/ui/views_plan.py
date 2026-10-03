"""views_plan.py - the plan page (B and C): one layout for the host and for joined people."""
from datetime import datetime
from html import escape

import streamlit as st

from ui.components import (ASSETS, CHECK, CLOCK, HOURGLASS, PIN, TILE_COLORS, USERS, bar_html, bdi,
                        row_html)
from ui.dialogs import confirm_cancel_dialog, confirm_leave_dialog
from ui.state import S, open_feed_view, viewer
from ui.strings import T, ar, fmt_duration

CONFETTI_COLORS = ["#512ABA", "#FFFFFF", "#F3B63F", "#E86A7A", "#7BC6A4"]


# ---------------- Hero ----------------
def hero_html(plan, role, phase):
    """Top block tinted with the category color: icon (hourglass or check), title, subtitle."""
    waiting = phase == "waiting"
    key = ("hero_host_" if role == "host" else "hero_join_") + ("wait" if waiting else "run")
    if role == "host" and waiting:
        icon = f'<div class="hourglass">{HOURGLASS}</div>'
    else:
        pieces = "".join(f'<i style="right:{6 + i * 8}%;background:{CONFETTI_COLORS[i % 5]};'
                         f'animation-delay:{(i % 5) * 0.12:.2f}s"></i>' for i in range(12))
        icon = f'<div class="confetti">{pieces}</div>{CHECK}'
    color = TILE_COLORS.get(plan.category, "#EFEAE0")
    return (f'<div class="hero" style="background:{color}">{icon}'
            f'<div class="hero-t">{T[key]}</div><div class="hero-s">{T[key + "_sub"]}</div></div>'
            '<div class="perf"><span></span></div>')


def details_html(plan):
    """Plan title and the rows with line icons (place, length, host)."""
    return (f'<div class="tk-body"><div class="tk-title">{bdi(plan.title)}</div>'
            f'{row_html(PIN, bdi(plan.place))}'
            f'{row_html(CLOCK, fmt_duration(plan.duration_min))}'
            f'{row_html(USERS, escape(T["hosted_by"].format(name=plan.host)))}</div>')


# ---------------- Live parts ----------------
@st.fragment(run_every=1)
def countdown(board, plan_id, phase):
    """Countdown bar, updated every second. Reruns the page when the phase changes or the plan ends."""
    now = datetime.now()
    plan = board.get_plan_for_participant(plan_id, viewer())
    if plan is None or plan.phase(now) != phase:
        st.rerun()
        return
    S["last_phase"] = phase                      # lets the router tell 'ended' from 'cancelled'
    S["last_secs"] = plan.seconds_to_end(now)
    if phase == "waiting":
        seconds, total, label = plan.seconds_to_start(now), plan.starts_in_min * 60, T["wait_left"]
    else:
        seconds, total, label = plan.seconds_to_end(now), plan.duration_min * 60, T["plan_left"]
    st.markdown(bar_html(label, seconds, seconds / total), unsafe_allow_html=True)


@st.fragment(run_every=3)
def participants_panel(board, plan_id):
    """Who is coming: host first, my own row marked. Refreshes so new people appear."""
    plan = board.get_plan_for_participant(plan_id, viewer())
    if plan is None:
        return
    rows = ""
    for name in plan.attendees:
        tag = f'<span class="tag-host">{T["host_tag"]}</span>' if name == plan.host else ""
        me = f'<span class="tag-me">{T["you"]}</span>' if name == viewer() else ""
        rows += (f'<div class="person"><span class="av{" host" if name == plan.host else ""}">'
                 f'{escape(name[:1])}</span><span class="pn">{bdi(name)}</span>{tag}{me}</div>')
    st.markdown(f'<div class="panel-h">{T["participants"]}'
                f'<span class="count-pill">{ar(plan.count())} / {ar(plan.capacity)}</span></div>{rows}',
                unsafe_allow_html=True)


# ---------------- Page ----------------
def render_plan_page(board, plan):
    """The page for the plan I host (C) or joined (B). Only the hero and the last button differ."""
    role = "host" if plan.host == viewer() else "joined"
    phase = plan.phase(datetime.now())
    logo_col, back_col = st.columns([4, 1], vertical_alignment="center")
    logo_col.image(str(ASSETS / "logo_full.png"), width=140)
    back_col.button(T["back"], key="back_btn", icon=":material/arrow_forward:",
                    on_click=open_feed_view)
    _, middle, _ = st.columns([1, 2.2, 1])
    with middle:
        with st.container(key="plan_card"):
            st.markdown(hero_html(plan, role, phase) + details_html(plan), unsafe_allow_html=True)
            countdown(board, plan.id, phase)
        with st.container(key="people_panel"):
            participants_panel(board, plan.id)
        if role == "host":
            if st.button(T["cancel"], key="plan_cancel", icon=":material/close:"):
                confirm_cancel_dialog(board, plan.id)
        elif st.button(T["leave_plan"], key="plan_leave", icon=":material/logout:"):
            confirm_leave_dialog(board, plan.id)
