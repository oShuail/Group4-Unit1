from datetime import datetime

import streamlit as st

from ui.components import CAT_ICON, LOGO, LOGO_MARK, category_label, cover
from ui.contract import CATEGORIES
from ui.dialogs import confirm_cancel_dialog, confirm_leave_dialog, post_dialog
from ui.state import S, enter_plan, flash, open_plan_view, show_flash, viewer
from ui.strings import CAT_AR, CAT_EN, MSG, T, ar, fmt_duration

REFRESH_SECONDS = 10
COLUMNS = 3


def render_name_menu(board):
    with st.popover(viewer(), icon=":material/account_circle:", key="profile"):
        st.markdown(f"**{T['dlg_rename']}**")
        new_name = st.text_input(T["f_new_name"], value=viewer(), max_chars=24, label_visibility="collapsed")
        if st.button(T["save"], key="rename_save", type="primary", width="stretch"):
            ok, msg = board.rename_person(viewer(), new_name)
            if ok:
                S["name"] = new_name.strip()
                flash(msg)
                st.rerun()
            else:
                st.error(MSG.get(msg, msg))


def render_top_bar(board):
    in_plan = S.get("my_plan_id") is not None
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.image(LOGO, width=118)
        keyword = st.text_input(T["search"], placeholder=T["search"], icon=":material/search:",
                                live=True, label_visibility="collapsed")
        render_name_menu(board)
        if st.button(T["post"], key="open_post", type="primary", icon=":material/add:", disabled=in_plan):
            post_dialog(board)
    st.markdown(f"## {T['greet'].format(name=viewer())}")
    st.caption(T["greet_sub"])
    keyword = keyword.strip()
    return CAT_EN.get(keyword, keyword)


def render_category_filter():
    choice = st.pills(T["all"], ["All"] + CATEGORIES, default="All", required=True,
                      format_func=category_label, label_visibility="collapsed")
    return None if choice == "All" else choice


def on_join(board, plan_id):
    ok, msg = board.join_plan(plan_id, viewer())
    flash(msg)
    if ok:
        enter_plan(plan_id)
        S["need_rerun"] = True


def render_card_button(plan, board, now):
    name = viewer()
    if plan.host == name:
        if st.button(T["cancel"], key=f"danger_cancel_{plan.id}", icon=":material/close:", width="stretch"):
            confirm_cancel_dialog(board, plan.id)
    elif plan.has_joined(name):
        if st.button(T["leave"], key=f"leave_{plan.id}", icon=":material/logout:", width="stretch"):
            confirm_leave_dialog(board, plan.id)
    else:
        closed = plan.phase(now) != "waiting"
        if closed:
            label = T["join_closed"]
        elif plan.is_full():
            label = T["full"]
        else:
            label = T["join"]
        disabled = closed or plan.is_full() or S.get("my_plan_id") is not None
        st.button(label, key=f"join_{plan.id}", type="primary", icon=":material/group_add:", width="stretch",
                  disabled=disabled, on_click=on_join, args=(board, plan.id))


def render_card(plan, board, now):
    with st.container(border=True, key=f"card_{plan.id}", height="stretch"):
        st.image(cover(plan.category), width="stretch")

        with st.container(horizontal=True, gap="xsmall"):
            minutes = plan.minutes_left(now)
            if minutes > 0:
                st.badge(T["starts_in"].format(n=ar(minutes)), icon=":material/schedule:", color="violet")
            else:
                st.badge(T["started"], icon=":material/play_circle:", color="green")
            st.badge(CAT_AR[plan.category], icon=CAT_ICON[plan.category], color="gray")

        st.markdown(f"#### {plan.title}")
        st.caption(f":material/location_on: {plan.place}  \n"
                   f":material/timelapse: {fmt_duration(plan.duration_min)}")
        if plan.description:
            st.write(plan.description)

        st.space("stretch")
        count = T["joined_count"].format(n=ar(plan.count()), cap=ar(plan.capacity))
        host = T["hosted_by"].format(name=plan.host)
        st.progress(plan.count() / plan.capacity, text=f"{count} · {host}")
        render_card_button(plan, board, now)


def render_my_plan(plan, now):
    role = T["my_plan_host"] if plan.host == viewer() else T["my_plan_joined"]
    if plan.phase(now) == "waiting":
        status = T["starts_in"].format(n=ar(plan.minutes_left(now)))
    else:
        status = T["running"]
    with st.container(border=True, key="my_plan", horizontal=True, vertical_alignment="center"):
        st.image(cover(plan.category), width=120)
        with st.container(gap="xxsmall"):
            st.badge(role, icon=":material/check_circle:", color="violet")
            st.markdown(f"#### {plan.title}")
            st.caption(f":material/location_on: {plan.place} · :material/schedule: {status}")
            st.caption(T["in_plan_notice"])
        st.button(T["view_plan"], key="view_my_plan", type="primary", icon=":material/arrow_back:",
                  icon_position="right", on_click=open_plan_view)


def split_into_rows(plans, n):
    return [plans[i:i + n] for i in range(0, len(plans), n)]


def render_empty(board, message):
    with st.container(border=True, key="empty_box", horizontal_alignment="center"):
        st.image(LOGO_MARK, width=120)
        st.markdown(f"**{message}**", width="content")
        if st.button(T["post"], key="empty_post", type="primary", icon=":material/add:",
                     disabled=S.get("my_plan_id") is not None):
            post_dialog(board)


@st.fragment(run_every=REFRESH_SECONDS)
def render_feed(board, keyword):
    if S.pop("need_rerun", False):   # set by on_join: a button callback can't open the plan page itself
        st.rerun()
    show_flash()
    board.prune_ended_plans()
    now = datetime.now()

    plan_id = S.get("my_plan_id")
    mine = board.get_plan_for_participant(plan_id, viewer()) if plan_id is not None else None
    if plan_id is not None and mine is None:
        st.rerun()
    if mine is not None:
        render_my_plan(mine, now)

    category = render_category_filter()
    plans = board.search_plans(keyword) if keyword else board.get_active_plans()
    if category:
        plans = [p for p in plans if p.category == category]
    if not plans:
        render_empty(board, T["no_match"] if keyword or category else T["no_plans"])
        return

    st.markdown(f"##### {T['plans_title']} ({ar(len(plans))})")
    for row in split_into_rows(plans, COLUMNS):
        for column, plan in zip(st.columns(COLUMNS, gap="medium"), row):
            with column:
                render_card(plan, board, now)
