import streamlit as st

from ui.state import (
    S,
    flash,
    leave_plan_state,
    me,
)
from ui.strings import T


def plan_title(board, plan_id):
    plan = board.get_plan_for_participant(
        plan_id,
        me(),
    )

    return (
        plan.title
        if plan
        else ""
    )


# =========================================
# مغادرة الخطة
# =========================================

@st.dialog("مغادرة الخطة")
def confirm_leave_dialog(
    board,
    plan_id,
):

    st.html(
        """
        <style>

        .leave-confirm-text {
            width: 100%;

            direction: rtl;
            text-align: center;

            color: #111111;

            font-size: 16px;
            font-weight: 400;

            margin: 4px auto 18px auto;
        }

        </style>

        <div class="leave-confirm-text">
            متأكد من مغادرة الخطة؟
        </div>
        """
    )

    # في RTL:
    # أول عمود = يمين
    # ثاني عمود = يسار

    leave_col, back_col = st.columns(
        2,
        gap="small",
    )

    # يمين
    with leave_col:

        if st.button(
            "مغادرة الخطة",
            key="confirm_leave_plan",
            width="stretch",
        ):

            ok, msg = board.leave_plan(
                plan_id,
                me(),
            )

            flash(msg)

            if ok:
                leave_plan_state()

            st.rerun()

    # يسار
    with back_col:

        if st.button(
            "ارجع",
            key="leave_back",
            type="primary",
            width="stretch",
        ):

            st.rerun()


# =========================================
# إلغاء الخطة
# =========================================

@st.dialog("الغاء الخطه")
def confirm_cancel_dialog(
    board,
    plan_id,
):

    st.html(
        """
        <style>

        .cancel-confirm-text {
            width: 100%;

            direction: rtl;
            text-align: center;

            color: #111111;

            font-size: 16px;
            font-weight: 400;

            margin: 4px auto 18px auto;
        }

        </style>

        <div class="cancel-confirm-text">
            متأكد بتلغي الخطه؟
        </div>
        """
    )

    # إلغاء الخطة يمين
    # ارجع يسار

    cancel_col, back_col = st.columns(
        2,
        gap="small",
    )

    # يمين
    with cancel_col:

        if st.button(
            "الغاء الخطه",
            key="danger_dlg_cancel",
            width="stretch",
        ):

            ok, msg = board.cancel_plan(
                plan_id,
                me(),
                S.get(
                    "my_host_key",
                    "",
                ),
            )

            flash(msg)

            if ok:
                leave_plan_state()

            st.rerun()

    # يسار
    with back_col:

        if st.button(
            "ارجع",
            key="cancel_back",
            type="primary",
            width="stretch",
        ):

            st.rerun()