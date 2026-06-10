"""Module 01 — Data ingestion, cleaning, feature engineering.

Pipeline:
  1. Load 2 CSVs (semicolon separator).
  2. Rename columns to snake_case.
  3. Parse dates (dd.mm.yyyy).
  4. Impute missing daily metrics (control row 5.08.2019).
  5. Engineer funnel rates: CTR, view_rate, atc_rate, CR, purchase_rate.
  6. Engineer revenue proxy (purchase * assumed AOV) and revenue-per-session.
  7. Merge to long-form (group, date, metrics).
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from .config import (
    CONTROL_FILE, TEST_FILE, COL_MAP, PROCESSED_DIR, ASSUMED_AOV_USD,
)


def _load_one(path, group_label: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns=COL_MAP)
    df["group"] = group_label
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y", errors="coerce")
    return df.sort_values("date").reset_index(drop=True)


def _impute_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill numeric columns then back-fill any residual."""
    num_cols = df.select_dtypes(include=np.number).columns
    df[num_cols] = df[num_cols].ffill().bfill()
    return df


def _engineer_funnel_rates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ctr"] = df["clicks"] / df["impressions"]
    df["view_rate"] = df["view_content"] / df["clicks"]
    df["atc_rate"] = df["add_to_cart"] / df["view_content"]
    df["cr"] = df["purchase"] / df["clicks"]
    df["purchase_rate"] = df["purchase"] / df["add_to_cart"]
    return df



def _engineer_revenue(df: pd.DataFrame, aov: float = ASSUMED_AOV_USD) -> pd.DataFrame:
    df = df.copy()
    df["revenue"] = df["purchase"] * aov
    df["revenue_per_session"] = df["revenue"] / df["clicks"]
    df["cpa"] = df["spend"] / df["purchase"].replace(0, np.nan)
    df["roas"] = df["revenue"] / df["spend"].replace(0, np.nan)
    return df

def build_dataset() -> dict[str, pd.DataFrame]:
    """Public entry. Returns dict with `control`, `test`, `combined` DataFrames."""
    control = _impute_missing(_parse_dates(_load_one(CONTROL_FILE, "Control")))
    test = _impute_missing(_parse_dates(_load_one(TEST_FILE, "Test")))

    control = _engineer_revenue(_engineer_funnel_rates(control))
    test = _engineer_revenue(_engineer_funnel_rates(test))

    combined = pd.concat([control, test], ignore_index=True)

    control.to_csv(PROCESSED_DIR / "control_processed.csv", index=False)
    test.to_csv(PROCESSED_DIR / "test_processed.csv", index=False)
    combined.to_csv(PROCESSED_DIR / "combined_processed.csv", index=False)

    return {"control": control, "test": test, "combined": combined}


def aggregate_totals(combined: pd.DataFrame) -> pd.DataFrame:
    """Sum funnel counts per group for proportion-test inputs."""
    agg = combined.groupby("group", as_index=False).agg(
        impressions=("impressions", "sum"),
        clicks=("clicks", "sum"),
        view_content=("view_content", "sum"),
        add_to_cart=("add_to_cart", "sum"),
        purchase=("purchase", "sum"),
        spend=("spend", "sum"),
        revenue=("revenue", "sum"),
    )
    agg["cr"] = agg["purchase"] / agg["clicks"]
    agg["revenue_per_session"] = agg["revenue"] / agg["clicks"]
    agg["roas"] = agg["revenue"] / agg["spend"]
    agg.to_csv(PROCESSED_DIR / "aggregate_totals.csv", index=False)
    return agg


if __name__ == "__main__":
    data = build_dataset()
    agg = aggregate_totals(data["combined"])
    print("== Aggregated totals ==")
    print(agg.to_string(index=False))
    print(f"\nProcessed files saved to: {PROCESSED_DIR}")
