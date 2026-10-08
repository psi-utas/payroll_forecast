from datetime import date

import pandas as pd
import streamlit as st
from core import data, calculations as calc, exports
from core.ui import clear_all_button


def rate_date_options(years_ahead: int = 3) -> list[date]:
    """July 1 of the current year through July 1 of the current year + years_ahead."""
    start = date.today().year
    return [date(y, 7, 1) for y in range(start, start + years_ahead + 1)]


def render():
    st.subheader("Casual Cost Calculator")
    clear_all_button("casual_")

    cas = data.load_casual()
    oc = data.load_on_costs()
    si = data.load_increases()

    # Only approved salary increases feed the rate schedule
    si = si[si["status"] == "APPROVED"].sort_values("year")

    # ---- Salary rate schedule (MM/YYYY) ----
    selected_date = st.selectbox(
        "Salary Rate Schedule (MM/YYYY)",
        rate_date_options(),
        format_func=lambda d: d.strftime("%m/%Y"),
        key="casual_rate_date",
    )
    selected_label = selected_date.strftime("%m/%Y")

    # Same compounding logic as the rest of the tool (see calculations.uplift_factor)
    rate_multiplier = calc.uplift_factor(selected_date, si)
    increase_pct = (rate_multiplier - 1) * 100

    ss = st.session_state
    ss.setdefault("casual_ids", [0])
    ss.setdefault("casual_next", 1)

    left = st.container()

    roles = []
    with left:
        for n, rid in enumerate(list(ss.casual_ids), 1):
            with st.container(border=True):
                h1, h2 = st.columns([5, 1])
                h1.markdown(f"**Role {n}**")
                if h2.button("Remove", key=f"casual_rm{rid}") and len(ss.casual_ids) > 1:
                    ss.casual_ids.remove(rid)
                    st.rerun()

                act = st.selectbox(
                    "Casual Activity *",
                    [None] + cas.index.tolist(),
                    key=f"casual_act{rid}",
                    format_func=lambda i: "Select a casual activity" if i is None else cas.description[i],
                )

                c1, c2, c3, c4 = st.columns(4)
                row = cas.loc[act] if act is not None else None
                adjusted_rate = round(float(row.rate) * rate_multiplier, 2) if row is not None else 0.0

                c1.text_input(
                    "Paycode",
                    row.paycode if row is not None else "",
                    disabled=True,
                    key=f"casual_pc{rid}_{act}",
                )
                c2.text_input(
                    f"Hourly Rate ($) - {selected_label}",
                    f"{adjusted_rate:.2f}" if row is not None else "",
                    disabled=True,
                    key=f"casual_rt{rid}_{act}_{selected_label}",
                )
                hrs = c3.number_input("Average Weekly Hours *", 0.0, 168.0, 1.0, step=1.0, key=f"casual_h{rid}")
                wks = c4.number_input("Number of Weeks *", 0.0, 520.0, 1.0, step=1.0, key=f"casual_w{rid}")

                if row is not None:
                    roles.append(
                        dict(
                            activity=row.description,
                            paycode=row.paycode,
                            rate=adjusted_rate,
                            hours=hrs,
                            weeks=wks,
                        )
                    )

        if st.button("+ Add role", key="casual_add"):
            ss.casual_ids.append(ss.casual_next)
            ss.casual_next += 1
            st.rerun()

        go = st.button("Calculate Cost", type="primary", key="casual_go")

    if go:
        if not roles or len(roles) != len(ss.casual_ids):
            st.error("Select a Casual Activity before calculating.")
            return
        bc = ss.get("budget_centre", "")
        ss.casual_result = (
            calc.casual_cost(roles, oc),
            roles,
            bc,
            selected_label,
            increase_pct,
        )

    if "casual_result" not in ss:
        return

    res, rs, bc, result_label, result_pct = ss.casual_result

    st.markdown("Estimated Casual Cost Summary")

    oc_df = pd.DataFrame(
        {
            "Component": ["Base", "Superannuation", "Payroll Tax", "Workers Compensation", "Total Estimated Cost"],
            "Amount": [res["base"], res["super"], res["payroll_tax"], res["workers_comp"], res["total"]],
        }
    )
    st.dataframe(oc_df, hide_index=True, width="stretch", column_config={
        "Amount": st.column_config.NumberColumn("Amount ($)", format="%.2f"),
    },
)

    role_df = pd.DataFrame(rs)
    summary_df = pd.DataFrame([{**res, "salary_schedule": result_label}])
    sheets = {"Roles": role_df, "On-costs": oc_df, "Summary": summary_df}

    b1, b2, b3 = st.columns([1, 1, 4])
    b1.download_button("Export Excel", exports.to_excel(sheets), "Casual_Cost_Forecast.xlsx")
    b2.download_button("Export PDF", exports.to_pdf("Casual Cost Forecast", sheets), "Casual_Cost_Forecast.pdf")