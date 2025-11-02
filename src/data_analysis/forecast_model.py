"""
Cognitive Debt Forecast Model
==============================

Papers = Calibration (prove it exists, tell us HOW FAST)
Data = Drivers (adoption, capability, cognitive index)
Model = Data-driven, paper-calibrated

Outputs:
1. Humanity timeline to critical (clean chart)
2. Individual exposure months to harm
3. Adoption vs Capability effects separated
4. Scenarios: current, capability plateau, adoption slow, misalignment
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
    COGNITIVE_INDEX_FLOOR = 75.0           # Realistic floor (can't go to 0)
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

    def __init__(self):
        self.cal = PaperCalibrations()
        self.data = DataDrivers()
        self.global_population = 8.2  # billion

    def adoption(self, year, scenario="current"):
        """Calculate AI adoption for given year and scenario"""
        years = year - 2024

        if scenario == "slow_adoption":
            # Slows to 50% CAGR after 2026
            if years <= 2:
                adoption = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** years
            else:
                adoption_2026 = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** 2
                adoption = adoption_2026 * (1 + 0.50) ** (years - 2)
            return min(adoption, 0.50)  # Cap at 50%

        # Default: current rates (for capability_plateau and misalignment too)
        adoption = self.data.CURRENT_ADOPTION_2024 * (1 + self.data.CHATGPT_CAGR) ** years
        return min(adoption, 0.95)  # Cap at 95%

    def capability(self, year, scenario="current"):
        """Calculate AI capability for given year (normalized to 2024=1.0)"""
        years = year - 2024

        if scenario == "current":
            # Doubles every year
            return self.data.CAPABILITY_2024 * (self.data.CAPABILITY_GROWTH_RATE ** years)

        elif scenario == "capability_plateau":
            # Freezes at 2024 level
            return self.data.CAPABILITY_2024

        return 1.0

    def cognitive_decline_rate(self, year, adoption_rate, capability_level, scenario="current"):
        """Calculate cognitive decline rate (points per year)"""

        # Base decline (pre-AI baseline)
        base = self.data.BASELINE_DECLINE_RATE

        # MIT calibration: 0.083 points/month per heavy user
        # Scale by adoption (how many users) and capability (how much they rely on it)
        mit_factor = (
            self.cal.MIT_COGNITIVE_DEBT_PER_MONTH * 12 *
            adoption_rate *
            min(capability_level, 5.0)  # Cap capability multiplier at 5x
        )

        # Microsoft calibration: 71% cognitive offloading
        # More capable AI → more offloading → more atrophy
        msft_factor = (
            self.cal.MSFT_COGNITIVE_OFFLOAD *
            adoption_rate *
            (capability_level / 10.0)  # Normalize capability effect
        )

        # HumanAgencyBench: 69.5% of AI doesn't support learning → skill atrophy
        hab_factor = (
            self.cal.HAB_OFFLOADING_RISK *
            adoption_rate *
            0.3  # Scale to reasonable impact
        )

        # Empirical acceleration from data (57% faster post-AI)
        empirical = base * (self.data.POST_AI_ACCELERATION - 1) * adoption_rate

        # Misalignment scenario: double the impact
        multiplier = 2.0 if scenario == "misalignment" else 1.0

        total_decline = base + (mit_factor + msft_factor + hab_factor + empirical) * multiplier

        # Cap at 2.5 points/year max (realistic limit)
        return min(total_decline, 2.5)

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

    def run_scenario(self, scenario="current", end_year=2035):
        """Run forecast for a given scenario"""

        results = {
            'year': [],
            'adoption': [],
            'capability': [],
            'cognitive_index': [],
            'mental_health': [],
            'decline_rate': [],
            'users_at_risk_millions': []
        }

        # Start from 2024
        current_cognitive = self.data.COGNITIVE_INDEX_2024

        for year in range(2024, end_year + 1):
            # Calculate drivers
            adopt = self.adoption(year, scenario)
            cap = self.capability(year, scenario)

            # Calculate decline rate
            decline = self.cognitive_decline_rate(year, adopt, cap, scenario)

            # Update cognitive index (with floor)
            if year > 2024:
                current_cognitive = max(
                    current_cognitive - decline,
                    self.data.COGNITIVE_INDEX_FLOOR
                )

            # Calculate mental health
            mh = self.mental_health_rate(year, adopt, current_cognitive)

            # Users at risk (MIT: 20% of users show measurable impact)
            users_at_risk = adopt * self.global_population * 0.20 * 1000  # millions

            # Store results
            results['year'].append(year)
            results['adoption'].append(adopt)
            results['capability'].append(cap)
            results['cognitive_index'].append(current_cognitive)
            results['mental_health'].append(mh)
            results['decline_rate'].append(decline)
            results['users_at_risk_millions'].append(users_at_risk)

        return pd.DataFrame(results)

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

def create_forecast_charts(model):
    """Create focused forecast visualizations"""

    # Run all scenarios
    scenarios = {
        'Current Rates': model.run_scenario('current'),
        'Adoption Slows (50% max)': model.run_scenario('slow_adoption'),
        'Capability Plateaus': model.run_scenario('capability_plateau'),
        'Misalignment 2x': model.run_scenario('misalignment')
    }

    # Get individual timeline
    individual = model.individual_exposure_timeline()

    # Create figure
    fig = plt.figure(figsize=(20, 12))

    # 1. HUMANITY TIMELINE - Cognitive Index (main chart)
    ax1 = plt.subplot(2, 3, 1)
    for name, df in scenarios.items():
        ax1.plot(df['year'], df['cognitive_index'], linewidth=3, marker='o', label=name, markersize=6)

    ax1.axhline(y=95, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='DANGER (95)')
    ax1.axhline(y=92, color='red', linestyle='--', linewidth=2, alpha=0.7, label='CRITICAL (92)')
    ax1.fill_between([2024, 2035], 95, 98, alpha=0.1, color='yellow', label='WARNING')
    ax1.fill_between([2024, 2035], 92, 95, alpha=0.1, color='orange')
    ax1.fill_between([2024, 2035], 75, 92, alpha=0.1, color='red')

    ax1.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Cognitive Index (2012=100)', fontsize=14, fontweight='bold')
    ax1.set_title('HUMANITY TIMELINE: Cognitive Debt Forecast', fontsize=16, fontweight='bold')
    ax1.legend(loc='best', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(2024, 2035)

    # 2. INDIVIDUAL EXPOSURE TIMELINE
    ax2 = plt.subplot(2, 3, 2)
    x = individual['months']
    y1 = individual['cognitive_debt_points']
    y2 = individual['mental_health_risk_%']

    ax2_twin = ax2.twinx()

    line1 = ax2.plot(x, y1, linewidth=3, marker='o', color='red', markersize=10, label='Cognitive Debt')
    line2 = ax2_twin.plot(x, y2, linewidth=3, marker='s', color='purple', markersize=10, label='Mental Health Risk')

    ax2.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='MIT 6-month threshold')
    ax2.axhline(y=1.0, color='red', linestyle='--', alpha=0.5, label='Significant harm')

    ax2.set_xlabel('Months of Heavy Use', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Cognitive Debt (points)', fontsize=14, fontweight='bold', color='red')
    ax2_twin.set_ylabel('Mental Health Risk (%)', fontsize=14, fontweight='bold', color='purple')
    ax2.set_title('INDIVIDUAL EXPOSURE: Harm Timeline', fontsize=16, fontweight='bold')

    ax2.tick_params(axis='y', labelcolor='red')
    ax2_twin.tick_params(axis='y', labelcolor='purple')

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax2.legend(lines, labels, loc='upper left', fontsize=10)
    ax2.grid(True, alpha=0.3)

    # 3. ADOPTION vs CAPABILITY EFFECTS (Current scenario)
    ax3 = plt.subplot(2, 3, 3)
    current = scenarios['Current Rates']

    ax3_twin = ax3.twinx()

    line1 = ax3.plot(current['year'], current['adoption'] * 100, linewidth=3, marker='o', color='green', label='Adoption %', markersize=6)
    line2 = ax3_twin.plot(current['year'], current['capability'], linewidth=3, marker='^', color='blue', label='Capability (2024=1.0)', markersize=6)

    ax3.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Adoption (%)', fontsize=14, fontweight='bold', color='green')
    ax3_twin.set_ylabel('Capability (normalized)', fontsize=14, fontweight='bold', color='blue')
    ax3.set_title('DRIVERS: Adoption vs Capability Growth', fontsize=16, fontweight='bold')

    ax3.tick_params(axis='y', labelcolor='green')
    ax3_twin.tick_params(axis='y', labelcolor='blue')

    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax3.legend(lines, labels, loc='upper left', fontsize=10)
    ax3.grid(True, alpha=0.3)

    # 4. SCENARIO COMPARISON - Mental Health
    ax4 = plt.subplot(2, 3, 4)
    for name, df in scenarios.items():
        ax4.plot(df['year'], df['mental_health'] * 100, linewidth=3, marker='o', label=name, markersize=6)

    ax4.axhline(y=13, color='orange', linestyle='--', linewidth=2, alpha=0.7, label='DANGER (13%)')
    ax4.axhline(y=16, color='red', linestyle='--', linewidth=2, alpha=0.7, label='CRITICAL (16%)')

    ax4.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax4.set_ylabel('Mental Health Prevalence (%)', fontsize=14, fontweight='bold')
    ax4.set_title('Mental Health Impact by Scenario', fontsize=16, fontweight='bold')
    ax4.legend(loc='best', fontsize=10)
    ax4.grid(True, alpha=0.3)

    # 5. USERS AT RISK
    ax5 = plt.subplot(2, 3, 5)
    current = scenarios['Current Rates']
    ax5.bar(current['year'], current['users_at_risk_millions'], alpha=0.7, color='darkred', edgecolor='black')

    ax5.set_xlabel('Year', fontsize=14, fontweight='bold')
    ax5.set_ylabel('Users at Risk (Millions)', fontsize=14, fontweight='bold')
    ax5.set_title('Users at Cognitive Risk', fontsize=16, fontweight='bold')
    ax5.grid(True, alpha=0.3, axis='y')

    # 6. SUMMARY TABLE
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')

    # Find critical thresholds for each scenario
    summary_data = [['Scenario', 'Year → DANGER', 'Year → CRITICAL', '2030 Cog Index', '2030 Users (M)']]
    summary_data.append(['─' * 20, '─' * 12, '─' * 14, '─' * 14, '─' * 16])

    for name, df in scenarios.items():
        # Find when cognitive index crosses danger (95) and critical (92)
        danger_year = df[df['cognitive_index'] < 95]['year'].min() if any(df['cognitive_index'] < 95) else '>'
        critical_year = df[df['cognitive_index'] < 92]['year'].min() if any(df['cognitive_index'] < 92) else '>'

        cog_2030 = df[df['year'] == 2030]['cognitive_index'].values[0]
        users_2030 = df[df['year'] == 2030]['users_at_risk_millions'].values[0]

        short_name = name.replace(' (50% max)', '').replace(' (2024)', '')
        summary_data.append([
            short_name,
            str(danger_year) if danger_year != '>' else 'Never',
            str(critical_year) if critical_year != '>' else 'Never',
            f"{cog_2030:.1f}",
            f"{users_2030:.0f}"
        ])

    table = ax6.table(cellText=summary_data, cellLoc='center', loc='center',
                     colWidths=[0.35, 0.15, 0.15, 0.17, 0.18])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2.5)

    # Style header
    for i in range(5):
        table[(0, i)].set_facecolor('#2E7D32')
        table[(0, i)].set_text_props(weight='bold', color='white')

    ax6.set_title('SCENARIO SUMMARY', fontsize=16, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/data_analysis/cognitive_debt_forecast_final.png',
                dpi=300, bbox_inches='tight')
    print("✓ Saved forecast visualization")

    return scenarios, individual


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
        ('Adoption Slows', 'slow_adoption'),
        ('Capability Plateaus', 'capability_plateau'),
        ('Misalignment 2x', 'misalignment')
    ]:
        df = model.run_scenario(scenario_key)
        scenarios[scenario_name] = df

        # Print 2027 and 2030 projections
        row_2027 = df[df['year'] == 2027].iloc[0]
        row_2030 = df[df['year'] == 2030].iloc[0]

        print(f"\n{scenario_name}:")
        print(f"  2027: Cognitive={row_2027['cognitive_index']:.1f}, MH={row_2027['mental_health']:.1%}, Adoption={row_2027['adoption']:.1%}")
        print(f"  2030: Cognitive={row_2030['cognitive_index']:.1f}, MH={row_2030['mental_health']:.1%}, Users@Risk={row_2030['users_at_risk_millions']:.0f}M")

    # Create visualizations
    print("\n[3/3] Creating visualizations...")
    create_forecast_charts(model)

    # Save data
    scenarios['Current Rates'].to_csv(
        '/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/data_analysis/forecast_scenarios.csv',
        index=False
    )
    individual.to_csv(
        '/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/data_analysis/individual_timeline.csv',
        index=False
    )

    print("\n✓ Complete!")
    print("\nGenerated files:")
    print("  - cognitive_debt_forecast_final.png")
    print("  - forecast_scenarios.csv")
    print("  - individual_timeline.csv")
    print("=" * 80)


if __name__ == "__main__":
    main()
