# What Can Be Learned from Aggregate Marketing Campaigns?

**Validity Diagnostics, Overdispersion, and Limits of Causal Interpretation**

This repository contains the replication code, data processing pipeline, and final diagnostic manuscript for a re-analysis of a public Kaggle dataset. Originally framed as a "checkout-page redesign A/B test", we demonstrate that the dataset structurally resembles a comparison of two aggregate marketing campaigns, and that a naive binomial interpretation of the results drastically underestimates the true noise level due to daily overdispersion.

## 🎯 Overview

Public A/B testing datasets often contain massive click counts but missing metadata (e.g., randomisation unit, tracking context). This project uses robust statistical checks to prove that taking such datasets at face value leads to false confidence. 

Key findings:
1. **Overdispersion**: Treating daily clicks as independent trials yields a $p < 10^{-30}$ effect for the Test campaign. However, applying a Quasi-Binomial GLM shows that the variance is inflated by roughly $163\times$. Correcting for this overdispersion makes the difference completely **non-significant** ($p = 0.342$).
2. **A/A Simulation**: Simulating random splits of the Control group yields an 87.8% False Positive Rate under standard independent-trials inference, highlighting that daily aggregate rows are not exchangeable experimental replicates.
3. **Compositional Selection Bias**: A funnel analysis shows the Test campaign drives massively higher click-through rates but lower cart and purchase progression. We interpret this as a traffic composition shift (bringing in lower-intent visitors) rather than a causal mid-funnel UI friction.

## 🛠 Project Structure

```
├── dataset/                  # Raw daily CSV files (Control & Test campaigns)
├── output/
│   ├── processed/            # Cleaned data
│   ├── figures/              # Plots (SRM, Funnel Waterfall, A/A simulations)
│   └── statistical_results.txt # Full text output of pipeline
├── paper/
│   ├── manuscript.md         # The main markdown manuscript of the paper
│   └── references.bib        # References
├── src/
│   ├── data_processing.py    # Load and merge CSVs
│   ├── analysis.py           # Quasi-binomial GLM, Classical inference
│   ├── ab_diagnostics.py     # SRM, A/A simulations
│   └── plotting.py           # Generating visualizations
├── main.py                   # Orchestrator pipeline
└── README.md
```

## 🚀 How to Run

1. Make sure you have `pandas`, `scipy`, `statsmodels`, and `matplotlib` installed.
   ```bash
   pip install pandas scipy statsmodels matplotlib
   ```
2. Run the main orchestrator script:
   ```bash
   python main.py
   ```
3. Check the `output/` directory for the newly generated `.txt` reports and `.png` figures.

## 📖 The Manuscript

The full analysis and methodological discussion are written up as a research manuscript in `paper/manuscript.md`. This manuscript warns against making causal product deployment decisions from incomplete, daily-aggregate data without rigorous overdispersion modeling.

*Note: LaTeX source files and PDFs are intentionally excluded from this repository.*
