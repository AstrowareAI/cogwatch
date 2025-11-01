"""
SpiralBench Data Collector for Cogwatch
Collects Spiral-Bench leaderboard data for safety scores and metrics
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import torch
import aiohttp
from bs4 import BeautifulSoup
import re
import json
import csv
import io


class SpiralBenchDataCollector:
    """Data collector for Spiral-Bench leaderboard data"""
    
    def __init__(self):
        self.spiral_bench_url = "https://eqbench.com/spiral-bench.html"
        self.spiral_bench_js_url = "https://eqbench.com/spiral-bench.js?v=1.0.1"
        
        # Individual metrics from Spiral-Bench (based on the rubric)
        self.INDIVIDUAL_METRICS = [
            'pushback',
            'escalation',
            'de-escalation',
            'sycophancy',
            'benign-warmth',
            'delusion-reinforcement',
            'topic-shut-down',
            'help-referral-warranted',
            'help-referral-unwarranted',
            'positive-sentience-claim',
            'uncertain-sentience-claim',
            'negative-sentience-claim',
            'harmful-advice',
            'confident-bullshitting',
            'boundary-setting',
            'validate-feelings-not-thoughts',
            'ritualization',
            'off-rails'
        ]
    
    async def fetch_spiral_bench_js(self) -> Optional[str]:
        """Fetch JavaScript file containing CSV data from Spiral-Bench"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.spiral_bench_js_url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"Failed to fetch Spiral-Bench JS file: {response.status}")
                        return None
        except Exception as e:
            print(f"Error fetching Spiral-Bench JS file: {e}")
            return None
    
    def parse_csv_from_js(self, js_content: str) -> List[Dict]:
        """
        Parse CSV data from JavaScript template literal
        Looks for the leaderboardDataDelusion variable containing CSV data
        """
        # Try to extract CSV data from the JS file
        # The CSV is in a template literal like: const leaderboardDataDelusion = `model_name,score_norm,...`
        csv_pattern = r'leaderboardDataDelusion\s*=\s*`([^`]+)`'
        match = re.search(csv_pattern, js_content, re.DOTALL)
        
        if not match:
            # Try alternative patterns
            csv_pattern = r'const\s+leaderboardDataDelusion\s*=\s*`([^`]+)`'
            match = re.search(csv_pattern, js_content, re.DOTALL)
        
        if not match:
            print("Could not find CSV data in JS file")
            return []
        
        csv_data = match.group(1).strip()
        
        # Parse CSV
        models_data = []
        csv_reader = csv.DictReader(io.StringIO(csv_data))
        
        for row in csv_reader:
            model_data = {
                'model': row.get('model_name', '').strip(),
                'safety_score': None,
                'score_norm': None,
                'score_0_100': None
            }
            
            # Parse safety score (prefer score_0_100, fallback to score_norm)
            score_0_100 = row.get('score_0_100', '').strip()
            score_norm = row.get('score_norm', '').strip()
            
            if score_0_100:
                try:
                    model_data['safety_score'] = float(score_0_100)
                    model_data['score_0_100'] = float(score_0_100)
                except (ValueError, TypeError):
                    pass
            elif score_norm:
                try:
                    model_data['safety_score'] = float(score_norm)
                    model_data['score_norm'] = float(score_norm)
                except (ValueError, TypeError):
                    pass
            
            # Parse all individual metrics
            for metric in self.INDIVIDUAL_METRICS:
                value_str = row.get(metric, '').strip()
                if value_str:
                    try:
                        model_data[metric] = float(value_str)
                    except (ValueError, TypeError):
                        pass
            
            # Only add if we have a model name and safety score
            if model_data['model'] and model_data['safety_score'] is not None:
                models_data.append(model_data)
        
        return models_data
    
    async def fetch_spiral_bench_html(self) -> Optional[str]:
        """Fetch HTML content from Spiral-Bench leaderboard (fallback method)"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.spiral_bench_url) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"Failed to fetch Spiral-Bench page: {response.status}")
                        return None
        except Exception as e:
            print(f"Error fetching Spiral-Bench HTML: {e}")
            return None
    
    def parse_spiral_bench_data(self, html: str) -> List[Dict]:
        """
        Parse Spiral-Bench leaderboard HTML to extract model scores
        Returns: List of model dictionaries with safety scores and individual metrics
        """
        soup = BeautifulSoup(html, 'html.parser')
        models_data = []
        
        # Try to find the leaderboard table or data structure
        # Method 1: Look for a table with model data
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            headers = []
            
            # Get headers from first row
            if rows:
                header_row = rows[0]
                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                
                # Check if this looks like a leaderboard table
                if 'model' in ' '.join(headers) or 'safety' in ' '.join(headers) or 'score' in ' '.join(headers):
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 2:
                            continue
                        
                        model_data = {}
                        
                        # First cell is likely model name
                        model_name = cells[0].get_text(strip=True)
                        if not model_name:
                            continue
                        model_data['model'] = model_name
                        
                        # Try to extract safety score
                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            
                            if i < len(headers):
                                header = headers[i]
                                
                                # Safety score might be in a column named "safety", "score", etc.
                                if 'safety' in header or ('score' in header and 'safety' not in header):
                                    try:
                                        safety_score = float(cell_text)
                                        model_data['safety_score'] = safety_score
                                    except (ValueError, TypeError):
                                        pass
                                
                                # Try to extract individual metrics
                                header_normalized = header.lower().replace(' ', '-').replace('_', '-')
                                if header_normalized in self.INDIVIDUAL_METRICS:
                                    try:
                                        metric_value = float(cell_text)
                                        model_data[header_normalized] = metric_value
                                    except (ValueError, TypeError):
                                        pass
                        
                        if 'safety_score' in model_data:
                            models_data.append(model_data)
        
        # Method 2: Look for data embedded in script tags
        if not models_data:
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string
                if script_text and ('safety' in script_text.lower() or 'spiral' in script_text.lower()):
                    json_matches = re.findall(r'\{[^{}]*"model"[^{}]*\}', script_text)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'model' in data or 'safety' in str(data).lower():
                                models_data.append(data)
                        except json.JSONDecodeError:
                            continue
        
        return models_data
    
    def _get_model_metadata(self, model_data: Dict) -> Dict:
        """Extract metadata from model data"""
        individual_scores = {
            metric: model_data.get(metric)
            for metric in self.INDIVIDUAL_METRICS
            if metric in model_data
        }
        
        return {
            'model_name': model_data.get('model'),
            'safety_score': model_data.get('safety_score'),
            'score_norm': model_data.get('score_norm'),
            'score_0_100': model_data.get('score_0_100'),
            'individual_scores': individual_scores
        }
    
    def _extract_metric_statistics(self, metric_scores: List[tuple], model_lookup: Dict) -> Dict:
        """Helper to calculate statistics for a single metric (handles ties)"""
        if not metric_scores:
            return {}
        
        metric_values = [s[0] for s in metric_scores]
        scores_tensor = torch.tensor(metric_values, dtype=torch.float32)
        
        max_value = float(torch.max(scores_tensor).item())
        min_value = float(torch.min(scores_tensor).item())
        median_value = float(torch.median(scores_tensor).item())
        mean_value = float(torch.mean(scores_tensor).item())
        
        # Find all models with top value (handle ties)
        top_idx = torch.argmax(scores_tensor).item()
        top_model_from_idx = metric_scores[top_idx][1]
        top_models = [model_name for score, model_name in metric_scores if abs(score - max_value) < 1e-6]
        top_model = top_models[0] if top_models else top_model_from_idx
        top_model_data = model_lookup.get(top_model, {})
        
        # Find all models with minimum value (handle ties)
        min_idx = torch.argmin(scores_tensor).item()
        min_model_from_idx = metric_scores[min_idx][1]
        min_models = [model_name for score, model_name in metric_scores if abs(score - min_value) < 1e-6]
        min_model = min_models[0] if min_models else min_model_from_idx
        min_model_data = model_lookup.get(min_model, {})
        
        # Find model closest to median
        median_idx = min(range(len(metric_values)), 
                        key=lambda i: abs(metric_values[i] - median_value))
        median_model = metric_scores[median_idx][1]
        median_models = [model_name for score, model_name in metric_scores 
                        if abs(score - median_value) < 1e-6]
        median_model_data = model_lookup.get(median_model, {})
        
        result = {
            'top': max_value,
            'top_model': top_model,
            'top_models': top_models if len(top_models) > 1 else None,
            'top_metadata': self._get_model_metadata(top_model_data),
            'minimum': min_value,
            'min_model': min_model,
            'min_models': min_models if len(min_models) > 1 else None,
            'min_metadata': self._get_model_metadata(min_model_data),
            'median': median_value,
            'median_model': median_model,
            'median_models': median_models if len(median_models) > 1 else None,
            'median_metadata': self._get_model_metadata(median_model_data),
            'mean': mean_value,
            'count': len(metric_scores)
        }
        
        # Remove None values for cleaner output
        return {k: v for k, v in result.items() if v is not None}
    
    def extract_safety_score_data(self, models_data: List[Dict]) -> Dict[str, Dict]:
        """Extract safety score data with detailed statistics"""
        if not models_data:
            return {}
        
        # Collect all scores with full model info
        all_scores = []
        model_lookup = {}
        
        for model in models_data:
            safety_score = model.get('safety_score')
            if safety_score is not None:
                try:
                    score_float = float(safety_score)
                    model_name = model.get('model', 'Unknown')
                    model_lookup[model_name] = model
                    all_scores.append((score_float, model_name))
                except (ValueError, TypeError):
                    continue
        
        if not all_scores:
            return {}
        
        stats = self._extract_metric_statistics(all_scores, model_lookup)
        
        return {
            'Safety Score': {
                'overall': stats
            }
        }
    
    def extract_individual_metric_data(self, models_data: List[Dict]) -> Dict[str, Dict]:
        """Extract individual metric data with detailed statistics"""
        results = {}
        
        model_lookup = {}
        for model in models_data:
            model_name = model.get('model', 'Unknown')
            model_lookup[model_name] = model
        
        for metric in self.INDIVIDUAL_METRICS:
            metric_scores = []
            
            for model_data in models_data:
                metric_value = model_data.get(metric)
                if metric_value is not None:
                    try:
                        value_float = float(metric_value)
                        model_name = model_data.get('model', 'Unknown')
                        metric_scores.append((value_float, model_name))
                    except (ValueError, TypeError):
                        continue
            
            if not metric_scores:
                continue
            
            stats = self._extract_metric_statistics(metric_scores, model_lookup)
            metric_display = metric.replace('-', ' ').title()
            results[metric_display] = stats
        
        return results
    
    async def scrape(self) -> Dict:
        """
        Scrape Spiral-Bench leaderboard data
        First tries to fetch CSV data from JS file, falls back to HTML scraping
        """
        # First attempt: Fetch CSV data from JavaScript file (preferred method)
        print(f"Attempting to fetch Spiral-Bench data from JS file: {self.spiral_bench_js_url}...")
        js_content = await self.fetch_spiral_bench_js()
        
        models_data = []
        source_used = None
        
        if js_content:
            print("Parsing CSV data from JS file...")
            models_data = self.parse_csv_from_js(js_content)
            source_used = self.spiral_bench_js_url
            
            if models_data:
                print(f"Successfully parsed {len(models_data)} models from JS file")
        
        # Fallback: HTML scraping if JS method failed
        if not models_data:
            print("JS method failed, falling back to HTML scraping...")
            html = await self.fetch_spiral_bench_html()
            
            if html:
                print("Parsing Spiral-Bench HTML...")
                models_data = self.parse_spiral_bench_data(html)
                source_used = self.spiral_bench_url
            else:
                return {
                    'success': False,
                    'error': 'Failed to fetch Spiral-Bench data (both JS and HTML methods failed)',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
        
        if not models_data:
            return {
                'success': False,
                'error': 'Failed to parse model data from Spiral-Bench',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': source_used
            }
        
        print(f"Found data for {len(models_data)} models")
        print("Extracting safety score data...")
        safety_score_data = self.extract_safety_score_data(models_data)
        
        if not safety_score_data:
            return {
                'success': False,
                'error': 'Failed to extract safety score data',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': source_used
            }
        
        print("Extracting individual metric data...")
        metric_data = self.extract_individual_metric_data(models_data)
        
        # Combine safety score and individual metrics
        all_metrics = {**safety_score_data, **metric_data}
        
        return {
            'success': True,
            'source': source_used,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metrics': all_metrics,
            'summary': {
                'total_metrics': len(all_metrics),
                'metric_names': list(all_metrics.keys()),
                'total_models': len(models_data)
            }
        }

