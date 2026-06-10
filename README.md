# A/B Testing Analysis for Checkout Page Design

Statistical analysis of an A/B test comparing two checkout-page variants on
conversion rate (CR) and revenue per session, with funnel breakdown,
bootstrap uplift CIs, post-hoc power, logistic regression, and OLS.

## Project structure

```
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
│   └── visualization.py        # Module 04 — paper-ready figures
├── paper/                      # 10 Q1/Q2 reference PDFs + references.bib
└── output/                     # Generated artefacts (gitignored)
    ├── statistical_results.txt
    ├── processed/              # Cleaned datasets
    ├── tables/                 # EDA + funnel-step CSVs
    └── figures/                # All PNG plots
```

## Quick start

```bash
git clone <your-repo-url>
cd AB_TESTING

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

The pipeline runs four stages and writes everything to `output/`.

## Pipeline stages

| Stage | Module | Outputs |
|---|---|---|
| 1. Data processing | `src/data_processing.py` | `output/processed/*.csv` |
| 2. EDA | `src/eda.py` | summary tables + 9 EDA figures |
| 3. Diagnostics | `src/ab_diagnostics.py` | SRM, A/A simulation, outliers |
| 4. Classical inference | `src/analysis.py` | `statistical_results.txt`, `funnel_step_tests.csv` |
| 5. CUPED | `src/cuped.py` | variance reduction (Deng et al. 2013) |
| 6. HTE | `src/hte_analysis.py` | per-segment uplift + Holm + forest plots |
| 7. Causal ML | `src/causal_ml.py` | S/T/X-learner uplift + Qini |
| 8. Final figures | `src/visualization.py` | bar CI, violin, waterfall, bootstrap, funnel |

## Methods implemented

### Classical inference
- **Two-proportion Z-test** on overall CR (statsmodels)
- **Welch t-test** and **Mann-Whitney U** on daily CR / revenue per session
- **Chi-square** test on 2×2 group × purchase contingency
- **Bootstrap percentile CI** (10 000 iters) for absolute and relative uplift
- **Post-hoc power analysis** (Cohen h, `zt_ind_solve_power`)
- **Required sample size** for MDE 5%, 10%, 15% relative
- **Logistic regression** purchase ~ is_test (odds ratio + 95% CI)
- **OLS regression** revenue_per_session ~ is_test + weekday controls
- **Funnel-step proportion tests** with **Holm multiple-test correction**

### Experimental validity & advanced methods
- **Sample Ratio Mismatch (SRM)** chi-square on traffic allocation
- **A/A simulation**: empirical false-positive rate against nominal alpha
- **Outlier-day** detection (1.5×IQR)
- **CUPED** variance reduction with weekday-level pre-experiment covariate
- **HTE by weekday & spend tier** with Wilson CIs + Holm correction
- **Forest plots** of segment-level absolute uplifts
- **Uplift meta-learners**: S-learner, T-learner, X-learner (Künzel et al. 2019)
- **Qini curves** + **AUUC** for ranking uplift models
- **ITE distribution** and aggregation by weekday

## Dataset

Daily-aggregated campaign metrics for Aug 2019, 30 days per variant:

```
campaign, date, spend, impressions, reach, clicks, searches,
view_content, add_to_cart, purchase
```

The control variant has one row (`5.08.2019`) with missing metric values;
the pipeline imputes via forward-fill before computing derived rates.

## References

See [`paper/README.md`](paper/README.md) and [`paper/references.bib`](paper/references.bib)
for the Q1/Q2 sources (Kohavi 2009/2013/2020, Larsen 2024, Taddy 2016,
Deng 2013/2018, Gubela 2020, McDowell 2016, etc.).

## License

MIT
