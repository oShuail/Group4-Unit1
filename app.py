import streamlit as st

from ui.contract import PlanBoard
from ui.components import ASSETS, load_css
from ui.state import S, leave_plan_state, me, show_flash, viewer
from ui.strings import T
from ui.views_create import render_create_page
from ui.views_feed import render_feed, render_top_bar
from ui.views_name import render_name_page
from ui.views_plan import render_plan_page


@st.cache_resource
def get_board():
    # One board for everyone, so all browsers see the same plans
    return PlanBoard()


def find_my_plan(board):
    plan_id = S.get("my_plan_id")
    if plan_id is None:
        return None
    plan = board.get_plan_for_participant(plan_id, me())
    if plan is None:
        # almost no time was left, so it ended by itself (the host did not cancel it)
        ended = S.get("last_phase") == "running" and (S.get("last_secs") or 99) <= 3
        st.toast(T["plan_ended"] if ended else T["plan_gone"])
        leave_plan_state()
    return plan


def main():
    st.set_page_config(page_title=T["page_title"], page_icon=str(ASSETS / "logo_mark.png"), layout="wide")
    load_css()
    board = get_board()
    if not viewer():
        render_name_page()
        return
    board.prune_ended_plans()
    show_flash()
    plan = find_my_plan(board)
    view = S.get("view", "feed")
    if plan is not None and view == "plan":
        render_plan_page(board, plan)
    elif plan is None and view == "create":   # you can't make a new plan while you are in one
        render_create_page(board)
    else:
        keyword, category = render_top_bar(board)
        render_feed(board, keyword, category)


main()

# -----------------------------------------------------------------------------
# Reflection
# - Most challenging: many people use the app at the same time, so the plans live
#   in one shared board with a lock, and two people can even have the same name.
# - Concept we enjoyed most: classes and dictionaries, a Plan knows its own time
#   and people, and the board keeps every plan by its id.
# - With more time: save plans in a database so they stay after a restart, and
#   send a notification when a plan is about to start.
# -----------------------------------------------------------------------------
