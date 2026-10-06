import streamlit as st

from ui.state import S, flash, leave_plan_state, me
from ui.strings import T


def plan_title(board, plan_id):
    plan = board.get_plan_for_participant(plan_id, me())
    return plan.title if plan else ""


@st.dialog(T["dlg_leave"], icon=":material/logout:")
def confirm_leave_dialog(board, plan_id):
    st.write(T["dlg_leave_q"])
    st.markdown(f"**{plan_title(board, plan_id)}**")
    stay, leave = st.columns(2)
    if stay.button(T["stay"], type="primary", width="stretch"):
        st.rerun()
    if leave.button(T["leave"], icon=":material/logout:", width="stretch"):
        ok, msg = board.leave_plan(plan_id, me())
        flash(msg)
        if ok:
            leave_plan_state()
        st.rerun()


@st.dialog(T["dlg_cancel"], icon=":material/event_busy:")
def confirm_cancel_dialog(board, plan_id):
    st.write(T["dlg_cancel_q"])
    st.markdown(f"**{plan_title(board, plan_id)}**")
    back, cancel = st.columns(2)
    if back.button(T["go_back"], type="primary", width="stretch"):
        st.rerun()
    if cancel.button(T["cancel"], key="danger_dlg_cancel", icon=":material/close:", width="stretch"):
        ok, msg = board.cancel_plan(plan_id, me(), S.get("my_host_key", ""))
        flash(msg)
        if ok:
            leave_plan_state()
        st.rerun()
