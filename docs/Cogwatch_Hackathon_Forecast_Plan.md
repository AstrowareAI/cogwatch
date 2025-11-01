# 🧠 Cogwatch: AI Cognitive Harm Early Warning & Forecasting System
**Hackathon:** Apart Research Forecasting Sprint (Oct 31 – Nov 2, 2025)  
**Focus on Track 3 – AI Progress Monitoring & Early Warning Systems**  


---

## 🌍 1. Project Summary

**The Problem**  
Governments and educators are unprepared for how rapidly AI impacts human cognition and mental resilience.  
Social-media harms became visible only after significant societal damage — AI may follow the same trajectory.

**The Goal**  
Build a live + forecasting dashboard that quantifies and projects the urgency of the emerging AI cognitive-harm crisis, combining real-time monitoring with calibrated early warnings.

| Dimension | Purpose |
|------------|----------|
| **Capability** | Tracks AI system progress and benchmark breakthroughs |
| **Harm / Misalignment** | Measures unsafe behaviors, incidents, and emerging risks |
| **Adoption** | Gauges the rate of public, enterprise, and developer AI usage |
| **Policy / Governance** | Captures regulatory responses and protective measures |
| **Cognitive / Health** | Maps AI exposure to cognitive and mental health outcomes |

All indicators are normalized against a **Policy Trigger Threshold = 1.0**, anchored to the **2023 U.S. Surgeon General Advisory on Social Media and Mental Health**.

---

## 🔮 2. Forecasting Component

Cogwatch doesn’t just monitor — it forecasts when the combined cognitive-harm signals will reach the “policy-critical” level.

### Forecast Goals
- **Predict when** each indicator (capability, harm, adoption, cognition) crosses the baseline threshold.  
- **Estimate time-to-harm:** “If current trajectory continues, cognitive harm index = 1.0 in X days.”  
- **Generate real-time alerts** for policymakers and researchers.

### Forecasting Method
1. **Aggregate daily/weekly metrics** from ingestion (e.g., number of new safety incidents, AI adoption index).  
2. **Fit simple trendlines** (linear/exponential using `numpy.polyfit`).  
3. **Project forward** 30–90 days to estimate threshold breach.  
4. **Display forecast bands** and confidence ranges on the dashboard.  
5. **Composite Calibrated Urgency Index (CUI)** = weighted sum of forecasted normalized signals.

### Calibration with Social Media & Mental Health Data
Cogwatch’s threshold and slope parameters are not arbitrary — they’re **calibrated using real-world precedent**:
- The **social-media crisis baseline (2010–2023)** provides a reference for how cognitive harms manifested historically (e.g., depression/suicide upticks vs. platform growth).  
- AI adoption and mental health datasets (from PubMed, WHO, Our World in Data) are used to correlate **AI-related terms and publication spikes** with **known cognitive stress indicators**.
- This yields a transfer function:  
  ```
  Cognitive_Harm_Trend = f(Adoption_Rate, AI_Capability_Acceleration, Mental_Health_Signal)
  ```
- As new AI data feeds in, Cogwatch recalibrates the urgency score against that historical social-media harm curve — turning real-time data into a “how close are we to another crisis” forecast.

---

## 🧱 3. System Overview

```
crawl4ai  →  Chutes.ai (LLM summarization)  →  Sentence-Transformer embeddings
         →  MongoDB Atlas (vector store + JSON)  →  Streamlit Dashboard + Forecast Graphs
```

---

## ⚙️ 4. Data Sources & Priority

| Signal | Primary | Secondary |
|---------|----------|-----------|
| **Capability** | [LLM-Stats](https://llm-stats.com/benchmarks/llm-leaderboard-full) | [MLCommons AILuminate](https://ailuminate.mlcommons.org/benchmarks/general_purpose_ai_chat/1.0-en_us-official-ensemble) |
| **Harm / Misalignment** | [AI Incident DB](https://incidentdatabase.ai/api/graphql) | [SpiralBench](https://eqbench.com/spiral-bench.html) / [Antischeming.ai](https://antischeming.ai) |
| **Safety Depth** | [Anthropic Alignment Blog](https://alignment.anthropic.com) | System Cards (OpenAI + Anthropic) |
| **Adoption** | [PyTrends](https://pypi.org/project/pytrends/) | [Stack Overflow AI Survey 2025](https://survey.stackoverflow.co/2025/ai) |
| **Policy** | [OECD AI Policy API](https://www.oecd.org/en/data/insights/data-explainers/2024/09/api.html) | [TechieRay Regulation Tracker](https://www.techieray.com/GlobalAIRegulationTracker) |
| **Cognitive / Health** | [PubMed API](https://pubmed.ncbi.nlm.nih.gov/) | [arXiv](https://pypi.org/project/arxiv/) / [Semantic Scholar](https://pypi.org/project/semanticscholar/) |

---

## 🧩 5. Ingestion Architecture

- **Crawl & Extract:** [`crawl4ai`](https://github.com/unclecode/crawl4ai)  
- **Summarize:** `Chutes.ai` (OpenAI-compatible cheap inference API)  
- **Vectorize & Dedup:** `sentence-transformers/all-MiniLM-L6-v2` + Mongo vector index  
- **Store:** MongoDB Atlas (with embedding + metadata schema)  
- **Forecast Compute:** `numpy`, `scikit-learn`, `pandas` (light trend fitting)

---

## ⚡ 6. Dashboard & Forecast UI

- Framework: **Streamlit**  
- Tabs:
  1. **Live Signal View** – Current normalized values vs. baseline 1.0  
  2. **Forecast Trends** – Predicted days until threshold breach per signal  
  3. **Composite Urgency Index (CUI)** – Combined risk projection  
  4. **Policy Heatmap** – Country-level readiness vs. risk  

---

## ⏱ 7. Build Phases (1.5 Days)

| Phase | Duration | Focus |
|--------|-----------|--------|
| **1. Setup & Schemas** | 0–8 h | Mongo + crawl4ai + Chutes integration |
| **2. Data Pulls + Trend Fit** | 8–16 h | Ingest 2–3 priority sources, summarize + forecast trends |
| **3. Dashboard MVP** | 16–20 h | Streamlit visualization + CUI projection |

---

## 🧰 8. Key Libraries

`crawl4ai`, `openai` (Chutes endpoint), `sentence-transformers`, `pymongo`, `numpy`, `pandas`, `streamlit`, `hashlib`, `datetime`, `asyncio`

---

## 💡 9. Future Extensions

- Extend calibration with **historical cognitive health datasets** (Google Trends, WHO).  
- Add Bayesian forecasting or ARIMA-based predictive smoothing.  
- Expand to “Governance Track”: policy effectiveness forecasting.  
- Integrate NewsAPI / GDELT for public discourse signals.  

---

**Outcome:**  
Cogwatch forecasts *when* AI-driven cognitive harm signals will reach socially critical thresholds — combining early detection, lightweight forecasting, and real-time interpretability.  
It transforms “concern” into quantifiable, actionable foresight.
