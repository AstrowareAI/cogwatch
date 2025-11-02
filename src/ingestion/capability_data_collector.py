"""
Capability Data Collector for Cogwatch
Fetches LLM benchmark scores from llm-stats.com API (MMLU, GPQA, MATH, Human Eval, etc.)
Also fetches EQ-Bench data: Emotional Intelligence, Creative Writing, Judgemark, BuzzBench
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import torch
import aiohttp
import re
import json
import csv
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from db.mongodb import get_collection


class CapabilityDataCollector:
    """Data collector for LLM capability benchmark data from llm-stats.com API"""
    
    # Key benchmarks we're interested in (mapped to API field names)
    BENCHMARK_MAPPING = {
        'MMLU': 'mmmu_score',  # Note: API uses 'mmmu_score' for MMLU
        'GPQA': 'gpqa_score',
        'Human Eval': 'humaneval_score',
        'DROP': 'drop_score',
        'AIME': 'aime_2025_score',
        'SWE-Bench': 'swe_bench_verified_score',
    }
    
    def __init__(self, collection_name: str = 'capability_snapshots'):
        self.api_url = "https://llm-stats.com/api/models"
        self.collection = get_collection(collection_name)
        
        # EQ-Bench benchmark URLs
        self.eqbench3_url = "https://eqbench.com/eqbench3_chartdata.js?v=1.0.4"
        self.creative_writing_longform_url = "https://eqbench.com/creative_writing_longform.js?v=1.0.9"
        self.creative_writing_url = "https://eqbench.com/creative_writing_chartdata.js?v=1.0.91"
        self.judgemark_url = "https://eqbench.com/judgemark-v2.js?v=1.08"
        self.buzzbench_url = "https://eqbench.com/buzzbench.js"
        
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
                open_max_value = float(torch.max(open_tensor).item())
                open_min_value = float(torch.min(open_tensor).item())
                open_median_value = float(torch.median(open_tensor).item())
                
                # Find all models with top value (handle ties)
                open_top_models = [model_name for score, model_name in open_scores 
                                  if abs(score - open_max_value) < 1e-6]
                open_top_idx = torch.argmax(open_tensor).item()
                open_top_model = open_top_models[0] if open_top_models else open_scores[open_top_idx][1]
                
                # Find all models with minimum value (handle ties)
                open_min_models = [model_name for score, model_name in open_scores 
                                  if abs(score - open_min_value) < 1e-6]
                open_min_idx = torch.argmin(open_tensor).item()
                open_min_model = open_min_models[0] if open_min_models else open_scores[open_min_idx][1]
                
                # Find model closest to median
                open_median_idx = min(range(len(open_values)), 
                                     key=lambda i: abs(open_values[i] - open_median_value))
                open_median_model = open_scores[open_median_idx][1]
                # Check for ties at median
                open_median_models = [model_name for score, model_name in open_scores 
                                      if abs(score - open_median_value) < 1e-6]
                
                # Get metadata
                top_model_data = model_lookup.get(open_top_model, {})
                min_model_data = model_lookup.get(open_min_model, {})
                median_model_data = model_lookup.get(open_median_model, {})
                
                open_stats = {
                    'top': open_max_value,
                    'top_model': open_top_model,
                    'top_models': open_top_models if len(open_top_models) > 1 else None,
                    'top_metadata': self._get_model_metadata(top_model_data),
                    'minimum': open_min_value,
                    'min_model': open_min_model,
                    'min_models': open_min_models if len(open_min_models) > 1 else None,
                    'min_metadata': self._get_model_metadata(min_model_data),
                    'median': open_median_value,
                    'median_model': open_median_model,
                    'median_models': open_median_models if len(open_median_models) > 1 else None,
                    'median_metadata': self._get_model_metadata(median_model_data),
                    'mean': float(torch.mean(open_tensor).item()),
                    'count': len(open_scores)
                }
                # Remove None values
                open_stats = {k: v for k, v in open_stats.items() if v is not None}
            
            # Calculate proprietary statistics
            proprietary_stats = {}
            if proprietary_scores:
                prop_values = [s[0] for s in proprietary_scores]
                prop_tensor = torch.tensor(prop_values, dtype=torch.float32)
                prop_max_value = float(torch.max(prop_tensor).item())
                prop_min_value = float(torch.min(prop_tensor).item())
                prop_median_value = float(torch.median(prop_tensor).item())
                
                # Find all models with top value (handle ties)
                prop_top_models = [model_name for score, model_name in proprietary_scores 
                                   if abs(score - prop_max_value) < 1e-6]
                prop_top_idx = torch.argmax(prop_tensor).item()
                prop_top_model = prop_top_models[0] if prop_top_models else proprietary_scores[prop_top_idx][1]
                
                # Find all models with minimum value (handle ties)
                prop_min_models = [model_name for score, model_name in proprietary_scores 
                                  if abs(score - prop_min_value) < 1e-6]
                prop_min_idx = torch.argmin(prop_tensor).item()
                prop_min_model = prop_min_models[0] if prop_min_models else proprietary_scores[prop_min_idx][1]
                
                # Find model closest to median
                prop_median_idx = min(range(len(prop_values)), 
                                    key=lambda i: abs(prop_values[i] - prop_median_value))
                prop_median_model = proprietary_scores[prop_median_idx][1]
                # Check for ties at median
                prop_median_models = [model_name for score, model_name in proprietary_scores 
                                      if abs(score - prop_median_value) < 1e-6]
                
                # Get metadata
                top_model_data = model_lookup.get(prop_top_model, {})
                min_model_data = model_lookup.get(prop_min_model, {})
                median_model_data = model_lookup.get(prop_median_model, {})
                
                proprietary_stats = {
                    'top': prop_max_value,
                    'top_model': prop_top_model,
                    'top_models': prop_top_models if len(prop_top_models) > 1 else None,
                    'top_metadata': self._get_model_metadata(top_model_data),
                    'minimum': prop_min_value,
                    'min_model': prop_min_model,
                    'min_models': prop_min_models if len(prop_min_models) > 1 else None,
                    'min_metadata': self._get_model_metadata(min_model_data),
                    'median': prop_median_value,
                    'median_model': prop_median_model,
                    'median_models': prop_median_models if len(prop_median_models) > 1 else None,
                    'median_metadata': self._get_model_metadata(median_model_data),
                    'mean': float(torch.mean(prop_tensor).item()),
                    'count': len(proprietary_scores)
                }
                # Remove None values
                proprietary_stats = {k: v for k, v in proprietary_stats.items() if v is not None}
            
            # Overall statistics
            overall_max_value = float(torch.max(scores_tensor).item())
            overall_min_value = float(torch.min(scores_tensor).item())
            overall_median_value = float(torch.median(scores_tensor).item())
            overall_mean_value = float(torch.mean(scores_tensor).item())
            
            # Find all models with top value (handle ties)
            overall_top_models = [model_name for score, model_name in all_scores 
                                 if abs(score - overall_max_value) < 1e-6]
            overall_top_model = overall_top_models[0] if overall_top_models else all_scores[top_idx][1]
            
            # Find all models with minimum value (handle ties)
            overall_min_models = [model_name for score, model_name in all_scores 
                                 if abs(score - overall_min_value) < 1e-6]
            overall_min_model = overall_min_models[0] if overall_min_models else all_scores[min_idx][1]
            
            # Find model closest to median
            overall_median_idx = min(range(len(all_score_values)), 
                                    key=lambda i: abs(all_score_values[i] - overall_median_value))
            overall_median_model = all_scores[overall_median_idx][1]
            # Check for ties at median
            overall_median_models = [model_name for score, model_name in all_scores 
                                    if abs(score - overall_median_value) < 1e-6]
            
            # Get metadata
            overall_top_model_data = model_lookup.get(overall_top_model, {})
            overall_min_model_data = model_lookup.get(overall_min_model, {})
            overall_median_model_data = model_lookup.get(overall_median_model, {})
            
            overall_result = {
                'top': overall_max_value,
                'top_model': overall_top_model,
                'top_models': overall_top_models if len(overall_top_models) > 1 else None,
                'top_metadata': self._get_model_metadata(overall_top_model_data),
                'minimum': overall_min_value,
                'min_model': overall_min_model,
                'min_models': overall_min_models if len(overall_min_models) > 1 else None,
                'min_metadata': self._get_model_metadata(overall_min_model_data),
                'median': overall_median_value,
                'median_model': overall_median_model,
                'median_models': overall_median_models if len(overall_median_models) > 1 else None,
                'median_metadata': self._get_model_metadata(overall_median_model_data),
                'mean': overall_mean_value,
                'count': len(all_scores)
            }
            # Remove None values
            overall_result = {k: v for k, v in overall_result.items() if v is not None}
            
            results[benchmark_name] = {
                'overall': overall_result,
                'open_source': open_stats,
                'proprietary': proprietary_stats
            }
        
        return results
    
    async def fetch_js_file(self, url: str) -> Optional[str]:
        """Fetch JavaScript file content"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"Failed to fetch {url}: {response.status}")
                        return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def parse_js_csv_data(self, js_content: str, var_name: str, header_var: Optional[str] = None) -> Optional[List[Dict]]:
        """Extract CSV data from JavaScript template literal, optionally with separate header definition"""
        # First, try to extract the header if provided
        headers = None
        if header_var:
            # Try to extract header array: const csv_header = ["col1", "col2", ...]
            header_patterns = [
                rf'(?:const|var|let)\s+{header_var}\s*=\s*\[([^\]]+)\]',
                rf'{header_var}\s*=\s*\[([^\]]+)\]',
            ]
            for pattern in header_patterns:
                match = re.search(pattern, js_content, re.DOTALL)
                if match:
                    header_str = match.group(1)
                    # Extract quoted strings
                    headers = re.findall(r'"([^"]+)"', header_str)
                    if headers:
                        break
        
        # Extract CSV data
        patterns = [
            rf'(?:const|var|let)\s+{var_name}\s*=\s*`([^`]+)`',
            rf'{var_name}\s*=\s*`([^`]+)`',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, js_content, re.DOTALL)
            if match:
                csv_data = match.group(1).strip()
                try:
                    if headers:
                        # Use provided headers
                        csv_reader = csv.DictReader(io.StringIO(csv_data), fieldnames=headers)
                        return list(csv_reader)
                    else:
                        # Try to auto-detect headers (first row as header)
                        csv_reader = csv.DictReader(io.StringIO(csv_data))
                        return list(csv_reader)
                except Exception as e:
                    print(f"  ⚠ Warning: Failed to parse CSV for {var_name}: {e}")
                    return None
        return None
    
    def parse_js_json_data(self, js_content: str, var_name: str) -> Optional[Dict]:
        """Extract JSON data from JavaScript file (looks for const varName = {...})"""
        # Try to extract JSON object from JS using balanced brace matching
        # Find the variable assignment
        patterns = [
            rf'(?:const|var|let)\s+{var_name}\s*=\s*({{)',
            rf'{var_name}\s*=\s*({{)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, js_content, re.DOTALL)
            if match:
                start_pos = match.end() - 1  # Position of opening brace
                brace_count = 0
                i = start_pos
                
                # Find the matching closing brace
                while i < len(js_content):
                    if js_content[i] == '{':
                        brace_count += 1
                    elif js_content[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            # Found matching brace
                            json_str = js_content[start_pos:i+1]
                            try:
                                # Remove trailing commas before } or ]
                                json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                                return json.loads(json_str)
                            except json.JSONDecodeError:
                                # Try one more time with more aggressive cleanup
                                try:
                                    # Remove comments and trailing commas
                                    json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
                                    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
                                    return json.loads(json_str)
                                except json.JSONDecodeError:
                                    break
                    i += 1
        
        return None
    
    def _extract_metric_statistics(self, metric_name: str, metric_scores: List[tuple], model_lookup: Dict) -> Dict:
        """Helper to calculate statistics for a single metric"""
        if not metric_scores:
            return {}
        
        metric_values = [s[0] for s in metric_scores]
        scores_tensor = torch.tensor(metric_values, dtype=torch.float32)
        
        max_value = float(torch.max(scores_tensor).item())
        min_value = float(torch.min(scores_tensor).item())
        median_value = float(torch.median(scores_tensor).item())
        mean_value = float(torch.mean(scores_tensor).item())
        
        # Find all models with top value (handle ties)
        top_models = [model_name for score, model_name in metric_scores if abs(score - max_value) < 1e-6]
        top_model = top_models[0] if top_models else metric_scores[0][1]
        top_model_data = model_lookup.get(top_model, {})
        
        # Find all models with minimum value (handle ties)
        min_models = [model_name for score, model_name in metric_scores if abs(score - min_value) < 1e-6]
        min_model = min_models[0] if min_models else metric_scores[0][1]
        min_model_data = model_lookup.get(min_model, {})
        
        # Find model closest to median (and collect all models at median if tied)
        median_idx = min(range(len(metric_values)), 
                        key=lambda i: abs(metric_values[i] - median_value))
        median_model = metric_scores[median_idx][1]
        # Check for ties at median value
        median_models = [model_name for score, model_name in metric_scores 
                        if abs(score - median_value) < 1e-6]
        median_model_data = model_lookup.get(median_model, {})
        
        # Return statistics directly (not wrapped in 'overall')
        # Only use 'overall' key for actual overall scores, individual metrics get direct statistics
        result = {
            'top': max_value,
            'top_model': top_model,
            'top_models': top_models if len(top_models) > 1 else None,  # Only include if multiple
            'top_metadata': top_model_data,
            'minimum': min_value,
            'min_model': min_model,
            'min_models': min_models if len(min_models) > 1 else None,  # Only include if multiple
            'min_metadata': min_model_data,
            'median': median_value,
            'median_model': median_model,
            'median_models': median_models if len(median_models) > 1 else None,  # Only include if multiple
            'median_metadata': median_model_data,
            'mean': mean_value,
            'count': len(metric_scores)
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
    
    def extract_eqbench3_data(self, chart_data: Dict) -> Dict[str, Dict]:
        """Extract EQ-Bench 3 (Emotional Intelligence) data - ALL individual metrics"""
        results = {}
        
        if not isinstance(chart_data, dict):
            print(f"  ✗ Warning: chart_data is not a dictionary, got {type(chart_data)}")
            return {}
        
        # Collect all metrics from absoluteRadar and relativeRadar
        # Structure: each model has absoluteRadar {labels: [...], values: [...]}
        model_lookup = {}
        all_metrics_data = {}  # metric_name -> [(score, model_name)]
        
        try:
            # First pass: collect all metrics and their values per model
            for model_name, data in chart_data.items():
                if not isinstance(data, dict):
                    continue
                
                model_data = {'model': model_name}
                
                # Extract absoluteRadar metrics
                absolute_radar = data.get('absoluteRadar', {})
                if isinstance(absolute_radar, dict):
                    labels = absolute_radar.get('labels', [])
                    values = absolute_radar.get('values', [])
                    
                    if labels and values and len(labels) == len(values):
                        for label, value in zip(labels, values):
                            try:
                                metric_name = f"absolute_{label}"
                                if metric_name not in all_metrics_data:
                                    all_metrics_data[metric_name] = []
                                all_metrics_data[metric_name].append((float(value), model_name))
                                model_data[f'absolute_{label}'] = float(value)
                            except (ValueError, TypeError):
                                continue
                
                # Extract relativeRadarLog metrics
                relative_radar = data.get('relativeRadarLog', {})
                if isinstance(relative_radar, dict):
                    labels = relative_radar.get('labels', [])
                    values = relative_radar.get('values', [])
                    
                    if labels and values and len(labels) == len(values):
                        for label, value in zip(labels, values):
                            try:
                                metric_name = f"relative_{label}"
                                if metric_name not in all_metrics_data:
                                    all_metrics_data[metric_name] = []
                                all_metrics_data[metric_name].append((float(value), model_name))
                                model_data[f'relative_{label}'] = float(value)
                            except (ValueError, TypeError):
                                continue
                
                model_lookup[model_name] = model_data
            
            # Second pass: calculate statistics for each metric
            for metric_name, metric_scores in all_metrics_data.items():
                # Format metric name for display
                display_name = metric_name.replace('absolute_', '').replace('relative_', '')
                if metric_name.startswith('absolute_'):
                    display_name = f"{display_name} (Absolute)"
                elif metric_name.startswith('relative_'):
                    display_name = f"{display_name} (Relative)"
                
                stats = self._extract_metric_statistics(display_name, metric_scores, model_lookup)
                if stats:
                    results[display_name] = stats
            
        except Exception as e:
            print(f"  ✗ Error extracting EQ-Bench 3 data: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        return results
    
    def extract_creative_writing_data(self, chart_data: Dict, benchmark_name: str) -> Dict[str, Dict]:
        """Extract Creative Writing benchmark data - ALL individual metrics"""
        results = {}
        
        if not isinstance(chart_data, dict):
            print(f"  ✗ Warning: chart_data is not a dictionary for {benchmark_name}, got {type(chart_data)}")
            return {}
        
        model_lookup = {}
        all_metrics_data = {}  # metric_name -> [(score, model_name)]
        
        try:
            # Extract all metrics from each model
            for model_name, data in chart_data.items():
                if not isinstance(data, dict):
                    continue
                
                model_data = {'model': model_name}
                
                # Extract all numeric fields from the model data
                # Common metrics: score, length, slop, repetition, degradation, rubric_score, elo_score, etc.
                for key, value in data.items():
                    # Skip non-numeric or nested structures, and skip model identifiers
                    if key in ['absoluteRadar', 'relativeRadarLog', 'strengths', 'weaknesses', 'model', 'model_name']:
                        continue
                    
                    # Handle CSV data (all values are strings initially)
                    if isinstance(value, str):
                        # Try to parse as number (remove $, commas, etc.)
                        clean_value = value.replace('$', '').replace(',', '').strip()
                        try:
                            numeric_value = float(clean_value)
                            if not (numeric_value != numeric_value):  # Not NaN
                                all_metrics_data.setdefault(key, []).append((numeric_value, model_name))
                                model_data[key] = numeric_value
                        except (ValueError, TypeError):
                            continue
                    # Handle already numeric values
                    elif isinstance(value, (int, float)):
                        try:
                            numeric_value = float(value)
                            if not (numeric_value != numeric_value):  # Not NaN
                                all_metrics_data.setdefault(key, []).append((numeric_value, model_name))
                                model_data[key] = numeric_value
                        except (ValueError, TypeError):
                            continue
                
                # Also check absoluteRadar structure if present
                if 'absoluteRadar' in data:
                    absolute_radar = data.get('absoluteRadar', {})
                    if isinstance(absolute_radar, dict):
                        labels = absolute_radar.get('labels', [])
                        values = absolute_radar.get('values', [])
                        if labels and values and len(labels) == len(values):
                            for label, value in zip(labels, values):
                                try:
                                    numeric_value = float(value)
                                    if not (numeric_value != numeric_value):
                                        all_metrics_data.setdefault(label, []).append((numeric_value, model_name))
                                        model_data[label] = numeric_value
                                except (ValueError, TypeError):
                                    continue
                
                # Calculate degradation for Longform Creative Writing
                # Formula: Degradation Score = (Initial Chapter Average Score - Final Chapter Average Score) / Initial Chapter Average Score
                # Where Initial = chapter1_avg and Final = chapter8_avg
                if benchmark_name == 'Creative Writing Longform':
                    chapter_keys = [f'chapter{i}_avg' for i in range(1, 9)]
                    chapter_scores = []
                    for ch_key in chapter_keys:
                        ch_val = data.get(ch_key)
                        if ch_val:
                            try:
                                if isinstance(ch_val, str):
                                    chapter_scores.append(float(ch_val.replace('$', '').replace(',', '').strip()))
                                else:
                                    chapter_scores.append(float(ch_val))
                            except (ValueError, TypeError):
                                pass
                    
                    if len(chapter_scores) >= 2:
                        # Calculate degradation using the correct formula (no * 100, returns decimal)
                        # Degradation Score = (Initial - Final) / Initial
                        # Negative values are capped at 0 (no degradation if scores improve)
                        initial_score = chapter_scores[0]  # chapter1_avg
                        final_score = chapter_scores[-1]    # chapter8_avg
                        if initial_score > 0:
                            degradation = (initial_score - final_score) / initial_score
                            # Cap at 0 - no negative degradation (improvement = 0 degradation)
                            degradation = max(0.0, degradation)
                            all_metrics_data.setdefault('degradation', []).append((degradation, model_name))
                            model_data['degradation'] = degradation
                
                model_lookup[model_name] = model_data
            
            # Calculate statistics for each metric
            for metric_name, metric_scores in all_metrics_data.items():
                # Format metric name for display (capitalize, handle underscores)
                display_name = metric_name.replace('_', ' ').title()
                
                stats = self._extract_metric_statistics(display_name, metric_scores, model_lookup)
                if stats:
                    results[display_name] = stats
            
        except Exception as e:
            print(f"  ✗ Error extracting {benchmark_name} data: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        return results
    
    def store_in_mongodb(self, data: Dict) -> bool:
        """
        Store capability data snapshot in MongoDB
        
        Args:
            data: The result dictionary from scrape() method
            
        Returns:
            bool: True if successfully stored, False otherwise
        """
        try:
            # Create document with datetime field
            document = {
                'datetime': datetime.now(timezone.utc),
                'timestamp': data.get('timestamp', datetime.now(timezone.utc).isoformat()),
                'success': data.get('success', True),
                'sources': data.get('sources', []),
                'capabilities': data.get('capabilities', {}),
                'summary': data.get('summary', {})
            }
            
            # Only add error field if present
            if 'error' in data:
                document['error'] = data['error']
            
            # Insert document into MongoDB
            result = self.collection.insert_one(document)
            
            if result.inserted_id:
                print(f"✓ Successfully stored capability snapshot in MongoDB (ID: {result.inserted_id})")
                return True
            else:
                print("✗ Failed to store capability snapshot in MongoDB")
                return False
                
        except Exception as e:
            print(f"✗ Error storing capability data in MongoDB: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def scrape(self) -> Dict:
        """
        Main scraping method
        Returns: Dict with hierarchical structure organized by capability type and source
        Structure:
        {
            'keyCapabilities': {
                'LLMStats': {MMLU, GPQA, Human Eval, ...}
            },
            'emotionalIntelligence': {
                'eqbench3': {...}
            },
            'creativeWriting': {
                'creativeWriting': {...},
                'creativeWritingLongform': {...}
            },
            'judgemark': {
                'judgemark': {...}
            },
            'buzzbench': {
                'buzzbench': {...}
            }
        }
        """
        results = {
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'sources': [],
            'capabilities': {}
        }
        
        # 1. Key Capabilities from LLMStats API
        print(f"Fetching key capability data from {self.api_url}...")
        models_data = await self.fetch_api_data()
        
        if models_data:
            print(f"Received data for {len(models_data)} models")
            print("Extracting benchmark scores...")
            benchmark_data = self.extract_benchmark_data(models_data)
            if benchmark_data:
                results['capabilities']['keyCapabilities'] = {
                    'LLMStats': benchmark_data
                }
                results['sources'].append(self.api_url)
                print(f"✓ Successfully loaded {len(benchmark_data)} key capability benchmark(s)")
        else:
            print("⚠ Warning: Failed to fetch LLMStats API data")
        
        # 2. Emotional Intelligence from EQ-Bench 3
        print("\nFetching Emotional Intelligence (EQ-Bench 3) data...")
        try:
            js_content = await self.fetch_js_file(self.eqbench3_url)
            if js_content:
                chart_data = self.parse_js_json_data(js_content, 'chartData')
                if chart_data:
                    eqbench3_data = self.extract_eqbench3_data(chart_data)
                    if eqbench3_data:
                        results['capabilities']['emotionalIntelligence'] = {
                            'eqbench3': eqbench3_data
                        }
                        results['sources'].append(self.eqbench3_url)
                        print("✓ Successfully loaded EQ-Bench 3 data")
        except Exception as e:
            print(f"⚠ Warning: Error fetching EQ-Bench 3: {e}")
        
        # 3. Creative Writing
        print("\nFetching Creative Writing data...")
        creative_writing_results = {}
        
        # Creative Writing (standard)
        try:
            js_content = await self.fetch_js_file(self.creative_writing_url)
            if js_content:
                chart_data = self.parse_js_json_data(js_content, 'chartData')
                if not chart_data:
                    chart_data = self.parse_js_json_data(js_content, 'data')
                if chart_data:
                    extracted = self.extract_creative_writing_data(chart_data, 'Creative Writing')
                    if extracted:
                        creative_writing_results['creativeWriting'] = extracted
                        print("✓ Successfully loaded Creative Writing data")
        except Exception as e:
            print(f"⚠ Warning: Error fetching Creative Writing: {e}")
        
        # Creative Writing Longform (CSV format)
        try:
            js_content = await self.fetch_js_file(self.creative_writing_longform_url)
            if js_content:
                # Try CSV first (most likely)
                csv_data = self.parse_js_csv_data(js_content, 'leaderboardDataLongformV3')
                if csv_data:
                    # Convert CSV to dict format
                    chart_data = {}
                    for row in csv_data:
                        model_name = row.get('model_name', '')
                        if model_name:
                            chart_data[model_name] = row
                    
                    extracted = self.extract_creative_writing_data(chart_data, 'Creative Writing Longform')
                    if extracted:
                        creative_writing_results['creativeWritingLongform'] = extracted
                        print("✓ Successfully loaded Creative Writing Longform data")
                else:
                    # Fallback to JSON parsing
                    chart_data = self.parse_js_json_data(js_content, 'chartData')
                    if not chart_data:
                        chart_data = self.parse_js_json_data(js_content, 'data')
                    if chart_data:
                        extracted = self.extract_creative_writing_data(chart_data, 'Creative Writing Longform')
                        if extracted:
                            creative_writing_results['creativeWritingLongform'] = extracted
                            print("✓ Successfully loaded Creative Writing Longform data")
        except Exception as e:
            print(f"⚠ Warning: Error fetching Creative Writing Longform: {e}")
        
        if creative_writing_results:
            results['capabilities']['creativeWriting'] = creative_writing_results
            # Add sources for successfully loaded benchmarks
            if 'creativeWriting' in creative_writing_results:
                results['sources'].append(self.creative_writing_url)
            if 'creativeWritingLongform' in creative_writing_results:
                results['sources'].append(self.creative_writing_longform_url)
        
        # 4. Judgemark (CSV format)
        print("\nFetching Judgemark v2 data...")
        try:
            js_content = await self.fetch_js_file(self.judgemark_url)
            if js_content:
                csv_data = self.parse_js_csv_data(js_content, 'leaderboardDataV2', header_var='csv_header')
                if csv_data:
                    # Convert CSV to dict format for extraction
                    chart_data = {}
                    for row in csv_data:
                        model_name = row.get('model') or row.get('model_name', '')
                        if model_name:
                            # Clean model name (remove * prefix, etc.)
                            model_name = model_name.lstrip('*').strip()
                            chart_data[model_name] = row
                    
                    extracted = self.extract_creative_writing_data(chart_data, 'Judgemark')
                    if extracted:
                        results['capabilities']['judgemark'] = {
                            'judgemark': extracted
                        }
                        results['sources'].append(self.judgemark_url)
                        print("✓ Successfully loaded Judgemark v2 data")
                else:
                    print("  ⚠ Warning: Failed to parse Judgemark CSV data")
        except Exception as e:
            print(f"⚠ Warning: Error fetching Judgemark v2: {e}")
        
        # 5. BuzzBench (CSV format)
        print("\nFetching BuzzBench data...")
        try:
            js_content = await self.fetch_js_file(self.buzzbench_url)
            if js_content:
                csv_data = self.parse_js_csv_data(js_content, 'leaderboardDataBuzzbench')
                if csv_data:
                    # Convert CSV to dict format
                    chart_data = {}
                    for row in csv_data:
                        model_name = row.get('model', '')
                        if model_name:
                            model_name = model_name.lstrip('*').strip()
                            chart_data[model_name] = row
                    
                    extracted = self.extract_creative_writing_data(chart_data, 'BuzzBench')
                    if extracted:
                        results['capabilities']['buzzbench'] = {
                            'buzzbench': extracted
                        }
                        results['sources'].append(self.buzzbench_url)
                        print("✓ Successfully loaded BuzzBench data")
                else:
                    print("  ⚠ Warning: Failed to parse BuzzBench CSV data")
        except Exception as e:
            print(f"⚠ Warning: Error fetching BuzzBench: {e}")
        
        # Summary
        total_benchmarks = 0
        for capability_type, sources in results['capabilities'].items():
            for source_name, benchmarks in sources.items():
                if isinstance(benchmarks, dict):
                    total_benchmarks += len(benchmarks)
        
        results['summary'] = {
            'total_capability_types': len(results['capabilities']),
            'total_benchmarks': total_benchmarks,
            'capability_types': list(results['capabilities'].keys())
        }
        
        if not results['capabilities']:
            results['success'] = False
            results['error'] = 'Failed to fetch any capability data'
        
        # Store in MongoDB
        self.store_in_mongodb(results)
        
        return results


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


def _print_benchmark_stats(benchmark_name: str, data: Dict, indent: str = "  "):
    """Helper to print benchmark statistics"""
    # Check if this is an actual overall score (like LLMStats benchmarks) or individual metric stats
    # Individual metrics have stats directly, overall scores have 'overall' key
    overall = data.get('overall', {})
    if overall:
        # This is an actual overall score (e.g., from LLMStats API)
        print(f"{indent}Overall:")
        # Handle ties - show all models if multiple share the same value
        top_str = overall['top_model']
        if 'top_models' in overall and overall['top_models']:
            top_str = ', '.join(overall['top_models'])
        print(f"{indent}  Top: {overall['top']:.4f} ({top_str})")
        
        min_str = overall['min_model']
        if 'min_models' in overall and overall['min_models']:
            min_str = ', '.join(overall['min_models'])
        print(f"{indent}  Minimum: {overall['minimum']:.4f} ({min_str})")
        
        median_str = overall.get('median_model', 'N/A')
        if 'median_models' in overall and overall['median_models']:
            median_str = ', '.join(overall['median_models'])
        print(f"{indent}  Median: {overall['median']:.4f} ({median_str})")
        print(f"{indent}  Mean: {overall['mean']:.4f}")
        print(f"{indent}  Count: {overall['count']}")
        
        # Open source stats (only for API benchmarks)
        if 'open_source' in data and data.get('open_source'):
            open_data = data['open_source']
            print(f"{indent}Open Source:")
            open_top_str = open_data['top_model']
            if 'top_models' in open_data and open_data['top_models']:
                open_top_str = ', '.join(open_data['top_models'])
            print(f"{indent}  Top: {open_data['top']:.4f} ({open_top_str})")
            
            open_min_str = open_data['min_model']
            if 'min_models' in open_data and open_data['min_models']:
                open_min_str = ', '.join(open_data['min_models'])
            print(f"{indent}  Minimum: {open_data['minimum']:.4f} ({open_min_str})")
            
            open_median_str = open_data.get('median_model', 'N/A')
            if 'median_models' in open_data and open_data['median_models']:
                open_median_str = ', '.join(open_data['median_models'])
            print(f"{indent}  Median: {open_data['median']:.4f} ({open_median_str})")
            print(f"{indent}  Mean: {open_data['mean']:.4f}")
            print(f"{indent}  Count: {open_data['count']}")
        
        # Proprietary stats (only for API benchmarks)
        if 'proprietary' in data and data.get('proprietary'):
            prop_data = data['proprietary']
            print(f"{indent}Proprietary:")
            prop_top_str = prop_data['top_model']
            if 'top_models' in prop_data and prop_data['top_models']:
                prop_top_str = ', '.join(prop_data['top_models'])
            print(f"{indent}  Top: {prop_data['top']:.4f} ({prop_top_str})")
            
            prop_min_str = prop_data['min_model']
            if 'min_models' in prop_data and prop_data['min_models']:
                prop_min_str = ', '.join(prop_data['min_models'])
            print(f"{indent}  Minimum: {prop_data['minimum']:.4f} ({prop_min_str})")
            
            prop_median_str = prop_data.get('median_model', 'N/A')
            if 'median_models' in prop_data and prop_data['median_models']:
                prop_median_str = ', '.join(prop_data['median_models'])
            print(f"{indent}  Median: {prop_data['median']:.4f} ({prop_median_str})")
            print(f"{indent}  Mean: {prop_data['mean']:.4f}")
            print(f"{indent}  Count: {prop_data['count']}")
    else:
        # This is an individual metric with direct statistics (no 'overall' wrapper)
        if 'top' in data:
            # Handle ties - show all models if multiple share the same value
            top_str = data['top_model']
            if 'top_models' in data and data['top_models']:
                top_str = ', '.join(data['top_models'])
            print(f"{indent}  Top: {data['top']:.4f} ({top_str})")
            
            min_str = data['min_model']
            if 'min_models' in data and data['min_models']:
                min_str = ', '.join(data['min_models'])
            print(f"{indent}  Minimum: {data['minimum']:.4f} ({min_str})")
            
            median_str = data.get('median_model', 'N/A')
            if 'median_models' in data and data['median_models']:
                median_str = ', '.join(data['median_models'])
            print(f"{indent}  Median: {data['median']:.4f} ({median_str})")
            print(f"{indent}  Mean: {data['mean']:.4f}")
            print(f"{indent}  Count: {data['count']}")


async def main():
    """Test the data collector"""
    collector = CapabilityDataCollector()
    result = await collector.scrape()
    
    print("\n" + "="*60)
    print("CAPABILITY BENCHMARK SUMMARY")
    print("="*60)
    
    if result['success']:
        capabilities = result.get('capabilities', {})
        
        # Key Capabilities (LLMStats)
        if 'keyCapabilities' in capabilities:
            print("\n📊 KEY CAPABILITIES (LLMStats API):")
            llmstats_data = capabilities['keyCapabilities'].get('LLMStats', {})
            for benchmark_name, benchmark_data in sorted(llmstats_data.items()):
                print(f"\n  {benchmark_name}:")
                _print_benchmark_stats(benchmark_name, benchmark_data, indent="    ")
        
        # Emotional Intelligence (EQ-Bench 3)
        if 'emotionalIntelligence' in capabilities:
            print("\n🧠 EMOTIONAL INTELLIGENCE (EQ-Bench 3):")
            eqbench3_data = capabilities['emotionalIntelligence'].get('eqbench3', {})
            for benchmark_name, benchmark_data in sorted(eqbench3_data.items()):
                print(f"\n  {benchmark_name}:")
                _print_benchmark_stats(benchmark_name, benchmark_data, indent="    ")
        
        # Creative Writing
        if 'creativeWriting' in capabilities:
            print("\n✍️ CREATIVE WRITING:")
            creative_data = capabilities['creativeWriting']
            for source_name, benchmarks in sorted(creative_data.items()):
                print(f"\n  {source_name}:")
                for benchmark_name, benchmark_data in sorted(benchmarks.items()):
                    print(f"    {benchmark_name}:")
                    _print_benchmark_stats(benchmark_name, benchmark_data, indent="      ")
        
        # Judgemark
        if 'judgemark' in capabilities:
            print("\n⚖️ JUDGEMARK:")
            judgemark_data = capabilities['judgemark'].get('judgemark', {})
            for benchmark_name, benchmark_data in sorted(judgemark_data.items()):
                print(f"\n  {benchmark_name}:")
                _print_benchmark_stats(benchmark_name, benchmark_data, indent="    ")
        
        # BuzzBench
        if 'buzzbench' in capabilities:
            print("\n😄 BUZZBENCH:")
            buzzbench_data = capabilities['buzzbench'].get('buzzbench', {})
            for benchmark_name, benchmark_data in sorted(buzzbench_data.items()):
                print(f"\n  {benchmark_name}:")
                _print_benchmark_stats(benchmark_name, benchmark_data, indent="    ")
        
        print(f"\n{'='*60}")
        summary = result.get('summary', {})
        print(f"Total Capability Types: {summary.get('total_capability_types', 0)}")
        print(f"Total Benchmarks: {summary.get('total_benchmarks', 0)}")
        print(f"Sources: {len(result.get('sources', []))}")
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())