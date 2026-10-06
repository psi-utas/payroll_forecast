import streamlit as st


def render(P):
    """P = dict of page objects built in app.py."""
    st.title("Payroll Forecasting Home")
    st.write("Select a calculator to prepare an employment cost estimate.")
    tiles = [("permanent", "📈", "Permanent / Fixed-Term Forecast", "Salary and employment costs over a forecast period."),
             ("casual", "👥", "Casual Cost Calculator", "Casual activity rates, hours and on-costs."),
             ("severance", "🛡️", "Severance Calculator", "Severance payment and Budget Centre cost.")]
    for col, (key, icon, title, desc) in zip(st.columns(3), tiles):
        with col.container(border=True):
            st.subheader(f"{icon} {title}")
            st.write(desc)
            st.page_link(P[key], label="Open Calculator →", width="stretch")
    st.info("Rates marked FORECAST are planning assumptions and may change.")
