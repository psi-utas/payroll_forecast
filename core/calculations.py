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
    base = R2(sum(R2(r["rate"] * r["hours"] * r["weeks"]) for r in roles))
    sup = R2(base * oc["CASUAL_SUPER"])
    ptax = R2((base + sup) * oc["PAYROLL_TAX"])
    wc = R2(base * oc["WORKERS_COMP"])
    total_oncosts = R2(sup + ptax + wc)

    return dict(
        base=base,
        super=sup,
        payroll_tax=ptax,
        workers_comp=wc,
        total_oncosts=total_oncosts,
        total=R2(base + total_oncosts),
    )


SEVERANCE_MAX_WEEKS = 4


def severance_cost(
    annual_salary: float,
    fraction_pct: float,
    weeks: float,
    oc: dict,
    as_at: date,
    increases: pd.DataFrame,
    salary_factor: float = 1.0,
) -> dict:
    weeks = min(weeks, SEVERANCE_MAX_WEEKS)
    annual = annual_salary * uplift_factor(as_at, increases) * salary_factor
    payment = annual / 52 * (fraction_pct / 100) * weeks
    tax = payment * oc["PAYROLL_TAX"]

    return dict(
        annual_salary=R2(annual),
        payment=R2(payment),
        payroll_tax=R2(tax),
        total=R2(payment + tax),
    )


def permanent_forecast(start: date, end: date, fraction_pct: float, salaries: pd.DataFrame,
                       classification: str, step: int, increases: pd.DataFrame, oc: dict,
                       include_first_year_increment: bool = True,
                       non_super_allowance: float = 0.0,
                       superable_allowance: float = 0.0) -> pd.DataFrame:
    """Fortnight-based costing, one row per period of constant step."""

    if end < start:
        raise ValueError("End date cannot be earlier than start date")

    tbl = salaries[salaries.classification == classification].set_index("step")["annual_salary"]
    max_step = int(tbl.index.max())
    fn = 1 / DAYS_PER_FORTNIGHT

    segs = []
    seg, n_inc, d = None, 0, start
    first_increment_processed = False

    while d <= end:

        if d > start and d.month == 3 and d.day == 1:
            if first_increment_processed or include_first_year_increment:
                n_inc += 1
            first_increment_processed = True

        cur_step = min(step + n_inc, max_step)
        cur_uplift = uplift_factor(d, increases)

        if seg is None or cur_step != seg["step"] or cur_uplift != seg["uplift"]:
            seg = dict(
                first=d,
                step=cur_step,
                uplift=cur_uplift,
                fortnights=0.0,
                salary=0.0,
                allowance=0.0,
                superable_allowance=0.0
            )
            segs.append(seg)

        fortnight_pay = tbl[cur_step] * cur_uplift * fraction_pct / 100 / FORTNIGHTS_PER_YEAR

        seg["fortnights"] += fn
        seg["salary"] += fortnight_pay * fn
        seg["allowance"] += non_super_allowance / FORTNIGHTS_PER_YEAR * fn
        seg["superable_allowance"] += superable_allowance / FORTNIGHTS_PER_YEAR * fn

        d += timedelta(days=1)

    out = []

    for g in segs:

        salary = g["salary"]
        non_super = g["allowance"]
        superable = g["superable_allowance"]

        superannuation = oc["SUPER"] * (salary + superable)

        payroll_tax = oc["PAYROLL_TAX"] * (
            salary + non_super + superable + superannuation
        )

        workers_comp = oc["WORKERS_COMP"] * (
            salary + non_super + superable
        )

        leave_levy = oc["LEAVE_LEVY"] * salary

        out.append({
            "Eff Dt": g["first"].strftime("%d/%m/%Y"),
            "Step": g["step"],
            "Fortnights": g["fortnights"],
            "PA Rate": salary / g["fortnights"] * FORTNIGHTS_PER_YEAR,
            "Salary": salary,
            "Allowance": non_super,
            "Superable Allowance": superable,
            "Superannuation": superannuation,
            "Payroll Tax": payroll_tax,
            "Workers Comp": workers_comp,
            "Central Leave Levy": leave_levy
        })

    df = pd.DataFrame(out)

    cost_cols = [
        c for c in df.columns
        if c not in ("Eff Dt", "Step", "Fortnights", "PA Rate")
    ]

    df["Total Cost"] = df[cost_cols].sum(axis=1)

    return df.round(2)
