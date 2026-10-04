from pathlib import Path

import streamlit as st
from PIL import Image

from ui.strings import CAT_AR, T

ASSETS = Path(__file__).parent / "assets"
LOGO = str(ASSETS / "logo_full.png")
LOGO_MARK = str(ASSETS / "logo_mark.png")

CAT_ICON = {
    "Lunch": ":material/restaurant:",
    "Study": ":material/menu_book:",
    "Work": ":material/work:",
    "Discussion": ":material/forum:",
    "Tuwaiq Talk": ":material/mic:",
    "Other": ":material/interests:",
}


def load_css():
    st.html(ASSETS / "style.css")


def category_label(category):
    if category == "All":
        return T["all"]
    return f"{CAT_ICON[category]} {CAT_AR[category]}"


@st.cache_resource
def cover(category, ratio=16 / 9):
    file_name = category.lower().replace(" ", "_") + ".png"
    image = Image.open(ASSETS / "covers" / file_name)
    width, height = image.size
    new_height = int(width / ratio)
    top = (height - new_height) // 2
    return image.crop((0, top, width, top + new_height))
