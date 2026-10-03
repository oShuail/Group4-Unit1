"""views_feed.py - the home page: top bar, filter chips, my-plan card, and the plan cards."""
from datetime import datetime
from html import escape

import streamlit as st

from ui.components import (ASSETS, avatar_stack_html, bdi, cover_html, image_data_uri, row_html,
                        CLOCK, PIN)
from ui.contract import CATEGORIES
from ui.dialogs import confirm_cancel_dialog, confirm_leave_dialog, post_dialog, rename_dialog
from ui.state import S, enter_plan, flash, open_plan_view, show_flash, viewer
from ui.strings import CAT_AR, CAT_EN, T, ar, fmt_duration

REFRESH_SECONDS = 10   # how often the feed (and its countdown texts) refresh themselves
COLUMNS = 3            # cards per row on desktop (Streamlit stacks them on phones)


# ---------------- Top bar ----------------
def render_top_bar(board):
    """Notice (if I am in a plan), then logo, search, name pill and 'Post a plan'. Returns the keyword."""
    in_plan = S.get("my_plan_id") is not None   # one plan at a time
    if in_plan:
        st.markdown(f'<div class="notice">{T["in_plan_notice"]}</div>', unsafe_allow_html=True)
    logo, search, name, post = st.columns([1.2, 4.5, 1.8, 1.5], vertical_alignment="center")
    logo.image(str(ASSETS / "logo_full.png"), width=140)
    keyword = search.text_input(T["search"], key="search_box", placeholder=T["search"],
                                label_visibility="collapsed").strip()
    if name.button(viewer(), key="name_pill", icon=":material/person:"):
        S["rename_input"] = viewer()
        rename_dialog(board)
    if post.button(T["post"], key="open_post", type="primary", disabled=in_plan):
        post_dialog(board)
    return CAT_EN.get(keyword, keyword)          # lets people search with the Arabic category name


def render_category_filter():
    """Chips to filter by category. Returns the English category, or None for 'all'."""
    choice = st.pills(T["all"], ["All"] + CATEGORIES, selection_mode="single", default="All",
                      key="cat_filter", label_visibility="collapsed",
                      format_func=lambda c: T["all"] if c == "All" else CAT_AR.get(c, c))
    return None if choice in (None, "All") else choice


# ---------------- Card buttons ----------------
def on_join(board, plan_id):
    """Button callback: try to join, remember the message, open my plan's page on success."""
    ok, msg = board.join_plan(plan_id, viewer())
    flash(msg)
    if ok:
        enter_plan(plan_id)
        S["need_rerun"] = True


def render_card_button(plan, board, now):
    """Pick the one button for this viewer: Cancel (host), Leave (member) or Join."""
    name = viewer()
    if plan.host == name:
        if st.button(T["cancel"], key=f"cancel_{plan.id}"):
            confirm_cancel_dialog(board, plan.id)
    elif plan.has_joined(name):
        if st.button(T["leave"], key=f"leave_{plan.id}"):
            confirm_leave_dialog(board, plan.id)
    else:
        closed = plan.phase(now) != "waiting"
        label = T["join_closed"] if closed else T["full"] if plan.is_full() else T["join"]
        disabled = closed or plan.is_full() or S.get("my_plan_id") is not None
        st.button(label, key=f"join_{plan.id}", type="primary", disabled=disabled,
                  on_click=on_join, args=(board, plan.id))


# ---------------- Plan card ----------------
def render_pin_card(plan, board, now):
    """One plan card: cover, title, rows with icons, people, and the action button."""
    minutes = plan.minutes_left(now)
    pill = T["starts_in"].format(n=ar(minutes)) if minutes > 0 else T["started"]
    description = f'<div class="pin-desc">{bdi(plan.description)}</div>' if plan.description else ""
    count = T["joined_count"].format(n=ar(plan.count()), cap=ar(plan.capacity))
    with st.container(border=True, key=f"pin_{plan.id}"):
        st.markdown(
            f'{cover_html(plan, pill, minutes <= 1)}'
            f'<div class="pin-body"><div class="pin-title">{bdi(plan.title)}</div>'
            f'{row_html(PIN, bdi(plan.place))}{row_html(CLOCK, fmt_duration(plan.duration_min))}'
            f'{description}'
            f'<div class="pin-people">{avatar_stack_html(plan, viewer())}'
            f'<div><b>{count}</b>{escape(T["hosted_by"].format(name=plan.host))}</div></div></div>',
            unsafe_allow_html=True)
        render_card_button(plan, board, now)


# ---------------- My plan (dedicated place at the top) ----------------
def render_my_plan(plan, now):
    """A card at the top of the feed for the plan I host or joined, with a button to open it."""
    role = T["my_plan_host"] if plan.host == viewer() else T["my_plan_joined"]
    if plan.phase(now) == "waiting":
        status = T["starts_in"].format(n=ar(plan.minutes_left(now)))
    else:
        status = T["running"]
    with st.container(key="my_plan"):
        text, button = st.columns([4, 1.4], vertical_alignment="center")
        text.markdown(
            f'<div class="mp-role">{role}</div><div class="mp-title">{bdi(plan.title)}</div>'
            f'<div class="mp-meta"><span class="time-pill soon">{status}</span>'
            f'{row_html(PIN, bdi(plan.place))}</div>', unsafe_allow_html=True)
        button.button(T["view_plan"], key="view_my_plan", type="primary", on_click=open_plan_view)


# ---------------- Feed ----------------
def split_into_rows(plans, n):
    """Cut the list into rows of n cards, in order, so a phone shows them soonest first."""
    return [plans[i:i + n] for i in range(0, len(plans), n)]


def render_empty(board, message):
    """Centered empty state: faded logo mark, the message and a 'Post a plan' button."""
    logo = image_data_uri(str(ASSETS / "logo_mark.png"))
    with st.container(key="empty_box"):
        st.markdown(f'<div class="empty"><img src="{logo}">{escape(message)}</div>',
                    unsafe_allow_html=True)
        _, middle, _ = st.columns([1, 1, 1])
        if middle.button(T["post"], key="empty_post", type="primary",
                         disabled=S.get("my_plan_id") is not None):
            post_dialog(board)


@st.fragment(run_every=REFRESH_SECONDS)
def render_feed(board, keyword, category):
    """My-plan card + plan cards, refreshed every REFRESH_SECONDS seconds."""
    if S.pop("need_rerun", False):               # a button asked for a page change
        st.rerun()
    show_flash()
    board.prune_ended_plans()
    now = datetime.now()

    plan_id = S.get("my_plan_id")
    mine = board.get_plan_for_participant(plan_id, viewer()) if plan_id is not None else None
    if plan_id is not None and mine is None:
        st.rerun()                               # my plan is over: the router shows the message
    if mine is not None:
        render_my_plan(mine, now)

    plans = board.search_plans(keyword) if keyword else board.get_active_plans()
    if category:
        plans = [p for p in plans if p.category == category]
    if not plans:
        render_empty(board, T["no_match"] if keyword or category else T["no_plans"])
        return
    for row in split_into_rows(plans, COLUMNS):
        for column, plan in zip(st.columns(COLUMNS, vertical_alignment="top"), row):
            with column:
                render_pin_card(plan, board, now)
