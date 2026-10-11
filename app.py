import html
import streamlit as st
from core.ui import load_css, logo_html, render_footer
from views import home, permanent, casual, severance

st.set_page_config(page_title="Payroll Forecasting Tool", page_icon="logo.png", layout="wide",
                   initial_sidebar_state="collapsed")

load_css()  # all styling lives in styles.css


# AUTH GATE
if not st.user.is_logged_in:
    col1, col2, col3 = st.columns([1, 1.1, 1])
    with col2:
        st.markdown(f"""
        <div class="login-card">
            <div class="login-logo">{logo_html()}</div>
            <p class="login-title">Payroll Forecasting Tool</p>
            <p class="login-subtitle">People Systems &amp; Insights</p>
            <hr class="login-divider">
            <p class="login-helper">Sign in with your UTAS account to continue</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Log in with UTAS Entra ID", width="stretch"):
            st.login("microsoft")
        st.markdown(
            "<p class='login-footer'>University of Tasmania &middot; Internal use only</p>",
            unsafe_allow_html=True
        )
    st.stop()

scale = {"Default": "100%", "Large": "112.5%", "Extra Large": "125%"}[st.session_state.get("text_size", "Default")]
st.markdown(f"<style>html {{ font-size: {scale}; }}</style>", unsafe_allow_html=True)

# Page objects are created first so the Home tiles can link to them.
P = {
    "permanent": st.Page(permanent.render, title="Permanent / Fixed-Term Forecast", icon="📈", url_path="permanent"),
    "casual": st.Page(casual.render, title="Casual Cost Calculator", icon="👥", url_path="casual"),
    "severance": st.Page(severance.render, title="Severance Calculator", icon="🛡️", url_path="severance"),
}

def home_page():
    home.render(P)

HOME = st.Page(home_page, title="Home", default=True, url_path="home")

pg = st.navigation([HOME, *P.values()], position="hidden")  # hidden = no sidebar menu

if pg is not HOME:  # slim top bar on every other page
    left, right = st.columns([3, 1], vertical_alignment="center")
    left.page_link(HOME, label="← Back to Home")
    right.markdown(f"<div class='topbar-logo'>{logo_html()}</div>", unsafe_allow_html=True)

pg.run()
render_footer()

# The sidebar is hidden, so the signed-in user and logout sit under the footer
left, right = st.columns([5, 1], vertical_alignment="center")
left.markdown(f"<p class='account-user'>Signed in as <strong>{html.escape(st.user.name or '')}</strong></p>",
              unsafe_allow_html=True)
if right.button("Log out", width="stretch"):
    st.logout()
