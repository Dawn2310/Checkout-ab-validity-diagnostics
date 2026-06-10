"""Module 04 — Final visualisations for the paper.

Outputs:
  figures/cr_bar_with_ci.png      : Bar chart of overall CR with Wilson 95% CI
  figures/uplift_waterfall.png    : Waterfall of funnel-step uplifts
  figures/cr_violin.png           : Violin distribution of daily CR
  figures/bootstrap_uplift.png    : Histogram of bootstrap relative uplift
  figures/funnel_per_variant.png  : Step-by-step funnel rates per variant
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from statsmodels.stats.proportion import proportion_confint

from .config import FIG_DIR

sns.set_theme(style="whitegrid", context="notebook")
PALETTE = {"Control": "#4C72B0", "Test": "#DD8452"}


def _save(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=130)
    plt.close()


def cr_bar_with_ci(agg: pd.DataFrame) -> None:
    rows = []
    for _, r in agg.iterrows():
        lo, hi = proportion_confint(r["purchase"], r["clicks"],
                                    alpha=0.05, method="wilson")
        rows.append((r["group"], r["purchase"] / r["clicks"], lo, hi))
    df = pd.DataFrame(rows, columns=["group", "cr", "lo", "hi"])
    err = np.array([df["cr"] - df["lo"], df["hi"] - df["cr"]])

    plt.figure(figsize=(7, 5))
    plt.bar(df["group"], df["cr"], yerr=err, capsize=12,
            color=[PALETTE[g] for g in df["group"]], edgecolor="black")
    for i, r in df.iterrows():
        plt.text(i, r["cr"] + (r["hi"] - r["cr"]) * 1.5,
                 f"{r['cr']:.2%}", ha="center", fontweight="bold")
    plt.title("Overall Conversion Rate — Wilson 95% CI")
    plt.ylabel("Conversion Rate")
    _save("cr_bar_with_ci.png")


def uplift_waterfall(funnel_tests: pd.DataFrame) -> None:
    df = funnel_tests.copy()
    df["rel_diff_pct"] = df["rel_diff"] * 100
    plt.figure(figsize=(9, 5))
    colors = ["#2CA02C" if v >= 0 else "#D62728" for v in df["rel_diff_pct"]]
    plt.bar(df["step"], df["rel_diff_pct"], color=colors, edgecolor="black")
    for i, v in enumerate(df["rel_diff_pct"]):
        plt.text(i, v + (0.3 if v >= 0 else -0.6), f"{v:+.1f}%",
                 ha="center", fontweight="bold")
    plt.axhline(0, color="black", linewidth=0.8)
    plt.title("Relative uplift per funnel step (Test vs Control)")
    plt.ylabel("Relative uplift (%)")
    plt.xticks(rotation=20)
    _save("uplift_waterfall.png")


def cr_violin(combined: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))
    sns.violinplot(x="group", y="cr", hue="group", data=combined,
                   palette=PALETTE, inner="box", legend=False)
    sns.stripplot(x="group", y="cr", data=combined,
                  color="black", size=3, alpha=0.5)
    plt.title("Daily Conversion Rate — distribution per variant")
    plt.ylabel("Daily CR")
    _save("cr_violin.png")


def bootstrap_uplift(samples_rel: np.ndarray) -> None:
    lo, hi = np.percentile(samples_rel, [2.5, 97.5])
    plt.figure(figsize=(9, 5))
    plt.hist(samples_rel * 100, bins=60, color="#4C72B0",
             edgecolor="white", alpha=0.85)
    plt.axvline(lo * 100, color="red", linestyle="--",
                label=f"2.5% = {lo:.2%}")
    plt.axvline(hi * 100, color="red", linestyle="--",
                label=f"97.5% = {hi:.2%}")
    plt.axvline(samples_rel.mean() * 100, color="black",
                label=f"mean = {samples_rel.mean():.2%}")
    plt.title("Bootstrap distribution of relative CR uplift")
    plt.xlabel("Relative uplift (%)")
    plt.ylabel("Frequency")
    plt.legend()
    _save("bootstrap_uplift.png")


def funnel_per_variant(agg: pd.DataFrame) -> None:
    df = agg.set_index("group")
    steps = ["impressions", "clicks", "view_content",
             "add_to_cart", "purchase"]
    plt.figure(figsize=(10, 5))
    x = np.arange(len(steps))
    w = 0.38
    plt.bar(x - w / 2, df.loc["Control", steps], w,
            label="Control", color=PALETTE["Control"])
    plt.bar(x + w / 2, df.loc["Test", steps], w,
            label="Test", color=PALETTE["Test"])
    plt.yscale("log")
    plt.xticks(x, [s.title().replace("_", " ") for s in steps])
    plt.ylabel("Count (log scale)")
    plt.title("Conversion funnel per variant")
    plt.legend()
    _save("funnel_per_variant.png")


def run(combined, agg, results) -> None:
    cr_bar_with_ci(agg)
    uplift_waterfall(results["funnel_steps"])
    cr_violin(combined)
    bootstrap_uplift(results["bootstrap"]["samples_rel"])
    funnel_per_variant(agg)


if __name__ == "__main__":
    from .data_processing import build_dataset, aggregate_totals
    from .analysis import run as run_analysis
    data = build_dataset()
    agg = aggregate_totals(data["combined"])
    res = run_analysis(data["combined"], agg)
    run(data["combined"], agg, res)
    print(f"Figures saved to {FIG_DIR}")
