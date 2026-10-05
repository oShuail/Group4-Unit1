import streamlit as st

from ui.contract import PlanBoard
from ui.components import ASSETS, load_css
from ui.state import S, leave_plan_state, show_flash, viewer
from ui.strings import T
from ui.views_feed import render_feed, render_top_bar
from ui.views_name import render_name_page
from ui.views_plan import render_plan_page
from ui.data_bridge import set_board, get_cancelled_plan_notice, participant_identity
from ui.legacy_design import ensure_session_state


@st.cache_resource
def get_board():
    return PlanBoard()


def find_my_plan(board):
    plan_id = S.get("my_plan_id")
    if plan_id is None:
        return None
    plan = board.get_plan_for_participant(plan_id, participant_identity(viewer()))
    if plan is None:
        cancelled = get_cancelled_plan_notice(plan_id, viewer())
        if cancelled:
            S["cancelled_notice"] = cancelled
        else:
            ended = S.get("last_phase") == "running" and (S.get("last_secs") or 99) <= 3
            st.toast(T["plan_ended"] if ended else T["plan_gone"])
        leave_plan_state()
    return plan


def main():
    st.set_page_config(page_title=T["page_title"], page_icon=str(ASSETS / "logo_mark.png"), layout="wide")
    ensure_session_state()  # ADDED: required for refresh/new Streamlit sessions.
    load_css()
    board = get_board()
    set_board(board)  # ADDED: binds the preserved UI to the PlanBoard core once per rerun.
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
        render_feed(board, keyword)


main()
