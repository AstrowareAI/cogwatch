"""
Plot Historical Cognitive Index Data (2012-2024) - Observed Data Only
This is the raw data, not the forecast
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

# Read the historical data
df = pd.read_csv('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/data/Cognitive_Debt-Cognitive Ability_Index.csv')

# Clean up (drop rows with NaN years)
df = df[df['Year'].notna()].copy()
df['Year'] = df['Year'].astype(int)
df['Cognitive Index (2012 = 100)'] = pd.to_numeric(df['Cognitive Index (2012 = 100)'], errors='coerce')
df = df[df['Year'] >= 2012]  # We only care about 2012-2024

# Create figure
fig, ax = plt.subplots(figsize=(14, 8))

# Plot the data
ax.plot(df['Year'], df['Cognitive Index (2012 = 100)'],
        linewidth=4, marker='o', color='darkblue',
        markersize=10, label='Observed Cognitive Index')

# Mark ChatGPT launch
ax.axvline(x=2022, color='red', linestyle='--', linewidth=3, alpha=0.7)
ax.text(2022.1, 97.5, 'ChatGPT Launch\n(Nov 2022)',
        fontsize=12, ha='left', color='red', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

# Calculate and show pre/post ChatGPT decline rates
pre_2022 = df[df['Year'] <= 2022]
post_2022 = df[df['Year'] >= 2022]

# Pre-ChatGPT rate (2012-2022)
years_pre = pre_2022['Year'].max() - pre_2022['Year'].min()
decline_pre = pre_2022['Cognitive Index (2012 = 100)'].iloc[0] - pre_2022['Cognitive Index (2012 = 100)'].iloc[-1]
rate_pre = decline_pre / years_pre

# Post-ChatGPT rate (2022-2024)
years_post = post_2022['Year'].max() - post_2022['Year'].min()
decline_post = post_2022['Cognitive Index (2012 = 100)'].iloc[0] - post_2022['Cognitive Index (2012 = 100)'].iloc[-1]
rate_post = decline_post / years_post if years_post > 0 else 0

# Add annotation
acceleration = ((rate_post - rate_pre) / rate_pre * 100) if rate_pre > 0 else 0

textbox = f"""Pre-ChatGPT (2012-2022):
Decline Rate: {rate_pre:.2f} pts/year

Post-ChatGPT (2022-2024):
Decline Rate: {rate_post:.2f} pts/year

Acceleration: {acceleration:.1f}%"""

ax.text(2013, 96.5, textbox, fontsize=11,
        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.8),
        verticalalignment='top', fontfamily='monospace')

# Styling
ax.set_xlabel('Year', fontsize=14, fontweight='bold')
ax.set_ylabel('Cognitive Index (2012=100)', fontsize=14, fontweight='bold')
ax.set_title('Historical Cognitive Index Decline (2012-2024)\nObserved Data from PISA, NAEP, and Flynn Effect Studies',
             fontsize=16, fontweight='bold', pad=20)
ax.legend(loc='upper right', fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xlim(2011.5, 2024.5)
ax.set_ylim(95.5, 100.5)

# Add horizontal reference lines
ax.axhline(y=100, color='green', linestyle=':', linewidth=1, alpha=0.5, label='Baseline (2012)')
ax.axhline(y=96.1, color='orange', linestyle=':', linewidth=1, alpha=0.5)

plt.tight_layout()
plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/historical_cognitive_index_observed.png',
            dpi=300, bbox_inches='tight')
print("✓ Saved historical data visualization")
print(f"\nPre-ChatGPT decline: {rate_pre:.3f} points/year")
print(f"Post-ChatGPT decline: {rate_post:.3f} points/year")
print(f"Acceleration: {acceleration:.1f}%")
