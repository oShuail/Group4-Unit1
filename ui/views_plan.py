from datetime import datetime

import streamlit as st

from ui.components import CAT_ICON, LOGO, cover, time_window
from ui.dialogs import confirm_cancel_dialog, confirm_leave_dialog
from ui.state import S, flash, me, open_feed_view, show_name
from ui.strings import CAT_AR, T, ar, fmt_clock, fmt_duration


@st.fragment(run_every=1)
def countdown(board, plan_id, phase):
    now = datetime.now()

    plan = board.get_plan_for_participant(
        plan_id,
        me(),
    )

    if plan is None or plan.phase(now) != phase:
        st.rerun()
        return

    S["last_phase"] = phase
    S["last_secs"] = plan.seconds_to_end(now)

    if phase == "waiting":
        seconds = plan.seconds_to_start(now)
        total = plan.starts_in_min * 60
        label = T["wait_left"]

    else:
        seconds = plan.seconds_to_end(now)
        total = plan.duration_min * 60
        label = T["plan_left"]

    with st.container(border=True):

        st.metric(
            label,
            fmt_clock(seconds),
            icon=":material/timer:",
        )

        st.progress(
            1 - seconds / total
        )


@st.fragment(run_every=2)
def participants_panel(board, plan_id):
    plan = board.get_plan_for_participant(
        plan_id,
        me(),
    )

    if plan is None:
        return

    with st.container(
        border=True,
        key="people_panel",
    ):

        st.markdown(
            f"#### {T['participants']} "
            f"({ar(plan.count())} / {ar(plan.capacity)})"
        )

        st.progress(
            plan.count() / plan.capacity
        )

        for person in plan.attendees:

            with st.container(
                horizontal=True,
                vertical_alignment="center",
            ):

                if plan.has_arrived(person):

                    st.markdown(
                        f":green[:material/check_circle:] "
                        f"{show_name(person)}",
                        width="content",
                    )

                    st.badge(
                        T["arrived_tag"],
                        icon=":material/where_to_vote:",
                        color="green",
                    )

                else:

                    st.markdown(
                        f":violet[:material/account_circle:] "
                        f"{show_name(person)}",
                        width="content",
                    )

                if person == plan.host:

                    st.badge(
                        T["host_tag"],
                        color="violet",
                    )

                if person == me():

                    st.badge(
                        T["you"],
                        color="gray",
                    )

        seats = (
            plan.capacity
            - plan.count()
        )

        if seats > 0:

            st.caption(
                T["seats_left"].format(
                    n=ar(seats)
                )
            )


def render_arrived_button(board, plan):
    done = plan.has_arrived(me())

    label = (
        T["arrived_done"]
        if done
        else T["arrive"]
    )

    if st.button(
        label,
        key="arrived_btn",
        icon=":material/where_to_vote:",
        disabled=done,
        width="stretch",
    ):

        ok, msg = board.mark_arrived(
            plan.id,
            me(),
        )

        flash(msg)

        st.rerun()


def render_plan_page(board, plan):

    role = (
        "host"
        if plan.host == me()
        else "join"
    )

    phase = plan.phase(
        datetime.now()
    )

    key = (
        f"hero_{role}_"
        + (
            "wait"
            if phase == "waiting"
            else "run"
        )
    )

    st.html(
        """
        <style>

        .st-key-plan_main_wrap {
            width: 400px !important;
            max-width: 100% !important;

            margin-left: 0 !important;
            margin-right: auto !important;
        }

        .st-key-plan_card {
            padding: 14px !important;
        }

        .st-key-plan_card h3 {
            margin-top: 5px !important;
            margin-bottom: 3px !important;
            line-height: 1.15 !important;
        }

        .st-key-plan_card [data-testid="stCaptionContainer"] {
            margin-top: 1px !important;
            margin-bottom: 3px !important;
        }

        .st-key-plan_card [data-testid="stCaptionContainer"] p {
            margin-bottom: 0 !important;
        }

        .st-key-plan_card [data-testid="stVerticalBlock"] {
            gap: 0.35rem !important;
        }

        .plan-info-line {
            direction: rtl;
            text-align: right;

            font-size: 15px;
            color: #302A48;

            margin: 2px 0 !important;
            line-height: 1.5;
        }

        .plan-info-label {
            font-weight: 700;
        }

        .st-key-plan_side_wrap {
            width: 100% !important;
        }

        .st-key-people_panel {
            max-width: 335px !important;

            margin-left: auto !important;
            margin-right: 0 !important;
        }

        .st-key-arrived_btn button {
            background: #35A866 !important;
            border: 1px solid #35A866 !important;
            color: white !important;

            min-height: 42px !important;
            border-radius: 14px !important;

            box-shadow: none !important;
            transform: none !important;
        }

        .st-key-arrived_btn button:hover,
        .st-key-arrived_btn button:active {
            background: #35A866 !important;
            border-color: #35A866 !important;
            color: white !important;

            box-shadow: none !important;
            transform: none !important;
        }

        .st-key-danger_plan_cancel button {
            background: #FFF8F7 !important;
            border: 1px solid #E89A92 !important;
            color: #C84A3D !important;

            min-height: 42px !important;
            border-radius: 14px !important;

            box-shadow: none !important;
        }

        .st-key-danger_plan_cancel button:hover {
            background: #FFF3F1 !important;
            border-color: #DF7F75 !important;
            color: #B73D32 !important;

            box-shadow: none !important;
            transform: none !important;
        }

        .st-key-plan_leave button {
            min-height: 42px !important;
            border-radius: 14px !important;
            box-shadow: none !important;
        }

        </style>
        """
    )

    with st.container(
        horizontal=True,
        vertical_alignment="center",
    ):

        st.image(
            LOGO,
            width=160,
        )

        st.space("stretch")

        st.button(
            "رجوع",
            icon=":material/arrow_back:",
            icon_position="right",
            on_click=open_feed_view,
        )

    main, side = st.columns(
        [1.15, 1],
        gap="large",
        vertical_alignment="center",
    )

    with main:

        with st.container(
            key="plan_main_wrap"
        ):

            with st.container(
                border=True,
                key="plan_card",
                gap="xsmall",
            ):

                st.image(
                    cover(
                        plan.category,
                        ratio=3,
                    ),
                    width="stretch",
                )

                with st.container(
                    horizontal=True,
                    gap="xsmall",
                ):

                    if phase == "waiting":

                        st.badge(
                            T[key],
                            icon=":material/hourglass_top:",
                            color="violet",
                        )

                    else:

                        st.badge(
                            T[key],
                            icon=":material/play_circle:",
                            color="green",
                        )

                    st.badge(
                        CAT_AR[plan.category],
                        icon=CAT_ICON[
                            plan.category
                        ],
                        color="gray",
                    )

                st.markdown(
                    f"### {plan.title}"
                )

                st.caption(
                    T[key + "_sub"]
                )

                # all four info lines in one block, so there is no gap between them
                st.html(
                    f"""
                    <div class="plan-info-line">
                        <span class="plan-info-label">المكان:</span>
                        {plan.place}
                    </div>
                    <div class="plan-info-line">
                        <span class="plan-info-label">الوقت:</span>
                        {time_window(plan)}
                    </div>
                    <div class="plan-info-line">
                        <span class="plan-info-label">المدة:</span>
                        {fmt_duration(plan.duration_min)}
                    </div>
                    <div class="plan-info-line">
                        <span class="plan-info-label">مع:</span>
                        {show_name(plan.host)}
                    </div>
                    """
                )

                if plan.description:

                    st.write(
                        plan.description
                    )

                countdown(
                    board,
                    plan.id,
                    phase,
                )

            if role == "host":

                arrived_col, cancel_col = st.columns(
                    2,
                    gap="xsmall",
                )

                with arrived_col:

                    render_arrived_button(
                        board,
                        plan,
                    )

                with cancel_col:

                    if st.button(
                        "الغاء الخطه",
                        key="danger_plan_cancel",
                        width="stretch",
                    ):

                        confirm_cancel_dialog(
                            board,
                            plan.id,
                        )

            else:

                arrived_col, leave_col = st.columns(
                    2,
                    gap="xsmall",
                )

                with arrived_col:

                    render_arrived_button(
                        board,
                        plan,
                    )

                with leave_col:

                    if st.button(
                        T["leave_plan"],
                        key="plan_leave",
                        width="stretch",
                    ):

                        confirm_leave_dialog(
                            board,
                            plan.id,
                        )

    with side:

        with st.container(
            key="plan_side_wrap"
        ):

            participants_panel(
                board,
                plan.id,
            )