"""
Comprehensive Exploratory Data Analysis for Cognitive Debt Forecasting
=======================================================================

This script analyzes the relationships between:
1. Population-normalized social media growth (2017-2025)
2. Population-normalized ChatGPT adoption (2022-2025)
3. Mental health disorders
4. Cognitive decline index
5. AI incidents and capabilities

The goal is to identify growth factors, correlations, and build components
for the cognitive debt forecast model.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import torch
import warnings

warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)

# ============================================================================
# 1. DATA LOADING AND PREPROCESSING
# ============================================================================

def load_all_data():
    """Load all sheets from the collated data Excel file"""
    file_path = '/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/data/Collated_data.xlsx'

    data = {}
    xls = pd.ExcelFile(file_path)

    for sheet in xls.sheet_names:
        data[sheet] = pd.read_excel(xls, sheet_name=sheet)
        print(f"✓ Loaded {sheet}: {data[sheet].shape}")

    return data


def clean_and_prepare_data(data):
    """Clean and prepare all datasets for analysis"""

    # ChatGPT Growth data
    chatgpt = data['ChatGPT Growth Rates'].copy()
    # Parse Half column (contains 'H1', 'H2', etc.)
    chatgpt['Half_Numeric'] = chatgpt['Half'].astype(str).str.extract(r'(\d+)').astype(int)
    chatgpt['Year_Period'] = chatgpt['Year'].astype(str) + '_' + chatgpt['Half'].astype(str)

    # Mental Health data
    mental_health = data['Mental health'].copy()

    # Population data
    population = data['Population'].copy()

    # Social Media data
    social_media = data['Social Media'].copy()

    # Cognitive Index
    cognitive = data['Cognitive Ability Index'].copy()
    # Clean the Annual Change column
    cognitive['Annual_Change_Numeric'] = cognitive['Annual Change (%)'].replace('—', np.nan)
    cognitive['Annual_Change_Numeric'] = cognitive['Annual_Change_Numeric'].str.replace('−', '-').str.replace('%', '')
    cognitive['Annual_Change_Numeric'] = pd.to_numeric(cognitive['Annual_Change_Numeric'], errors='coerce')

    # AI Capability
    ai_capability = data['AI Capability in completing lon'].copy()
    ai_capability['Date'] = pd.to_datetime(ai_capability['Month'])
    ai_capability['Year'] = ai_capability['Date'].dt.year

    # Screen Time
    screen_time = data['SCREEN_TIME_USAGE_HOURS'].copy()

    def parse_screen_time(value):
        """Parse various screen time formats to hours as float"""
        if pd.isna(value):
            return np.nan

        value_str = str(value).strip().replace('~', '').strip()

        # Handle ranges like "4.5-5" or "5.0-5.5"
        if '-' in value_str and 'hours' not in value_str.lower():
            try:
                parts = value_str.split('-')
                return np.mean([float(p) for p in parts])
            except ValueError:
                pass

        # Remove any text in parentheses like "(recovery)"
        import re
        value_str = re.sub(r'\([^)]*\)', '', value_str).strip()

        # Handle "X hours Y minutes" format
        if 'hours' in value_str.lower() and 'minutes' in value_str.lower():
            hours_match = re.search(r'(\d+)\s*hours?', value_str.lower())
            minutes_match = re.search(r'(\d+)\s*minutes?', value_str.lower())
            hours = float(hours_match.group(1)) if hours_match else 0
            minutes = float(minutes_match.group(1)) if minutes_match else 0
            return hours + (minutes / 60)

        # Handle "X hours" format
        if 'hours' in value_str.lower():
            hours_match = re.search(r'(\d+)\s*hours?', value_str.lower())
            if hours_match:
                return float(hours_match.group(1))

        # Try to convert directly
        try:
            return float(value_str)
        except ValueError:
            return np.nan

    # Clean screen time columns
    for col in screen_time.columns:
        if 'Hours' in col:
            screen_time[col + '_Clean'] = screen_time[col].apply(parse_screen_time)

    # AI Incidents
    ai_incidents = data['AI Incidents'].copy()

    return {
        'chatgpt': chatgpt,
        'mental_health': mental_health,
        'population': population,
        'social_media': social_media,
        'cognitive': cognitive,
        'ai_capability': ai_capability,
        'screen_time': screen_time,
        'ai_incidents': ai_incidents
    }


# ============================================================================
# 2. POPULATION NORMALIZATION
# ============================================================================

def normalize_by_population(cleaned_data):
    """Normalize social media and ChatGPT data by population"""

    results = {}

    # Social Media Normalized
    social_pop = cleaned_data['social_media'].merge(
        cleaned_data['population'],
        on='Year',
        how='inner'
    )
    social_pop['Social_Media_Penetration_%'] = (
        social_pop['Number_of_Social_media_users_in_Billions'] /
        social_pop['Population_In_Billion']
    ) * 100

    # Calculate year-over-year growth
    social_pop = social_pop.sort_values('Year')
    social_pop['Social_Media_YoY_Growth_%'] = social_pop['Social_Media_Penetration_%'].pct_change() * 100

    results['social_media_normalized'] = social_pop

    # ChatGPT Normalized (already has population column)
    chatgpt = cleaned_data['chatgpt'].copy()
    # ChatGPT penetration is already calculated, let's verify
    chatgpt['ChatGPT_Penetration_Calculated_%'] = (
        chatgpt['WAU_Millions'] / 1000 / chatgpt['Total_Population_in_Billions']
    ) * 100

    results['chatgpt_normalized'] = chatgpt

    # Mental Health Normalized
    mental_pop = cleaned_data['mental_health'].merge(
        cleaned_data['population'],
        on='Year',
        how='inner'
    )
    mental_pop['Mental_Health_Prevalence_%'] = (
        mental_pop['Total_In_Billion'] /
        mental_pop['Population_In_Billion']
    ) * 100
    mental_pop = mental_pop.sort_values('Year')
    mental_pop['Mental_Health_YoY_Growth_%'] = mental_pop['Mental_Health_Prevalence_%'].pct_change() * 100

    results['mental_health_normalized'] = mental_pop

    return results


# ============================================================================
# 3. GROWTH FACTOR ANALYSIS
# ============================================================================

def analyze_growth_factors(normalized_data):
    """Analyze and compare growth factors for social media and ChatGPT"""

    results = {}

    # Social Media Growth Analysis (2017-2025)
    social = normalized_data['social_media_normalized']
    social_period = social[(social['Year'] >= 2017) & (social['Year'] <= 2025)]

    if len(social_period) > 1:
        # Calculate CAGR (Compound Annual Growth Rate)
        start_val = social_period.iloc[0]['Social_Media_Penetration_%']
        end_val = social_period.iloc[-1]['Social_Media_Penetration_%']
        years = social_period.iloc[-1]['Year'] - social_period.iloc[0]['Year']

        social_cagr = ((end_val / start_val) ** (1/years) - 1) * 100 if years > 0 else 0

        results['social_media'] = {
            'period': '2017-2025',
            'start_penetration_%': start_val,
            'end_penetration_%': end_val,
            'cagr_%': social_cagr,
            'total_growth_%': ((end_val - start_val) / start_val) * 100,
            'avg_yoy_growth_%': social_period['Social_Media_YoY_Growth_%'].mean()
        }

    # ChatGPT Growth Analysis (2022-2025)
    chatgpt = normalized_data['chatgpt_normalized']
    chatgpt_period = chatgpt[(chatgpt['Year'] >= 2022) & (chatgpt['Year'] <= 2025)]
    # Filter out NaN values
    chatgpt_period = chatgpt_period.dropna(subset=['ChatGPT_Penetration_Calculated_%'])

    if len(chatgpt_period) > 1:
        start_val = chatgpt_period.iloc[0]['ChatGPT_Penetration_Calculated_%']
        end_val = chatgpt_period.iloc[-1]['ChatGPT_Penetration_Calculated_%']

        # Calculate time in half-years
        start_time = (chatgpt_period.iloc[0]['Year'] - 2022) + (chatgpt_period.iloc[0]['Half_Numeric'] - 1) * 0.5
        end_time = (chatgpt_period.iloc[-1]['Year'] - 2022) + (chatgpt_period.iloc[-1]['Half_Numeric'] - 1) * 0.5
        years = end_time - start_time

        chatgpt_cagr = ((end_val / start_val) ** (1/years) - 1) * 100 if years > 0 else 0

        results['chatgpt'] = {
            'period': '2022-2025',
            'start_penetration_%': start_val,
            'end_penetration_%': end_val,
            'cagr_%': chatgpt_cagr,
            'total_growth_%': ((end_val - start_val) / start_val) * 100,
            'avg_hoh_growth_%': chatgpt_period['HoH_Growth_%'].mean()
        }

    # Compare growth rates
    if 'social_media' in results and 'chatgpt' in results:
        results['comparison'] = {
            'chatgpt_vs_social_media_cagr_ratio': results['chatgpt']['cagr_%'] / results['social_media']['cagr_%'],
            'growth_acceleration_factor': results['chatgpt']['cagr_%'] / results['social_media']['cagr_%']
        }

    return results


# ============================================================================
# 4. CORRELATION ANALYSIS
# ============================================================================

def analyze_correlations(cleaned_data, normalized_data):
    """Analyze correlations between different variables"""

    results = {}

    # Merge datasets on Year for correlation analysis
    # Start with cognitive index as the target
    merged = cleaned_data['cognitive'][['Year', 'Cognitive Index (2012 = 100)']].copy()

    # Add mental health
    merged = merged.merge(
        normalized_data['mental_health_normalized'][['Year', 'Mental_Health_Prevalence_%']],
        on='Year',
        how='left'
    )

    # Add social media
    merged = merged.merge(
        normalized_data['social_media_normalized'][['Year', 'Social_Media_Penetration_%']],
        on='Year',
        how='left'
    )

    # Add AI incidents (sum across categories)
    merged = merged.merge(
        cleaned_data['ai_incidents'][['Year', 'Total']],
        on='Year',
        how='left'
    )
    merged.rename(columns={'Total': 'AI_Incidents_Total'}, inplace=True)

    # Calculate correlations
    correlation_matrix = merged.corr()

    results['correlation_matrix'] = correlation_matrix
    results['merged_data'] = merged

    # Key correlations with Cognitive Index
    cognitive_correlations = correlation_matrix['Cognitive Index (2012 = 100)'].sort_values()
    results['cognitive_correlations'] = cognitive_correlations

    return results


# ============================================================================
# 5. SOCIAL MEDIA & MENTAL HEALTH RELATIONSHIP
# ============================================================================

def analyze_social_media_mental_health(normalized_data, cleaned_data):
    """Analyze relationship between social media usage and mental health"""

    # Merge social media and mental health data
    merged = normalized_data['social_media_normalized'][
        ['Year', 'Social_Media_Penetration_%']
    ].merge(
        normalized_data['mental_health_normalized'][
            ['Year', 'Mental_Health_Prevalence_%']
        ],
        on='Year',
        how='inner'
    )

    # Calculate correlation
    correlation = merged['Social_Media_Penetration_%'].corr(merged['Mental_Health_Prevalence_%'])

    # Fit linear regression
    X = merged['Social_Media_Penetration_%'].values
    y = merged['Mental_Health_Prevalence_%'].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)

    results = {
        'correlation': correlation,
        'regression': {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'std_err': std_err
        },
        'data': merged
    }

    return results


# ============================================================================
# 6. AI ADOPTION & COGNITIVE DECLINE RELATIONSHIP
# ============================================================================

def analyze_ai_cognitive_relationship(cleaned_data, normalized_data):
    """Analyze relationship between AI adoption and cognitive decline"""

    # Focus on 2022-2024 period where we have ChatGPT data
    cognitive_subset = cleaned_data['cognitive'][
        (cleaned_data['cognitive']['Year'] >= 2022) &
        (cleaned_data['cognitive']['Year'] <= 2024)
    ].copy()

    # Get ChatGPT data aggregated by year
    chatgpt_yearly = normalized_data['chatgpt_normalized'].groupby('Year').agg({
        'ChatGPT_Penetration_Calculated_%': 'mean',
        'WAU_Millions': 'mean'
    }).reset_index()

    # Merge
    merged = cognitive_subset.merge(chatgpt_yearly, on='Year', how='left')

    # Calculate correlation if we have data
    if not merged['ChatGPT_Penetration_Calculated_%'].isna().all():
        correlation = merged['Cognitive Index (2012 = 100)'].corr(
            merged['ChatGPT_Penetration_Calculated_%']
        )
    else:
        correlation = None

    results = {
        'correlation': correlation,
        'data': merged,
        'cognitive_decline_2022_2024': {
            'start_index': cognitive_subset.iloc[0]['Cognitive Index (2012 = 100)'],
            'end_index': cognitive_subset.iloc[-1]['Cognitive Index (2012 = 100)'],
            'total_decline': cognitive_subset.iloc[0]['Cognitive Index (2012 = 100)'] -
                           cognitive_subset.iloc[-1]['Cognitive Index (2012 = 100)'],
            'decline_rate_%': (
                (cognitive_subset.iloc[0]['Cognitive Index (2012 = 100)'] -
                 cognitive_subset.iloc[-1]['Cognitive Index (2012 = 100)']) /
                cognitive_subset.iloc[0]['Cognitive Index (2012 = 100)']
            ) * 100
        }
    }

    return results


# ============================================================================
# 7. PREDICTIVE MODELING WITH PYTORCH
# ============================================================================

def build_growth_model_pytorch(normalized_data):
    """Build growth prediction model using PyTorch"""

    # Prepare social media data for modeling
    social = normalized_data['social_media_normalized'][
        ['Year', 'Social_Media_Penetration_%']
    ].dropna()

    if len(social) < 3:
        return None

    # Convert to PyTorch tensors
    X = torch.tensor(social['Year'].values, dtype=torch.float32).reshape(-1, 1)
    y = torch.tensor(social['Social_Media_Penetration_%'].values, dtype=torch.float32).reshape(-1, 1)

    # Normalize
    X_mean, X_std = X.mean(), X.std()
    y_mean, y_std = y.mean(), y.std()
    X_norm = (X - X_mean) / X_std
    y_norm = (y - y_mean) / y_std

    # Simple linear model
    class GrowthModel(torch.nn.Module):
        def __init__(self):
            super(GrowthModel, self).__init__()
            self.linear = torch.nn.Linear(1, 1)

        def forward(self, x):
            return self.linear(x)

    model = GrowthModel()
    criterion = torch.nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    # Train
    epochs = 1000
    for epoch in range(epochs):
        optimizer.zero_grad()
        predictions = model(X_norm)
        loss = criterion(predictions, y_norm)
        loss.backward()
        optimizer.step()

    # Get predictions
    with torch.no_grad():
        predictions_norm = model(X_norm)
        predictions = predictions_norm * y_std + y_mean

    results = {
        'model': model,
        'X_mean': X_mean.item(),
        'X_std': X_std.item(),
        'y_mean': y_mean.item(),
        'y_std': y_std.item(),
        'predictions': predictions.numpy().flatten(),
        'actual': y.numpy().flatten(),
        'years': X.numpy().flatten()
    }

    return results


# ============================================================================
# 8. FORECAST COMPONENTS PREPARATION
# ============================================================================

def prepare_forecast_components(growth_factors, correlations, sm_mh_analysis, ai_cog_analysis):
    """Prepare all components needed for the forecast formula"""

    components = {
        'growth_factors': growth_factors,
        'correlations': correlations['cognitive_correlations'].to_dict(),
        'social_media_mental_health': {
            'correlation': sm_mh_analysis['correlation'],
            'regression_slope': sm_mh_analysis['regression']['slope'],
            'r_squared': sm_mh_analysis['regression']['r_squared']
        },
        'ai_cognitive_decline': {
            'correlation': ai_cog_analysis['correlation'],
            'decline_2022_2024': ai_cog_analysis['cognitive_decline_2022_2024']
        }
    }

    return components


# ============================================================================
# 9. VISUALIZATION
# ============================================================================

def create_visualizations(cleaned_data, normalized_data, growth_factors,
                         correlations, sm_mh_analysis, ai_cog_analysis):
    """Create comprehensive visualizations"""

    # Create figure with subplots
    fig = plt.figure(figsize=(20, 12))

    # 1. Population-Normalized Growth Comparison
    ax1 = plt.subplot(3, 3, 1)
    social = normalized_data['social_media_normalized']
    ax1.plot(social['Year'], social['Social_Media_Penetration_%'],
             marker='o', label='Social Media', linewidth=2)
    ax1.set_xlabel('Year')
    ax1.set_ylabel('Penetration (%)')
    ax1.set_title('Social Media Penetration (Population-Normalized)')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. ChatGPT Growth
    ax2 = plt.subplot(3, 3, 2)
    chatgpt = normalized_data['chatgpt_normalized']
    ax2.plot(chatgpt.index, chatgpt['ChatGPT_Penetration_Calculated_%'],
             marker='s', color='green', label='ChatGPT', linewidth=2)
    ax2.set_xlabel('Period')
    ax2.set_ylabel('Penetration (%)')
    ax2.set_title('ChatGPT Penetration (Population-Normalized)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # 3. Cognitive Index Decline
    ax3 = plt.subplot(3, 3, 3)
    cognitive = cleaned_data['cognitive']
    ax3.plot(cognitive['Year'], cognitive['Cognitive Index (2012 = 100)'],
             marker='o', color='red', linewidth=2)
    ax3.axvline(x=2022, color='gray', linestyle='--', label='ChatGPT Launch')
    ax3.set_xlabel('Year')
    ax3.set_ylabel('Cognitive Index')
    ax3.set_title('Cognitive Ability Index (2012=100)')
    ax3.legend()
    ax3.grid(True, alpha=0.3)

    # 4. Mental Health Prevalence
    ax4 = plt.subplot(3, 3, 4)
    mental = normalized_data['mental_health_normalized']
    ax4.plot(mental['Year'], mental['Mental_Health_Prevalence_%'],
             marker='o', color='orange', linewidth=2)
    ax4.set_xlabel('Year')
    ax4.set_ylabel('Prevalence (%)')
    ax4.set_title('Mental Health Disorder Prevalence')
    ax4.grid(True, alpha=0.3)

    # 5. Social Media vs Mental Health
    ax5 = plt.subplot(3, 3, 5)
    sm_mh_data = sm_mh_analysis['data']
    ax5.scatter(sm_mh_data['Social_Media_Penetration_%'],
                sm_mh_data['Mental_Health_Prevalence_%'], s=100, alpha=0.6)
    # Add regression line
    X = sm_mh_data['Social_Media_Penetration_%'].values
    y_pred = (sm_mh_analysis['regression']['slope'] * X +
              sm_mh_analysis['regression']['intercept'])
    ax5.plot(X, y_pred, 'r--', linewidth=2,
             label=f"R²={sm_mh_analysis['regression']['r_squared']:.3f}")
    ax5.set_xlabel('Social Media Penetration (%)')
    ax5.set_ylabel('Mental Health Prevalence (%)')
    ax5.set_title('Social Media vs Mental Health')
    ax5.legend()
    ax5.grid(True, alpha=0.3)

    # 6. Correlation Heatmap
    ax6 = plt.subplot(3, 3, 6)
    corr_matrix = correlations['correlation_matrix']
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, ax=ax6, cbar_kws={'shrink': 0.8})
    ax6.set_title('Correlation Matrix')

    # 7. AI Incidents Over Time
    ax7 = plt.subplot(3, 3, 7)
    incidents = cleaned_data['ai_incidents']
    ax7.bar(incidents['Year'], incidents['Total'], alpha=0.7, color='purple')
    ax7.set_xlabel('Year')
    ax7.set_ylabel('Total Incidents')
    ax7.set_title('AI Harm Incidents Over Time')
    ax7.grid(True, alpha=0.3)

    # 8. AI Capability Growth
    ax8 = plt.subplot(3, 3, 8)
    capability = cleaned_data['ai_capability']
    ax8.plot(capability['Date'], capability['P50_Hours_Max'],
             marker='o', label='P50', linewidth=2)
    ax8.plot(capability['Date'], capability['P80_Hours_Max'],
             marker='s', label='P80', linewidth=2)
    ax8.set_xlabel('Date')
    ax8.set_ylabel('Hours Max')
    ax8.set_title('AI Capability (Task Completion)')
    ax8.legend()
    ax8.grid(True, alpha=0.3)
    plt.setp(ax8.xaxis.get_majorticklabels(), rotation=45)

    # 9. Growth Factor Comparison
    ax9 = plt.subplot(3, 3, 9)
    if 'social_media' in growth_factors and 'chatgpt' in growth_factors:
        factors = ['Social Media\nCAGR', 'ChatGPT\nCAGR']
        values = [growth_factors['social_media']['cagr_%'],
                 growth_factors['chatgpt']['cagr_%']]
        colors = ['skyblue', 'lightgreen']
        bars = ax9.bar(factors, values, color=colors, alpha=0.7)
        ax9.set_ylabel('CAGR (%)')
        ax9.set_title('Growth Rate Comparison')
        ax9.grid(True, alpha=0.3, axis='y')
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax9.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig('/Users/preethamsathyamurthy/Github/Astroware/cogwatch/src/data_analysis/exploratory_analysis_comprehensive.png',
                dpi=300, bbox_inches='tight')
    print("\n✓ Saved comprehensive visualization")

    return fig


# ============================================================================
# 10. MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function"""

    print("=" * 80)
    print("COGNITIVE DEBT EXPLORATORY DATA ANALYSIS")
    print("=" * 80)

    # Load data
    print("\n[1/9] Loading data...")
    raw_data = load_all_data()

    # Clean and prepare
    print("\n[2/9] Cleaning and preparing data...")
    cleaned_data = clean_and_prepare_data(raw_data)

    # Normalize by population
    print("\n[3/9] Normalizing by population...")
    normalized_data = normalize_by_population(cleaned_data)

    # Analyze growth factors
    print("\n[4/9] Analyzing growth factors...")
    growth_factors = analyze_growth_factors(normalized_data)

    # Correlation analysis
    print("\n[5/9] Analyzing correlations...")
    correlations = analyze_correlations(cleaned_data, normalized_data)

    # Social media & mental health
    print("\n[6/9] Analyzing social media & mental health relationship...")
    sm_mh_analysis = analyze_social_media_mental_health(normalized_data, cleaned_data)

    # AI adoption & cognitive decline
    print("\n[7/9] Analyzing AI adoption & cognitive decline relationship...")
    ai_cog_analysis = analyze_ai_cognitive_relationship(cleaned_data, normalized_data)

    # Build PyTorch model
    print("\n[8/9] Building growth model with PyTorch...")
    growth_model = build_growth_model_pytorch(normalized_data)

    # Create visualizations
    print("\n[9/9] Creating visualizations...")
    fig = create_visualizations(cleaned_data, normalized_data, growth_factors,
                                correlations, sm_mh_analysis, ai_cog_analysis)

    # Prepare forecast components
    print("\nPreparing forecast components...")
    forecast_components = prepare_forecast_components(
        growth_factors, correlations, sm_mh_analysis, ai_cog_analysis
    )

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY OF KEY FINDINGS")
    print("=" * 80)

    print("\n1. GROWTH FACTORS:")
    if 'social_media' in growth_factors:
        sm = growth_factors['social_media']
        print("   Social Media (2017-2025):")
        print(f"   - CAGR: {sm['cagr_%']:.2f}%")
        print(f"   - Total Growth: {sm['total_growth_%']:.2f}%")

    if 'chatgpt' in growth_factors:
        cg = growth_factors['chatgpt']
        print("\n   ChatGPT (2022-2025):")
        print(f"   - CAGR: {cg['cagr_%']:.2f}%")
        print(f"   - Total Growth: {cg['total_growth_%']:.2f}%")

    if 'comparison' in growth_factors:
        comp = growth_factors['comparison']
        print("\n   ChatGPT vs Social Media:")
        print(f"   - Growth Acceleration Factor: {comp['growth_acceleration_factor']:.2f}x")

    print("\n2. SOCIAL MEDIA & MENTAL HEALTH:")
    print(f"   - Correlation: {sm_mh_analysis['correlation']:.3f}")
    print(f"   - R²: {sm_mh_analysis['regression']['r_squared']:.3f}")
    print(f"   - Slope: {sm_mh_analysis['regression']['slope']:.4f}")

    print("\n3. AI ADOPTION & COGNITIVE DECLINE (2022-2024):")
    decline = ai_cog_analysis['cognitive_decline_2022_2024']
    print(f"   - Total Cognitive Decline: {decline['total_decline']:.2f} points")
    print(f"   - Decline Rate: {decline['decline_rate_%']:.2f}%")
    if ai_cog_analysis['correlation'] is not None:
        print(f"   - Correlation with ChatGPT: {ai_cog_analysis['correlation']:.3f}")

    print("\n4. KEY CORRELATIONS WITH COGNITIVE INDEX:")
    cog_corr = correlations['cognitive_correlations']
    for var, corr in cog_corr.items():
        if var != 'Cognitive Index (2012 = 100)':
            print(f"   - {var}: {corr:.3f}")

    print("\n" + "=" * 80)
    print("Analysis complete! Ready for forecast model building.")
    print("=" * 80)

    return {
        'raw_data': raw_data,
        'cleaned_data': cleaned_data,
        'normalized_data': normalized_data,
        'growth_factors': growth_factors,
        'correlations': correlations,
        'sm_mh_analysis': sm_mh_analysis,
        'ai_cog_analysis': ai_cog_analysis,
        'growth_model': growth_model,
        'forecast_components': forecast_components
    }


if __name__ == "__main__":
    results = main()
