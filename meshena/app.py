"""مشينا | Join Me - app entry point: set up the page and choose which screen to show.

Pseudocode:
    load the CSS and get the one shared board
    no name yet?            -> name page
    show the saved message (toast)
    I am in a plan and chose to open it -> plan page (host or joined)
    otherwise               -> the feed (top bar, my-plan card, plan cards)
"""
import streamlit as st

from ui.contract import PlanBoard   # the swap to the real logic is done inside contract.py
from ui.components import ASSETS, load_css
from ui.state import S, leave_plan_state, show_flash, viewer
from ui.strings import T
from ui.views_feed import render_category_filter, render_feed, render_top_bar
from ui.views_name import render_name_page
from ui.views_plan import render_plan_page


@st.cache_resource
def get_board():
    """Create the one PlanBoard that all browsers share."""
    return PlanBoard()


def find_my_plan(board):
    """The plan I am in, or None. If it just ended or was cancelled, say so and go to the feed."""
    plan_id = S.get("my_plan_id")
    if plan_id is None:
        return None
    plan = board.get_plan_for_participant(plan_id, viewer())
    if plan is None:
        # The countdown saved how long was left: almost nothing left means it ended on its own.
        ended = S.get("last_phase") == "running" and (S.get("last_secs") or 99) <= 3
        st.toast(T["plan_ended"] if ended else T["plan_gone"])
        leave_plan_state()
    return plan


def main():
    """Choose the screen."""
    st.set_page_config(page_title=T["page_title"], page_icon=str(ASSETS / "logo_mark.png"), layout="wide")
    load_css()
    board = get_board()
    if not viewer():
        render_name_page()
        return
    board.prune_ended_plans()
    show_flash()
    plan = find_my_plan(board)
    if plan is not None and S.get("view") == "plan":
        render_plan_page(board, plan)
    else:
        keyword = render_top_bar(board)
        category = render_category_filter()
        render_feed(board, keyword, category)


main()
