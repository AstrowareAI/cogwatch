"""
Validation Script: Test IMPACT_SCALING = 0.22 against historical data
======================================================================

Check if the scaling factor matches the observed 2022-2024 decline pattern.
"""

import pandas as pd
import numpy as np
import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from forecast.forecast_model import CognitiveDebtModel, DataDrivers, PaperCalibrations

def test_scaling_factors():
    """Test different IMPACT_SCALING values against historical data"""
    
    # Historical data from exploratory analysis
    # 2022-2024: Cognitive index declined from ~97.2 to 96.1 = 1.1 points over 2 years
    # Observed decline rate: ~0.55 points/year (vs baseline 0.35)
    
    historical_data = {
        'year': [2022, 2023, 2024],
        'cognitive_index_observed': [97.2, 96.6, 96.1],  # Estimated from data
        'adoption_observed': [0.01, 0.04, 0.091],  # ChatGPT penetration
        'capability_observed': [0.25, 0.5, 1.0]  # Normalized (2024=1.0)
    }
    
    # Test different scaling factors
    scaling_factors = [0.10, 0.15, 0.22, 0.30, 0.40, 0.50, 1.0]
    
    results = []
    
    for scale in scaling_factors:
        model = CognitiveDebtModel()
        # Override scaling factor
        original_scale = model.cal.IMPACT_SCALING
        model.cal.IMPACT_SCALING = scale
        
        predictions = []
        # Start from 2022 observed value (97.2) - this is what actually happened
        current_cognitive = historical_data['cognitive_index_observed'][0]  # 97.2
        
        for i, year in enumerate([2022, 2023, 2024]):
            adopt = historical_data['adoption_observed'][i]
            cap = historical_data['capability_observed'][i]
            
            # Calculate decline rate
            decline = model.cognitive_decline_rate(year, adopt, cap, current_cognitive, 'current')
            
            # For 2022, just record the starting value (no update needed)
            # For 2023 and 2024, apply decline
            if i > 0:
                distance_from_floor = current_cognitive - model.data.COGNITIVE_INDEX_FLOOR
                if distance_from_floor > 0:
                    decay_multiplier = 1.0 - np.exp(-model.data.COGNITIVE_INDEX_ASYMPTOTE_STEEPNESS * distance_from_floor)
                    effective_decline = min(decline * decay_multiplier, distance_from_floor)
                    current_cognitive = current_cognitive - effective_decline
                else:
                    current_cognitive = model.data.COGNITIVE_INDEX_FLOOR
            
            predictions.append({
                'year': year,
                'predicted_index': current_cognitive,
                'observed_index': historical_data['cognitive_index_observed'][i],
                'decline_rate': decline,
                'error': abs(current_cognitive - historical_data['cognitive_index_observed'][i])
            })
        
        # Calculate total error
        total_error = sum([p['error'] for p in predictions])
        total_decline_predicted = predictions[0]['predicted_index'] - predictions[-1]['predicted_index']
        total_decline_observed = historical_data['cognitive_index_observed'][0] - historical_data['cognitive_index_observed'][-1]
        
        results.append({
            'scaling_factor': scale,
            'predicted_2024_index': predictions[-1]['predicted_index'],
            'observed_2024_index': historical_data['cognitive_index_observed'][-1],
            'total_error': total_error,
            'total_decline_predicted': total_decline_predicted,
            'total_decline_observed': total_decline_observed,
            'decline_match_error': abs(total_decline_predicted - total_decline_observed),
            'avg_decline_rate_predicted': predictions[-1]['decline_rate']
        })
        
        # Restore original
        model.cal.IMPACT_SCALING = original_scale
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(results)
    
    # Find best match
    best_match_idx = df['decline_match_error'].idxmin()
    best_match = df.iloc[best_match_idx]
    
    print("=" * 80)
    print("IMPACT_SCALING VALIDATION AGAINST HISTORICAL DATA (2022-2024)")
    print("=" * 80)
    print(f"\nObserved Data:")
    print(f"  Cognitive Index: {historical_data['cognitive_index_observed'][0]:.1f} (2022) → {historical_data['cognitive_index_observed'][-1]:.1f} (2024)")
    print(f"  Total Decline: {total_decline_observed:.2f} points over 2 years")
    print(f"  Average Decline Rate: ~0.55 points/year (vs baseline 0.35)")
    print(f"\n{'=' * 80}")
    
    print(f"\nResults for Different Scaling Factors:")
    print(f"{'Scaling':<12} {'Pred 2024':<12} {'Obs 2024':<12} {'Total Error':<15} {'Decline Match':<15} {'Best':<8}")
    print("-" * 80)
    
    for idx, row in df.iterrows():
        best_marker = "★ BEST" if idx == best_match_idx else ""
        print(f"{row['scaling_factor']:<12.2f} {row['predicted_2024_index']:<12.2f} {row['observed_2024_index']:<12.2f} "
              f"{row['total_error']:<15.3f} {row['decline_match_error']:<15.3f} {best_marker:<8}")
    
    print(f"\n{'=' * 80}")
    print(f"\n★ BEST MATCH: Scaling Factor = {best_match['scaling_factor']:.2f}")
    print(f"   Predicted 2024 Index: {best_match['predicted_2024_index']:.2f}")
    print(f"   Observed 2024 Index: {best_match['observed_2024_index']:.2f}")
    print(f"   Error: {best_match['total_error']:.3f} points")
    print(f"   Decline Match Error: {best_match['decline_match_error']:.3f} points")
    
    print(f"\n{'=' * 80}")
    print(f"\nCURRENT MODEL (0.22):")
    current_result = df[df['scaling_factor'] == 0.22].iloc[0]
    print(f"   Predicted 2024 Index: {current_result['predicted_2024_index']:.2f}")
    print(f"   Observed 2024 Index: {current_result['observed_2024_index']:.2f}")
    print(f"   Total Error: {current_result['total_error']:.3f} points")
    print(f"   Decline Match Error: {current_result['decline_match_error']:.3f} points")
    
    if abs(current_result['predicted_2024_index'] - current_result['observed_2024_index']) < 1.0:
        print(f"   ✓ 0.22 is REASONABLE - within 1 point of observed")
    else:
        print(f"   ⚠ 0.22 may need adjustment")
    
    print(f"\n{'=' * 80}")
    print("\nInterpretation:")
    print("  - Lower scaling (0.10-0.15) = Conservative, slower decline")
    print("  - Current (0.22) = Moderate scaling")
    print("  - Higher scaling (0.30-0.50) = More aggressive decline")
    print("  - Unscaled (1.0) = Full paper effects (likely too extreme)")
    
    return df, best_match

def analyze_scaling_rationale():
    """Analyze why 0.22 might be chosen"""
    
    print("\n" + "=" * 80)
    print("WHY SCALING FACTOR MIGHT BE NEEDED:")
    print("=" * 80)
    
    print("\n1. Individual vs Population Effects:")
    print("   - Papers measure: Heavy users, controlled experiments")
    print("   - Model needs: Population average, mixed usage patterns")
    print("   - Rationale: Not everyone is a heavy user → lower average impact")
    
    print("\n2. Paper Effects May Not Be Additive:")
    print("   - MIT: 0.083 pts/month per heavy user")
    print("   - Microsoft: 71% offloading (different measurement)")
    print("   - HumanAgencyBench: 69.5% risk (qualitative)")
    print("   - Rationale: These may overlap or measure different things")
    
    print("\n3. Conservative Forecasting:")
    print("   - Better to underestimate than overestimate alarm")
    print("   - Provides buffer for model uncertainty")
    print("   - Rationale: Avoid false alarms while still showing risk")
    
    print("\n4. Data-Driven Calibration:")
    print("   - Scale to match observed 2022-2024 decline pattern")
    print("   - Balances paper findings with real-world data")
    print("   - Rationale: Combine best of both (papers + data)")

if __name__ == "__main__":
    df, best_match = test_scaling_factors()
    analyze_scaling_rationale()

