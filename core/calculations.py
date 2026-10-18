"""Pure calculation functions (no Streamlit) so they can be unit tested."""
from datetime import date, timedelta
import pandas as pd 
from . import data


FORTNIGHTS_PER_YEAR = 26.0893  # 365.25 / 14
DAYS_PER_FORTNIGHT = 14
R2 = lambda x: round(x + 0.0, 2)

def rate_date_options(years_ahead: int = 4) -> list[date]:
    """July 1 of the current year through July 1 of current year + 4."""
    start = date.today().year
    return [date(y, 7, 1) for y in range(start, start + years_ahead + 1)]


def uplift_factor(on: date, increases: pd.DataFrame, base_year: int = data.BASE_YEAR) -> float:
    """Compound every mid-year increase after the base year that is effective on/before `on`."""
    f = 1.0
    for r in increases.itertuples():
        if r.year > base_year and r.effective_from.date() <= on:
            f *= 1 + r.mid_year_increase_pct / 100
    return f


def casual_cost(roles: list[dict], oc: dict) -> dict:
    """roles: [{'rate','hours','weeks'}]. Super & WC on base; payroll tax on base+super.
    Every step is rounded to 2 dp so the displayed figures add up exactly."""
    base = R2(sum(R2(r["rate"] * r["hours"] * r["weeks"]) for r in roles))  # each role to 2 dp
    sup = R2(base * oc["CASUAL_SUPER"])
    ptax = R2((base + sup) * oc["PAYROLL_TAX"])
    wc = R2(base * oc["WORKERS_COMP"])
    total_oncosts = R2(sup + ptax + wc)
    return dict(base=base, super=sup, payroll_tax=ptax, workers_comp=wc,
                total_oncosts=total_oncosts, total=R2(base + total_oncosts))


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
                       include_increments: bool = False,
                       non_super_allowance: float = 0.0) -> pd.DataFrame:
    """Fortnight-based costing, one row per period of constant step.

    Pay per fortnight = annual amount / 26.0893. Fortnights in a period = days (start and end
    both included) / 14, so part fortnights count fractionally.

    ROWS:
      * increments ticked: a new row starts on every 1 March where the step actually moves up
        (no new row once the top step is reached)
      * increments not ticked: a new row starts each 1 January
    ASSUMPTIONS (confirm with the tool owners):
      * salary = 2025 table value x compounded mid-year increases effective on the day
        (so a 1 July increase inside a row is blended into that row's PA Rate)
      * the allowance is a non-superannuable annual amount, paid per fortnight (not scaled by FTE)
      * super 17% on salary only; leave levy on salary;
        workers comp on salary + allowance; payroll tax on salary + super + allowance
    """
    if end < start:
        raise ValueError("End date cannot be earlier than start date")
    tbl = salaries[salaries.classification == classification].set_index("step")["annual_salary"]
    max_step = int(tbl.index.max())
    fn = 1 / DAYS_PER_FORTNIGHT  # one day = 1/14 of a fortnight

    segs: list[dict] = []
    seg, n_inc, d = None, 0, start
    while d <= end:
        if include_increments and d > start and d.month == 3 and d.day == 1:
            n_inc += 1  # annual increment on 1 March
        cur_step = min(step + n_inc, max_step)  # top step: no further move
        new_year = (not include_increments) and d.month == 1 and d.day == 1
        if seg is None or cur_step != seg["step"] or new_year:
            seg = dict(first=d, last=d, step=cur_step, fortnights=0.0, salary=0.0, allowance=0.0)
            segs.append(seg)
        fortnight_pay = tbl[cur_step] * uplift_factor(d, increases) * fraction_pct / 100 / FORTNIGHTS_PER_YEAR
        seg["last"] = d
        seg["fortnights"] += fn
        seg["salary"] += fortnight_pay * fn
        seg["allowance"] += non_super_allowance / FORTNIGHTS_PER_YEAR * fn
        d += timedelta(days=1)

    out = []
    for g in segs:
        s, na = g["salary"], g["allowance"]
        sup = oc["SUPER"] * s
        out.append({"Eff Dt": g["first"].strftime("%d/%m/%Y"),
                    "Step": g["step"], "Fortnights": g["fortnights"],
                    "PA Rate": s / g["fortnights"] * FORTNIGHTS_PER_YEAR,  # salary annualised
                    "Salary": s, "Allowance": na, "Superannuation": sup,
                    "Payroll Tax": oc["PAYROLL_TAX"] * (s + sup + na),
                    "Workers Compensation": oc["WORKERS_COMP"] * (s + na),
                    "Central Leave Levy": oc["LEAVE_LEVY"] * s})
    df = pd.DataFrame(out)
    cost_cols = [c for c in df.columns if c not in ("Eff Dt", "Step", "Fortnights", "PA Rate")]
    df["Total Cost"] = df[cost_cols].sum(axis=1)
    return df.round(2)
