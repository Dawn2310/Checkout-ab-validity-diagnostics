"""Module 05 — A/B test validity diagnostics.

Implements:
  - Sample Ratio Mismatch (SRM) check via chi-square on traffic allocation
  - A/A test simulation: random split of Control into two halves N times,
    compare empirical false-positive rate vs nominal alpha
  - Outlier-day detection via IQR on daily CR per group
  - Pre-experiment sanity: trends in CTR before/after split
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

from .config import TABLE_DIR, FIG_DIR, ALPHA, RNG_SEED


def _save(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=130)
    plt.close()


def sample_ratio_mismatch(agg: pd.DataFrame, expected_ratio: float = 0.5) -> dict:
    """Chi-square test that observed click split matches the design ratio.

    H0: Control / (Control + Test) = expected_ratio.
    """
    n_c = float(agg.set_index("group").loc["Control", "clicks"])
    n_t = float(agg.set_index("group").loc["Test", "clicks"])
    total = n_c + n_t
    obs = np.array([n_c, n_t])
    exp = np.array([total * expected_ratio, total * (1 - expected_ratio)])
    chi2 = ((obs - exp) ** 2 / exp).sum()
    p = 1 - stats.chi2.cdf(chi2, df=1)
    return {
        "n_control_clicks": int(n_c),
        "n_test_clicks": int(n_t),
        "observed_ratio_control": n_c / total,
        "expected_ratio_control": expected_ratio,
        "chi2": float(chi2),
        "p_value": float(p),
        "srm_detected": bool(p < ALPHA),
    }


def aa_simulation(combined: pd.DataFrame,
                  n_iters: int = 2000,
                  seed: int = RNG_SEED) -> dict:
    """Permute Control rows into two halves, run Z-test on CR, repeat.

    Reports the empirical false-positive rate against the nominal alpha
    and the distribution of p-values (should be roughly U[0,1]).
    """
    rng = np.random.default_rng(seed)
    ctrl = combined.loc[combined["group"] == "Control",
                        ["clicks", "purchase"]].values
    n_rows = len(ctrl)
    p_values = np.empty(n_iters)
    for i in range(n_iters):
        idx = rng.permutation(n_rows)
        half = n_rows // 2
        a = ctrl[idx[:half]].sum(axis=0)
        b = ctrl[idx[half:]].sum(axis=0)
        _, p = proportions_ztest([a[1], b[1]], [a[0], b[0]])
        p_values[i] = p

    fpr = float((p_values < ALPHA).mean())

    plt.figure(figsize=(8, 5))
    plt.hist(p_values, bins=40, color="#4C72B0",
             edgecolor="white", alpha=0.85)
    plt.axvline(ALPHA, color="red", linestyle="--",
                label=f"alpha = {ALPHA}")
    plt.title(f"A/A null distribution of p-values\n"
              f"empirical FPR = {fpr:.3%}  (nominal = {ALPHA:.2%})")
    plt.xlabel("p-value")
    plt.ylabel("Frequency")
    plt.legend()
    _save("aa_simulation_pvalues.png")

    return {
        "n_iters": n_iters,
        "empirical_fpr": fpr,
        "nominal_alpha": ALPHA,
        "ks_uniform_p": float(stats.kstest(p_values, "uniform").pvalue),
    }


def outlier_days(combined: pd.DataFrame) -> pd.DataFrame:
    """Tukey 1.5×IQR rule on daily CR per group."""
    rows = []
    for grp, sub in combined.groupby("group"):
        q1, q3 = np.percentile(sub["cr"], [25, 75])
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out = sub.loc[(sub["cr"] < lo) | (sub["cr"] > hi),
                      ["date", "cr", "clicks", "purchase"]]
        for _, r in out.iterrows():
            rows.append({
                "group": grp,
                "date": r["date"].date(),
                "cr": r["cr"],
                "clicks": int(r["clicks"]),
                "purchase": int(r["purchase"]),
                "iqr_lo": lo, "iqr_hi": hi,
            })
    df = pd.DataFrame(rows)
    df.to_csv(TABLE_DIR / "outlier_days.csv", index=False)
    return df


def run(combined: pd.DataFrame, agg: pd.DataFrame) -> dict:
    res = {
        "srm": sample_ratio_mismatch(agg),
        "aa": aa_simulation(combined),
        "outliers": outlier_days(combined),
    }
    _write_report(res)
    return res


def _write_report(res):
    s = res["srm"]
    aa = res["aa"]
    out = res["outliers"]
    lines = [
        "=" * 70,
        "A/B DIAGNOSTICS REPORT",
        "=" * 70,
        "",
        "[1] SAMPLE RATIO MISMATCH (SRM)",
        f"  Control clicks = {s['n_control_clicks']:,}",
        f"  Test    clicks = {s['n_test_clicks']:,}",
        f"  Observed control share = {s['observed_ratio_control']:.4f}  "
        f"(design = {s['expected_ratio_control']})",
        f"  chi2 = {s['chi2']:.4f}  p = {s['p_value']:.2e}",
        f"  => SRM {'DETECTED — randomization may be broken' if s['srm_detected'] else 'not detected'}",
        "",
        "[2] A/A SIMULATION (split Control into two halves)",
        f"  n_iters = {aa['n_iters']:,}   nominal alpha = {aa['nominal_alpha']}",
        f"  empirical false-positive rate = {aa['empirical_fpr']:.3%}",
        f"  KS test vs U[0,1]: p = {aa['ks_uniform_p']:.4f}  "
        f"({'uniform' if aa['ks_uniform_p'] > 0.05 else 'NOT uniform'})",
        "",
        f"[3] OUTLIER DAYS (1.5×IQR on daily CR): {len(out)} day(s)",
    ]
    if len(out) > 0:
        lines.append(out.to_string(index=False))
    lines += ["", "=" * 70]
    (TABLE_DIR.parent / "diagnostics_report.txt").write_text(
        "\n".join(lines), encoding="utf-8")
