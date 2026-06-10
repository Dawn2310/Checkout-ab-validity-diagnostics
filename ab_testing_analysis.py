import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.power import zt_ind_solve_power
from statsmodels.stats.proportion import proportion_effectsize
import os
import warnings
warnings.filterwarnings('ignore')

# Create output dir
os.makedirs('output', exist_ok=True)

# Load datasets
control = pd.read_csv('dataset/control_group.csv', sep=';')
test = pd.read_csv('dataset/test_group.csv', sep=';')

# Clean column names
control.columns = [c.strip() for c in control.columns]
test.columns = [c.strip() for c in test.columns]

# Rename columns for easier access
col_map = {
    'Campaign Name': 'campaign',
    'Date': 'date',
    'Spend [USD]': 'spend',
    '# of Impressions': 'impressions',
    'Reach': 'reach',
    '# of Website Clicks': 'clicks',
    '# of Searches': 'searches',
    '# of View Content': 'view_content',
    '# of Add to Cart': 'add_to_cart',
    '# of Purchase': 'purchase'
}
control.rename(columns=col_map, inplace=True)
test.rename(columns=col_map, inplace=True)

# Handle missing values (e.g. 5.08.2019 in Control)
control = control.ffill()

# Calculate daily Conversion Rate (CR) = Purchase / Clicks
control['CR'] = control['purchase'] / control['clicks']
test['CR'] = test['purchase'] / test['clicks']

# 1. Statistical Testing
# Daily T-test on CR
t_stat, p_val_t = stats.ttest_ind(control['CR'], test['CR'], equal_var=False)

# Overall Proportion Z-test on CR
successes = np.array([test['purchase'].sum(), control['purchase'].sum()])
nobs = np.array([test['clicks'].sum(), control['clicks'].sum()])
z_stat, p_val_z = proportions_ztest(successes, nobs)

# Uplift calculation
overall_cr_control = control['purchase'].sum() / control['clicks'].sum()
overall_cr_test = test['purchase'].sum() / test['clicks'].sum()
uplift = (overall_cr_test - overall_cr_control) / overall_cr_control

# Power analysis
h = proportion_effectsize(overall_cr_test, overall_cr_control)
power = zt_ind_solve_power(effect_size=h, nobs1=nobs[0], alpha=0.05, ratio=nobs[1]/nobs[0])

with open('output/statistical_results.txt', 'w', encoding='utf-8') as f:
    f.write(f"--- A/B Testing Results ---\n")
    f.write(f"Control Overall CR (Purchase/Clicks): {overall_cr_control:.2%}\n")
    f.write(f"Test Overall CR (Purchase/Clicks): {overall_cr_test:.2%}\n")
    f.write(f"Uplift (Relative): {uplift:.2%}\n\n")
    f.write(f"Proportion Z-test p-value: {p_val_z:.4f}\n")
    if p_val_z < 0.05:
        f.write("=> Sự khác biệt về CR tổng thể có ý nghĩa thống kê (p < 0.05).\n")
    else:
        f.write("=> Sự khác biệt về CR tổng thể KHÔNG có ý nghĩa thống kê (p >= 0.05).\n")
    
    f.write(f"\nDaily T-test p-value: {p_val_t:.4f}\n")
    if p_val_t < 0.05:
        f.write("=> Sự khác biệt về CR trung bình ngày có ý nghĩa thống kê (p < 0.05).\n")
    else:
        f.write("=> Sự khác biệt về CR trung bình ngày KHÔNG có ý nghĩa thống kê (p >= 0.05).\n")
        
    f.write(f"\nStatistical Power (Post-hoc): {power:.4f}\n")
    if power >= 0.8:
        f.write("=> Power >= 0.8: Kích thước mẫu đủ lớn để phát hiện sự khác biệt.\n")
    else:
        f.write("=> Power < 0.8: Kích thước mẫu có thể chưa đủ lớn.\n")

# 2. Visualizations
sns.set_theme(style="whitegrid")

# a. Bar CR with CI
plt.figure(figsize=(8, 6))
cr_data = pd.DataFrame({
    'Group': ['Control', 'Test'],
    'CR': [overall_cr_control, overall_cr_test]
})
ci_control = 1.96 * np.sqrt((overall_cr_control * (1 - overall_cr_control)) / nobs[1])
ci_test = 1.96 * np.sqrt((overall_cr_test * (1 - overall_cr_test)) / nobs[0])

plt.bar(cr_data['Group'], cr_data['CR'], yerr=[ci_control, ci_test], capsize=10, color=['#4C72B0', '#DD8452'])
plt.title('Overall Conversion Rate with 95% CI')
plt.ylabel('Conversion Rate (Purchase / Clicks)')
plt.savefig('output/cr_bar_plot.png')
plt.close()

# b. Funnel per variant
funnel_cols = ['impressions', 'clicks', 'view_content', 'add_to_cart', 'purchase']
control_funnel = control[funnel_cols].sum()
test_funnel = test[funnel_cols].sum()

plt.figure(figsize=(10, 6))
x = np.arange(len(funnel_cols))
width = 0.35
plt.bar(x - width/2, control_funnel, width, label='Control', color='#4C72B0')
plt.bar(x + width/2, test_funnel, width, label='Test', color='#DD8452')
plt.xticks(x, ['Impressions', 'Clicks', 'View Content', 'Add to Cart', 'Purchase'])
plt.yscale('log')
plt.title('Conversion Funnel (Log Scale)')
plt.ylabel('Count')
plt.legend()
plt.savefig('output/funnel_plot.png')
plt.close()

# c. Violin distribution of daily CR
plt.figure(figsize=(8, 6))
combined = pd.concat([control[['CR', 'campaign']], test[['CR', 'campaign']]])
sns.violinplot(x='campaign', y='CR', data=combined, palette=['#4C72B0', '#DD8452'])
plt.title('Daily Conversion Rate Distribution')
plt.ylabel('Daily CR')
plt.savefig('output/violin_plot.png')
plt.close()

print("Analysis complete. Results and plots saved to 'output' directory.")
