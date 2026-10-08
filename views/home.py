import streamlit as st
from core.ui import logo_html

VERSION_BADGE = "https://img.shields.io/badge/beta version-psi%200.0.0.1-green"

TILES = [  # (page key, icon, title, description)
    ("permanent", "📈", "Permanent / Fixed-Term Forecast", "Salary and employment costs over a forecast period."),
    ("casual", "👥", "Casual Cost Calculator", "Casual activity rates, hours and on-costs."),
    ("severance", "🛡️", "Severance Calculator", "Severance payment and Budget Centre cost."),
]


def render(P):
    """P = dict of page objects built in app.py."""
    st.markdown(f'<img src="{VERSION_BADGE}">', unsafe_allow_html=True)

    st.markdown(f"""
<div class="header-container">
  <div>
    <p class="header-title">Payroll Forecasting Tool</p>
    <p class="header-subtitle">People Systems &amp; Insights</p>
  </div>
  <div class="logo-container">{logo_html()}</div>
</div>""", unsafe_allow_html=True)

    st.markdown('<p class="section-label">Calculators</p>', unsafe_allow_html=True)
    st.markdown('<p class="lead">Select a calculator to prepare an employment cost estimate.</p>',
                unsafe_allow_html=True)

    for col, (key, icon, title, desc) in zip(st.columns(3, gap="medium"), TILES):
        with col.container(key=f"tile_{key}"):   # "tile_*" is styled in styles.css
            st.markdown(f"""
<div class="tile-body">
  <div class="tile-icon">{icon}</div>
  <p class="tile-title">{title}</p>
  <p class="tile-desc">{desc}</p>
</div>""", unsafe_allow_html=True)
            st.page_link(P[key], label="Open Calculator →", width="stretch")

    st.markdown('<div class="note">Rates marked <b>FORECAST</b> are planning assumptions '
                'and may change.</div>', unsafe_allow_html=True)