"""
Cognitive Debt Forecast Model
==============================

Papers = Calibration (prove it exists, tell us HOW FAST)
Data = Drivers (adoption, capability, cognitive index)
Model = Data-driven, paper-calibrated

Outputs:
1. Humanity timeline to critical (clean chart)
2. Scenarios: current, capability plateau, adoption slow, misalignment
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style("whitegrid")

# ============================================================================
# PAPER CALIBRATIONS (Proof + Speed/Magnitude)
# ============================================================================

class PaperCalibrations:
    """What papers tell us about speed and magnitude"""

    # MIT (2025) - Neural Connectivity
    MIT_COGNITIVE_DEBT_PER_6_MONTHS = 0.5  # cognitive index points
    MIT_COGNITIVE_DEBT_PER_MONTH = 0.083   # per month heavy use
    MIT_NEURAL_REDUCTION = 0.35            # 35% connectivity reduction
    MIT_MEMORY_LOSS = 0.45                 # 45% memory/ownership loss

    # Microsoft/CMU (2025) - Critical Thinking
    MSFT_COGNITIVE_OFFLOAD = 0.71          # 71% effort offloaded
    MSFT_TRUST_NEGATIVE_BETA = -0.12       # trust → less thinking

    # OpenAI (2025) - Mental Health
    OPENAI_MENTAL_HEALTH_RATE_PER_WEEK = 0.0022  # 0.22% severe signals
    OPENAI_ANNUAL_RISK = 0.0022 * 52              # 11.4% per year

    # METR (2025) - Hidden Cost
    METR_PRODUCTIVITY_PENALTY = 0.19       # 19% slower
    METR_PERCEPTION_GAP = 0.44             # 44% overestimate

    # HumanAgencyBench (2025) - Design Flaw
    HAB_LEARNING_SUPPORT = 0.305           # only 30.5% support learning
    HAB_OFFLOADING_RISK = 0.695            # 69.5% risk

    # Stack Overflow (2025) - Adoption
    SO_ADOPTION_CEILING = 0.84             # 84% realistic max
    SO_DAILY_USAGE = 0.51                  # 51% use daily

    # Model Robustness & Correction Factors
    # These account for real-world variability, non-linear effects, and model uncertainty

    # DEFAULT values - can be overridden in __init__ for uncertainty analysis
    DEFAULT_IMPACT_SCALING = 0.22          # Correction factor: Accounts for (1) Individual vs population effects
                                           # (papers measure heavy users, model needs population average),
                                           # (2) Non-linear/additive assumption uncertainties (MIT+MSFT+HAB may overlap),
                                           # (3) Real-world moderators (adaptation, regulations, awareness campaigns),
                                           # (4) Scenario buffers (slower adoption, capability plateaus, policy interventions)
                                           # Acts as robustness buffer: if rates slow or capability growth moderates,
                                           # this scaling provides conservative margin

    DEFAULT_RESILIENCE_STRENGTH = 0.55     # Biological resilience activation factor: Accounts for (1) Individual variation
                                           # in cognitive resilience, (2) Adaptive responses as cognitive load increases,
                                           # (3) Compensatory mechanisms (behavioral adjustments, awareness, intervention),
                                           # (4) Model uncertainty in extreme scenarios
                                           # Higher value = stronger resilience response (more gradual decline under stress)
                                           # Acts as correction for non-linear biological limits and human adaptability

    def __init__(self, impact_scaling=None, resilience_strength=None):
        """
        Allow overriding scaling factors for uncertainty analysis

        Args:
            impact_scaling: Override IMPACT_SCALING (default 0.22)
                - 0.22 = conservative (lower bound)
                - 0.50 = central estimate
                - 1.0 = aggressive (full paper effects, upper bound)
            resilience_strength: Override RESILIENCE_STRENGTH (default 0.55)
        """
        self.IMPACT_SCALING = impact_scaling if impact_scaling is not None else self.DEFAULT_IMPACT_SCALING
        self.RESILIENCE_STRENGTH = resilience_strength if resilience_strength is not None else self.DEFAULT_RESILIENCE_STRENGTH


# ============================================================================
# DATA DRIVERS (From Exploratory Analysis)
# ============================================================================

class DataDrivers:
    """What our data tells us about trends"""

    # Adoption Growth
    CHATGPT_CAGR = 1.5632                  # 156.32% annual growth
    CURRENT_ADOPTION_2024 = 0.091          # 9.1%

    # Cognitive Index
    COGNITIVE_INDEX_2024 = 96.1            # Current level
    COGNITIVE_INDEX_2012 = 100.0           # Baseline
    COGNITIVE_INDEX_2020 = 98.0            # Pre-ChatGPT (2020)
    COGNITIVE_RESILIENCE_THRESHOLD = 84.0  # Below this, resilience kicks in gradually
    COGNITIVE_INDEX_FLOOR = 80.0            # Smooth asymptotic floor (~80-82)
    COGNITIVE_INDEX_ASYMPTOTE_STEEPNESS = 0.15  # Controls how smoothly it approaches floor (higher = smoother)
    BASELINE_DECLINE_RATE = 0.35           # Pre-AI: 0.35 points/year

    # Mental Health
    MENTAL_HEALTH_2024 = 0.119             # 11.9%
    MENTAL_HEALTH_2012 = 0.091             # 9.1%
    MENTAL_HEALTH_CEILING = 0.30           # Realistic ceiling (30%)

    # AI Capability (normalized 0-1)
    # From 0.04 hours (2019) → 100+ hours (2025)
    # Exponential growth: ~3x per year
    CAPABILITY_GROWTH_RATE = 2.0           # Doubles every year
    CAPABILITY_2024 = 1.0                  # Normalized to 1.0 in 2024

    # Empirical Acceleration
    POST_AI_ACCELERATION = 1.57            # 57% faster decline post-2022


# ============================================================================
# FORECAST MODEL
# ============================================================================

class CognitiveDebtModel:
    """Main forecast model: data-driven, paper-calibrated"""

    def __init__(self, impact_scaling=None, resilience_strength=None):
        """
        Initialize model with optional parameter overrides for uncertainty analysis

        Args:
            impact_scaling: Override IMPACT_SCALING (default 0.22)
                - 0.22 = conservative (current model, lower bound)
                - 0.50 = central estimate (moderate real-world effects)
                - 1.0 = aggressive (full paper effects, upper bound)
            resilience_strength: Override RESILIENCE_STRENGTH (default 0.55)
        """
        self.cal = PaperCalibrations(impact_scaling, resilience_strength)
        self.data = DataDrivers()
        self.global_population = 8.2  # billion

    def adoption(self, year, scenario="current"):
        """Calculate AI adoption for given year and scenario"""
        years = year - 2024

        # Handle years before 2024
        if year < 2024:
            # Pre-ChatGPT era (2020-2024)
            if year < 2022:
                return 0.0  # No ChatGPT yet
            elif year == 2022:
                return 0.01  # 1% (launch year H2)
            elif year == 2023:
                return 0.04  # 4% (growing)
            else:
                return self.data.CURRENT_ADOPTION_2024

        if scenario == "slow_10":
            growth_rate = self.data.CHATGPT_CAGR * 0.9
            adoption = self.data.CURRENT_ADOPTION_2024 * (1 + growth_rate) ** years
            return min(adoption, 0.90)

        elif scenario == "slow_20":
            growth_rate = self.data.CHATGPT_CAGR * 0.8
            adoption = self.data.CURRENT_ADOPTION_2024 * (1 + growth_rate) ** years
            return min(adoption, 0.85)

        elif scenario == "slow_50":
            growth_rate = self.data.CHATGPT_CAGR * 0.5
            adoption = self.data.CURRENT_ADOPTION_2024 * (1 + growth_rate) ** years
            return min(adoption, 0.70)

        elif scenario == "accel_1.2x":
            # 20% faster adoption
            growth_rate = self.data.CHATGPT_CAGR * 1.2
            adoption = self.data.CURRENT_ADOPTION_2024 * (1 + growth_rate) ** years
            return min(adoption, 0.97)  # Higher ceiling for faster adoption

        elif scenario == "accel_1.5x":
            # 50% faster adoption
            growth_rate = self.data.CHATGPT_CAGR * 1.5
            adoption = self.data.CURRENT_ADOPTION_2024 * (1 + growth_rate) ** years
            return min(adoption, 0.98)  # Higher ceiling for faster adoption

        elif scenario == "accel_2x":
            # 2x faster adoption
            growth_rate = self.data.CHATGPT_CAGR * 2.0
            adoption = self.data.CURRENT_ADOPTION_2024 * (1 + growth_rate) ** years
            return min(adoption, 0.99)  # Higher ceiling for faster adoption

        elif scenario == "intervention_2026":
            # Policy response kicks in 2026: awareness campaigns, regulations
            # Growth continues until 2026, then slows dramatically
            if year <= 2026:
                adoption = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** min(years, 2)
            else:
                # After 2026: growth rate drops to 25% (was 156%)
                adoption_2026 = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** 2
                years_after = year - 2026
                adoption = adoption_2026 * (1 + 0.25) ** years_after
            return min(adoption, 0.70)  # Lower ceiling with intervention

        elif scenario == "intervention_2028":
            # Delayed policy response (2028)
            if year <= 2028:
                adoption = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** min(years, 4)
            else:
                adoption_2028 = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** 4
                years_after = year - 2028
                adoption = adoption_2028 * (1 + 0.25) ** years_after
            return min(adoption, 0.75)

        # Default: current rates
        adoption = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** years
        return min(adoption, 0.95)

    def capability(self, year, scenario="current"):
        """Calculate AI capability for given year (normalized to 2024=1.0)"""
        years = year - 2024

        if scenario == "capability_plateau_2026":
            # Plateau at 2026 level
            years_capped = min(years, 2)
            return self.data.CAPABILITY_2024 * (self.data.CAPABILITY_GROWTH_RATE ** years_capped)

        elif scenario == "capability_plateau_2028":
            # Plateau at 2028 level
            years_capped = min(years, 4)
            return self.data.CAPABILITY_2024 * (self.data.CAPABILITY_GROWTH_RATE ** years_capped)

        elif scenario == "capability_accel_1.5x":
            # 1.5x faster capability growth (3x per year instead of 2x)
            accel_rate = self.data.CAPABILITY_GROWTH_RATE * 1.5
            return self.data.CAPABILITY_2024 * (accel_rate ** years)

        elif scenario == "capability_deceleration":
            # Gradual slowdown: starts at 2x, decreases over time
            # 2024-2026: 2x per year
            # 2026-2028: 1.5x per year
            # 2028-2030: 1.2x per year
            # 2030+: 1.1x per year
            if years <= 0:
                return self.data.CAPABILITY_2024

            # Calculate cumulative capability
            capability = self.data.CAPABILITY_2024
            for y in range(1, int(years) + 1):
                age = y
                if age <= 2:
                    capability *= 2.0
                elif age <= 4:
                    capability *= 1.5
                elif age <= 6:
                    capability *= 1.2
                else:
                    capability *= 1.1

            return capability

        # Default: current rates
        return self.data.CAPABILITY_2024 * (self.data.CAPABILITY_GROWTH_RATE ** years)

    def cognitive_decline_rate(self, year, adoption_rate, capability_level, current_index, scenario="current"):
        """Calculate cognitive decline rate (points per year)"""

        # Base decline (pre-AI baseline)
        base = self.data.BASELINE_DECLINE_RATE

        # MIT calibration: 0.083 points/month per heavy user
        # Capability effect with logarithmic scaling (prevents extreme growth)
        mit_factor = (
            self.cal.MIT_COGNITIVE_DEBT_PER_MONTH * 12 *
            adoption_rate *
            min(np.log1p(capability_level) * 2.5, 10.0)  # log scaling, cap at 10
        )

        # Microsoft calibration: 71% cognitive offloading
        # Stronger capability effect to differentiate scenarios
        # Design improvement scenario reduces offloading
        if scenario == "design_improvement_2026":
            # After 2026, AI design improves to support learning
            # HumanAgencyBench "Encourage Learning" goes from 30.5% → 60%
            # This reduces effective cognitive offload by 40%
            if year >= 2026:
                design_multiplier = 0.6  # 40% reduction in offloading
            else:
                design_multiplier = 1.0
        else:
            design_multiplier = 1.0

        msft_factor = (
            self.cal.MSFT_COGNITIVE_OFFLOAD *
            adoption_rate *
            (np.log1p(capability_level) * 0.8) *
            design_multiplier  # Apply design improvement
        )

        # HumanAgencyBench: 69.5% risk
        hab_factor = (
            self.cal.HAB_OFFLOADING_RISK *
            adoption_rate *
            0.3
        )

        # Empirical acceleration
        empirical = base * (self.data.POST_AI_ACCELERATION - 1) * adoption_rate

        # Misalignment scenario: double the impact
        multiplier = 2.0 if scenario == "misalignment" else 1.0

        # Apply IMPACT_SCALING correction factor: Acts as robustness buffer
        # Accounts for real-world moderators: slower adoption rates, capability growth moderation,
        # policy interventions, awareness campaigns, individual variation (heavy vs light users),
        # and model uncertainty in additive assumptions. This prevents alarmist projections while
        # maintaining data-driven grounding.
        total_decline = base + (mit_factor + msft_factor + hab_factor + empirical) * multiplier * self.cal.IMPACT_SCALING

        # Biological resilience: gradual, smooth slowdown below 84
        # Uses sigmoid-like function for smooth transition (no sharp step)
        if current_index < self.data.COGNITIVE_RESILIENCE_THRESHOLD:
            # Distance below threshold (0 to 4, since floor is 80)
            distance_below = self.data.COGNITIVE_RESILIENCE_THRESHOLD - current_index
            max_distance = self.data.COGNITIVE_RESILIENCE_THRESHOLD - self.data.COGNITIVE_INDEX_FLOOR

            # RESILIENCE_STRENGTH activation: Acts as biological resilience correction factor
            # Accounts for adaptive responses, compensatory mechanisms, individual variation in
            # cognitive resilience, and non-linear biological limits. As stress increases (lower index),
            # resilience activation increases (slower decline rate). This acts as a robustness buffer
            # for scenarios where adaptation, awareness, or intervention moderate decline.
            # Resilience factor: stronger as you go lower (0.1 to 1.0)
            # At 84: factor = 1.0 (no slowdown)
            # At 82 (halfway): factor ~0.5 (50% slower)
            # At 80: factor ~0.1 (90% slower, then asymptotic decay takes over)
            resilience_factor = 1.0 - (self.cal.RESILIENCE_STRENGTH * (distance_below / max_distance))
            resilience_factor = max(0.05, resilience_factor)  # Never fully stops (biological floor)

            total_decline *= resilience_factor

        # Cap at 5.0 points/year max (increased to allow scenario differentiation)
        return min(total_decline, 5.0)

    def mental_health_rate(self, year, adoption_rate, cognitive_index):
        """Calculate mental health prevalence"""

        # OpenAI calibration: 0.22% severe signals per week
        # Scale to annual and by total users
        users = adoption_rate * self.global_population
        annual_risk = self.cal.OPENAI_ANNUAL_RISK
        new_cases = users * annual_risk / self.global_population

        # Coupling with cognitive decline
        cognitive_decline_total = self.data.COGNITIVE_INDEX_2012 - cognitive_index
        cognitive_coupling = cognitive_decline_total * 0.003  # 0.3% per point

        # Start from current baseline
        prevalence = self.data.MENTAL_HEALTH_2024 + new_cases + cognitive_coupling

        # Cap at ceiling
        return min(prevalence, self.data.MENTAL_HEALTH_CEILING)

    def run_scenario(self, scenario="current", start_year=2020, end_year=2035):
        """Run forecast for a given scenario"""

        results = {
            'year': [],
            'adoption': [],
            'capability': [],
            'cognitive_index': [],
            'cognitive_debt': [],
            'mental_health': [],
            'decline_rate': [],
            'users_at_risk_millions': []
        }

        # Start from 2020 to show baseline
        current_cognitive = self.data.COGNITIVE_INDEX_2020

        for year in range(start_year, end_year + 1):
            # Calculate drivers
            adopt = self.adoption(year, scenario)
            cap = self.capability(year, scenario)

            # Calculate decline rate
            decline = self.cognitive_decline_rate(year, adopt, cap, current_cognitive, scenario)

            # Update cognitive index (with smooth asymptotic approach to floor)
            if year > start_year:
                # Calculate distance from floor
                distance_from_floor = current_cognitive - self.data.COGNITIVE_INDEX_FLOOR
                
                # Apply smooth exponential decay as we approach the floor
                # As distance_from_floor approaches 0, decay_multiplier approaches 0
                # This creates smooth asymptotic behavior (no sudden step)
                if distance_from_floor > 0:
                    # Exponential decay: steeper = smoother approach to floor
                    decay_multiplier = 1.0 - np.exp(-self.data.COGNITIVE_INDEX_ASYMPTOTE_STEEPNESS * distance_from_floor)
                    # Ensure we never go below floor
                    effective_decline = min(decline * decay_multiplier, distance_from_floor)
                    current_cognitive = current_cognitive - effective_decline
                else:
                    # Already at or below floor, maintain floor value
                    current_cognitive = self.data.COGNITIVE_INDEX_FLOOR

            # Calculate cognitive debt (inverse of index)
            cognitive_debt = self.data.COGNITIVE_INDEX_2012 - current_cognitive

            # Calculate mental health
            mh = self.mental_health_rate(year, adopt, current_cognitive)

            # Users at risk
            users_at_risk = adopt * self.global_population * 0.20 * 1000

            # Store results
            results['year'].append(year)
            results['adoption'].append(adopt)
            results['capability'].append(cap)
            results['cognitive_index'].append(current_cognitive)
            results['cognitive_debt'].append(cognitive_debt)
            results['mental_health'].append(mh)
            results['decline_rate'].append(decline)
            results['users_at_risk_millions'].append(users_at_risk)

        return pd.DataFrame(results)

    def run_scenario_with_uncertainty(self, scenario="current", start_year=2020, end_year=2035):
        """
        Run scenario with three uncertainty levels

        Args:
            scenario: Which scenario to run (current, slow_50, etc.)
            start_year: Start year for forecast
            end_year: End year for forecast

        Returns:
            dict: {
                'conservative': DataFrame (IMPACT_SCALING=0.22),
                'central': DataFrame (IMPACT_SCALING=0.50),
                'aggressive': DataFrame (IMPACT_SCALING=1.0)
            }
        """
        impact_levels = {
            'conservative': 0.22,  # Current model (lower bound)
            'central': 0.50,       # Moderate estimate
            'aggressive': 1.0      # Full paper effects (upper bound)
        }

        results = {}
        for level_name, scaling in impact_levels.items():
            model = CognitiveDebtModel(impact_scaling=scaling)
            df = model.run_scenario(scenario, start_year, end_year)
            results[level_name] = df

        return results

    def individual_exposure_timeline(self):
        """Calculate individual harm timeline (MIT + OpenAI calibration)"""

        timeline = []
        for months in [0, 3, 6, 12, 18, 24, 36]:
            cognitive_debt = months * self.cal.MIT_COGNITIVE_DEBT_PER_MONTH
            mental_health_risk = (months / 4.33) * self.cal.OPENAI_MENTAL_HEALTH_RATE_PER_WEEK  # weeks

            if months == 0:
                status = "Baseline"
            elif months <= 3:
                status = "Early dependency"
            elif months <= 6:
                status = "Measurable decline"
            elif months <= 12:
                status = "Significant harm"
            elif months <= 24:
                status = "Serious impairment"
            else:
                status = "Severe impairment"

            timeline.append({
                'months': months,
                'cognitive_debt_points': round(cognitive_debt, 2),
                'mental_health_risk_%': round(mental_health_risk * 100, 1),
                'status': status
            })

        return pd.DataFrame(timeline)


# ============================================================================
# VISUALIZATION
# ============================================================================

def create_simple_forecast_chart(model):
    """Create clean, simple chart showing ONLY Current Rates - for general audiences"""

    # Run only current rates scenario
    df = model.run_scenario('current')

    # Create figure - 2 charts side by side
    fig = plt.figure(figsize=(18, 8))

    # CHART 1: Cognitive Index
    ax1 = plt.subplot(1, 2, 1)

    ax1.plot(df['year'], df['cognitive_index'],
             linewidth=4, marker='o', color='darkblue',
             label='Projected Cognitive Index', markersize=6)

    # Risk zones
    ax1.axhline(y=95, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='WARNING (95)')
    ax1.axhline(y=92, color='red', linestyle='--', linewidth=2, alpha=0.7, label='DANGER (92)')
    ax1.axhline(y=88, color='purple', linestyle='--', linewidth=1.5, alpha=0.7, label='CRITICAL (88)')

    ax1.fill_between([2020, 2035], 95, 100, alpha=0.1, color='yellow')
    ax1.fill_between([2020, 2035], 92, 95, alpha=0.1, color='orange')
    ax1.fill_between([2020, 2035], 88, 92, alpha=0.1, color='red')
    ax1.fill_between([2020, 2035], 84, 88, alpha=0.08, color='darkred')

    # Mark ChatGPT launch
    ax1.axvline(x=2022, color='gray', linestyle=':', linewidth=2, alpha=0.5)
    ax1.text(2022, 79, 'ChatGPT\nLaunch', fontsize=10, ha='center', alpha=0.6)

    # Highlight key years
    for year in [2027, 2030]:
        idx_val = df[df['year'] == year]['cognitive_index'].iloc[0]
        ax1.scatter([year], [idx_val], s=200, color='red', zorder=5, edgecolors='white', linewidths=2)
        ax1.text(year, idx_val + 1, f'{year}\n{idx_val:.1f}',
                ha='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Cognitive Index (2012=100)', fontsize=14, fontweight='bold')
    ax1.set_title('Humanity Cognitive Index - Current Rates Projection', fontsize=16, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(2020, 2035)
    ax1.set_ylim(78, 100)

    # CHART 2: Cognitive Debt
    ax2 = plt.subplot(1, 2, 2)

    ax2.plot(df['year'], df['cognitive_debt'],
             linewidth=4, marker='o', color='darkred',
             label='Projected Cognitive Debt', markersize=6)

    # Risk zones (inverted)
    ax2.axhline(y=5, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='WARNING (5)')
    ax2.axhline(y=8, color='red', linestyle='--', linewidth=2, alpha=0.7, label='DANGER (8)')
    ax2.axhline(y=12, color='purple', linestyle='--', linewidth=1.5, alpha=0.7, label='CRITICAL (12)')

    ax2.fill_between([2020, 2035], 0, 5, alpha=0.1, color='yellow')
    ax2.fill_between([2020, 2035], 5, 8, alpha=0.1, color='orange')
    ax2.fill_between([2020, 2035], 8, 12, alpha=0.1, color='red')
    ax2.fill_between([2020, 2035], 12, 25, alpha=0.08, color='darkred')

    # Mark ChatGPT launch
    ax2.axvline(x=2022, color='gray', linestyle=':', linewidth=2, alpha=0.5)
    ax2.text(2022, 2, 'ChatGPT\nLaunch', fontsize=10, ha='center', alpha=0.6)

    # Highlight key years
    for year in [2027, 2030]:
        debt_val = df[df['year'] == year]['cognitive_debt'].iloc[0]
        ax2.scatter([year], [debt_val], s=200, color='red', zorder=5, edgecolors='white', linewidths=2)
        ax2.text(year, debt_val + 1.5, f'{year}\n{debt_val:.1f}',
                ha='center', fontsize=9, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.7))

    ax2.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Cognitive Debt (points)', fontsize=14, fontweight='bold')
    ax2.set_title('Humanity Cognitive Debt - Current Rates Projection', fontsize=16, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(2020, 2035)
    ax2.set_ylim(0, 25)

    plt.tight_layout(pad=2.0)
    plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/forecast_current_rates_only.png',
                dpi=300, bbox_inches='tight')
    print("✓ Saved simple forecast (current rates only)")

    return df


def create_forecast_charts(model):
    """Create focused forecast visualizations - 2 charts only"""

    # Run all scenarios
    scenarios = {
        'Current Rates': model.run_scenario('current'),
        'Adoption 1.2x Faster': model.run_scenario('accel_1.2x'),
        'Adoption 1.5x Faster': model.run_scenario('accel_1.5x'),
        'Adoption 2x Faster': model.run_scenario('accel_2x'),
        'Capability 1.5x Faster': model.run_scenario('capability_accel_1.5x'),
        'Capability Plateau 2026': model.run_scenario('capability_plateau_2026'),
        'Capability Plateau 2028': model.run_scenario('capability_plateau_2028'),
        'Adoption 50% Slower': model.run_scenario('slow_50')
    }

    # Create figure - 2 charts only
    fig = plt.figure(figsize=(18, 8))

    # CHART 1: Cognitive Index Decline (2020-2035)
    ax1 = plt.subplot(1, 2, 1)

    for name, df in scenarios.items():
        ax1.plot(df['year'], df['cognitive_index'], linewidth=2.5, marker='o', label=name, markersize=5)

    # Risk zones
    ax1.axhline(y=95, color='orange', linestyle='--', linewidth=2, alpha=0.7)
    ax1.axhline(y=92, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.axhline(y=88, color='purple', linestyle='--', linewidth=1.5, alpha=0.7)
    ax1.axhline(y=84, color='darkgray', linestyle='--', linewidth=1.5, alpha=0.5)

    ax1.fill_between([2020, 2035], 95, 100, alpha=0.1, color='yellow', label='WARNING')
    ax1.fill_between([2020, 2035], 92, 95, alpha=0.1, color='orange', label='DANGER')
    ax1.fill_between([2020, 2035], 88, 92, alpha=0.1, color='red', label='CRITICAL')
    ax1.fill_between([2020, 2035], 84, 88, alpha=0.08, color='darkred', label='SEVERE')
    ax1.fill_between([2020, 2035], 80, 84, alpha=0.05, color='gray', label='Resilience Zone')

    # Mark ChatGPT launch
    ax1.axvline(x=2022, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax1.text(2022, 79, 'ChatGPT\nLaunch', fontsize=8, ha='center', alpha=0.6)

    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Cognitive Index (2012=100)', fontsize=14, fontweight='bold')
    ax1.set_title('Humanity Cognitive Index Forecast', fontsize=16, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8, ncol=1)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(2020, 2035)
    ax1.set_ylim(78, 100)  # Adjusted to show smooth asymptotic approach to ~80

    # CHART 2: Cognitive Debt Increase (2020-2035)
    ax2 = plt.subplot(1, 2, 2)

    for name, df in scenarios.items():
        ax2.plot(df['year'], df['cognitive_debt'], linewidth=2.5, marker='o', label=name, markersize=5)

    # Risk zones (inverted: 100-84=16, 100-88=12, 100-92=8, 100-95=5)
    ax2.axhline(y=5, color='orange', linestyle='--', linewidth=2, alpha=0.7)
    ax2.axhline(y=8, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax2.axhline(y=12, color='purple', linestyle='--', linewidth=1.5, alpha=0.7)
    ax2.axhline(y=16, color='darkgray', linestyle='--', linewidth=1.5, alpha=0.5)

    ax2.fill_between([2020, 2035], 0, 5, alpha=0.1, color='yellow', label='WARNING')
    ax2.fill_between([2020, 2035], 5, 8, alpha=0.1, color='orange', label='DANGER')
    ax2.fill_between([2020, 2035], 8, 12, alpha=0.1, color='red', label='CRITICAL')
    ax2.fill_between([2020, 2035], 12, 16, alpha=0.08, color='darkred', label='SEVERE')
    ax2.fill_between([2020, 2035], 16, 25, alpha=0.05, color='gray', label='Resilience Zone')

    # Mark ChatGPT launch
    ax2.axvline(x=2022, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax2.text(2022, 2, 'ChatGPT\nLaunch', fontsize=8, ha='center', alpha=0.6)

    ax2.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Cognitive Debt (points)', fontsize=14, fontweight='bold')
    ax2.set_title('Humanity Cognitive Debt Forecast', fontsize=16, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=8, ncol=1)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(2020, 2035)
    ax2.set_ylim(0, 25)  # Adjusted to show smooth asymptotic approach to ~20 (100-80)

    plt.tight_layout(pad=2.0)
    plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/cognitive_debt_forecast_final.png',
                dpi=300, bbox_inches='tight')
    print("✓ Saved forecast visualization")

    return scenarios


def create_uncertainty_visualization(model):
    """Create forecast with uncertainty bands"""

    # Run current scenario with 3 uncertainty levels
    uncertainty_results = model.run_scenario_with_uncertainty('current')

    # Create figure - 2 charts
    fig = plt.figure(figsize=(18, 8))

    # CHART 1: Cognitive Index with Uncertainty Band
    ax1 = plt.subplot(1, 2, 1)

    conservative_df = uncertainty_results['conservative']
    central_df = uncertainty_results['central']
    aggressive_df = uncertainty_results['aggressive']

    years = conservative_df['year']

    # Fill uncertainty band (conservative to aggressive)
    ax1.fill_between(
        years,
        conservative_df['cognitive_index'],
        aggressive_df['cognitive_index'],
        alpha=0.25, color='steelblue', label='Uncertainty Band\n(0.22 → 1.0 scaling)'
    )

    # Plot three lines
    ax1.plot(years, conservative_df['cognitive_index'],
             linewidth=2, linestyle='--', color='green',
             label='Conservative (0.22)', alpha=0.7)
    ax1.plot(years, central_df['cognitive_index'],
             linewidth=3, color='darkblue',
             label='Central Estimate (0.50)')
    ax1.plot(years, aggressive_df['cognitive_index'],
             linewidth=2, linestyle='--', color='red',
             label='Aggressive (1.0)', alpha=0.7)

    # Risk zones
    ax1.axhline(y=95, color='orange', linestyle='--', linewidth=2, alpha=0.7)
    ax1.axhline(y=92, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.axhline(y=88, color='purple', linestyle='--', linewidth=1.5, alpha=0.7)
    ax1.axhline(y=84, color='darkgray', linestyle='--', linewidth=1.5, alpha=0.5)

    ax1.fill_between([2020, 2035], 95, 100, alpha=0.1, color='yellow', label='WARNING')
    ax1.fill_between([2020, 2035], 92, 95, alpha=0.1, color='orange', label='DANGER')
    ax1.fill_between([2020, 2035], 88, 92, alpha=0.1, color='red', label='CRITICAL')
    ax1.fill_between([2020, 2035], 84, 88, alpha=0.08, color='darkred', label='SEVERE')

    # Mark ChatGPT launch
    ax1.axvline(x=2022, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax1.text(2022, 79, 'ChatGPT\nLaunch', fontsize=8, ha='center', alpha=0.6)

    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Cognitive Index (2012=100)', fontsize=14, fontweight='bold')
    ax1.set_title('Cognitive Index Forecast with Uncertainty Bands', fontsize=16, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9, ncol=1)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(2020, 2035)
    ax1.set_ylim(78, 100)

    # CHART 2: Cognitive Debt with Uncertainty Band
    ax2 = plt.subplot(1, 2, 2)

    # Fill uncertainty band
    ax2.fill_between(
        years,
        conservative_df['cognitive_debt'],
        aggressive_df['cognitive_debt'],
        alpha=0.25, color='coral', label='Uncertainty Band'
    )

    # Plot three lines
    ax2.plot(years, conservative_df['cognitive_debt'],
             linewidth=2, linestyle='--', color='green',
             label='Conservative (0.22)', alpha=0.7)
    ax2.plot(years, central_df['cognitive_debt'],
             linewidth=3, color='darkred',
             label='Central Estimate (0.50)')
    ax2.plot(years, aggressive_df['cognitive_debt'],
             linewidth=2, linestyle='--', color='red',
             label='Aggressive (1.0)', alpha=0.7)

    # Risk zones
    ax2.axhline(y=5, color='orange', linestyle='--', linewidth=2, alpha=0.7)
    ax2.axhline(y=8, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax2.axhline(y=12, color='purple', linestyle='--', linewidth=1.5, alpha=0.7)

    ax2.fill_between([2020, 2035], 0, 5, alpha=0.1, color='yellow')
    ax2.fill_between([2020, 2035], 5, 8, alpha=0.1, color='orange')
    ax2.fill_between([2020, 2035], 8, 12, alpha=0.1, color='red')
    ax2.fill_between([2020, 2035], 12, 25, alpha=0.08, color='darkred')

    # Mark ChatGPT launch
    ax2.axvline(x=2022, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax2.text(2022, 2, 'ChatGPT\nLaunch', fontsize=8, ha='center', alpha=0.6)

    ax2.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Cognitive Debt (points)', fontsize=14, fontweight='bold')
    ax2.set_title('Cognitive Debt Forecast with Uncertainty Bands', fontsize=16, fontweight='bold')
    ax2.legend(loc='upper left', fontsize=9, ncol=1)
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(2020, 2035)
    ax2.set_ylim(0, 25)

    plt.tight_layout(pad=2.0)
    plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/forecast_uncertainty_bands.png',
                dpi=300, bbox_inches='tight')
    print("✓ Saved uncertainty bands visualization")

    return uncertainty_results


def create_scenario_comparison_chart(model):
    """Compare all scenarios including new ones"""

    scenarios = {
        # Baseline
        'Current Rates': model.run_scenario('current'),

        # Adoption variations
        'Adoption 50% Slower': model.run_scenario('slow_50'),
        'Adoption 1.5x Faster': model.run_scenario('accel_1.5x'),

        # Capability variations
        'Capability Plateau 2026': model.run_scenario('capability_plateau_2026'),
        'Capability Deceleration': model.run_scenario('capability_deceleration'),

        # Intervention scenarios
        'Intervention 2026': model.run_scenario('intervention_2026'),
        'Intervention 2028': model.run_scenario('intervention_2028'),

        # Design improvement
        'Design Improvement 2026': model.run_scenario('design_improvement_2026')
    }

    fig, ax = plt.subplots(figsize=(16, 10))

    # Plot all scenarios
    for name, df in scenarios.items():
        ax.plot(df['year'], df['cognitive_index'],
                linewidth=2.5, marker='o', label=name, markersize=4)

    # Risk zones
    ax.axhline(y=95, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='WARNING')
    ax.axhline(y=92, color='red', linestyle='--', linewidth=2, alpha=0.7, label='DANGER')
    ax.axhline(y=88, color='purple', linestyle='--', linewidth=1.5, alpha=0.7, label='CRITICAL')

    ax.fill_between([2020, 2035], 95, 100, alpha=0.1, color='yellow')
    ax.fill_between([2020, 2035], 92, 95, alpha=0.1, color='orange')
    ax.fill_between([2020, 2035], 88, 92, alpha=0.1, color='red')

    # Mark ChatGPT launch
    ax.axvline(x=2022, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
    ax.text(2022, 79, 'ChatGPT Launch', fontsize=10, ha='center', alpha=0.6)

    ax.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax.set_ylabel('Cognitive Index (2012=100)', fontsize=14, fontweight='bold')
    ax.set_title('Scenario Comparison: All Paths', fontsize=16, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10, ncol=2)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(2020, 2035)
    ax.set_ylim(78, 100)

    plt.tight_layout()
    plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/scenario_comparison_all.png',
                dpi=300, bbox_inches='tight')
    print("✓ Saved scenario comparison visualization")

    return scenarios


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("COGNITIVE DEBT FORECAST MODEL")
    print("Papers = Calibration | Data = Drivers")
    print("=" * 80)

    # Initialize model
    model = CognitiveDebtModel()

    # Generate individual timeline
    print("\n[1/3] Individual Exposure Timeline:")
    print("=" * 80)
    individual = model.individual_exposure_timeline()
    print(individual.to_string(index=False))

    # Run scenarios
    print("\n[2/3] Running Scenarios...")
    print("=" * 80)

    scenarios = {}
    for scenario_name, scenario_key in [
        ('Current Rates', 'current'),
        ('Adoption 1.2x Faster', 'accel_1.2x'),
        ('Adoption 1.5x Faster', 'accel_1.5x'),
        ('Adoption 2x Faster', 'accel_2x'),
        ('Capability 1.5x Faster', 'capability_accel_1.5x'),
        ('Capability Plateau 2026', 'capability_plateau_2026'),
        ('Capability Plateau 2028', 'capability_plateau_2028'),
        ('Adoption 50% Slower', 'slow_50')
    ]:
        df = model.run_scenario(scenario_key)
        scenarios[scenario_name] = df

        # Print 2028 and 2030 projections with more precision
        row_2028 = df[df['year'] == 2028].iloc[0]
        row_2030 = df[df['year'] == 2030].iloc[0]
        row_2027 = df[df['year'] == 2027].iloc[0]

        print(f"\n{scenario_name}:")
        print(f"  2027: Index={row_2027['cognitive_index']:.2f}, Capability={row_2027['capability']:.2f}, Decline Rate={row_2027['decline_rate']:.3f}")
        print(f"  2028: Index={row_2028['cognitive_index']:.2f}, Capability={row_2028['capability']:.2f}, Decline Rate={row_2028['decline_rate']:.3f}")
        print(f"  2030: Index={row_2030['cognitive_index']:.2f}, Capability={row_2030['capability']:.2f}, Users@Risk={row_2030['users_at_risk_millions']:.0f}M")

    # Create visualizations
    print("\n[3/6] Creating simple forecast (current rates only)...")
    create_simple_forecast_chart(model)

    print("\n[4/6] Creating comprehensive scenario visualizations...")
    create_forecast_charts(model)

    print("\n[5/6] Creating uncertainty visualizations...")
    create_uncertainty_visualization(model)

    print("\n[6/6] Creating scenario comparison...")
    create_scenario_comparison_chart(model)

    # Save data
    scenarios['Current Rates'].to_csv(
        '/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/forecast_scenarios.csv',
        index=False
    )
    individual.to_csv(
        '/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/results/individual_timeline.csv',
        index=False
    )

    print("\n✓ Complete!")
    print("\nGenerated files:")
    print("  - forecast_current_rates_only.png (NEW: simple chart for general audiences)")
    print("  - cognitive_debt_forecast_final.png (comprehensive scenarios)")
    print("  - forecast_uncertainty_bands.png (uncertainty quantification)")
    print("  - scenario_comparison_all.png (all scenarios compared)")
    print("  - forecast_scenarios.csv")
    print("  - individual_timeline.csv")
    print("=" * 80)


if __name__ == "__main__":
    main()
