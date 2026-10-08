from datetime import date
import pandas as pd
import streamlit as st
from core import data, calculations as calc, exports
from core.ui import clear_all_button


def render():
    st.markdown("Severance Pay Calculator")
    clear_all_button("sev_")
    sal, inc, oc = data.load_salaries(), data.load_increases(), data.load_on_costs()

    today = date.today()  # salary rate is always as at today's date

    left, right = st.columns(2)
    with left.container(border=True):
        st.subheader("Severance Details")
        cls = st.selectbox("Classification / Level *", sorted(sal.classification.unique()), key="sev_cls")
        step = st.selectbox("Step *", sal[sal.classification == cls].step.tolist(), key=f"sev_step_{cls}")
        frac = st.number_input("Average Service Fraction (%) *", 0.0, 100.0, 100.0, key="sev_frac")
        wks = st.number_input(
            "Number of Weeks of Severance Payable *", 0.0, float(calc.SEVERANCE_MAX_WEEKS), 4.0,
            help="Budget Centre will only be charged first 4 weeks for Severance Pay so calculation limited to 4 weeks costs.",
            key="sev_wks",
        )
        st.caption(f"Salary rate as at today: {today.strftime('%d/%m/%Y')}")
        go = st.button("Calculate Severance Pay", type="primary", key="sev_go")

    with right.container(border=True):
        st.subheader("Severance Pay Estimate")
        if go:
            annual = float(sal[(sal.classification == cls) & (sal.step == step)].annual_salary.iloc[0])
            st.session_state.sev_result = dict(
                calc=calc.severance_cost(annual, frac, wks, oc, today, inc),
                inputs=dict(
                    Classification=cls,
                    Step=step,
                    Fraction=frac,
                    Weeks=min(wks, calc.SEVERANCE_MAX_WEEKS),
                    Salary_As_At=today.strftime("%d/%m/%Y"),
                ),
            )

        saved = st.session_state.get("sev_result")
        if not saved:
            st.info("No estimate calculated yet.")
            return
        r, inp = saved["calc"], saved["inputs"]

        st.caption(
            f"{inp['Classification']} Step {inp['Step']} | {inp['Fraction']}% | "
            f"{inp['Weeks']} weeks | Salary as at {inp['Salary_As_At']}"
        )
        st.metric("Estimated Severance Payment", f"${r['payment']:,.2f}")
        st.metric("Payroll Tax", f"${r['payroll_tax']:,.2f}")
        st.metric("Total Estimated Budget Centre Cost", f"${r['total']:,.2f}")

        sheets = {"Severance": pd.DataFrame([{**inp, **r}])}
        st.download_button("Export Excel", exports.to_excel(sheets), "Severance_Estimate.xlsx")
        st.download_button("Export PDF", exports.to_pdf("Severance Estimate", sheets), "Severance_Estimate.pdf")