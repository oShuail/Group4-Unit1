from pathlib import Path

import streamlit as st
from PIL import Image

from ui.strings import ar

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


@st.cache_resource
def cover(category, ratio=16 / 9):
    file_name = category.lower().replace(" ", "_") + ".png"
    image = Image.open(ASSETS / "covers" / file_name)
    width, height = image.size
    new_height = int(width / ratio)
    top = (height - new_height) // 2
    return image.crop((0, top, width, top + new_height))


def fmt_time(moment):
    # 13:05 -> "١:٠٥ م"
    hour = moment.hour % 12
    if hour == 0:
        hour = 12
    suffix = "ص" if moment.hour < 12 else "م"
    return f"{ar(hour)}:{ar(f'{moment.minute:02d}')} {suffix}"


def time_window(plan):
    # When the plan starts and ends, like "١:٠٥ م - ٢:٠٥ م"
    return f"{fmt_time(plan.start_time())} - {fmt_time(plan.ends_at())}"
