from datetime import date
import pandas as pd
import streamlit as st
from core import data, calculations as calc, exports
from core.ui import clear_all_button

FMT = "DD/MM/YYYY"


def render():
    st.markdown("### Permanent / Fixed-Term Forecast")
    clear_all_button("perm_")
    sal, inc, oc = data.load_salaries(), data.load_increases(), data.load_on_costs()

    st.subheader("1. Employment Details")
    c1, c2, c3 = st.columns(3)
    start = c1.date_input("Start Date for Costing *", date(2026, 7, 1), format=FMT, key="perm_start")
    end = c2.date_input("End Date for Costing *", date(2027, 6, 30), format=FMT, key="perm_end")
    frac = c3.number_input("Fraction of Appointment (%) *", 0.0, 100.0, 100.0, 5.0, key="perm_frac")
    c4, c5 = st.columns(2)
    cls = c4.selectbox("Classification / Level *", sorted(sal.classification.unique()), key="perm_cls")
    steps = sal[sal.classification == cls].step.tolist()  # steps follow the chosen classification
    step = c5.selectbox("Step *", steps, key=f"perm_step_{cls}")

    st.subheader("2. Increment Options")
    inc_on = st.checkbox("Include Increments? (moves up one step each 1 March, up to the top step)",
                         key="perm_inc")

    st.subheader("3. Allowance")
    non_a = st.number_input("Non-superannuable allowance ($ p.a.)", 0.0, step=100.0, key="perm_non")
    go = st.button("Calculate Forecast", type="primary", key="perm_go")

    if go:
        if end < start:
            st.error("End date cannot be earlier than start date.")
            return
        st.session_state.perm_result = dict(
            df=calc.permanent_forecast(start, end, frac, sal, cls, step, inc, oc, inc_on, non_a),
            summary=pd.DataFrame([dict(Start=start.strftime("%d/%m/%Y"), End=end.strftime("%d/%m/%Y"),
                                       Classification=cls, Step=step, Fraction=frac,
                                       Increments=inc_on, NonSuper_Allowance=non_a)]).astype(str))
    r = st.session_state.get("perm_result")
    if not r:
        return
    df = r["df"]

    st.subheader("Forecast Result")
    st.dataframe(r["summary"], hide_index=True, width="stretch")

# Create total row
    tot = df.drop(columns="Year").sum()
    total_row = { "Year": "Total", **tot.round(2).to_dict(), "PA Rate": pd.NA  # display blank in Total row
             }

    show = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    show["Year"] = show["Year"].astype(str)

    st.dataframe(show, hide_index=True, width="stretch"
    )

    st.warning( "Future salary increases marked FORECAST are planning estimates and may change.")

    sheets = { "Inputs": r["summary"],"Breakdown": show
    }

    b1, b2 = st.columns(2)
    b1.download_button("Export Excel", exports.to_excel(sheets), "Permanent_Forecast.xlsx")
    b2.download_button( "Export PDF", exports.to_pdf( "Permanent / Fixed-Term Forecast", sheets ), "Permanent_Forecast.pdf")