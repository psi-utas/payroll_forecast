"""Loads reference data. Salary/casual rates come from data/db.xlsx (2025 column,
effective 1 July 2025); increases and on-costs come from the CSVs in data/."""
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"
BASE_YEAR = 2025  # the year of the dollar column in db.xlsx


def load_casual() -> pd.DataFrame:
    df = pd.read_excel(DATA / "db.xlsx", sheet_name="casual", header=1)
    df.columns = ["paycode", "description", "rate"]
    df = df.dropna(subset=["paycode", "rate"])
    df["description"] = df["description"].astype(str).str.strip()
    return df.reset_index(drop=True)  # paycodes repeat (e.g. CPNOR): key on description


def load_salaries() -> pd.DataFrame:
    df = pd.read_excel(DATA / "db.xlsx", sheet_name="fixedterm_Ongoing", header=1)
    df.columns = ["description", "annual_salary"]
    df = df.dropna()
    parts = df["description"].str.extract(r"^(.*?)\s+Step\s+(\d+)$")
    df["classification"] = parts[0]
    df["step"] = parts[1].astype(int)
    return df.sort_values(["classification", "step"]).reset_index(drop=True)


def classifications_table() -> pd.DataFrame:
    s = load_salaries()
    g = s.groupby("classification")["step"].agg(["min", "max", lambda x: ", ".join(map(str, sorted(x)))])
    g.columns = ["first_step", "max_step", "steps"]
    return g.reset_index()


def load_increases() -> pd.DataFrame:
    return pd.read_csv(DATA / "salary_increases.csv", parse_dates=["effective_from"])


def load_on_costs() -> dict:
    df = pd.read_csv(DATA / "on_costs.csv")
    return {r.cost_code: r.rate_pct / 100 for r in df.itertuples()}


def load_on_costs_table() -> pd.DataFrame:
    return pd.read_csv(DATA / "on_costs.csv")
