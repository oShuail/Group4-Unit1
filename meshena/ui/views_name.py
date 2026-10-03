"""views_name.py - the name page (A): shown first, nothing else on it."""
import streamlit as st

from ui.components import ASSETS, image_data_uri
from ui.state import S
from ui.strings import T


def render_name_page():
    """A: faint logo mark, logo, and one card with a single name field."""
    mark = image_data_uri(str(ASSETS / "logo_mark.png"))
    st.markdown(f'<img class="bg-mark" src="{mark}">', unsafe_allow_html=True)
    st.markdown(f'<img class="name-logo" src="{image_data_uri(str(ASSETS / "logo_full.png"))}">',
                unsafe_allow_html=True)
    with st.container(key="name_card"):
        with st.form("name_form", border=False):
            st.markdown(f'<div class="name-lead">{T["welcome"]}</div>', unsafe_allow_html=True)
            name = st.text_input(T["name_hint"], placeholder=T["name_hint"], max_chars=24,
                                 label_visibility="collapsed")
            submitted = st.form_submit_button(T["name_btn"], type="primary")
        if submitted:
            if name.strip():
                S["name"] = name.strip()
                st.rerun()
            else:
                st.error(T["name_empty"])
