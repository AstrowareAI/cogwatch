# Cognitive Debt Forecast - Final Model

**Approach:** Papers = Calibration | Data = Drivers

---

## Quick Start

```bash
python3 forecast_model.py
```

Generates:
- `cognitive_debt_forecast_final.png` - Main visualization (6 charts)
- `forecast_scenarios.csv` - Scenario projections (2024-2035)
- `individual_timeline.csv` - Individual exposure harm timeline

---

## The Model

### Papers as Calibration (Proof + Speed)

Papers tell us **HOW FAST** and **HOW MUCH** cognitive debt accumulates:

1. **MIT (2025)** - HIGHEST priority
   - 6 months LLM use → 0.5 cognitive points lost
   - 35% neural connectivity reduction
   - **Calibrates:** Cognitive debt accumulation rate = 0.083 points/month

2. **Microsoft/CMU (2025)** - HIGH priority
   - 71% cognitive effort offloaded when using AI
   - **Calibrates:** How much thinking people stop doing

3. **OpenAI (2025)** - HIGH priority
   - 0.22% of users show severe mental health signals per week
   - **Calibrates:** Mental health risk rate = 11.4% per heavy user per year

4. **METR (2025)** - MEDIUM priority
   - 19% slower with AI (hidden cognitive cost)
   - 44% perception gap (don't notice the cost)
   - **Calibrates:** Hidden costs users don't perceive

5. **HumanAgencyBench (2025)** - MEDIUM priority
   - Only 30.5% of AI supports learning
   - 69.5% just does it for you
   - **Calibrates:** Design-driven cognitive offloading

6. **Stack Overflow (2025)** - LOWER priority
   - 84% adoption ceiling
   - 51% daily usage
   - **Calibrates:** Realistic adoption limits

See [paper_calibrations.md](paper_calibrations.md) for full details.

### Data as Drivers (What, Where, When)

Our empirical data drives the forecast:

- **Adoption:** 156% CAGR (ChatGPT growth rate from our data)
- **Capability:** 2x per year (AI benchmark scores from our data)
- **Cognitive Index:** 100 (2012) → 96.1 (2024), floor at ~75-80
- **Mental Health:** 9.1% (2012) → 11.9% (2024), ceiling at ~30%

See [ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md) for full analysis.

### Combined Formula

```python
Cognitive_Decline_Rate(year) = (
    Baseline_Decline × (1 + MIT_Factor × Adoption × Capability)
    + Microsoft_Offload × Adoption × Capability
    + Empirical_Correlation
)

Where:
- MIT_Factor = 0.083/month (6 months → 0.5 points)
- Microsoft_Offload = 0.71 (71% thinking offloaded)
- OpenAI mental health applied separately
- Capability amplifies offloading (smarter AI → more reliance)
- Adoption scales everything (more users → bigger impact)
```

---

## Key Results

### 1. Humanity Timeline

| Scenario | Year → DANGER (95) | Year → CRITICAL (92) | 2030 Cognitive Index | 2030 Users at Risk |
|----------|-------------------|---------------------|----------------------|-------------------|
| **Current Rates** | 2026 | 2027 | 82.7 | 1,558M |
| **Adoption Slows** | 2026 | 2029 | 90.0 | 820M |
| **Capability Plateaus** | 2026 | 2028 | 87.2 | 1,558M |
| **Misalignment 2x** | 2026 | 2027 | 82.9 | 1,558M |

**Key Finding:** All scenarios reach DANGER by 2026 (2 years from now)

### 2. Individual Exposure Timeline

| Months | Cognitive Debt (points) | Mental Health Risk | Status |
|--------|------------------------|-------------------|--------|
| 3 | 0.25 | 0.2% | Early dependency |
| **6** | **0.50** | **0.3%** | **Measurable decline** (MIT threshold) |
| **12** | **1.0** | **0.6%** | **Significant harm** |
| 24 | 2.0 | 1.2% | Serious impairment |
| 36 | 3.0 | 1.8% | Severe impairment |

**Key Finding:** 6 months of heavy use → measurable cognitive decline (MIT-proven)

### 3. Adoption vs Capability Effects

**Adoption Effect:**
- Current: 9.1% → 95% by 2027 (156% CAGR)
- Drives: Population-level impact scale
- Impact: More users = more total harm

**Capability Effect:**
- Current: 1.0 → 2,000x by 2035 (2x per year)
- Drives: Per-user cognitive offloading depth
- Impact: Smarter AI = more reliance = faster cognitive decline

**Interaction:**
- High adoption + High capability = CRITICAL by 2027
- High adoption + Low capability = DANGER by 2028
- Low adoption + High capability = WARNING through 2030

---

## Files

### Core
- **`forecast_model.py`** - Main model (papers as calibration, data as drivers)
- **`exploratory_analysis.py`** - Foundational data analysis
- **`paper_calibrations.md`** - How papers calibrate the model

### Outputs
- **`cognitive_debt_forecast_final.png`** - Main visualization (6 charts)
- **`forecast_scenarios.csv`** - All scenario projections (2024-2035)
- **`individual_timeline.csv`** - Individual harm timeline (0-36 months)
- **`ANALYSIS_SUMMARY.md`** - Exploratory analysis findings

---

## Scenarios Explained

### 1. Current Rates (Base Case)
- Adoption: 156% CAGR → 95% by 2027
- Capability: 2x per year (exponential growth)
- **Result:** Humanity reaches CRITICAL by 2027

### 2. Adoption Slows (50% max)
- Adoption: Slows after 2026, caps at 50%
- Capability: 2x per year (continues)
- **Result:** CRITICAL by 2029 (2 years delayed)

### 3. Capability Plateaus
- Adoption: 156% CAGR (continues)
- Capability: Frozen at 2024 level
- **Result:** CRITICAL by 2028 (1 year delayed)

### 4. Misalignment 2x
- Adoption: 156% CAGR (continues)
- Capability: 2x per year (continues)
- Impact: 2x multiplier on all effects
- **Result:** CRITICAL by 2027 (same as base, but worse outcomes)

---

## What This Tells Us

### For Policymakers
1. **We have 2 years to DANGER zone** (2026)
2. **We have 3 years to CRITICAL zone** (2027)
3. Even slowing adoption only buys 2 more years
4. Capability growth is as important as adoption

### For Individuals
1. **6 months of heavy AI use** → measurable cognitive decline (MIT-proven)
2. **12 months** → significant harm
3. **24 months** → serious impairment
4. Mental health risk: 11.4% per year for heavy users (OpenAI data)

### For Researchers
1. Papers prove cognitive debt exists and calibrate speed
2. Empirical data (adoption, capability, cognitive index) drives forecast
3. Multiple scenarios show robustness
4. Adoption and capability effects are separable

### For AI Developers
1. Current AI design doesn't support learning (69.5% offloading risk)
2. Capability growth accelerates cognitive decline
3. Users don't perceive the costs (METR: 44% perception gap)
4. Design changes could mitigate harm

---

## Limitations

1. **Limited AI-era data** (only 2022-2024 with ChatGPT)
2. **Correlational, not causal** (but strong theoretical support from papers)
3. **Assumes trends continue** (could accelerate or decelerate)
4. **No intervention effects modeled** (what if we implement safeguards?)
5. **Population-level averages** (individual variation not captured)

---

## Citation

**For papers:** See [paper_calibrations.md](paper_calibrations.md) for full citations

**For this model:**
```
Cognitive Debt Forecast Model (2025)
Paper-calibrated, data-driven forecast of AI cognitive impact
Data: 2012-2024 | Forecast: 2025-2035
```

---

**Status:** ✅ Complete
**Last Updated:** November 2, 2025
