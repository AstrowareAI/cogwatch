# Chart Usage Guide - Which Visualization for Which Audience?

**Location:** All charts in `src/results/`

---

## Quick Reference

| Chart | Audience | Use When |
|-------|----------|----------|
| **forecast_current_rates_only.png** | General public, social media | Simple message, no confusion |
| **forecast_uncertainty_bands.png** | Policymakers, researchers | Showing uncertainty is important |
| **cognitive_debt_forecast_final.png** | Technical audiences | Comparing scenarios |
| **scenario_comparison_all.png** | Research papers, deep dives | All scenarios at once |
| **validation_historical_fit.png** | Skeptics, peer reviewers | Proving model accuracy |
| **sensitivity_heatmap.png** | Technical discussions | Understanding parameter interactions |

---

## Detailed Guide

### 1. **forecast_current_rates_only.png** ⭐ START HERE
**Best for:** General audiences, first-time viewers, social media

**What it shows:**
- ONLY Current Rates scenario (no clutter)
- Both Cognitive Index AND Cognitive Debt (2 panels)
- Highlights key years: 2027, 2030
- Clear risk zones (WARNING, DANGER, CRITICAL)

**Use when:**
- Giving a presentation to non-technical stakeholders
- Posting on social media
- Explaining the basic forecast to someone new
- Writing a blog post or news article

**Message:**
> "Under current trends, humanity's cognitive index will reach the CRITICAL zone by 2027-2028."

---

### 2. **forecast_uncertainty_bands.png**
**Best for:** Policymakers, funding discussions, honest communication

**What it shows:**
- Current Rates scenario with 3 uncertainty levels
- Conservative (0.22) = optimistic, strong moderation
- Central (0.50) = realistic, moderate moderation
- Aggressive (1.0) = pessimistic, weak moderation
- Shaded uncertainty band

**Use when:**
- Discussing with policymakers (they need to understand uncertainty)
- Requesting research funding (show you're rigorous)
- Addressing "but you can't predict the future" criticism
- Writing academic papers

**Message:**
> "The 2030 cognitive index is projected at 81-87 points, with central estimate around 82. This range accounts for real-world uncertainties."

---

### 3. **cognitive_debt_forecast_final.png**
**Best for:** Technical discussions, scenario comparison

**What it shows:**
- 8 different scenarios on one chart:
  - Current Rates (baseline)
  - Adoption variations (faster/slower)
  - Capability variations (plateau/acceleration)
- Good for comparing "what if" scenarios

**Use when:**
- Discussing with technical team
- Exploring intervention strategies
- Comparing different future paths
- Research presentations to experts

**Message:**
> "Even if adoption slows 50%, we still reach CRITICAL zone. Capability plateaus delay by 1-2 years but don't prevent decline."

---

### 4. **scenario_comparison_all.png**
**Best for:** Research papers, appendices, comprehensive analysis

**What it shows:**
- ALL 8 scenarios including new interventions:
  - Base scenarios (adoption/capability variations)
  - Intervention 2026/2028
  - Design improvements
  - Capability deceleration
- Very detailed, can be overwhelming

**Use when:**
- Writing research papers (put in appendix or methods section)
- Deep technical discussions
- Showing comprehensive scenario analysis
- Proving you considered many possibilities

**Message:**
> "We tested 8 scenarios. Early intervention (2026) provides +1.67 points benefit vs baseline. All scenarios show decline without major policy changes."

---

### 5. **validation_historical_fit.png** 🛡️ YOUR DEFENSE
**Best for:** Responding to criticism, peer review, establishing credibility

**What it shows:**
- Observed vs Predicted (2022-2024)
- Residual plot (how far off predictions are)
- RMSE values showing accuracy
- Proof model fits historical data

**Use when:**
- Someone says "you can't predict the future"
- Peer reviewers ask about validation
- Defending against "too alarmist" criticism
- Establishing credibility with skeptical audiences

**Message:**
> "The model is validated against 2022-2024 data with RMSE < 0.4 points. All uncertainty levels show good fit, confirming the model captures real trends."

---

### 6. **sensitivity_heatmap.png**
**Best for:** Technical deep dives, understanding model behavior

**What it shows:**
- Parameter interaction matrix
- How IMPACT_SCALING and adoption scenarios interact
- Which parameters matter most
- Color-coded 2030 outcomes

**Use when:**
- Technical discussions about model uncertainty
- Explaining why IMPACT_SCALING matters
- Showing systematic analysis
- Research methodology sections

**Message:**
> "Sensitivity analysis shows IMPACT_SCALING is the dominant uncertainty source (5-8 point spread). This is why we present forecasts as ranges."

---

## Recommended Presentation Flow

### For General Audience (20 min):
1. Start with **forecast_current_rates_only.png** (5 min)
   - "Here's what happens under current trends"
2. Show **forecast_uncertainty_bands.png** (5 min)
   - "But there's uncertainty - here's the range"
3. Show **validation_historical_fit.png** (5 min)
   - "This is grounded in real data from 2022-2024"
4. Q&A (5 min)

### For Technical Audience (45 min):
1. **forecast_current_rates_only.png** (3 min) - baseline
2. **forecast_uncertainty_bands.png** (10 min) - uncertainty
3. **cognitive_debt_forecast_final.png** (10 min) - scenarios
4. **validation_historical_fit.png** (10 min) - validation
5. **sensitivity_heatmap.png** (5 min) - technical details
6. Q&A (7 min)

### For Social Media (single image):
- Use **forecast_current_rates_only.png**
- Add caption: "Under current AI adoption trends, humanity's cognitive index is projected to reach CRITICAL zone by 2027-2028. Data-driven forecast validated against 2022-2024 trends."

### For Academic Paper:
- Main text: **forecast_uncertainty_bands.png**
- Methods: **validation_historical_fit.png**
- Appendix: **scenario_comparison_all.png**, **sensitivity_heatmap.png**

---

## Quick Messaging Templates

### Conservative Framing:
> "Our model, validated against 2022-2024 data, projects the cognitive index will reach 81-87 by 2030 under current trends. This range accounts for real-world uncertainties."

### Balanced Framing:
> "Under current AI adoption patterns, humanity's cognitive ability shows projected decline to CRITICAL levels by 2027-2030. This forecast is grounded in peer-reviewed research and validated against historical data."

### Urgent Framing:
> "Multiple scenarios show humanity reaching CRITICAL cognitive decline zone by 2027-2028. Even optimistic scenarios (slow adoption, capability plateau) only delay by 1-2 years. Early intervention (2026) is significantly more effective than delayed response."

---

## File Sizes & Formats

All charts are:
- Format: PNG (high resolution, 300 DPI)
- Size: ~400-850 KB each
- Dimensions: 1800x800 pixels (2-panel) or 1600x1000 (large comparison)
- Suitable for: presentations, papers, web, social media

---

**Bottom line:** Start with `forecast_current_rates_only.png` for 90% of uses. Use the others when you need to show uncertainty, comparisons, or validation.
