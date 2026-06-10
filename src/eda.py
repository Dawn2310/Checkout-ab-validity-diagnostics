"""Module 02 — Exploratory Data Analysis.

Outputs (saved under output/):
  tables/eda_summary_stats.csv          : describe() per group
  tables/eda_funnel_summary.csv         : totals + funnel-step rates per group
  tables/eda_missing_report.csv         : null counts per column per group
  tables/eda_weekday_breakdown.csv      : CR by weekday × group
  figures/eda_timeseries_<metric>.png   : daily metric over time
  figures/eda_distribution_<metric>.png : histogram + kde per group
  figures/eda_correlation_heatmap.png   : Pearson correlation across metrics
  figures/eda_funnel_combined.png       : funnel counts (log scale) per group
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from .config import FIG_DIR, TABLE_DIR, FUNNEL_STEPS

sns.set_theme(style="whitegrid", context="notebook")
PALETTE = {"Control": "#4C72B0", "Test": "#DD8452"}


def _save_fig(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=130)
    plt.close()


def summary_statistics(combined: pd.DataFrame) -> pd.DataFrame:
    metrics = ["spend", "impressions", "clicks", "view_content",
               "add_to_cart", "purchase", "ctr", "view_rate",
               "atc_rate", "cr", "revenue_per_session"]
    summary = combined.groupby("group")[metrics].describe().T
    summary.to_csv(TABLE_DIR / "eda_summary_stats.csv")
    return summary


def funnel_summary(combined: pd.DataFrame) -> pd.DataFrame:
    g = combined.groupby("group")[FUNNEL_STEPS].sum()
    rates = pd.DataFrame(index=g.index)
    rates["ctr"] = g["clicks"] / g["impressions"]
    rates["view_rate"] = g["view_content"] / g["clicks"]
    rates["atc_rate"] = g["add_to_cart"] / g["view_content"]
    rates["purchase_rate"] = g["purchase"] / g["add_to_cart"]
    rates["cr"] = g["purchase"] / g["clicks"]
    out = g.join(rates)
    out.to_csv(TABLE_DIR / "eda_funnel_summary.csv")
    return out


def missing_report(combined: pd.DataFrame) -> pd.DataFrame:
    rep = (combined.groupby("group")[combined.columns.drop("group")]
                    .apply(lambda d: d.isna().sum()))
    rep.to_csv(TABLE_DIR / "eda_missing_report.csv")
    return rep


def weekday_breakdown(combined: pd.DataFrame) -> pd.DataFrame:
    df = combined.copy()
    df["weekday"] = df["date"].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
    table = (df.groupby(["weekday", "group"])
               .agg(cr=("cr", "mean"),
                    rps=("revenue_per_session", "mean"),
                    n=("date", "count"))
               .reset_index())
    table["weekday"] = pd.Categorical(table["weekday"], order, ordered=True)
    table = table.sort_values(["weekday", "group"])
    table.to_csv(TABLE_DIR / "eda_weekday_breakdown.csv", index=False)
    return table


def plot_timeseries(combined: pd.DataFrame, metric: str = "cr") -> None:
    plt.figure(figsize=(11, 5))
    for grp, sub in combined.groupby("group"):
        plt.plot(sub["date"], sub[metric], marker="o",
                 label=grp, color=PALETTE[grp], linewidth=2)
    plt.title(f"Daily {metric.upper()} over experiment window")
    plt.xlabel("Date")
    plt.ylabel(metric)
    plt.xticks(rotation=30)
    plt.legend()
    _save_fig(f"eda_timeseries_{metric}.png")


def plot_distribution(combined: pd.DataFrame, metric: str) -> None:
    plt.figure(figsize=(9, 5))
    for grp, sub in combined.groupby("group"):
        sns.histplot(sub[metric], kde=True, label=grp,
                     color=PALETTE[grp], alpha=0.45, bins=15)
    plt.title(f"Distribution of daily {metric}")
    plt.xlabel(metric)
    plt.legend()
    _save_fig(f"eda_distribution_{metric}.png")


def plot_correlation(combined: pd.DataFrame) -> None:
    cols = ["spend", "impressions", "clicks", "view_content",
            "add_to_cart", "purchase", "ctr", "view_rate",
            "atc_rate", "cr"]
    corr = combined[cols].corr()
    plt.figure(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm",
                center=0, vmin=-1, vmax=1, square=True)
    plt.title("Pearson correlation across funnel metrics")
    _save_fig("eda_correlation_heatmap.png")


def plot_funnel_combined(combined: pd.DataFrame) -> None:
    funnel = combined.groupby("group")[FUNNEL_STEPS].sum()
    x = np.arange(len(FUNNEL_STEPS))
    w = 0.38
    plt.figure(figsize=(10, 5))
    plt.bar(x - w / 2, funnel.loc["Control"], w,
            label="Control", color=PALETTE["Control"])
    plt.bar(x + w / 2, funnel.loc["Test"], w,
            label="Test", color=PALETTE["Test"])
    plt.yscale("log")
    plt.xticks(x, [s.replace("_", " ").title() for s in FUNNEL_STEPS])
    plt.ylabel("Count (log)")
    plt.title("Conversion funnel — Control vs Test")
    plt.legend()
    _save_fig("eda_funnel_combined.png")


def run(combined: pd.DataFrame) -> dict[str, pd.DataFrame]:
    res = {
        "summary": summary_statistics(combined),
        "funnel": funnel_summary(combined),
        "missing": missing_report(combined),
        "weekday": weekday_breakdown(combined),
    }
    for m in ["cr", "revenue_per_session", "ctr", "atc_rate"]:
        plot_timeseries(combined, m)
        plot_distribution(combined, m)
    plot_correlation(combined)
    plot_funnel_combined(combined)
    return res


if __name__ == "__main__":
    from .data_processing import build_dataset
    data = build_dataset()
    run(data["combined"])
    print(f"EDA outputs saved to {FIG_DIR} and {TABLE_DIR}")
