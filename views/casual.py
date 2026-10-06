import pandas as pd
import streamlit as st
from core import data, calculations as calc, exports
from core.ui import clear_all_button


def render():
    st.title("Casual Cost Calculator")
    clear_all_button("casual_")
    cas, oc = data.load_casual(), data.load_on_costs()
    ss = st.session_state
    ss.setdefault("casual_ids", [0])
    ss.setdefault("casual_next", 1)

    left, right = st.columns([3, 1])
    with right.container(border=True):
        st.markdown("**On-Cost Rates** (applied automatically)")
        st.write(f"Superannuation: **{oc['CASUAL_SUPER']*100:.3f}%**")
        st.write(f"Payroll Tax: **{oc['PAYROLL_TAX']*100:.3f}%**")
        st.write(f"Workers Compensation: **{oc['WORKERS_COMP']*100:.3f}%**")

    roles = []
    with left:
        for n, rid in enumerate(list(ss.casual_ids), 1):
            with st.container(border=True):
                h1, h2 = st.columns([5, 1])
                h1.markdown(f"**Role {n}**")
                if h2.button("Remove", key=f"casual_rm{rid}") and len(ss.casual_ids) > 1:
                    ss.casual_ids.remove(rid)
                    st.rerun()
                act = st.selectbox("Casual Activity *", [None] + cas.index.tolist(), key=f"casual_act{rid}",
                                   format_func=lambda i: "Select a casual activity" if i is None else cas.description[i])
                c1, c2, c3, c4 = st.columns(4)
                row = cas.loc[act] if act is not None else None
                c1.text_input("Paycode", row.paycode if row is not None else "", disabled=True, key=f"casual_pc{rid}_{act}")
                c2.text_input("Hourly Rate ($) — from database", f"{row.rate:.2f}" if row is not None else "",
                              disabled=True, key=f"casual_rt{rid}_{act}")
                hrs = c3.number_input("Average Weekly Hours *", 0.0, 168.0, 20.0, key=f"casual_h{rid}")
                wks = c4.number_input("Number of Weeks *", 0.0, 520.0, 20.0, key=f"casual_w{rid}")
                if row is not None:
                    roles.append(dict(activity=row.description, paycode=row.paycode, rate=float(row.rate),
                                      hours=hrs, weeks=wks))
        if st.button("+ Add role", key="casual_add"):
            ss.casual_ids.append(ss.casual_next)
            ss.casual_next += 1
            st.rerun()
        bc = st.text_input("Budget Centre (Optional)", key="casual_bc")
        go = st.button("Calculate Cost", type="primary", key="casual_go")

    if go:
        if not roles or len(roles) != len(ss.casual_ids):
            st.error("Select a Casual Activity for every role before calculating.")
            return
        ss.casual_result = (calc.casual_cost(roles, oc), roles, bc)
    if "casual_result" not in ss:
        return
    res, rs, bc = ss.casual_result
    st.subheader("Estimated Casual Cost Summary")
    st.caption(f"Budget Centre: {bc or 'Not provided'}")
    cols = st.columns(5)
    for col, (k, lab) in zip(cols, [("base", "Base Casual Cost"), ("super", "Superannuation"),
                                    ("payroll_tax", "Payroll Tax"), ("workers_comp", "Workers Compensation"),
                                    ("total", "Total Estimated Cost")]):
        col.metric(lab, f"${res[k]:,.2f}")
    oc_df = pd.DataFrame({"Component": ["Superannuation", "Payroll Tax", "Workers Compensation", "Total On-Costs"],
                          "Amount": [res["super"], res["payroll_tax"], res["workers_comp"], res["total_oncosts"]],
                          "Status": ["Applied"] * 3 + [""]})
    st.dataframe(oc_df, hide_index=True, width="stretch")
    role_df = pd.DataFrame(rs)
    sheets = {"Roles": role_df, "On-costs": oc_df, "Summary": pd.DataFrame([res])}
    b1, b2, b3 = st.columns([1, 1, 4])
    b1.download_button("Export Excel", exports.to_excel(sheets), "Casual_Cost_Forecast.xlsx")
    b2.download_button("Export PDF", exports.to_pdf("Casual Cost Forecast", sheets), "Casual_Cost_Forecast.pdf")
