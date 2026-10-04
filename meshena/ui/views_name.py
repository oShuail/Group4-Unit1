import streamlit as st

from ui.components import LOGO
from ui.state import S
from ui.strings import T


def render_name_page():
    st.space("large")
    with st.container(horizontal_alignment="center", gap="large"):
        st.image(LOGO, width=220)
        with st.container(border=True, key="name_card", width=440, gap="small"):
            st.markdown(f"### {T['welcome']}")
            st.caption(T["name_privacy"])
            with st.form("name_form", border=False):
                name = st.text_input(T["name_hint"], placeholder=T["name_hint"], max_chars=24,
                                     icon=":material/person:", label_visibility="collapsed")
                submitted = st.form_submit_button(T["name_btn"], type="primary", width="stretch",
                                                  icon=":material/arrow_back:", icon_position="right")
            if submitted:
                if name.strip():
                    S["name"] = name.strip()
                    st.rerun()
                else:
                    st.error(T["name_empty"], icon=":material/error:")
        with st.container(horizontal=True, horizontal_alignment="center", gap="small", width=440):
            st.badge(T["feat_post"], icon=":material/add_circle:", color="violet")
            st.badge(T["feat_join"], icon=":material/group_add:", color="violet")
            st.badge(T["feat_quick"], icon=":material/bolt:", color="violet")
