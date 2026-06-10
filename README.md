# What Can Be Learned from a Daily-Aggregate Checkout A/B Test?
**Validity Diagnostics, Funnel Decomposition, and Limits of Causal Interpretation**

This repository contains the code, datasets, and a manuscript re-analysing a public daily-aggregate e-commerce A/B testing dataset for a checkout-page redesign. Instead of a standard conversion-rate optimisation (CRO) playbook, this project is framed as a **methodological caution**. 

We demonstrate how a seemingly decisive pooled conversion-rate result becomes fragile when the analyst accounts for design ambiguity, time aggregation, post-treatment selection into clicks, and sparse subgroup evidence.

## Project Structure

```text
.
├── main.py                     # End-to-end pipeline entry point
├── requirements.txt
├── dataset/                    # Raw CSVs (semicolon-separated)
│   ├── control_group.csv
│   └── test_group.csv
├── src/
│   ├── config.py               # Paths and constants
│   ├── data_processing.py      # Module 01 — load, clean, feature engineering
│   ├── eda.py                  # Module 02 — exploratory data analysis
│   ├── analysis.py             # Module 03 — statistical inference
│   ├── ab_diagnostics.py       # Module 04 — validity checks (SRM, A/A simulation)
│   ├── cuped.py                # Module 05 — CUPED variance reduction (Delta method)
│   ├── hte_analysis.py         # Module 06 — heterogeneous treatment effects
│   ├── causal_ml.py            # Module 07 — pseudo-session uplift simulation
│   └── visualization.py        # Module 08 — paper-ready figures
├── paper/                      
│   ├── manuscript.md           # The detailed manuscript draft
│   ├── references.bib          # Bibliography
│   └── manuscript/             # LaTeX templates and resources
└── output/                     # Generated artifacts (gitignored by default)
    ├── statistical_results.txt
    ├── tables/                 
    └── figures/                # All generated plots (PDF format)
```

## Core Contributions & Findings

1. **Unit-of-Analysis Paradox**: We show that while a click-pooled $Z$-test yields a highly significant negative effect for the Test variant ($p < 10^{-30}$), this result evaporates when calendar days are treated as the effective unit of variation.
2. **Sample Ratio Mismatch (SRM)**: We detect a severe mismatch in traffic allocation. Because the randomisation unit is undocumented, this serves as an ambiguity warning rather than definitive proof of broken randomisation.
3. **A/A Simulation on Aggregate Data**: We simulate A/A tests by splitting Control days. The empirical false-positive rate balloons to $87.8\%$, proving that daily aggregate rows do not behave like exchangeable experimental replicates.
4. **Acquisition–Conversion Trade-off**: Funnel decomposition reveals that the Test variant generates more clicks but lowers downstream progression among clickers. We emphasise that this is a compositional change (selection bias), not necessarily direct evidence of mid-funnel friction.
5. **Exploratory Weekday Heterogeneity**: We map out potential sign reversals by weekday (e.g., Test performs well on Sunday, poorly on Saturday), but explicitly bound these claims due to the small 30-day sample size.

## Quick Start

```bash
git clone https://github.com/Dawn2310/Checkout-ab-validity-diagnostics.git
cd Checkout-ab-validity-diagnostics

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the complete pipeline
python main.py
```

The pipeline runs sequentially and writes all tables, statistical summaries, and PDF figures to the `output/` directory.

## Methods Implemented

### Validity Diagnostics
- **Sample Ratio Mismatch (SRM)** chi-square sensitivity analysis across reference allocations.
- **A/A simulation** on historical Control splits to diagnose empirical FPR.
- **Outlier-day** detection.

### Statistical Inference
- **Two-proportion Z-test** on overall CR.
- **Welch t-test** and **Mann-Whitney U** on daily CR.
- **Delta-method approximation** for ratio metrics.
- **Bootstrap percentile CIs** (10,000 iterations) over daily resamples.
- **Funnel-stage comparisons** with Holm multiple-test correction.

### Advanced Modeling
- **CUPED** variance reduction adapted for day-level data.
- **HTE by weekday & spend tier** with Wilson CIs and forest plots.
- **Uplift Meta-learners** (S/T/X-learner) evaluated via Qini curves (implemented as a simulation exercise in pseudo-sessions).

## Data and Limitations

The raw data (`dataset/`) consists of 30 days of campaign metrics per variant. Because the dataset lacks documentation on the randomisation unit, intended allocation ratio, and session boundaries, it cannot support confident causal rollout decisions. It serves primarily as a pedagogical tool for A/B testing validity diagnostics.

## License

MIT
