from pathlib import Path
from PIL import Image
import streamlit as st
from ui.strings import CAT_AR, T

ASSETS = Path(__file__).parent / "assets"
LOGO = str(ASSETS / "logo_full.png")
LOGO_MARK = str(ASSETS / "logo_mark.png")

CAT_ICON = {
    "Lunch": ":material/restaurant:",
    "Study": ":material/menu_book:",
    "Work": ":material/work:",
    "Discussion": ":material/forum:",
    "Tuwaiq Talk": ":material/record_voice_over:",
    "Other": ":material/interests:",
}


def load_css():
    # ADDED: retained for the modular app.py API. legacy_design.base_css() injects
    # the exact supplied CSS plus its original dynamic rules.
    return None


def category_label(category):
    if category == "All":
        return T["all"]
    return f"{CAT_ICON.get(category, ':material/category:')} {CAT_AR.get(category, category)}"


@st.cache_resource
def cover(category, ratio=16 / 9):
    # ADDED: compatibility fallback; preserved card design does not call cover().
    path = ASSETS / "covers" / (category.lower().replace(" ", "_") + ".png")
    image = Image.open(path) if path.exists() else Image.new("RGB", (1280, 720), "white")
    width, height = image.size
    new_height = min(height, int(width / ratio))
    top = max(0, (height - new_height) // 2)
    return image.crop((0, top, width, top + new_height))
