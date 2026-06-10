"""Module 07 — Heterogeneous Treatment Effects.

Proxy moderators (dataset has no device/source):
  - weekday  (Mon..Sun)
  - spend_tier (Low / Medium / High by tertile of daily spend)

Per segment we compute the two-proportion Z-test on CR and apply
Holm correction. We then render a forest plot of absolute uplift with
Wilson 95% CIs.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import (
    proportions_ztest, proportion_confint,
)
from statsmodels.stats.multitest import multipletests

from .config import TABLE_DIR, FIG_DIR, ALPHA


def _save(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=130)
    plt.close()


def _segment_uplift(df: pd.DataFrame, seg_col: str, seg_name: str) -> pd.DataFrame:
    rows = []
    for seg, sub in df.groupby(seg_col, observed=True):
        agg = sub.groupby("group")[["clicks", "purchase"]].sum()
        if not {"Control", "Test"}.issubset(agg.index):
            continue
        n_c, x_c = agg.loc["Control", "clicks"], agg.loc["Control", "purchase"]
        n_t, x_t = agg.loc["Test", "clicks"], agg.loc["Test", "purchase"]
        if n_c == 0 or n_t == 0:
            continue
        cr_c, cr_t = x_c / n_c, x_t / n_t
        z, p = proportions_ztest([x_t, x_c], [n_t, n_c])
        lo_c, hi_c = proportion_confint(x_c, n_c, alpha=ALPHA, method="wilson")
        lo_t, hi_t = proportion_confint(x_t, n_t, alpha=ALPHA, method="wilson")
        rows.append({
            "moderator": seg_name,
            "segment": seg,
            "n_control": int(n_c),
            "n_test": int(n_t),
            "cr_control": cr_c,
            "cr_test": cr_t,
            "abs_uplift": cr_t - cr_c,
            "rel_uplift": (cr_t - cr_c) / cr_c if cr_c > 0 else np.nan,
            "ci_control_lo": lo_c, "ci_control_hi": hi_c,
            "ci_test_lo": lo_t, "ci_test_hi": hi_t,
            "z": z, "p_raw": p,
        })
    return pd.DataFrame(rows)


def _add_holm(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if len(df) == 0:
        df["p_holm"] = []
        df["significant_holm"] = []
        return df
    _, p_adj, _, _ = multipletests(df["p_raw"], alpha=ALPHA, method="holm")
    df["p_holm"] = p_adj
    df["significant_holm"] = df["p_holm"] < ALPHA
    return df


def hte_by_weekday(combined: pd.DataFrame) -> pd.DataFrame:
    df = combined.copy()
    df["weekday"] = df["date"].dt.day_name()
    res = _segment_uplift(df, "weekday", "weekday")
    order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
    res["segment"] = pd.Categorical(res["segment"], order, ordered=True)
    res = res.sort_values("segment")
    return _add_holm(res)


def hte_by_spend_tier(combined: pd.DataFrame) -> pd.DataFrame:
    df = combined.copy()
    df["spend_tier"] = pd.qcut(df["spend"], q=3,
                                labels=["Low", "Medium", "High"])
    res = _segment_uplift(df, "spend_tier", "spend_tier")
    order = ["Low", "Medium", "High"]
    res["segment"] = pd.Categorical(res["segment"], order, ordered=True)
    res = res.sort_values("segment")
    return _add_holm(res)


def forest_plot(df: pd.DataFrame, title: str, fname: str) -> None:
    if len(df) == 0:
        return
    fig, ax = plt.subplots(figsize=(10, 0.5 * len(df) + 2))
    y = np.arange(len(df))
    abs_up = df["abs_uplift"].values * 100
    # symmetric CI proxy via SE from z and uplift
    se = np.where(np.abs(df["z"]) > 1e-6,
                  np.abs(abs_up / df["z"]),
                  np.nan)
    err = 1.96 * se
    colors = ["#2CA02C" if v >= 0 else "#D62728" for v in abs_up]
    ax.errorbar(abs_up, y, xerr=err, fmt="o",
                ecolor="gray", capsize=4, markersize=7,
                markerfacecolor="white", markeredgecolor="black")
    for i, (v, sig) in enumerate(zip(abs_up, df["significant_holm"])):
        ax.scatter(v, y[i], color=colors[i], s=60, zorder=3,
                   marker="s" if sig else "o")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_yticks(y)
    ax.set_yticklabels([str(s) for s in df["segment"]])
    ax.set_xlabel("Absolute CR uplift (Test − Control, percentage points)")
    ax.set_title(title)
    ax.invert_yaxis()
    _save(fname)


def run(combined: pd.DataFrame) -> dict:
    wd = hte_by_weekday(combined)
    st = hte_by_spend_tier(combined)
    wd.to_csv(TABLE_DIR / "hte_weekday.csv", index=False)
    st.to_csv(TABLE_DIR / "hte_spend_tier.csv", index=False)

    forest_plot(wd, "HTE by weekday — absolute CR uplift",
                "hte_forest_weekday.png")
    forest_plot(st, "HTE by spend tier — absolute CR uplift",
                "hte_forest_spend_tier.png")

    lines = [
        "=" * 70, "HETEROGENEOUS TREATMENT EFFECTS",
        "=" * 70, "",
        "[A] BY WEEKDAY", wd.to_string(index=False), "",
        "[B] BY SPEND TIER", st.to_string(index=False), "",
        "=" * 70,
    ]
    (TABLE_DIR.parent / "hte_report.txt").write_text(
        "\n".join(lines), encoding="utf-8")
    return {"weekday": wd, "spend_tier": st}
