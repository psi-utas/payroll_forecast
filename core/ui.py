import base64
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent  # project folder, next to app.py


def load_css(filename: str = "styles.css"):
    """Read a CSS file from the project folder and apply it to the page."""
    css = (ROOT / filename).read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def load_svg(filename: str) -> str:
    """Read an SVG file from the project folder and return its markup as text."""
    return (ROOT / filename).read_text(encoding="utf-8")


def logo_html() -> str:
    """Logo markup for the page header: utas_logo.svg if present, else logo.png, else nothing."""
    svg, png = ROOT / "utas_logo.svg", ROOT / "logo.png"
    if svg.exists():
        return svg.read_text(encoding="utf-8")
    if png.exists():
        b64 = base64.b64encode(png.read_bytes()).decode()
        return f'<img src="data:image/png;base64,{b64}">'
    return ""


def _clear(prefix: str):
    for k in [k for k in st.session_state if k.startswith(prefix)]:
        del st.session_state[k]


def clear_all_button(prefix: str):
    """Top-right 'Clear All': removes every widget value and result whose key starts with `prefix`."""
    _, c = st.columns([6, 1])
    c.button("Clear All", key=f"{prefix}clear_btn", on_click=_clear, args=(prefix,), width="stretch")


def render_footer():
    """Shown on every page (called once from app.py)."""
    st.markdown("---")
    st.markdown("<p class='footer'>Designed &amp; Developed by People Systems &amp; Insights, "
                "University of Tasmania</p>", unsafe_allow_html=True)
