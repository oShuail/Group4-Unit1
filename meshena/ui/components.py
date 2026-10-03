"""components.py - small pieces of HTML shared by the screens: icons, cover, avatars, bars."""
import base64
from html import escape
from pathlib import Path

import streamlit as st

from ui.strings import CAT_AR, ar, fmt_clock

ASSETS = Path(__file__).parent / "assets"

# Soft tile color for each category (used when there is no cover image).
TILE_COLORS = {"Lunch": "#FFE7D1", "Study": "#E6DEFA", "Work": "#DCEBFB",
               "Discussion": "#D8F1E5", "Tuwaiq Talk": "#FBE3EC", "Other": "#EFEAE0"}


def _icon(body):
    """Wrap SVG shapes into a small line icon that takes the text color."""
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>')


PIN = _icon('<path d="M12 21s-6-5.2-6-10a6 6 0 0 1 12 0c0 4.8-6 10-6 10z"/><circle cx="12" cy="11" r="2.2"/>')
CLOCK = _icon('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>')
HOURGLASS = _icon('<path d="M6 3h12M6 21h12M7 3c0 5 5 6 5 9s-5 4-5 9M17 3c0 5-5 6-5 9s5 4 5 9"/>')
USERS = _icon('<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.5 3-6 6.5-6s6.5 2.5 6.5 6"/>'
              '<path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14c2.2.6 3.5 2.6 3.5 6"/>')
LOGOUT = _icon('<path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4M15 8l4 4-4 4M19 12H9"/>')
CLOSE = _icon('<circle cx="12" cy="12" r="9"/><path d="M9 9l6 6M15 9l-6 6"/>')
PERSON = _icon('<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7"/>')
CHECK = ('<svg class="check" viewBox="0 0 80 80"><circle cx="40" cy="40" r="38"/>'
         '<path d="M24 41l11 11 21-23"/></svg>')


def load_css():
    """Read assets/style.css and add it to the page."""
    css = (ASSETS / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


@st.cache_data
def image_data_uri(path):
    """Turn an image file into a data: link so it can sit inside our HTML."""
    data = base64.b64encode(Path(path).read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def bdi(text):
    """Escaped user text, isolated so Arabic and Latin names do not break the layout."""
    return f"<bdi>{escape(str(text))}</bdi>"


def category_slug(plan):
    """File name of the cover: 'Tuwaiq Talk' -> 'tuwaiq_talk'."""
    return plan.category.lower().replace(" ", "_")


def cover_height(plan):
    """Uneven but stable cover height: the same plan always gets the same height."""
    return 150 + (plan.id * 53) % 90


def cover_html(plan, pill_text, soon):
    """Cover image (or a color tile if there is no image) with the time pill on top."""
    height = cover_height(plan)
    image = ASSETS / "covers" / f"{category_slug(plan)}.png"
    if image.exists():
        picture = f'<img src="{image_data_uri(str(image))}" style="height:{height}px">'
    else:
        color = TILE_COLORS.get(plan.category, "#EFEAE0")
        word = escape(CAT_AR.get(plan.category, plan.category))
        picture = f'<div class="tile" style="height:{height}px;background:{color}">{word}</div>'
    css = "time-pill soon" if soon else "time-pill"
    return f'<div class="cover">{picture}<span class="{css}">{escape(pill_text)}</span></div>'


def avatar_stack_html(plan, viewer):
    """Overlapping circles with first letters: host first (ring), me filled, '+N' for the rest."""
    circles = ""
    for name in plan.attendees[:4]:
        css = "av"
        if name == plan.host:
            css += " host"
        if name == viewer:
            css += " me"
        circles += f'<span class="{css}">{escape(name[:1])}</span>'
    extra = plan.count() - 4
    if extra > 0:
        circles += f'<span class="av more">+{ar(extra)}</span>'
    return f'<div class="avatars">{circles}</div>'


def row_html(icon, text):
    """One line with a small icon, used on cards and plan pages."""
    return f'<div class="row-icon"><span class="ic">{icon}</span><span>{text}</span></div>'


def bar_html(label, seconds, fraction):
    """Countdown bar: label, big clock and a thin progress line."""
    percent = max(0.0, min(fraction, 1.0)) * 100
    return (f'<div class="cd-bar"><span class="cd-label"><i class="pulse"></i>{escape(label)}</span>'
            f'<b class="cd-clock">{fmt_clock(seconds)}</b>'
            f'<div class="cd-prog"><i style="width:{percent:.1f}%"></i></div></div>')


def dialog_head_html(icon, kind, heading, text=""):
    """Centered header for the small dialogs: round icon (kind: 'soft' or 'danger'), heading, text."""
    body = f'<p class="dlg-text">{text}</p>' if text else ""
    return (f'<div class="dlg-head"><div class="dlg-icon {kind}">{icon}</div>'
            f'<div class="dlg-h">{heading}</div>{body}</div>')
