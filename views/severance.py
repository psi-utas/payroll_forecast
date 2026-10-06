from datetime import date
import pandas as pd
import streamlit as st
from core import data, calculations as calc, exports
from core.ui import clear_all_button


def render():
    st.title("Severance Pay Calculator")
    clear_all_button("sev_")
    sal, inc, oc = data.load_salaries(), data.load_increases(), data.load_on_costs()
    left, right = st.columns(2)
    with left.container(border=True):
        st.subheader("Severance Details")
        cls = st.selectbox("Classification / Level *", sorted(sal.classification.unique()), key="sev_cls")
        step = st.selectbox("Step *", sal[sal.classification == cls].step.tolist(), key=f"sev_step_{cls}")
        frac = st.number_input("Average Service Fraction (%) *", 0.0, 100.0, 100.0, key="sev_frac")
        wks = st.number_input("Number of Weeks of Severance Payable *", 0.0, float(calc.SEVERANCE_MAX_WEEKS),
                              4.0, help="A maximum of 4 weeks can be calculated.", key="sev_wks")
        as_at = st.date_input("Salary as at", date.today(), key="sev_asat")
        go = st.button("Calculate Severance Pay", type="primary", key="sev_go")
    with right.container(border=True):
        st.subheader("Severance Pay Estimate")
        if go:
            annual = float(sal[(sal.classification == cls) & (sal.step == step)].annual_salary.iloc[0])
            st.session_state.sev_result = calc.severance_cost(annual, frac, wks, oc, as_at, inc)
        r = st.session_state.get("sev_result")
        if not r:
            st.info("No estimate calculated yet.")
            return
        st.metric("Estimated Severance Payment", f"${r['payment']:,.2f}")
        st.metric("Payroll Tax", f"${r['payroll_tax']:,.2f}")
        st.metric("Total Estimated Budget Centre Cost", f"${r['total']:,.2f}")
        sheets = {"Severance": pd.DataFrame([dict(Classification=cls, Step=step, Fraction=frac, Weeks=wks, **r)])}
        st.download_button("Export Excel", exports.to_excel(sheets), "Severance_Estimate.xlsx")
        st.download_button("Export PDF", exports.to_pdf("Severance Estimate", sheets), "Severance_Estimate.pdf")
