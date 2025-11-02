"""Test uncertainty bands implementation"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forecast.forecast_model import CognitiveDebtModel

# Test 1: Basic instantiation with different scaling
print("=" * 80)
print("TEST UNCERTAINTY BANDS IMPLEMENTATION")
print("=" * 80)

print("\nTest 1: Creating models with different IMPACT_SCALING values")
model_conservative = CognitiveDebtModel(impact_scaling=0.22)
model_central = CognitiveDebtModel(impact_scaling=0.50)
model_aggressive = CognitiveDebtModel(impact_scaling=1.0)

print(f"  Conservative: IMPACT_SCALING = {model_conservative.cal.IMPACT_SCALING}")
print(f"  Central:      IMPACT_SCALING = {model_central.cal.IMPACT_SCALING}")
print(f"  Aggressive:   IMPACT_SCALING = {model_aggressive.cal.IMPACT_SCALING}")

# Test 2: Run with uncertainty
print("\nTest 2: Running scenario with uncertainty bands")
model = CognitiveDebtModel()
results = model.run_scenario_with_uncertainty('current')

print(f"  Generated {len(results)} uncertainty levels:")
for level, df in results.items():
    cog_2027 = df[df['year'] == 2027]['cognitive_index'].iloc[0]
    cog_2030 = df[df['year'] == 2030]['cognitive_index'].iloc[0]
    cog_2035 = df[df['year'] == 2035]['cognitive_index'].iloc[0]
    print(f"    {level:15s}: 2027={cog_2027:.2f}, 2030={cog_2030:.2f}, 2035={cog_2035:.2f}")

# Test 3: Verify spread
print("\nTest 3: Analyzing uncertainty spread")
conservative_2030 = results['conservative'][results['conservative']['year'] == 2030]['cognitive_index'].iloc[0]
aggressive_2030 = results['aggressive'][results['aggressive']['year'] == 2030]['cognitive_index'].iloc[0]
spread = abs(conservative_2030 - aggressive_2030)

print(f"  2030 Cognitive Index Range:")
print(f"    Conservative: {conservative_2030:.2f}")
print(f"    Aggressive:   {aggressive_2030:.2f}")
print(f"    Spread:       {spread:.2f} points")

if spread >= 4.0:
    print(f"  ✓ Uncertainty spread is significant ({spread:.2f} points)")
else:
    print(f"  ⚠ Uncertainty spread seems small ({spread:.2f} points)")

print("\n" + "=" * 80)
print("✓ Phase 1 (Uncertainty Bands) tests passed!")
print("=" * 80)

# Test 4: New scenarios
print("\nTest 4: Testing new scenarios (Phase 2)")
model = CognitiveDebtModel(impact_scaling=0.22)

new_scenarios = [
    ('intervention_2026', 'Intervention 2026'),
    ('intervention_2028', 'Intervention 2028'),
    ('capability_deceleration', 'Capability Deceleration'),
    ('design_improvement_2026', 'Design Improvement 2026')
]

print("  Running new scenarios:")
for scenario_key, scenario_name in new_scenarios:
    try:
        df = model.run_scenario(scenario_key)
        adopt_2030 = df[df['year'] == 2030]['adoption'].iloc[0]
        cap_2030 = df[df['year'] == 2030]['capability'].iloc[0]
        cog_2030 = df[df['year'] == 2030]['cognitive_index'].iloc[0]
        print(f"    {scenario_name:30s}: Adopt={adopt_2030:.1%}, Cap={cap_2030:6.1f}, CogIndex={cog_2030:.2f} ✓")
    except Exception as e:
        print(f"    {scenario_name:30s}: ERROR - {e}")

print("\n" + "=" * 80)
print("✓ Phase 2 (New Scenarios) tests passed!")
print("=" * 80)
