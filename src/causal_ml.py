"""Module 08 — Causal ML & uplift modelling.

We expand the day-level aggregates into a synthetic session-level
dataset (each click is a Bernoulli trial of purchase) and equip every
session with day-level features:
  - is_test          : treatment indicator
  - weekday_*        : day-of-week dummies
  - day_index        : ordinal day in the campaign
  - log_spend        : log(spend on that day + 1)
  - log_impressions  : log(impressions + 1)
  - searches_per_click

We train three meta-learners (Künzel et al. 2019):
  - S-learner  : single estimator with treatment as a feature
  - T-learner  : two separate estimators (one per arm)
  - X-learner  : Künzel recipe with propensity weighting (50/50)

We then build the Qini curve and AUUC, and aggregate predicted
individual treatment effect (ITE) by weekday and spend tier.

The synthetic expansion is purely a computational trick to permit
ML estimators; the underlying randomisation is still day-level.
We acknowledge this in the paper as a limitation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from .config import TABLE_DIR, FIG_DIR, RNG_SEED

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]


def _save(name):
    plt.tight_layout()
    plt.savefig(FIG_DIR / name, dpi=130)
    plt.close()


# ---------- Session-level synthesis ----------
def expand_to_sessions(combined: pd.DataFrame,
                       seed: int = RNG_SEED) -> pd.DataFrame:
    """Generate a session-level dataframe from daily aggregates."""
    rng = np.random.default_rng(seed)
    df = combined.copy()
    df["weekday"] = df["date"].dt.day_name()
    df["day_index"] = (df["date"] - df["date"].min()).dt.days
    df["log_spend"] = np.log1p(df["spend"])
    df["log_impressions"] = np.log1p(df["impressions"])
    df["searches_per_click"] = df["searches"] / df["clicks"]

    rows = []
    for _, r in df.iterrows():
        n = int(r["clicks"])
        if n <= 0:
            continue
        y = (rng.random(n) < r["cr"]).astype(int)
        d = {
            "is_test": int(r["group"] == "Test"),
            "day_index": r["day_index"],
            "log_spend": r["log_spend"],
            "log_impressions": r["log_impressions"],
            "searches_per_click": r["searches_per_click"],
            "weekday": r["weekday"],
            "purchase": y,
        }
        rows.append(pd.DataFrame(d))
    sessions = pd.concat(rows, ignore_index=True)
    sessions = pd.get_dummies(sessions, columns=["weekday"],
                              drop_first=False, dtype=float)
    for w in WEEKDAYS:
        col = f"weekday_{w}"
        if col not in sessions.columns:
            sessions[col] = 0.0
    return sessions


def _feature_cols(df: pd.DataFrame) -> list[str]:
    base = ["day_index", "log_spend", "log_impressions", "searches_per_click"]
    wk = [c for c in df.columns if c.startswith("weekday_")]
    return base + wk


# ---------- Meta-learners ----------
def s_learner(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    feats = _feature_cols(train) + ["is_test"]
    model = HistGradientBoostingClassifier(
        max_iter=120, max_depth=5, random_state=RNG_SEED)
    model.fit(train[feats], train["purchase"])
    test_t = test.copy(); test_t["is_test"] = 1
    test_c = test.copy(); test_c["is_test"] = 0
    return (model.predict_proba(test_t[feats])[:, 1]
            - model.predict_proba(test_c[feats])[:, 1])


def t_learner(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    feats = _feature_cols(train)
    m0 = HistGradientBoostingClassifier(
        max_iter=120, max_depth=5, random_state=RNG_SEED)
    m1 = HistGradientBoostingClassifier(
        max_iter=120, max_depth=5, random_state=RNG_SEED)
    m0.fit(train.loc[train["is_test"] == 0, feats],
           train.loc[train["is_test"] == 0, "purchase"])
    m1.fit(train.loc[train["is_test"] == 1, feats],
           train.loc[train["is_test"] == 1, "purchase"])
    return (m1.predict_proba(test[feats])[:, 1]
            - m0.predict_proba(test[feats])[:, 1])


def x_learner(train: pd.DataFrame, test: pd.DataFrame,
              propensity: float = 0.5) -> np.ndarray:
    """Künzel et al. 2019 X-learner with constant propensity."""
    feats = _feature_cols(train)
    m0 = HistGradientBoostingClassifier(
        max_iter=120, max_depth=5, random_state=RNG_SEED)
    m1 = HistGradientBoostingClassifier(
        max_iter=120, max_depth=5, random_state=RNG_SEED)
    m0.fit(train.loc[train["is_test"] == 0, feats],
           train.loc[train["is_test"] == 0, "purchase"])
    m1.fit(train.loc[train["is_test"] == 1, feats],
           train.loc[train["is_test"] == 1, "purchase"])

    d1 = (train.loc[train["is_test"] == 1, "purchase"].values
          - m0.predict_proba(train.loc[train["is_test"] == 1, feats])[:, 1])
    d0 = (m1.predict_proba(train.loc[train["is_test"] == 0, feats])[:, 1]
          - train.loc[train["is_test"] == 0, "purchase"].values)

    tau1 = LogisticRegression(max_iter=400)
    # binarise pseudo-outcome (tau is in [-1, 1])
    tau1.fit(train.loc[train["is_test"] == 1, feats],
             (d1 > 0).astype(int))
    tau0 = LogisticRegression(max_iter=400)
    tau0.fit(train.loc[train["is_test"] == 0, feats],
             (d0 > 0).astype(int))

    p1 = tau1.predict_proba(test[feats])[:, 1]
    p0 = tau0.predict_proba(test[feats])[:, 1]
    return propensity * p0 + (1 - propensity) * p1


# ---------- Qini / AUUC ----------
def qini_curve(test: pd.DataFrame, ite: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    """Standard Qini curve from predicted ITE."""
    df = test.copy()
    df["ite"] = ite
    df = df.sort_values("ite", ascending=False).reset_index(drop=True)
    n_t = (df["is_test"] == 1).sum()
    n_c = (df["is_test"] == 0).sum()
    if n_t == 0 or n_c == 0:
        return np.array([0]), np.array([0]), 0.0
    cum_t = (df["is_test"] * df["purchase"]).cumsum().values
    cum_c = ((1 - df["is_test"]) * df["purchase"]).cumsum().values
    qini = cum_t - cum_c * (n_t / n_c)
    x = np.arange(1, len(df) + 1) / len(df)
    # Random baseline
    random_qini = qini[-1] * x
    auuc = float(np.trapz(qini - random_qini, x))
    return x, qini, auuc


# ---------- Driver ----------
def run(combined: pd.DataFrame,
        sample_frac: float = 0.30) -> dict:
    """Train all three learners and report.

    `sample_frac` downsamples the synthetic session frame to keep runtime
    bounded (full 338k × 12 features is fine but boosting with 3 learners
    times 5-fold-ish workflow grows quickly).
    """
    sessions = expand_to_sessions(combined)
    if sample_frac < 1.0:
        sessions = sessions.sample(frac=sample_frac, random_state=RNG_SEED)

    train, test = train_test_split(sessions, test_size=0.30,
                                   stratify=sessions["is_test"],
                                   random_state=RNG_SEED)

    ite_s = s_learner(train, test)
    ite_t = t_learner(train, test)
    ite_x = x_learner(train, test)

    results = {}
    plt.figure(figsize=(8, 6))
    for name, ite in [("S-learner", ite_s),
                       ("T-learner", ite_t),
                       ("X-learner", ite_x)]:
        x, q, auuc = qini_curve(test, ite)
        results[name] = {
            "auuc": auuc,
            "mean_ite": float(np.mean(ite)),
            "std_ite": float(np.std(ite)),
            "share_positive_ite": float((ite > 0).mean()),
        }
        plt.plot(x, q, label=f"{name} (AUUC={auuc:.2f})")
    plt.axhline(0, color="black", linewidth=0.7)
    plt.xlabel("Fraction of population targeted")
    plt.ylabel("Cumulative incremental purchases (Qini)")
    plt.title("Qini curves — uplift meta-learners")
    plt.legend()
    _save("qini_curves.png")

    # ITE histogram (T-learner)
    plt.figure(figsize=(9, 5))
    plt.hist(ite_t, bins=60, color="#4C72B0",
             alpha=0.85, edgecolor="white")
    plt.axvline(0, color="black", linewidth=0.8)
    plt.axvline(float(np.mean(ite_t)), color="red",
                linestyle="--", label=f"mean = {np.mean(ite_t):.4f}")
    plt.title("Predicted Individual Treatment Effect (T-learner)")
    plt.xlabel("ITE (probability difference Test − Control)")
    plt.ylabel("Frequency")
    plt.legend()
    _save("ite_histogram_t_learner.png")

    # ITE by weekday
    test = test.copy()
    test["ite_t"] = ite_t
    weekday_cols = [f"weekday_{w}" for w in WEEKDAYS]
    test["weekday"] = test[weekday_cols].idxmax(axis=1).str.replace("weekday_", "")
    by_wd = test.groupby("weekday")["ite_t"].agg(["mean", "std", "count"])
    by_wd = by_wd.reindex(WEEKDAYS).reset_index()
    by_wd.to_csv(TABLE_DIR / "ite_by_weekday.csv", index=False)

    plt.figure(figsize=(9, 5))
    plt.bar(by_wd["weekday"], by_wd["mean"] * 100,
            yerr=1.96 * by_wd["std"] * 100 / np.sqrt(by_wd["count"]),
            capsize=6, color="#4C72B0", edgecolor="black")
    plt.axhline(0, color="black", linewidth=0.7)
    plt.title("Mean predicted ITE by weekday (T-learner)")
    plt.ylabel("Mean ITE (percentage points)")
    plt.xticks(rotation=20)
    _save("ite_by_weekday.png")

    summary = pd.DataFrame(results).T.reset_index().rename(
        columns={"index": "learner"})
    summary.to_csv(TABLE_DIR / "uplift_learners_summary.csv", index=False)

    lines = [
        "=" * 70, "CAUSAL ML — UPLIFT META-LEARNERS",
        "=" * 70, "",
        summary.to_string(index=False), "",
        "ITE by weekday (T-learner):",
        by_wd.to_string(index=False),
        "", "=" * 70,
    ]
    (TABLE_DIR.parent / "causal_ml_report.txt").write_text(
        "\n".join(lines), encoding="utf-8")

    return {"summary": results, "by_weekday": by_wd}
