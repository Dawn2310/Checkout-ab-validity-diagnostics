"""Module 03 — Statistical analysis & inference.

Implements:
  - Two-proportion Z-test on overall CR (statsmodels)
  - Welch's t-test on daily CR (scipy)
  - Mann-Whitney U as nonparametric robustness check
  - Chi-square test on funnel contingency table
  - Bootstrap percentile CI for absolute & relative uplift
  - Post-hoc power analysis (zt_ind_solve_power)
  - Required sample-size (MDE = 5%, 10%, 15% relative)
  - Logistic regression: purchase ~ group (clicks weighted)
  - OLS: revenue_per_session ~ group + weekday
  - Funnel-step breakdown z-tests (multiple-test via Holm correction)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.proportion import (
    proportions_ztest, proportion_effectsize, proportion_confint,
)
from statsmodels.stats.power import zt_ind_solve_power
from statsmodels.stats.multitest import multipletests

from .config import (
    TABLE_DIR, OUTPUT_DIR, ALPHA, POWER_TARGET, BOOTSTRAP_ITERS, RNG_SEED,
)


# ---------- Core proportion tests ----------
def overall_cr_test(agg: pd.DataFrame) -> dict:
    ctrl = agg.set_index("group").loc["Control"]
    tst = agg.set_index("group").loc["Test"]
    successes = np.array([tst["purchase"], ctrl["purchase"]])
    nobs = np.array([tst["clicks"], ctrl["clicks"]])
    z, p = proportions_ztest(successes, nobs)
    cr_t = tst["purchase"] / tst["clicks"]
    cr_c = ctrl["purchase"] / ctrl["clicks"]
    ci_c = proportion_confint(ctrl["purchase"], ctrl["clicks"],
                              alpha=ALPHA, method="wilson")
    ci_t = proportion_confint(tst["purchase"], tst["clicks"],
                              alpha=ALPHA, method="wilson")
    return {
        "cr_control": cr_c, "cr_test": cr_t,
        "abs_uplift": cr_t - cr_c, "rel_uplift": (cr_t - cr_c) / cr_c,
        "z_stat": z, "p_value": p,
        "ci_control_lo": ci_c[0], "ci_control_hi": ci_c[1],
        "ci_test_lo": ci_t[0], "ci_test_hi": ci_t[1],
    }


# ---------- Daily-level mean tests ----------
def daily_mean_tests(combined: pd.DataFrame, metric: str = "cr") -> dict:
    c = combined.loc[combined["group"] == "Control", metric].values
    t = combined.loc[combined["group"] == "Test", metric].values
    t_stat, p_t = stats.ttest_ind(t, c, equal_var=False)
    u_stat, p_u = stats.mannwhitneyu(t, c, alternative="two-sided")
    cohens_d = (np.mean(t) - np.mean(c)) / np.sqrt(
        ((len(t) - 1) * np.var(t, ddof=1) + (len(c) - 1) * np.var(c, ddof=1))
        / (len(t) + len(c) - 2)
    )
    return {
        "metric": metric,
        "mean_control": np.mean(c), "mean_test": np.mean(t),
        "welch_t": t_stat, "welch_p": p_t,
        "mw_u": u_stat, "mw_p": p_u,
        "cohens_d": cohens_d,
    }


# ---------- Chi-square on full funnel contingency ----------
def chi_square_funnel(agg: pd.DataFrame) -> dict:
    """Test independence of group × outcome (purchase vs non-purchase among clicks)."""
    ctrl = agg.set_index("group").loc["Control"]
    tst = agg.set_index("group").loc["Test"]
    table = np.array([
        [ctrl["purchase"], ctrl["clicks"] - ctrl["purchase"]],
        [tst["purchase"], tst["clicks"] - tst["purchase"]],
    ])
    chi2, p, dof, expected = stats.chi2_contingency(table)
    return {"chi2": chi2, "p_value": p, "dof": dof}


# ---------- Bootstrap CI on uplift ----------
def bootstrap_uplift_ci(combined: pd.DataFrame,
                        iters: int = BOOTSTRAP_ITERS,
                        seed: int = RNG_SEED) -> dict:
    rng = np.random.default_rng(seed)
    c = combined.loc[combined["group"] == "Control", ["purchase", "clicks"]].values
    t = combined.loc[combined["group"] == "Test", ["purchase", "clicks"]].values
    abs_u, rel_u = np.empty(iters), np.empty(iters)
    for i in range(iters):
        ci = c[rng.integers(0, len(c), len(c))]
        ti = t[rng.integers(0, len(t), len(t))]
        cr_c = ci[:, 0].sum() / ci[:, 1].sum()
        cr_t = ti[:, 0].sum() / ti[:, 1].sum()
        abs_u[i] = cr_t - cr_c
        rel_u[i] = (cr_t - cr_c) / cr_c
    return {
        "abs_uplift_ci": tuple(np.percentile(abs_u, [2.5, 97.5])),
        "rel_uplift_ci": tuple(np.percentile(rel_u, [2.5, 97.5])),
        "abs_uplift_mean": abs_u.mean(),
        "rel_uplift_mean": rel_u.mean(),
        "samples_abs": abs_u, "samples_rel": rel_u,
    }


# ---------- Power & sample-size ----------
def power_and_sample_size(agg: pd.DataFrame) -> dict:
    ctrl = agg.set_index("group").loc["Control"]
    tst = agg.set_index("group").loc["Test"]
    cr_c = ctrl["purchase"] / ctrl["clicks"]
    cr_t = tst["purchase"] / tst["clicks"]
    n_c, n_t = ctrl["clicks"], tst["clicks"]

    h = proportion_effectsize(cr_t, cr_c)
    post_hoc = zt_ind_solve_power(effect_size=h, nobs1=n_t,
                                  alpha=ALPHA, ratio=n_c / n_t)

    required = {}
    for mde_rel in (0.05, 0.10, 0.15):
        cr_target = cr_c * (1 + mde_rel)
        h_mde = proportion_effectsize(cr_target, cr_c)
        n = zt_ind_solve_power(effect_size=abs(h_mde), alpha=ALPHA,
                               power=POWER_TARGET, ratio=1.0)
        required[f"mde_{int(mde_rel*100)}pct"] = int(np.ceil(n))

    return {
        "observed_effect_h": h,
        "post_hoc_power": post_hoc,
        "n_required_per_group": required,
    }


# ---------- Logistic regression at session level ----------
def logistic_regression(agg: pd.DataFrame) -> dict:
    """Reconstruct binary outcomes from daily aggregates and fit logistic.

    purchase ~ group (Test = 1). Each click is a Bernoulli trial.
    """
    rows = []
    for grp, r in agg.set_index("group").iterrows():
        n_pos = int(r["purchase"])
        n_neg = int(r["clicks"] - r["purchase"])
        rows.append(pd.DataFrame({
            "purchase": np.concatenate([np.ones(n_pos), np.zeros(n_neg)]),
            "is_test": int(grp == "Test"),
        }))
    df = pd.concat(rows, ignore_index=True)
    X = sm.add_constant(df["is_test"])
    model = sm.Logit(df["purchase"], X).fit(disp=0)
    or_test = np.exp(model.params["is_test"])
    ci = np.exp(model.conf_int().loc["is_test"]).tolist()
    return {
        "summary": str(model.summary()),
        "coef_is_test": model.params["is_test"],
        "p_value_is_test": model.pvalues["is_test"],
        "odds_ratio": or_test,
        "or_ci_95": (ci[0], ci[1]),
        "pseudo_r2": model.prsquared,
    }


# ---------- OLS revenue per session ----------
def ols_revenue(combined: pd.DataFrame) -> dict:
    df = combined.copy()
    df["is_test"] = (df["group"] == "Test").astype(int)
    df["weekday"] = df["date"].dt.day_name()
    df = pd.get_dummies(df, columns=["weekday"], drop_first=True, dtype=float)
    weekday_cols = [c for c in df.columns if c.startswith("weekday_")]
    X = sm.add_constant(df[["is_test", *weekday_cols]])
    y = df["revenue_per_session"]
    model = sm.OLS(y, X).fit()
    return {
        "summary": str(model.summary()),
        "coef_is_test": model.params["is_test"],
        "p_value_is_test": model.pvalues["is_test"],
        "r_squared": model.rsquared,
    }


# ---------- Funnel-step rates with Holm correction ----------
def funnel_step_tests(agg: pd.DataFrame) -> pd.DataFrame:
    ctrl = agg.set_index("group").loc["Control"]
    tst = agg.set_index("group").loc["Test"]
    steps = [
        ("ctr", "impressions", "clicks"),
        ("view_rate", "clicks", "view_content"),
        ("atc_rate", "view_content", "add_to_cart"),
        ("purchase_rate", "add_to_cart", "purchase"),
        ("cr", "clicks", "purchase"),
    ]
    rows = []
    for name, denom, numer in steps:
        s = np.array([tst[numer], ctrl[numer]])
        n = np.array([tst[denom], ctrl[denom]])
        z, p = proportions_ztest(s, n)
        rate_c = ctrl[numer] / ctrl[denom]
        rate_t = tst[numer] / tst[denom]
        rows.append({
            "step": name,
            "rate_control": rate_c, "rate_test": rate_t,
            "abs_diff": rate_t - rate_c,
            "rel_diff": (rate_t - rate_c) / rate_c,
            "z": z, "p_raw": p,
        })
    out = pd.DataFrame(rows)
    _, p_adj, _, _ = multipletests(out["p_raw"], alpha=ALPHA, method="holm")
    out["p_holm"] = p_adj
    out["significant_holm"] = out["p_holm"] < ALPHA
    out.to_csv(TABLE_DIR / "funnel_step_tests.csv", index=False)
    return out


# ---------- Orchestrator ----------
def run(combined: pd.DataFrame, agg: pd.DataFrame) -> dict:
    results = {
        "overall_cr": overall_cr_test(agg),
        "daily_cr": daily_mean_tests(combined, "cr"),
        "daily_rps": daily_mean_tests(combined, "revenue_per_session"),
        "chi2": chi_square_funnel(agg),
        "bootstrap": bootstrap_uplift_ci(combined),
        "power": power_and_sample_size(agg),
        "logit": logistic_regression(agg),
        "ols_rps": ols_revenue(combined),
        "funnel_steps": funnel_step_tests(agg),
    }

    _write_report(results)
    return results


def _write_report(res: dict) -> None:
    lines = ["=" * 70, "A/B TESTING — STATISTICAL REPORT", "=" * 70, ""]

    o = res["overall_cr"]
    lines += [
        "[1] OVERALL CONVERSION RATE — Two-proportion Z-test",
        f"  CR Control = {o['cr_control']:.4%}  (95% Wilson CI: "
        f"{o['ci_control_lo']:.4%} – {o['ci_control_hi']:.4%})",
        f"  CR Test    = {o['cr_test']:.4%}  (95% Wilson CI: "
        f"{o['ci_test_lo']:.4%} – {o['ci_test_hi']:.4%})",
        f"  Absolute uplift = {o['abs_uplift']:+.4%}",
        f"  Relative uplift = {o['rel_uplift']:+.2%}",
        f"  z = {o['z_stat']:.4f}    p-value = {o['p_value']:.6f}",
        f"  => {'SIGNIFICANT' if o['p_value'] < ALPHA else 'NOT SIGNIFICANT'} at alpha={ALPHA}",
        "",
    ]

    d = res["daily_cr"]
    lines += [
        "[2] DAILY CR — Welch t-test & Mann-Whitney U",
        f"  mean(Control)={d['mean_control']:.4%}  mean(Test)={d['mean_test']:.4%}",
        f"  Welch t = {d['welch_t']:.4f}  p = {d['welch_p']:.6f}",
        f"  MW U    = {d['mw_u']:.1f}     p = {d['mw_p']:.6f}",
        f"  Cohen's d = {d['cohens_d']:.4f}",
        "",
    ]

    r = res["daily_rps"]
    lines += [
        "[3] DAILY REVENUE PER SESSION — Welch t-test & Mann-Whitney U",
        f"  mean(Control)=${r['mean_control']:.3f}  mean(Test)=${r['mean_test']:.3f}",
        f"  Welch t = {r['welch_t']:.4f}  p = {r['welch_p']:.6f}",
        f"  MW U    = {r['mw_u']:.1f}     p = {r['mw_p']:.6f}",
        f"  Cohen's d = {r['cohens_d']:.4f}",
        "",
    ]

    c = res["chi2"]
    lines += [
        "[4] CHI-SQUARE — group × purchase (2×2)",
        f"  chi2 = {c['chi2']:.4f}  dof = {c['dof']}  p = {c['p_value']:.6f}",
        "",
    ]

    b = res["bootstrap"]
    lines += [
        f"[5] BOOTSTRAP CI ({BOOTSTRAP_ITERS} iters)",
        f"  absolute uplift  mean = {b['abs_uplift_mean']:+.4%}  "
        f"95% CI = [{b['abs_uplift_ci'][0]:+.4%}, {b['abs_uplift_ci'][1]:+.4%}]",
        f"  relative uplift  mean = {b['rel_uplift_mean']:+.2%}  "
        f"95% CI = [{b['rel_uplift_ci'][0]:+.2%}, {b['rel_uplift_ci'][1]:+.2%}]",
        "",
    ]

    p = res["power"]
    lines += [
        "[6] POWER ANALYSIS",
        f"  Observed effect size (Cohen h) = {p['observed_effect_h']:.4f}",
        f"  Post-hoc power = {p['post_hoc_power']:.4f}  "
        f"({'adequate' if p['post_hoc_power'] >= POWER_TARGET else 'INSUFFICIENT'})",
        f"  Required n/group for 80% power:",
    ]
    for k, v in p["n_required_per_group"].items():
        lines.append(f"      {k}: {v:,}")
    lines.append("")

    lg = res["logit"]
    lines += [
        "[7] LOGISTIC REGRESSION — purchase ~ is_test",
        f"  Coef(is_test) = {lg['coef_is_test']:.4f}  p = {lg['p_value_is_test']:.6f}",
        f"  Odds Ratio    = {lg['odds_ratio']:.4f}  "
        f"95% CI = [{lg['or_ci_95'][0]:.4f}, {lg['or_ci_95'][1]:.4f}]",
        f"  Pseudo R^2    = {lg['pseudo_r2']:.6f}",
        "",
    ]

    ol = res["ols_rps"]
    lines += [
        "[8] OLS — revenue_per_session ~ is_test + weekday",
        f"  Coef(is_test) = {ol['coef_is_test']:.4f}  p = {ol['p_value_is_test']:.6f}",
        f"  R^2 = {ol['r_squared']:.4f}",
        "",
    ]

    fs = res["funnel_steps"]
    lines += ["[9] FUNNEL-STEP TESTS (Holm-corrected)"]
    lines += [fs.to_string(index=False), ""]

    lines += ["=" * 70,
              "CONCLUSION: see overall_cr p-value & bootstrap CI above.",
              "=" * 70]

    (OUTPUT_DIR / "statistical_results.txt").write_text(
        "\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    from .data_processing import build_dataset, aggregate_totals
    data = build_dataset()
    agg = aggregate_totals(data["combined"])
    run(data["combined"], agg)
    print(f"Report written to {OUTPUT_DIR / 'statistical_results.txt'}")
