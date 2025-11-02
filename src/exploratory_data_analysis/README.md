# Exploratory Data Analysis

**Purpose:** Comprehensive analysis of relationships between AI adoption, social media usage, mental health, and cognitive decline.

---

## Quick Start

```bash
python src/exploratory_data_analysis/exploratory_analysis.py
```

**Generates (saved to `src/results/`):**
- `exploratory_analysis_comprehensive.png` - 9-panel visualization dashboard

---

## What This Analysis Does

1. **Population Normalization** - Normalizes social media and ChatGPT adoption by global population
2. **Growth Factor Analysis** - Calculates CAGR for social media (8.5%) and ChatGPT (156.32%)
3. **Correlation Analysis** - Identifies relationships between variables
4. **Social Media & Mental Health** - Quantifies R²=0.829 relationship
5. **AI Adoption & Cognitive Decline** - Analyzes 2022-2024 decline pattern
6. **Visualization** - Creates comprehensive dashboard

---

## Key Findings

See [ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md) for complete findings.

**Key Numbers:**
- ChatGPT CAGR: 156.32% (vs Social Media: 8.50%)
- Cognitive Index: 100 (2012) → 96.1 (2024)
- Mental Health: 9.1% (2012) → 11.9% (2024)
- Social Media → Mental Health: R² = 0.829

---

## Files

- `exploratory_analysis.py` - Main analysis script
- `ANALYSIS_SUMMARY.md` - Complete analysis findings and methodology
- `README.md` - This file

**Output Files (in `src/results/`):**
- `exploratory_analysis_comprehensive.png` - Visualization dashboard

---

## Data Source

Input data: `src/data/Collated_data.xlsx`

Requires sheets:
- ChatGPT Growth Rates
- Mental health
- Population
- Social Media
- Cognitive Ability Index
- AI Capability in completing lon
- AI Incidents
- SCREEN_TIME_USAGE_HOURS

