"""End-to-end pipeline for A/B Testing analysis on checkout-page design.

Stages:
  1. Data processing
  2. Exploratory data analysis
  3. A/B validity diagnostics  (SRM, A/A simulation, outliers)
  4. Classical statistical analysis
  5. CUPED variance reduction
  6. Heterogeneous treatment effects
  7. Causal ML — uplift meta-learners
  8. Paper-ready figures

Usage:
    python main.py
"""
from __future__ import annotations

from src.data_processing import build_dataset, aggregate_totals
from src import eda, analysis, visualization
from src import ab_diagnostics, cuped, hte_analysis, causal_ml
from src.config import OUTPUT_DIR


def main() -> None:
    bar = "=" * 70
    print(bar)
    print("A/B TESTING PIPELINE — Checkout Page Design")
    print(bar)

    print("\n[1/8] Data processing ...")
    data = build_dataset()
    agg = aggregate_totals(data["combined"])
    print(f"      Control rows: {len(data['control'])}  "
          f"Test rows: {len(data['test'])}")
    print(agg.to_string(index=False))

    print("\n[2/8] EDA ...")
    eda.run(data["combined"])

    print("\n[3/8] Diagnostics (SRM, A/A, outliers) ...")
    ab_diagnostics.run(data["combined"], agg)

    print("\n[4/8] Classical statistical analysis ...")
    results = analysis.run(data["combined"], agg)

    print("\n[5/8] CUPED variance reduction ...")
    cuped.run(data["combined"])

    print("\n[6/8] Heterogeneous treatment effects ...")
    hte_analysis.run(data["combined"])

    print("\n[7/8] Causal ML — uplift meta-learners ...")
    causal_ml.run(data["combined"])

    print("\n[8/8] Final paper figures ...")
    visualization.run(data["combined"], agg, results)

    print("\n" + bar)
    print(f"DONE. See {OUTPUT_DIR}")
    print("  - statistical_results.txt   : classical inference")
    print("  - diagnostics_report.txt    : SRM / A/A / outliers")
    print("  - cuped_report.txt          : variance reduction")
    print("  - hte_report.txt            : heterogeneous treatment effects")
    print("  - causal_ml_report.txt      : uplift meta-learners")
    print("  - figures/                  : PNG plots")
    print("  - tables/                   : CSV summaries")
    print("  - processed/                : cleaned datasets")
    print(bar)


if __name__ == "__main__":
    main()
