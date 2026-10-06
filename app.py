import streamlit as st
from views import home, permanent, casual, severance, reference, settings, help_about

st.set_page_config(page_title="Payroll Forecasting Tool", page_icon="💼", layout="wide",
                   initial_sidebar_state="collapsed")

size = {"Default": "16px", "Large": "18px", "Extra Large": "21px"}[st.session_state.get("text_size", "Default")]
st.markdown(f"""<style>
html, body, [class*='st-'] {{font-size:{size};}}
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarNav"] {{display:none;}}
</style>""", unsafe_allow_html=True)

# Page objects are created first so the Home tiles can link to them.
P = {
    "permanent": st.Page(permanent.render, title="Permanent / Fixed-Term Forecast", icon="📈", url_path="permanent"),
    "casual": st.Page(casual.render, title="Casual Cost Calculator", icon="👥", url_path="casual"),
    "severance": st.Page(severance.render, title="Severance Calculator", icon="🛡️", url_path="severance"),
    "increases": st.Page(reference.salary_increases, title="Salary Increase Rates", icon="💲", url_path="increases"),
    "classifications": st.Page(reference.classifications, title="Classifications & Steps", icon="📘", url_path="classifications"),
    "oncosts": st.Page(reference.on_costs, title="On-Cost Rates", icon="📉", url_path="oncosts"),
    "settings": st.Page(settings.render, title="Settings", icon="⚙️", url_path="settings"),
    "help": st.Page(help_about.render, title="Help & About", icon="❓", url_path="help"),
}


def home_page():
    home.render(P)


HOME = st.Page(home_page, title="Home", icon="🏠", default=True, url_path="home")

pg = st.navigation([HOME, *P.values()], position="hidden")  # hidden = no sidebar menu
if pg is not HOME:
    st.page_link(HOME, label="← Back to Home")
pg.run()
