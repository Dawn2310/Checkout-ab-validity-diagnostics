# Deconstructing Aggregate A/B Tests

**Validity Diagnostics, Overdispersion, and Funnel Dynamics**

[![Code Repository](https://img.shields.io/badge/GitHub-Repository-blue.svg)](https://github.com/Dawn2310/Checkout-ab-validity-diagnostics)

This repository contains the replication code, data processing pipeline, and final diagnostic manuscript for a re-analysis of a public Kaggle dataset. Originally framed as a "checkout-page redesign A/B test", we demonstrate that the dataset structurally resembles a comparison of two aggregate marketing campaigns, and that a naive binomial interpretation of the results drastically underestimates the true noise level due to daily overdispersion.

## 🎯 Overview & Research Questions

Public A/B testing datasets often contain massive click counts but lack critical metadata (e.g., randomization unit, tracking context, session boundaries). This project uses robust statistical checks to prove that taking such aggregated datasets at face value leads to false confidence and broken causal inference.

We address three primary research questions:
1. **RQ1:** What does the aggregate conversion comparison show, and how does the conclusion change when the analysis unit shifts from independent clicks to calendar days?
2. **RQ2:** What do overdispersion modelling, sample-ratio-mismatch (SRM) diagnostics, and A/A simulations reveal about the reliability of naive inference on this aggregate dataset?
3. **RQ3:** What descriptive funnel and temporal patterns appear, and why should they be treated as hypothesis-generating rather than direct causal effects?

## 📊 Key Findings

1. **Massive Overdispersion & False Significance**  
   Treating daily clicks as independent trials yields a highly significant but misleading effect for the Test campaign ($p \approx 7.22 \times 10^{-34}$), with Control CR at **9.85%** and Test CR at **8.64%** (Relative Uplift: **-12.28%**). However, applying a Quasi-Binomial GLM reveals that the variance is inflated by roughly **$163\times$** due to unobserved daily shocks. Correcting for this overdispersion makes the difference completely **non-significant** ($p = 0.342$).

2. **Severe Sample Ratio Mismatch (SRM)**  
   The experiment exhibits a massive traffic imbalance with **157,368** Control clicks vs. **180,970** Test clicks (observed Control share of 46.51% instead of the designed 50%). This results in an extreme Sample Ratio Mismatch ($\chi^2 = 1646.44$, $p < 0.0001$), indicating either a broken randomization process or an upstream compositional shift in traffic.

3. **High False Positive Rates in A/A Simulations**  
   Simulating 2,000 random splits of the Control group yields an **87.8% False Positive Rate** under standard independent-trials inference (at a nominal 5% alpha). This highlights that daily aggregate rows are absolutely not exchangeable experimental replicates.

4. **Compositional Selection Bias via Funnel Analysis**  
   A step-by-step funnel analysis shows the Test campaign drives a massively higher Click-Through Rate (**+67.0%** relative uplift, $p < 0.0001$) but suffers from significantly lower downstream progression, such as Add-to-Cart rate (**-30.0%** relative drop). Rather than assuming the Test checkout page inherently causes friction, we interpret this pattern as a **compositional selection shift** — the new campaign brings in broader, lower-intent visitors whose downstream conversion is naturally lower.

## 🛠 Methodology

To arrive at these conclusions, the analysis employs several advanced statistical techniques tailored for grouped summary data:
- **Two-Proportion Z-Tests:** As a naive baseline to highlight the flaws in treating clicks as independent.
- **Quasi-Binomial GLM:** To estimate the overdispersion scale parameter from daily Pearson chi-square statistics, allowing standard errors to expand dynamically based on true variance.
- **A/A Resampling Simulations:** Splitting known Control days to build empirical null distributions.
- **Holm-Corrected Funnel Decompositions:** To isolate relative drops at each step while adjusting for multiple testing.

*(Note: Advanced methodologies like CUPED, Heterogeneous Treatment Effects, and Causal ML Uplift Meta-learners are included in the codebase for reference, but are largely skipped or relegated to supplementary appendices because daily aggregate reconstructions do not yield true individual-level causal uplift.)*

## 📁 Project Structure

```text
├── dataset/                  # Raw daily CSV files (Control & Test campaigns)
├── output/
│   ├── processed/            # Cleaned data
│   ├── figures/              # Plots (SRM, Funnel Waterfall, A/A simulations)
│   ├── statistical_results.txt # Statistical metrics & inference logs
│   ├── diagnostics_report.txt  # SRM, A/A simulations, and outlier details
│   └── ...                   # Other analytical reports
├── paper/
│   ├── manuscript.md         # The main markdown manuscript of the paper
│   └── references.bib        # References
├── src/
│   ├── data_processing.py    # Load and merge CSVs
│   ├── analysis.py           # Quasi-binomial GLM, Classical inference
│   ├── ab_diagnostics.py     # SRM, A/A simulations
│   └── visualization.py      # Generating visualizations
├── main.py                   # Orchestrator pipeline
└── README.md
```

## 🚀 How to Run

### 1. Data Pipeline
1. **Environment Setup:** Ensure the required dependencies are installed.
   ```bash
   pip install pandas scipy statsmodels matplotlib
   ```

2. **Execute Pipeline:** Run the main orchestrator script to regenerate all analyses:
   ```bash
   python main.py
   ```

3. **View Outputs:** Check the `output/` directory for the newly generated diagnostic reports (`.txt`), figures (`.png`), and processed datasets.

### 2. Interactive Webapp & RAG Chatbot
This project includes a Flask webapp serving the data visualizations and a RAG (Retrieval-Augmented Generation) chatbot that can answer questions based on the pipeline's statistical reports.

1. **Install Web Dependencies:**
   ```bash
   pip install flask openai python-dotenv pandas
   ```

2. **Configure API Key:**
   Create a `.env` file in the `webapp/` folder (`webapp/.env`) and add your OpenAI API key and model preference:
   ```env
   OPENAI_API_KEY=sk-...
   OPENAI_MODEL=gpt-4o-mini
   ```
   *(Note: The `webapp/.env` file is intentionally ignored by git to protect your API key).*

3. **Start the Server:**
   ```bash
   python webapp/app.py
   ```
4. **Access the Webapp:** Open `http://127.0.0.1:5000` in your browser.

## 📖 The Manuscript & Practical Implications

The full analysis, statistical theory, and methodological discussion are written up as a research manuscript in `paper/manuscript.md`. 

**Practical Lesson for Analysts:** This manuscript serves as a caution against making causal product deployment decisions from incomplete, daily-aggregate data without rigorous overdispersion modeling. Aggregate dashboards should trigger questions, not immediate deployment. Analysts must demand metadata such as the true randomization unit, intended allocation ratio, and session boundaries before calculating $p$-values.

*Note: LaTeX source files and compiled PDFs are intentionally excluded from this repository.*
