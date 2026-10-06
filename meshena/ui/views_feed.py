from datetime import datetime

import streamlit as st

from ui.components import CAT_ICON, LOGO, LOGO_MARK, cover, time_window
from ui.contract import CATEGORIES
from ui.state import S, enter_plan, flash, me, open_create_view, open_plan_view, show_flash, show_name, viewer
from ui.strings import CAT_AR, CAT_EN, MSG, T, ar

REFRESH_SECONDS = 10
COLUMNS = 2


def render_name_menu(board):
    with st.popover(viewer(), icon=":material/account_circle:", key="profile"):
        st.markdown(f"**{T['dlg_rename']}**")
        new_name = st.text_input(T["f_new_name"], value=viewer(), max_chars=24, label_visibility="collapsed")
        if st.button(T["save"], key="rename_save", type="primary", width="stretch"):
            new_name = new_name.replace("#", "").strip()
            if new_name == "":
                st.error(MSG["Enter your name first"])
            else:
                old_me = me()
                S["name"] = new_name
                ok, msg = board.rename_person(old_me, me())
                flash(msg)
                st.rerun()


def render_top_bar(board):
    in_plan = S.get("my_plan_id") is not None
    with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
        st.image(LOGO, width=130)
        st.space("stretch")
        render_name_menu(board)
        st.button(T["post"], key="open_post", type="primary", icon=":material/add:", disabled=in_plan,
                  on_click=open_create_view)
    st.markdown(f"## {T['greet'].format(name=viewer())}")
    st.caption(T["greet_sub"])

    search_col, category_col = st.columns([3, 1])
    keyword = search_col.text_input(T["search"], placeholder=T["search"], icon=":material/search:",
                                    live=True, label_visibility="collapsed")
    category = category_col.selectbox(T["all"], ["All"] + CATEGORIES, label_visibility="collapsed",
                                      format_func=lambda c: T["all"] if c == "All" else CAT_AR[c])
    keyword = keyword.strip()
    return CAT_EN.get(keyword, keyword), category


def on_join(board, plan_id):
    ok, msg = board.join_plan(plan_id, me())
    flash(msg)
    if ok:
        enter_plan(plan_id)
        S["need_rerun"] = True


def render_card_button(plan, board, now):
    if plan.has_joined(me()):
        st.button(T["view_plan"], key=f"view_{plan.id}", type="primary", icon=":material/visibility:",
                  width="stretch", on_click=open_plan_view)
    elif S.get("my_plan_id") is not None:
        st.caption(f":material/lock: {T['in_other_plan']}")
    else:
        closed = plan.phase(now) != "waiting"
        if closed:
            label = T["join_closed"]
        elif plan.is_full():
            label = T["full"]
        else:
            label = T["join"]
        st.button(label, key=f"join_{plan.id}", type="primary", icon=":material/group_add:", width="stretch",
                  disabled=closed or plan.is_full(), on_click=on_join, args=(board, plan.id))


def render_card(plan, board, now, preview=False):
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
        st.caption(f":material/person: {T['hosted_by'].format(name=show_name(plan.host))}  \n"
                   f":material/location_on: {plan.place}  \n"
                   f":material/schedule: {time_window(plan)}")
        if plan.description:
            st.write(plan.description)

        st.space("stretch")
        count = T["joined_count"].format(n=ar(plan.count()), cap=ar(plan.capacity))
        names = "، ".join(show_name(person) for person in plan.attendees)
        st.progress(plan.count() / plan.capacity, text=f"{count} · {names}")
        if not preview:
            render_card_button(plan, board, now)


def split_into_rows(plans, n):
    return [plans[i:i + n] for i in range(0, len(plans), n)]


def render_grid(plans, board, now):
    for row in split_into_rows(plans, COLUMNS):
        for column, plan in zip(st.columns(COLUMNS, gap="medium"), row):
            with column:
                render_card(plan, board, now)


def render_empty(message):
    with st.container(border=True, key="empty_box", horizontal_alignment="center"):
        st.image(LOGO_MARK, width=120)
        st.markdown(f"**{message}**", width="content")
        st.button(T["post"], key="empty_post", type="primary", icon=":material/add:",
                  disabled=S.get("my_plan_id") is not None, on_click=open_create_view)


@st.fragment(run_every=REFRESH_SECONDS)
def render_feed(board, keyword, category):
    if S.pop("need_rerun", False):   # a button in this fragment (Join, View plan, Post) asked to change the page
        st.rerun()
    show_flash()
    board.prune_ended_plans()
    now = datetime.now()

    # My plan (the one I host or joined) always shows first, even after it started
    plan_id = S.get("my_plan_id")
    mine = board.get_plan_for_participant(plan_id, me()) if plan_id is not None else None
    if plan_id is not None and mine is None:
        st.rerun()   # it ended or got cancelled, app.py shows the message
    if mine is not None:
        title = T["my_plans"] if mine.host == me() else T["joined_section"]
        st.markdown(f"##### {title}")
        render_grid([mine], board, now)

    plans = board.search_plans(keyword) if keyword else board.get_active_plans()
    if category != "All":
        plans = [p for p in plans if p.category == category]
    if mine is not None:
        plans = [p for p in plans if p.id != mine.id]

    if not plans:
        if keyword or category != "All":
            render_empty(T["no_match"])
        elif mine is not None:
            st.caption(T["no_other_plans"])
        else:
            render_empty(T["no_plans"])
        return

    title = T["other_plans"] if mine is not None else T["plans_title"]
    st.markdown(f"##### {title} ({ar(len(plans))})")
    render_grid(plans, board, now)
