from datetime import date
import pandas as pd
import streamlit as st

from core import data, calculations as calc, exports
from core.ui import clear_all_button

FMT = "DD/MM/YYYY"
MIN_DATE = date(2026, 7, 1)
MAX_DATE = date(2034, 6, 30)

def render():

  st.markdown("### Permanent / Fixed-Term Forecast")

  clear_all_button("perm_")

  sal = data.load_salaries()
  inc = data.load_increases()
  oc = data.load_on_costs()

  # Employment Details

  st.subheader("1. Employment Details")

  c1, c2, c3 = st.columns(3)

  start = c1.date_input(
    "Start Date for Costing *",
    MIN_DATE,
    format=FMT,
    min_value=MIN_DATE,
    max_value=MAX_DATE,
    key="perm_start",
  )

  end = c2.date_input(
    "End Date for Costing *",
    date(2027, 6, 30),
    format=FMT,
    min_value=MIN_DATE,
    max_value=MAX_DATE,
    key="perm_end",
  )

  frac = c3.number_input(
    "Fraction of Appointment (%) *",
    min_value=0.0,
    max_value=100.0,
    value=100.0,
    step=5.0,
    key="perm_frac",
  )

  c4, c5 = st.columns(2)

  cls = c4.selectbox(
    "Classification / Level *",
    sorted(sal.classification.unique()),
    key="perm_cls",
  )

  steps = sal[sal.classification == cls].step.tolist()

  step = c5.selectbox(
    "Step *",
    steps,
    key=f"perm_step_{cls}",
  )

  # ------------------------------------------------------------------
  # Increment Options
  # ------------------------------------------------------------------

  st.subheader("2. Increment Options")

  inc_first_year = st.checkbox(
    "Include increment in first year?",
    value=True,
    key="perm_inc_first_year",
  )

  st.caption(
    "All subsequent annual increments will be applied automatically up to the top step."
  )

  # Allowances

  st.subheader("3. Allowances")

  c6, c7 = st.columns(2)

  non_a = c6.number_input(
    "Non-superannuable allowance ($ p.a.)",
    min_value=0.0,
    value=0.0,
    step=100.0,
    key="perm_non",
  )

  super_a = c7.number_input(
    "Superable allowance ($ p.a.)",
    min_value=0.0,
    value=0.0,
    step=100.0,
    key="perm_super",
  )

  # Calculate

  go = st.button(
    "Calculate Forecast",
    type="primary",
    key="perm_go",
  )

  if go:

    if end < start:
      st.error("End date cannot be earlier than start date.")
      return

    st.session_state.perm_result = dict(
      df=calc.permanent_forecast(
        start=start,
        end=end,
        fraction_pct=frac,
        salaries=sal,
        classification=cls,
        step=step,
        increases=inc,
        oc=oc,
        include_first_year_increment=inc_first_year,
        non_super_allowance=non_a,
        superable_allowance=super_a,
      ),
      summary=pd.DataFrame(
        [
          {
            "Start": start.strftime("%d/%m/%Y"),
            "End": end.strftime("%d/%m/%Y"),
            "Classification": cls,
            "Step": step,
            "Fraction (%)": frac,
            "First Year Increment": inc_first_year,
            "Non-Super Allowance": non_a,
            "Superable Allowance": super_a,
          }
        ]
      ).astype(str),
    )

  # Results

  r = st.session_state.get("perm_result")

  if not r:
    return

  df = r["df"]

  st.subheader("Forecast Result")
  st.info(
    "Forecast assumption: Salary increases from 1 July 2030 onwards are modelled at 3.0% p.a. for budgeting and planning purposes."
  )

  st.dataframe(
    r["summary"],
    hide_index=True,
    width="stretch",
  )

  tot = df.drop(columns=["Eff Dt", "Step"]).sum()

  total_row = {
    "Eff Dt": "Total",
    "Step": pd.NA,
    **tot.round(2).to_dict(),
    "PA Rate": float("nan"),
  }

  show = pd.concat(
    [df, pd.DataFrame([total_row])],
    ignore_index=True,
  )

  show["Step"] = show["Step"].astype("Int64")

  money = {
    c: "{:,.2f}"
    for c in show.select_dtypes("number").columns
    if c != "Step"
  }

  money["PA Rate"] = "${:,.0f}"

  st.dataframe(
    show.style.format(money, na_rep=""),
    hide_index=True,
    width="stretch",
  )

   # Annual Summary

  annual = df.copy()

  annual["Year"] = pd.to_datetime(
    annual["Eff Dt"],
    format="%d/%m/%Y"
  ).dt.year

  yearly = (
    annual.drop(columns=["Step", "Fortnights", "PA Rate"])
    .groupby("Year")
    .sum(numeric_only=True)
    .reset_index()
  )

  year_tot = yearly.drop(columns=["Year"]).sum()

  yearly_total = pd.DataFrame([{
    "Year": "Total",
    **year_tot.round(2).to_dict()
  }])

  yearly_show = pd.concat(
    [yearly, yearly_total],
    ignore_index=True
  )

  st.subheader("Annual Summary")

  yearly_money = {
    c: "{:,.2f}"
    for c in yearly_show.columns
    if c != "Year"
  }

  st.dataframe(
    yearly_show.style.format(yearly_money, na_rep=""),
    hide_index=True,
    width="stretch",
  )

  sheets = {
    "Inputs": r["summary"],
    "Forecast Detail": show,
    "Annual Summary": yearly_show,
  }

  c1, c2 = st.columns(2)

  c1.download_button(
    "Export Excel",
    exports.to_excel(sheets),
    "Permanent_Forecast.xlsx",
  )

  c2.download_button(
    "Export PDF",
    exports.to_pdf(
      "Permanent / Fixed-Term Forecast",
      sheets,
    ),
    "Permanent_Forecast.pdf",
  )
