# Paper Calibrations for Cognitive Debt Model

## Purpose
Papers provide **proof cognitive debt exists** and **calibration for speed/magnitude**.
Our empirical data (adoption, capability, cognitive index) drives the actual forecast.

---

## 1. MIT (2025) - Neural Connectivity & Cognitive Debt
**Priority: HIGHEST** - Direct brain measurements, controlled experiment

**What they measured:**
- 54 participants, EEG brain scans during essay writing
- LLM group vs Search vs Brain-only over 3-4 sessions

**Calibration values:**
- **6 months of LLM use → 35% neural connectivity reduction**
- **6 months → 45% memory/ownership loss**
- Brain-only > Search > LLM in connectivity

**Calibration factor for model:**
```
Cognitive_Debt_Rate = 0.5 points per 6 months of heavy use
                    = 0.083 points per month
                    = 1.0 points per year (heavy user)
```

**What this proves:** Cognitive debt is real, measurable in brain, happens in MONTHS not years.

---

## 2. Microsoft/CMU (2025) - Critical Thinking Reduction
**Priority: HIGH** - Large sample, quantified cognitive effort

**What they measured:**
- 319 knowledge workers, 936 task examples
- Self-reported cognitive effort across 6 domains (Bloom's taxonomy)

**Calibration values:**
- **71% average reduction in cognitive effort** when using GenAI
- Knowledge: 72% less, Comprehension: 79%, Application: 69%, Analysis: 72%, Synthesis: 76%, Evaluation: 55%
- Trust in AI → less critical thinking (β = -0.12)

**Calibration factor for model:**
```
Cognitive_Offloading = 0.71 (71% of thinking offloaded to AI)
Effort_Multiplier = (1 - 0.71 × adoption × capability_normalized)
```

**What this proves:** People stop engaging cognitive processes when AI is available. Disuse atrophy.

---

## 3. OpenAI (2025) - Mental Health Prevalence
**Priority: HIGH** - Real-world data, millions of users

**What they measured:**
- Internal ChatGPT conversation data
- Detection of mental health signals at scale

**Calibration values:**
- **0.07% of weekly users show psychosis/mania signals**
- **0.15% show suicidal intent signals**
- **0.22% combined severe mental health signals per week**

**Calibration factor for model:**
```
Mental_Health_Risk = 0.0022 per user per week
Annual_Risk = 0.0022 × 52 = 11.4% chance per heavy user per year
Population_Impact = Total_Users × 0.0022
```

**What this proves:** Mental health impact is measurable and significant at population scale.

---

## 4. METR (2025) - Hidden Cognitive Cost
**Priority: MEDIUM** - Gold RCT but small sample (n=16)

**What they measured:**
- 16 experienced developers, real issues on their repos
- AI-allowed (Cursor + Claude) vs AI-disallowed, randomized

**Calibration values:**
- **-19% productivity** (developers 19% SLOWER with AI)
- **Expectation gap: 44%** (expected +24% speed, got -19%)
- Perception completely mismatched with reality

**Calibration factor for model:**
```
Hidden_Cost = 0.19 (tasks take 19% longer)
Perception_Gap = 0.44 (people don't notice)
Overconfidence_Factor = 1.44 (think 1.44x faster, actually 0.81x)
```

**What this proves:** AI has hidden cognitive costs users don't perceive. Dangerous.

---

## 5. HumanAgencyBench (2025) - AI Design Flaws
**Priority: MEDIUM** - Systematic evaluation of AI systems

**What they measured:**
- 20 LLMs tested on 6 agency dimensions
- 3,000 tests per model

**Calibration values:**
- **Only 30.5% encourage learning** (most AI just gives answers)
- **Only 38.7% defer important decisions** (AI decides for you)
- **69.5% cognitive offloading risk** (100% - 30.5%)

**Calibration factor for model:**
```
Learning_Support = 0.305 (only 30.5% of AI helps you learn)
Offloading_Risk = 0.695 (69.5% just does it for you)
Agency_Erosion = 1 - 0.387 = 0.613 (61.3% don't help you decide)
```

**What this proves:** Current AI is designed to DO FOR YOU, not TEACH YOU. Skill atrophy by design.

---

## 6. Stack Overflow (2025) - Adoption Reality
**Priority: LOWER** - Large survey but self-reported, no cognitive measurement

**What they measured:**
- 49K+ developers surveyed on AI usage

**Calibration values:**
- **84% use or plan to use AI**
- **51% use daily**
- **46% distrust AI accuracy** (but use anyway)
- **40% say AI fails at complex tasks**

**Calibration factor for model:**
```
Adoption_Ceiling = 0.84 (realistic maximum)
Daily_Usage_Rate = 0.51 (heavy user baseline)
Trust_Disconnect = 0.46 (use despite distrust)
```

**What this proves:** Adoption is high, usage is daily, people use AI they don't trust. Behavioral pattern concern.

---

## How Calibrations Map to Model

### Individual Exposure Timeline
Based on MIT + Microsoft + OpenAI:

| Months | Cognitive Debt | Mental Health Risk | Status |
|--------|----------------|-------------------|--------|
| 3 | 0.25 points | 2.9% | Early dependency |
| 6 | 0.50 points (MIT) | 5.7% | Measurable decline |
| 12 | 1.0 points | 11.4% (OpenAI) | Significant harm |
| 24 | 2.0 points | 23% | Serious impairment |

### Population Impact
```
Cognitive_Decline_Rate(t) =
    Baseline_Rate × (1 + MIT_Factor × Adoption(t) × Capability(t))
    + Microsoft_Offload × Adoption(t) × Capability(t)
    + Correlation_Factor

Where:
- MIT_Factor = 0.083/month cognitive debt accumulation
- Microsoft_Offload = 0.71 thinking offload percentage
- OpenAI mental health applied separately
- METR hidden cost compounds over time
- HumanAgency design flaw amplifies all effects
```

### Capability Amplification
```
Capability(t) affects cognitive offloading:
- Better AI → more tasks offloaded (Microsoft 71%)
- More offloading → faster cognitive decline (MIT 6mo)
- Smarter AI → harder to notice problems (METR 44% gap)
```

### Adoption Amplification
```
Adoption(t) scales everything:
- More users → more mental health cases (OpenAI 0.22%)
- More usage → more cognitive debt accumulation (MIT)
- Higher adoption → higher societal baseline shift
```

---

## Summary

**Papers tell us HOW FAST and HOW MUCH:**
- MIT: 6 months → 0.5 cognitive points
- Microsoft: 71% cognitive effort offloaded
- OpenAI: 0.22% severe mental health per week
- METR: 19% hidden time cost, 44% perception gap
- HumanAgency: 69.5% of AI doesn't support learning
- Stack Overflow: 84% adoption ceiling, 51% daily use

**Data tells us WHERE and WHEN:**
- Adoption: 156% CAGR → 95% by 2027
- Capability: Exponential growth (0.04→100+ hours)
- Cognitive Index: 100 (2012) → 96.1 (2024) → floor at ~75-80
- Mental Health: 9.1% (2012) → 11.9% (2024) → ceiling at ~30%

**Model combines them:**
- Papers calibrate speed/magnitude
- Data drives trajectory
- Scenarios test sensitivity
