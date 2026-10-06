"""Pure calculation functions (no Streamlit) so they can be unit tested."""
from datetime import date, timedelta
import calendar
import pandas as pd
from . import data

R2 = lambda x: round(x + 0.0, 2)


def uplift_factor(on: date, increases: pd.DataFrame, base_year: int = data.BASE_YEAR) -> float:
    """Compound every mid-year increase after the base year that is effective on/before `on`."""
    f = 1.0
    for r in increases.itertuples():
        if r.year > base_year and r.effective_from.date() <= on:
            f *= 1 + r.mid_year_increase_pct / 100
    return f


def casual_cost(roles: list[dict], oc: dict) -> dict:
    """roles: [{'rate','hours','weeks'}]. Super & WC on base; payroll tax on base+super."""
    base = sum(r["rate"] * r["hours"] * r["weeks"] for r in roles)
    sup = base * oc["CASUAL_SUPER"]
    ptax = (base + sup) * oc["PAYROLL_TAX"]
    wc = base * oc["WORKERS_COMP"]
    return dict(base=R2(base), super=R2(sup), payroll_tax=R2(ptax), workers_comp=R2(wc),
                total_oncosts=R2(sup + ptax + wc), total=R2(base + sup + ptax + wc))


SEVERANCE_MAX_WEEKS = 4


def severance_cost(annual_salary: float, fraction_pct: float, weeks: float, oc: dict,
                   as_at: date, increases: pd.DataFrame, salary_factor: float = 1.0) -> dict:
    weeks = min(weeks, SEVERANCE_MAX_WEEKS)
    annual = annual_salary * uplift_factor(as_at, increases) * salary_factor
    payment = annual / 52 * (fraction_pct / 100) * weeks
    tax = payment * oc["PAYROLL_TAX"]
    return dict(annual_salary=R2(annual), payment=R2(payment), payroll_tax=R2(tax), total=R2(payment + tax))


def permanent_forecast(start: date, end: date, fraction_pct: float, salaries: pd.DataFrame,
                       classification: str, step: int, increases: pd.DataFrame, oc: dict,
                       include_increments: bool = False, first_increment: date | None = None,
                       super_allowance: float = 0.0, non_super_allowance: float = 0.0) -> pd.DataFrame:
    """Day-by-day costing, aggregated by calendar year.

    ASSUMPTIONS 
      * salary = 2025 table value x compounded mid-year increases effective on the day
      * increments: +1 step every 12 months from `first_increment`, capped at max step
      * allowances are annual amounts, pro-rated by day (not scaled by FTE)
      * super 17% on salary + superannuable allowance; leave levy on salary;
        workers comp on salary + allowances; payroll tax on salary + super + allowances
    """
    if end < start:
        raise ValueError("End date cannot be earlier than start date")
    tbl = salaries[salaries.classification == classification].set_index("step")["annual_salary"]
    max_step = int(tbl.index.max())
    rows: dict[int, dict] = {}
    d, n_inc = start, 0
    nxt = first_increment or date(start.year + 1, start.month, min(start.day, 28))
    while d <= end:
        if include_increments and d >= nxt:
            n_inc += 1
            nxt = date(nxt.year + 1, nxt.month, nxt.day)
        cur_step = min(step + n_inc, max_step)
        yr_days = 366 if calendar.isleap(d.year) else 365
        sal = tbl[cur_step] * uplift_factor(d, increases) * fraction_pct / 100 / yr_days
        r = rows.setdefault(d.year, dict(salary=0.0, super_allowance=0.0, non_super_allowance=0.0))
        r["salary"] += sal
        r["super_allowance"] += super_allowance / yr_days
        r["non_super_allowance"] += non_super_allowance / yr_days
        d += timedelta(days=1)
    out = []
    for y, r in sorted(rows.items()):
        s, sa, na = r["salary"], r["super_allowance"], r["non_super_allowance"]
        sup = oc["SUPER"] * (s + sa)
        out.append({"Year": y, "Salary": s, "Superannuable Allowance": sa,
                    "Non-Superannuable Allowance": na, "Superannuation": sup,
                    "Payroll Tax": oc["PAYROLL_TAX"] * (s + sup + sa + na),
                    "Workers Compensation": oc["WORKERS_COMP"] * (s + sa + na),
                    "Central Leave Levy": oc["LEAVE_LEVY"] * s})
    df = pd.DataFrame(out).round(2)
    df["Total Cost"] = df.drop(columns="Year").sum(axis=1).round(2)
    return df
