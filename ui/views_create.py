from datetime import datetime

import streamlit as st

from ui.components import LOGO
from ui.contract import (
    CATEGORIES,
    MAX_START_MIN,
    MIN_START_MIN,
    Plan,
)
from ui.state import (
    S,
    enter_plan,
    flash,
    me,
    open_feed_view,
    viewer,
)
from ui.strings import CAT_AR, MSG, T, fmt_duration
from ui.views_feed import render_card


DURATIONS = [15, 30, 45, 60, 90, 120, 180, 240]

FORM_KEYS = [
    "c_title",
    "c_category",
    "c_place",
    "c_description",
    "c_wait",
    "c_duration",
    "c_capacity",
]


@st.dialog(" ")
def create_error_dialog():

    errors = S.get("create_errors", [])

    st.html(
        """
        <style>

        div[data-testid="stDialog"] div[role="dialog"] {
            max-width: 360px !important;
            border-radius: 20px !important;
            padding: 6px 10px 10px 10px !important;
        }

        .create-error-wrap {
            width: 100%;
            direction: rtl;
            text-align: center;
            color: #111111;
        }

        .create-error-icon-circle {
            width: 46px;
            height: 46px;

            margin: 0 auto 10px auto;

            border-radius: 50%;

            background: #F1ECFF;
            color: #5B34C9;

            display: flex;
            align-items: center;
            justify-content: center;

            font-size: 26px;
            font-weight: 800;

            line-height: 1;
        }

        .create-error-title {
            width: 100%;

            text-align: center;

            font-size: 16px;
            font-weight: 700;

            color: #111111;

            margin: 0 auto 14px auto;
        }

        .create-error-item {
            width: 100%;

            text-align: center;

            font-size: 15px;
            font-weight: 400;

            color: #111111;

            margin: 6px auto;
        }

        </style>

        <div class="create-error-wrap">

            <div class="create-error-icon-circle">
                !
            </div>

            <div class="create-error-title">
                البيانات التالية مطلوبة لنشر الخطة
            </div>

        </div>
        """
    )

    for error in errors:

        st.html(
            f"""
            <div class="create-error-item">
                {error}
            </div>
            """
        )

    st.space("small")

    if st.button(
        "متابعة",
        key="close_create_error",
        width="stretch",
        type="primary",
    ):
        S["create_errors"] = []
        st.rerun()


def post_plan(
    board,
    title,
    category,
    place,
    wait,
    description,
    duration,
    capacity,
):

    errors = board.validate_input(
        title,
        place,
        viewer(),
        wait,
        duration,
        capacity,
    )

    if errors:

        S["create_errors"] = [
            MSG.get(error, error)
            for error in errors
        ]

        create_error_dialog()
        return

    ok, msg, plan_id, host_key = board.create_plan(
        title,
        category,
        place,
        wait,
        description,
        me(),
        duration,
        capacity,
    )

    if not ok:

        S["create_errors"] = [
            MSG.get(msg, msg)
        ]

        create_error_dialog()
        return

    flash(msg)

    for key in FORM_KEYS:
        S.pop(key, None)

    enter_plan(
        plan_id,
        host_key,
    )

    st.rerun()


def render_create_page(board):

    st.markdown(
        """
        <style>

        .st-key-create_preview {
            position: sticky !important;
            top: 24px !important;
            align-self: flex-start !important;
            z-index: 2;
        }

        .create-preview-label {
            width: 100%;
            text-align: center;

            font-size: 16px;
            font-weight: 600;

            margin-bottom: 14px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

    # =========================
    # Header
    # =========================

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
            "رجوع  ←",
            key="create_back",
            on_click=open_feed_view,
        )

    st.markdown(
        f"## {T['dlg_post']}"
    )

    form_col, preview_col = st.columns(
        [1.15, 1],
        gap="large",
    )

    # =========================
    # FORM
    # =========================

    with form_col:

        with st.container(
            border=True,
            key="form_card",
            gap="xsmall",
        ):

            st.caption(
                f":material/person: تنشر باسم **{viewer()}**"
            )

            # الفئة
            category = st.selectbox(
                T["f_category"],
                CATEGORIES,
                key="c_category",
                format_func=lambda c: CAT_AR[c],
            )

            # عنوان الخطة
            title = st.text_input(
                T["f_title"],
                key="c_title",
                max_chars=40,
                placeholder=T["f_title_hint"],
            )

            # المكان
            place = st.text_input(
                "المكان",
                key="c_place",
                max_chars=40,
                placeholder=T["f_place_hint"],
                icon=":material/location_on:",
            )

            # الوصف
            description = st.text_area(
                "وصف بسيط",
                key="c_description",
                max_chars=140,
                height=80,
                placeholder=T["f_description_hint"],
            )

            # =========================
            # الوقت والعدد
            # =========================

            wait_col, duration_col, capacity_col = st.columns(
                3,
                gap="small",
            )

            wait = wait_col.number_input(
                T["f_wait"],
                min_value=MIN_START_MIN,
                max_value=MAX_START_MIN,
                value=5,
                key="c_wait",
                icon=":material/schedule:",
            )

            duration = duration_col.selectbox(
                T["f_duration"],
                DURATIONS,
                index=3,
                key="c_duration",
                format_func=fmt_duration,
            )

            capacity = capacity_col.number_input(
                T["f_capacity"],
                min_value=2,
                max_value=10,
                value=4,
                step=1,
                key="c_capacity",
                icon=":material/group:",
            )

            # =========================
            # نشر الخطة
            # =========================

            if st.button(
                T["f_post"],
                type="primary",
                icon=":material/send:",
                width="stretch",
                key="create_plan_button",
            ):

                post_plan(
                    board,
                    title,
                    category,
                    place,
                    wait,
                    description,
                    duration,
                    capacity,
                )

    # =========================
    # PREVIEW
    # =========================

    with preview_col:

        with st.container(
            key="create_preview",
        ):

            st.markdown(
                """
                <div class="create-preview-label">
                    كذا بتطلع خطتك
                </div>
                """,
                unsafe_allow_html=True,
            )

            preview = Plan(
                0,

                title.strip()
                or T["preview_title"],

                category,

                place.strip()
                or T["preview_place"],

                description.strip(),

                me(),

                wait,
                duration,
                capacity,

                "",
            )

            render_card(
                preview,
                board,
                datetime.now(),
                preview=True,
            )