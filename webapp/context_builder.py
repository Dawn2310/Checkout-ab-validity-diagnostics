"""Builds the chatbot system prompt from the pipeline's text reports.

The knowledge base is small (a few KB), so the whole thing is embedded
in the system prompt — no vector store needed.
"""
from __future__ import annotations

from pathlib import Path

PAPER_SUMMARY = """
PAPER: "What Can Be Learned from a Daily-Aggregate Marketing Campaign Dataset?
Validity Diagnostics, Overdispersion, and Limits of Causal Interpretation"
Authors: Nguyen Luong Hai Dang, Duong Quoc Huu, Nguyen Thi Thanh Tien
(Faculty of Artificial Intelligence, FPT University, Vietnam)

KEY FINDINGS:
1. AGGREGATE (click-pooled): CR Control = 9.85%, CR Test = 8.64%,
   relative difference -12.28%, two-proportion Z = -12.139 (p < 1e-30).
   BUT this is only valid if clicks are independent trials — which the
   dataset cannot guarantee.
2. OVERDISPERSION: quasi-binomial GLM dispersion scale = 162.95
   (daily variance ~163x larger than naive binomial). After correction,
   the conversion difference is NOT significant (p = 0.342).
   Daily Welch t-test also not significant (p = 0.135).
   Bootstrap 95% CI for relative uplift = [-32.19%, +12.71%] (crosses zero).
3. SRM: click split 46.51% / 53.49%, chi2 = 1646.44 (p ~ 0) under a 50/50
   reference. Ambiguous: could be allocation failure OR the Test variant's
   higher CTR (assignment unit is undocumented).
4. A/A SIMULATION: splitting Control days randomly gives an 87.8%
   false-positive rate at nominal alpha = 5% — daily aggregates are not
   exchangeable replicates; naive pooled inference is invalid.
5. FUNNEL (all Holm-significant): CTR +67.0% (4.84% -> 8.09%),
   view-per-click -15.5%, add-to-cart per view -30.0%,
   purchase-given-cart +48.3%, overall CR -12.3%.
   Interpretation: compositional confounding (Test attracts lower-intent
   clickers) is the cautious explanation, NOT direct checkout friction.
6. WEEKDAY (exploratory only, 4-5 obs/weekday): relative CR difference
   ranges from -55.4% (Saturday) to +63.0% (Sunday). Hypothesis-generating,
   not a deployment rule.
7. CONCLUSION: the dataset supports diagnostic/methodological claims, not
   a causal rollout decision. Next step = a properly logged unit-level
   experiment with documented randomisation and session identifiers.

DATASET: 60 daily rows (1-30 Aug 2019), Control vs Test campaign.
Columns: spend, impressions, reach, clicks, searches, view-content,
add-to-cart, purchases. One Control row (5 Aug) imputed by forward-fill.
Revenue is NOT observed (assumed-AOV metrics were removed from the paper).

METHODS USED: two-proportion Z-test, Welch t-test, Mann-Whitney U,
chi-square, bootstrap percentile CI (B=10,000), post-hoc power,
quasi-binomial GLM (scale='X2'), SRM chi-square, A/A permutation simulation,
funnel two-proportion tests with Holm correction, weekday segment analysis,
CUPED (appendix sensitivity check only — variance reduction ~1%, negligible).
Uplift meta-learners were REMOVED from the main evidence because
pseudo-session reconstruction cannot create real individual heterogeneity.
"""

SYSTEM_TEMPLATE = """You are the research assistant for an academic data-science \
project on A/B testing validity diagnostics. Visitors are typically the authors' \
professor or fellow students. Answer questions about the study accurately, \
citing the exact numbers below. Default to Vietnamese unless the user writes \
in English. Be concise but precise; use the numbers, do not invent new ones. \
If a question is outside the scope of this study, say so briefly.

{summary}

--- FULL TEXT REPORTS FROM THE ANALYSIS PIPELINE ---
{reports}
"""


def _read(path: Path, limit: int = 6000) -> str:
    try:
        text = path.read_text(encoding="utf-8")
        return text[:limit]
    except OSError:
        return ""


def build_system_prompt(output_dir: Path, tables_dir: Path) -> str:
    reports = []
    for name in ("statistical_results.txt", "diagnostics_report.txt"):
        body = _read(output_dir / name)
        if body:
            reports.append(f"### {name}\n{body}")

    hte = _read(tables_dir / "hte_weekday.csv", limit=3000)
    if hte:
        reports.append(f"### hte_weekday.csv\n{hte}")

    return SYSTEM_TEMPLATE.format(
        summary=PAPER_SUMMARY,
        reports="\n\n".join(reports) if reports else "(reports unavailable)",
    )
