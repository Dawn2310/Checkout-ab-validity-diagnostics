"""Module 06 — CUPED variance reduction (Deng, Xu, Kohavi, Walker, WSDM 2013).

Original CUPED uses a pre-experiment covariate per user. Here, with daily
aggregates and no user IDs, we adapt CUPED at the day level:

    Y_d = daily CR (observed during experiment)
    X_d = pre-experiment baseline CR for the same weekday
          (computed from the first WEEK_PRE days of CONTROL only)

Adjusted statistic:
    Y'_d = Y_d - theta * (X_d - E[X_d])
    theta = Cov(Y, X) / Var(X)

We then run Welch's t-test on Y' between groups and compare variance and
standard error against the un-adjusted statistic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

from .config import TABLE_DIR, FIG_DIR

WEEK_PRE = 7  # use first 7 days of Control as "pre-experiment"


def _save(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=130)
    plt.close()


def _weekday_baseline(combined: pd.DataFrame) -> pd.Series:
    """Per-weekday mean CR from the first WEEK_PRE Control days."""
    ctrl = combined[combined["group"] == "Control"].sort_values("date")
    pre = ctrl.head(WEEK_PRE).copy()
    pre["weekday"] = pre["date"].dt.day_name()
    return pre.groupby("weekday")["cr"].mean()


def cuped_adjust(combined: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Return df with cr_adj column + estimated theta."""
    df = combined.copy()
    df["weekday"] = df["date"].dt.day_name()
    baseline = _weekday_baseline(df)
    df["x_pre"] = df["weekday"].map(baseline)

    # Restrict regression of theta to *post-pre* rows of both groups
    ctrl_sorted = df[df["group"] == "Control"].sort_values("date")
    post_dates = ctrl_sorted["date"].iloc[WEEK_PRE:]
    post = df[df["date"].isin(post_dates)]

    cov = np.cov(post["cr"], post["x_pre"], ddof=1)
    theta = cov[0, 1] / cov[1, 1] if cov[1, 1] != 0 else 0.0
    mean_x = post["x_pre"].mean()
    df["cr_adj"] = df["cr"] - theta * (df["x_pre"] - mean_x)
    return df, float(theta)


def evaluate(combined: pd.DataFrame) -> dict:
    df, theta = cuped_adjust(combined)
    ctrl_sorted = df[df["group"] == "Control"].sort_values("date")
    post_dates = ctrl_sorted["date"].iloc[WEEK_PRE:]
    post = df[df["date"].isin(post_dates)]

    c = post[post["group"] == "Control"]
    t = post[post["group"] == "Test"]

    # Un-adjusted
    t_raw, p_raw = stats.ttest_ind(t["cr"], c["cr"], equal_var=False)
    var_raw = post.groupby("group")["cr"].var(ddof=1)

    # CUPED-adjusted
    t_cup, p_cup = stats.ttest_ind(t["cr_adj"], c["cr_adj"], equal_var=False)
    var_cup = post.groupby("group")["cr_adj"].var(ddof=1)

    # Average variance reduction
    var_red = 1 - (var_cup.mean() / var_raw.mean())

    # Save side-by-side daily series
    plt.figure(figsize=(11, 5))
    for grp, sub in post.groupby("group"):
        plt.plot(sub["date"], sub["cr"], "--", alpha=0.55,
                 label=f"{grp} raw")
        plt.plot(sub["date"], sub["cr_adj"], "-",
                 label=f"{grp} CUPED")
    plt.title(f"CUPED-adjusted daily CR  (theta={theta:.3f}, "
              f"variance reduction = {var_red:.2%})")
    plt.xlabel("Date")
    plt.ylabel("CR")
    plt.xticks(rotation=30)
    plt.legend()
    _save("cuped_adjustment.png")

    out_df = pd.DataFrame({
        "metric": ["mean_cr_control", "mean_cr_test",
                   "mean_cr_adj_control", "mean_cr_adj_test",
                   "var_cr_control", "var_cr_test",
                   "var_cr_adj_control", "var_cr_adj_test",
                   "theta", "variance_reduction",
                   "t_raw", "p_raw", "t_cuped", "p_cuped"],
        "value": [c["cr"].mean(), t["cr"].mean(),
                  c["cr_adj"].mean(), t["cr_adj"].mean(),
                  var_raw["Control"], var_raw["Test"],
                  var_cup["Control"], var_cup["Test"],
                  theta, var_red,
                  t_raw, p_raw, t_cup, p_cup],
    })
    out_df.to_csv(TABLE_DIR / "cuped_results.csv", index=False)

    return {
        "theta": theta,
        "variance_reduction": var_red,
        "t_raw": t_raw, "p_raw": p_raw,
        "t_cuped": t_cup, "p_cuped": p_cup,
        "mean_cr_control_raw": c["cr"].mean(),
        "mean_cr_test_raw": t["cr"].mean(),
        "mean_cr_control_adj": c["cr_adj"].mean(),
        "mean_cr_test_adj": t["cr_adj"].mean(),
        "n_post_days_per_group": len(c),
    }


def run(combined: pd.DataFrame) -> dict:
    res = evaluate(combined)
    lines = [
        "=" * 70, "CUPED VARIANCE REDUCTION (Deng et al. 2013)",
        "=" * 70, "",
        f"  Pre-experiment window: first {WEEK_PRE} days of Control",
        f"  Post-experiment days per group: {res['n_post_days_per_group']}",
        f"  theta (Cov/Var) = {res['theta']:.4f}",
        "",
        f"  Mean CR (raw)     Control={res['mean_cr_control_raw']:.4%}  "
        f"Test={res['mean_cr_test_raw']:.4%}",
        f"  Mean CR (CUPED)   Control={res['mean_cr_control_adj']:.4%}  "
        f"Test={res['mean_cr_test_adj']:.4%}",
        "",
        f"  Welch t-test (raw)   t={res['t_raw']:.4f}   p={res['p_raw']:.4f}",
        f"  Welch t-test (CUPED) t={res['t_cuped']:.4f}   p={res['p_cuped']:.4f}",
        "",
        f"  >>> Average variance reduction = {res['variance_reduction']:.2%}",
        "", "=" * 70,
    ]
    (TABLE_DIR.parent / "cuped_report.txt").write_text(
        "\n".join(lines), encoding="utf-8")
    return res
