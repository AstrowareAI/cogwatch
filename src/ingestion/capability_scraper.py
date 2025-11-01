"""
Capability Data Scraper for Cogwatch
Fetches LLM benchmark scores from llm-stats.com API (MMLU, GPQA, MATH, Human Eval, etc.)
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import torch
import aiohttp


class CapabilityScraper:
    """Scraper for LLM capability benchmark data from llm-stats.com API"""
    
    # Key benchmarks we're interested in (mapped to API field names)
    BENCHMARK_MAPPING = {
        'MMLU': 'mmmu_score',  # Note: API uses 'mmmu_score' for MMLU
        'GPQA': 'gpqa_score',
        'Human Eval': 'humaneval_score',
        'DROP': 'drop_score',
        'AIME': 'aime_2025_score',
        'SWE-Bench': 'swe_bench_verified_score',
    }
    
    def __init__(self):
        self.api_url = "https://llm-stats.com/api/models"
        
    async def fetch_api_data(self) -> Optional[List[Dict]]:
        """Fetch benchmark data from the LLM-Stats API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"API request failed with status {response.status}")
                        return None
        except Exception as e:
            print(f"Error fetching API data: {e}")
            return None
    
    def _is_open_source(self, license_str: Optional[str]) -> bool:
        """Determine if a license is considered open source"""
        if not license_str:
            return False
        
        license_lower = license_str.lower()
        proprietary_keywords = ['proprietary', 'commercial']
        open_keywords = ['mit', 'apache', 'llama', 'apache_2_0', 'cc_by_nc', 
                        'deepseek', 'qwen', 'gemma', 'nvidia_open', 'mistral_research']
        
        # Check for proprietary first
        if any(keyword in license_lower for keyword in proprietary_keywords):
            return False
        
        # Check for open source
        if any(keyword in license_lower for keyword in open_keywords):
            return True
        
        # Default to proprietary if unclear
        return False
    
    def _format_price(self, price: Optional[float]) -> Optional[float]:
        """Format price from scientific notation to dollars (rounded)"""
        if price is None:
            return None
        try:
            # Convert to float and round to reasonable precision
            price_float = float(price)
            # Round to 10 decimal places to handle very small values
            # This ensures we get a clean decimal representation
            return round(price_float, 10)
        except (ValueError, TypeError):
            return None
    
    def _format_price_display(self, price: Optional[float]) -> str:
        """Format price for display (converts scientific notation to readable decimal)"""
        if price is None:
            return "N/A"
        try:
            price_float = float(price)
            # Use f-string formatting to avoid scientific notation for display
            # For very small values, show with enough precision
            if price_float < 0.0001:
                # For very small prices, format with up to 10 decimal places
                formatted = f"{price_float:.10f}".rstrip('0').rstrip('.')
                return formatted
            else:
                return f"{price_float:.6f}".rstrip('0').rstrip('.')
        except (ValueError, TypeError):
            return "N/A"
    
    def _get_model_metadata(self, model: Dict) -> Dict:
        """Extract metadata from model data"""
        # Convert multimodal to boolean (0/1 or False/True)
        multimodal_value = model.get('multimodal')
        is_multimodal = bool(multimodal_value) if multimodal_value is not None else None
        
        return {
            'context': model.get('context'),
            'country': model.get('organization_country'),
            'organization': model.get('organization'),
            'input_price': self._format_price(model.get('input_price')),
            'output_price': self._format_price(model.get('output_price')),
            'multimodal': is_multimodal,
            'knowledge_cutoff': model.get('knowledge_cutoff'),
            'params': model.get('params')  # Number of parameters (in billions typically)
        }
    
    def extract_benchmark_data(self, models_data: List[Dict]) -> Dict[str, Dict]:
        """
        Extract benchmark scores from API data with detailed statistics
        Returns: Dict with benchmark names as keys, containing comprehensive stats
        """
        results = {}
        
        for benchmark_name, api_field in self.BENCHMARK_MAPPING.items():
            if api_field is None:
                continue
            
            # Collect all scores with full model info
            all_scores = []  # (score, model_data)
            open_scores = []  # (score, model_data)
            proprietary_scores = []  # (score, model_data)
            
            # Create a mapping from model name to full model data for lookup
            model_lookup = {}
            
            for model in models_data:
                score = model.get(api_field)
                if score is not None:
                    try:
                        score_float = float(score)
                        model_name = model.get('name', model.get('model_id', 'Unknown'))
                        is_open = self._is_open_source(model.get('license'))
                        
                        # Store model data for metadata lookup
                        model_lookup[model_name] = model
                        
                        all_scores.append((score_float, model_name))
                        
                        if is_open:
                            open_scores.append((score_float, model_name))
                        else:
                            proprietary_scores.append((score_float, model_name))
                    except (ValueError, TypeError):
                        continue
            
            if not all_scores:
                continue
            
            # Calculate overall statistics
            all_score_values = [s[0] for s in all_scores]
            scores_tensor = torch.tensor(all_score_values, dtype=torch.float32)
            
            # Find top and minimum models
            top_idx = torch.argmax(scores_tensor).item()
            min_idx = torch.argmin(scores_tensor).item()
            
            # Calculate open source statistics
            open_stats = {}
            if open_scores:
                open_values = [s[0] for s in open_scores]
                open_tensor = torch.tensor(open_values, dtype=torch.float32)
                open_top_idx = torch.argmax(open_tensor).item()
                open_min_idx = torch.argmin(open_tensor).item()
                open_median_value = float(torch.median(open_tensor).item())
                
                # Find model closest to median
                open_median_idx = min(range(len(open_values)), 
                                     key=lambda i: abs(open_values[i] - open_median_value))
                
                # Get metadata for top, min, and median models
                top_model_data = model_lookup.get(open_scores[open_top_idx][1], {})
                min_model_data = model_lookup.get(open_scores[open_min_idx][1], {})
                median_model_data = model_lookup.get(open_scores[open_median_idx][1], {})
                
                open_stats = {
                    'top': float(torch.max(open_tensor).item()),
                    'top_model': open_scores[open_top_idx][1],
                    'top_metadata': self._get_model_metadata(top_model_data),
                    'minimum': float(torch.min(open_tensor).item()),
                    'min_model': open_scores[open_min_idx][1],
                    'min_metadata': self._get_model_metadata(min_model_data),
                    'median': open_median_value,
                    'median_model': open_scores[open_median_idx][1],
                    'median_metadata': self._get_model_metadata(median_model_data),
                    'mean': float(torch.mean(open_tensor).item()),
                    'count': len(open_scores)
                }
            
            # Calculate proprietary statistics
            proprietary_stats = {}
            if proprietary_scores:
                prop_values = [s[0] for s in proprietary_scores]
                prop_tensor = torch.tensor(prop_values, dtype=torch.float32)
                prop_top_idx = torch.argmax(prop_tensor).item()
                prop_min_idx = torch.argmin(prop_tensor).item()
                prop_median_value = float(torch.median(prop_tensor).item())
                
                # Find model closest to median
                prop_median_idx = min(range(len(prop_values)), 
                                    key=lambda i: abs(prop_values[i] - prop_median_value))
                
                # Get metadata for top, min, and median models
                top_model_data = model_lookup.get(proprietary_scores[prop_top_idx][1], {})
                min_model_data = model_lookup.get(proprietary_scores[prop_min_idx][1], {})
                median_model_data = model_lookup.get(proprietary_scores[prop_median_idx][1], {})
                
                proprietary_stats = {
                    'top': float(torch.max(prop_tensor).item()),
                    'top_model': proprietary_scores[prop_top_idx][1],
                    'top_metadata': self._get_model_metadata(top_model_data),
                    'minimum': float(torch.min(prop_tensor).item()),
                    'min_model': proprietary_scores[prop_min_idx][1],
                    'min_metadata': self._get_model_metadata(min_model_data),
                    'median': prop_median_value,
                    'median_model': proprietary_scores[prop_median_idx][1],
                    'median_metadata': self._get_model_metadata(median_model_data),
                    'mean': float(torch.mean(prop_tensor).item()),
                    'count': len(proprietary_scores)
                }
            
            # Overall statistics
            overall_median_value = float(torch.median(scores_tensor).item())
            overall_median_idx = min(range(len(all_score_values)), 
                                    key=lambda i: abs(all_score_values[i] - overall_median_value))
            
            # Get metadata for overall top, min, and median models
            overall_top_model_data = model_lookup.get(all_scores[top_idx][1], {})
            overall_min_model_data = model_lookup.get(all_scores[min_idx][1], {})
            overall_median_model_data = model_lookup.get(all_scores[overall_median_idx][1], {})
            
            results[benchmark_name] = {
                'overall': {
                    'top': float(torch.max(scores_tensor).item()),
                    'top_model': all_scores[top_idx][1],
                    'top_metadata': self._get_model_metadata(overall_top_model_data),
                    'minimum': float(torch.min(scores_tensor).item()),
                    'min_model': all_scores[min_idx][1],
                    'min_metadata': self._get_model_metadata(overall_min_model_data),
                    'median': overall_median_value,
                    'median_model': all_scores[overall_median_idx][1],
                    'median_metadata': self._get_model_metadata(overall_median_model_data),
                    'mean': float(torch.mean(scores_tensor).item()),
                    'count': len(all_scores)
                },
                'open_source': open_stats,
                'proprietary': proprietary_stats
            }
        
        return results
    
    async def scrape(self) -> Dict:
        """
        Main scraping method
        Returns: Dict with metadata and benchmark results
        """
        print(f"Fetching capability data from {self.api_url}...")
        models_data = await self.fetch_api_data()
        
        if not models_data:
            return {
                'success': False,
                'error': 'Failed to fetch API data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        print(f"Received data for {len(models_data)} models")
        print("Extracting benchmark scores...")
        benchmark_data = self.extract_benchmark_data(models_data)
        
        if not benchmark_data:
            return {
                'success': False,
                'error': 'Failed to extract benchmark data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        return {
            'success': True,
            'source': self.api_url,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'benchmarks': benchmark_data,
            'summary': {
                'total_benchmarks': len(benchmark_data),
                'benchmark_names': list(benchmark_data.keys()),
                'total_models': len(models_data)
            }
        }


def _format_price_display(price: Optional[float]) -> str:
    """Format price for display (converts scientific notation to readable decimal)"""
    if price is None:
        return "N/A"
    try:
        price_float = float(price)
        # Use f-string formatting to avoid scientific notation for display
        # For very small values, show with enough precision
        if price_float < 0.0001:
            # For very small prices, format with up to 10 decimal places
            formatted = f"{price_float:.10f}".rstrip('0').rstrip('.')
            return formatted
        else:
            return f"{price_float:.6f}".rstrip('0').rstrip('.')
    except (ValueError, TypeError):
        return "N/A"


def _print_metadata(metadata: Dict, indent: str = "      "):
    """Helper to print model metadata"""
    if metadata:
        print(f"{indent}Context: {metadata.get('context', 'N/A')}")
        print(f"{indent}Organization: {metadata.get('organization', 'N/A')}")
        print(f"{indent}Country: {metadata.get('country', 'N/A')}")
        
        # Multimodal (boolean)
        multimodal = metadata.get('multimodal')
        multimodal_str = "Yes" if multimodal is True else ("No" if multimodal is False else "N/A")
        print(f"{indent}Multimodal: {multimodal_str}")
        
        # Knowledge cutoff
        knowledge_cutoff = metadata.get('knowledge_cutoff')
        print(f"{indent}Knowledge Cutoff: {knowledge_cutoff if knowledge_cutoff else 'N/A'}")
        
        # Parameters
        params = metadata.get('params')
        if params is not None:
            # Format parameters - if large, show in billions
            if params >= 1_000_000_000:
                params_str = f"{params / 1_000_000_000:.1f}B"
            elif params >= 1_000_000:
                params_str = f"{params / 1_000_000:.1f}M"
            else:
                params_str = f"{params:,.0f}"
            print(f"{indent}Parameters: {params_str}")
        else:
            print(f"{indent}Parameters: N/A")
        
        # Prices
        input_price = metadata.get('input_price')
        output_price = metadata.get('output_price')
        input_display = _format_price_display(input_price)
        output_display = _format_price_display(output_price)
        input_str = f"${input_display}" if input_display != "N/A" else "N/A"
        output_str = f"${output_display}" if output_display != "N/A" else "N/A"
        print(f"{indent}Input Price: {input_str}")
        print(f"{indent}Output Price: {output_str}")


async def main():
    """Test the scraper"""
    scraper = CapabilityScraper()
    result = await scraper.scrape()
    
    if result['success']:
        print("\n" + "="*50)
        print("BENCHMARK SUMMARY")
        print("="*50)
        for benchmark, data in result['benchmarks'].items():
            print(f"\n{benchmark}:")
            
            # Overall stats
            overall = data['overall']
            print("  Overall:")
            print(f"    Top: {overall['top']:.4f} ({overall['top_model']})")
            if 'top_metadata' in overall:
                _print_metadata(overall['top_metadata'])
            print(f"    Minimum: {overall['minimum']:.4f} ({overall['min_model']})")
            if 'min_metadata' in overall:
                _print_metadata(overall['min_metadata'])
            print(f"    Median: {overall['median']:.4f} ({overall.get('median_model', 'N/A')})")
            if 'median_metadata' in overall:
                _print_metadata(overall['median_metadata'])
            print(f"    Mean: {overall['mean']:.4f}")
            print(f"    Count: {overall['count']}")
            
            # Open source stats
            if data['open_source']:
                open_data = data['open_source']
                print("  Open Source:")
                print(f"    Top: {open_data['top']:.4f} ({open_data['top_model']})")
                if 'top_metadata' in open_data:
                    _print_metadata(open_data['top_metadata'])
                print(f"    Minimum: {open_data['minimum']:.4f} ({open_data['min_model']})")
                if 'min_metadata' in open_data:
                    _print_metadata(open_data['min_metadata'])
                print(f"    Median: {open_data['median']:.4f} ({open_data.get('median_model', 'N/A')})")
                if 'median_metadata' in open_data:
                    _print_metadata(open_data['median_metadata'])
                print(f"    Mean: {open_data['mean']:.4f}")
                print(f"    Count: {open_data['count']}")
            
            # Proprietary stats
            if data['proprietary']:
                prop_data = data['proprietary']
                print("  Proprietary:")
                print(f"    Top: {prop_data['top']:.4f} ({prop_data['top_model']})")
                if 'top_metadata' in prop_data:
                    _print_metadata(prop_data['top_metadata'])
                print(f"    Minimum: {prop_data['minimum']:.4f} ({prop_data['min_model']})")
                if 'min_metadata' in prop_data:
                    _print_metadata(prop_data['min_metadata'])
                print(f"    Median: {prop_data['median']:.4f} ({prop_data.get('median_model', 'N/A')})")
                if 'median_metadata' in prop_data:
                    _print_metadata(prop_data['median_metadata'])
                print(f"    Mean: {prop_data['mean']:.4f}")
                print(f"    Count: {prop_data['count']}")
            
            print()
    else:
        print(f"Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())