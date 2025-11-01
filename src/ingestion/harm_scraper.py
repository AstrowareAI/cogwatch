"""
Harm/Misalignment Data Scraper for Cogwatch
Scrapes Spiral-Bench leaderboard and fetches data from AI Incident Database
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import torch
import aiohttp
from bs4 import BeautifulSoup
import re
import json


class HarmScraper:
    """Scraper for harm/misalignment data from Spiral-Bench and AI Incident DB"""
    
    def __init__(self):
        self.spiral_bench_url = "https://eqbench.com/spiral-bench.html"
        self.spiral_bench_js_url = "https://eqbench.com/spiral-bench.js?v=1.0.1"
        self.incident_db_url = "https://incidentdatabase.ai/api/graphql"
        
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
        import csv
        import io
        
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
        # The page might use a table, divs, or JavaScript-rendered content
        # We'll look for common patterns
        
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
                            
                            # Look for safety score (usually numeric, possibly 0-100)
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
        
        # Method 2: Look for data embedded in script tags (common for JS-rendered tables)
        if not models_data:
            scripts = soup.find_all('script')
            for script in scripts:
                script_text = script.string
                if script_text and ('safety' in script_text.lower() or 'spiral' in script_text.lower()):
                    # Try to extract JSON data
                    json_matches = re.findall(r'\{[^{}]*"model"[^{}]*\}', script_text)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'model' in data or 'safety' in str(data).lower():
                                models_data.append(data)
                        except json.JSONDecodeError:
                            continue
            
            # Also try to find data attributes or data-* attributes
            data_elements = soup.find_all(attrs={'data-model': True})
            for elem in data_elements:
                model_name = elem.get('data-model') or elem.get_text(strip=True)
                safety_attr = elem.get('data-safety-score') or elem.get('data-score')
                if model_name and safety_attr:
                    try:
                        model_data = {
                            'model': model_name,
                            'safety_score': float(safety_attr)
                        }
                        
                        # Extract other metric attributes
                        for metric in self.INDIVIDUAL_METRICS:
                            metric_attr = elem.get(f'data-{metric}')
                            if metric_attr:
                                try:
                                    model_data[metric] = float(metric_attr)
                                except (ValueError, TypeError):
                                    pass
                        
                        models_data.append(model_data)
                    except (ValueError, TypeError):
                        continue
        
        # Method 3: Fallback - look for structured divs or lists
        if not models_data:
            # Look for elements with class names that suggest model entries
            model_elements = soup.find_all(class_=re.compile(r'model|entry|row', re.I))
            for elem in model_elements:
                model_text = elem.get_text()
                # Look for patterns like "Model Name: X, Safety Score: Y"
                model_match = re.search(r'([A-Za-z0-9\-_\.]+(?:[:\s]+[A-Za-z0-9\-_\.]+)*)', model_text)
                safety_match = re.search(r'safety[:\s]+(\d+\.?\d*)', model_text, re.I)
                
                if model_match and safety_match:
                    model_data = {
                        'model': model_match.group(1).strip(),
                        'safety_score': float(safety_match.group(1))
                    }
                    models_data.append(model_data)
        
        return models_data
    
    def _get_model_metadata(self, model_data: Dict) -> Dict:
        """Extract metadata from model data (similar to capability scraper structure)"""
        # Spiral-Bench has limited metadata, but we'll structure it consistently
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
        # Use the index from argmax to ensure we get the correct model
        top_idx = torch.argmax(scores_tensor).item()
        top_model_from_idx = metric_scores[top_idx][1]
        top_models = [model_name for score, model_name in metric_scores if abs(score - max_value) < 1e-6]
        # Use the model from argmax if top_models list is empty (shouldn't happen, but safe fallback)
        top_model = top_models[0] if top_models else top_model_from_idx
        top_model_data = model_lookup.get(top_model, {})
        
        # Find all models with minimum value (handle ties)
        min_idx = torch.argmin(scores_tensor).item()
        min_model_from_idx = metric_scores[min_idx][1]
        min_models = [model_name for score, model_name in metric_scores if abs(score - min_value) < 1e-6]
        # Use the model from argmin if min_models list is empty
        min_model = min_models[0] if min_models else min_model_from_idx
        min_model_data = model_lookup.get(min_model, {})
        
        # Find model closest to median (and collect all models at median if tied)
        median_idx = min(range(len(metric_values)), 
                        key=lambda i: abs(metric_values[i] - median_value))
        median_model = metric_scores[median_idx][1]
        # Check for ties at median value
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
        """
        Extract safety score data with detailed statistics (similar structure to capability scraper)
        Returns: Dict with 'Safety Score' as key, containing comprehensive stats with 'overall' wrapper
        """
        if not models_data:
            return {}
        
        # Collect all scores with full model info
        all_scores = []  # (score, model_name)
        model_lookup = {}
        
        for model in models_data:
            safety_score = model.get('safety_score')
            if safety_score is not None:
                try:
                    score_float = float(safety_score)
                    model_name = model.get('model', 'Unknown')
                    
                    # Store model data for metadata lookup
                    model_lookup[model_name] = model
                    
                    all_scores.append((score_float, model_name))
                except (ValueError, TypeError):
                    continue
        
        if not all_scores:
            return {}
        
        # Use helper method to calculate statistics with tie handling
        stats = self._extract_metric_statistics(all_scores, model_lookup)
        
        # Wrap in 'overall' since this is an actual overall score
        return {
            'Safety Score': {
                'overall': stats
            }
        }
    
    def extract_individual_metric_data(self, models_data: List[Dict]) -> Dict[str, Dict]:
        """
        Extract individual metric data with detailed statistics (similar structure to capability scraper)
        Returns: Dict with metric names as keys, containing direct statistics (no 'overall' wrapper)
        """
        results = {}
        
        # Create a mapping from model name to full model data for lookup
        model_lookup = {}
        for model in models_data:
            model_name = model.get('model', 'Unknown')
            model_lookup[model_name] = model
        
        for metric in self.INDIVIDUAL_METRICS:
            # Collect all scores with full model info
            metric_scores = []  # (score, model_name)
            
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
            
            # Use helper method to calculate statistics with tie handling
            stats = self._extract_metric_statistics(metric_scores, model_lookup)
            
            # Format metric name for display (convert kebab-case to Title Case)
            metric_display = metric.replace('-', ' ').title()
            
            # Return direct statistics (no 'overall' wrapper for individual metrics)
            results[metric_display] = stats
        
        return results
    
    async def fetch_incident_db_data(self, query: Optional[str] = None) -> Optional[Dict]:
        """
        Fetch data from AI Incident Database GraphQL API
        If query is None, uses a default query to get recent incidents
        """
        if query is None:
            # Default query to get recent incidents with basic info
            query = """
            query {
                incidents(first: 100, orderBy: date_submitted, orderDirection: desc) {
                    edges {
                        node {
                            id
                            title
                            date_submitted
                            date_harms_started
                            description
                            nlp_method
                            authors
                        }
                    }
                }
            }
            """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.incident_db_url,
                    json={'query': query},
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        print(f"AI Incident DB API request failed: {response.status}")
                        error_text = await response.text()
                        print(f"Error details: {error_text}")
                        return None
        except Exception as e:
            print(f"Error fetching AI Incident DB data: {e}")
            return None
    
    async def scrape_spiral_bench(self) -> Dict:
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
        
        # Combine safety score and individual metrics into a single 'metrics' structure
        # (similar to 'benchmarks' in capability scraper)
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
    
    async def scrape_incident_db(self, limit: int = 100) -> Dict:
        """Scrape AI Incident Database"""
        print(f"Fetching AI Incident DB data from {self.incident_db_url}...")
        
        # Query for recent incidents
        query = f"""
        query {{
            incidents(first: {limit}, orderBy: date_submitted, orderDirection: desc) {{
                edges {{
                    node {{
                        id
                        title
                        date_submitted
                        date_harms_started
                        description
                        nlp_method
                        authors
                        severity
                    }}
                }}
            }}
        }}
        """
        
        data = await self.fetch_incident_db_data(query)
        
        if not data:
            return {
                'success': False,
                'error': 'Failed to fetch AI Incident DB data',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        
        # Extract incidents from GraphQL response
        incidents = []
        if 'data' in data and 'incidents' in data['data']:
            edges = data['data']['incidents'].get('edges', [])
            for edge in edges:
                incidents.append(edge.get('node', {}))
        
        return {
            'success': True,
            'source': self.incident_db_url,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'incidents': incidents,
            'summary': {
                'total_incidents': len(incidents)
            }
        }
    
    async def scrape(self) -> Dict:
        """
        Main scraping method - fetches both Spiral-Bench and AI Incident DB data
        """
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'spiral_bench': {},
            'incident_db': {}
        }
        
        # Scrape Spiral-Bench
        spiral_results = await self.scrape_spiral_bench()
        results['spiral_bench'] = spiral_results
        
        # Scrape AI Incident DB
        incident_results = await self.scrape_incident_db()
        results['incident_db'] = incident_results
        
        return results


async def main():
    """Test the harm scraper"""
    scraper = HarmScraper()
    result = await scraper.scrape()
    
    print("\n" + "="*50)
    print("HARM/MISALIGNMENT DATA SUMMARY")
    print("="*50)
    
    # Spiral-Bench results
    if result['spiral_bench'].get('success'):
        spiral_data = result['spiral_bench']
        print("\n📊 SPIRAL-BENCH RESULTS:")
        
        metrics = spiral_data.get('metrics', {})
        if metrics:
            for metric_name, metric_info in metrics.items():
                print(f"\n  {metric_name}:")
                
                # Check if this is an actual overall score (Safety Score) or individual metric
                overall = metric_info.get('overall', {})
                if overall:
                    # This is Safety Score (actual overall score)
                    print("    Overall:")
                    
                    # Handle ties - show all models if multiple share the same value
                    top_str = overall['top_model']
                    if 'top_models' in overall and overall['top_models']:
                        top_str = ', '.join(overall['top_models'])
                    print(f"      Top: {overall['top']:.4f} ({top_str})")
                    
                    # Show individual scores for top model
                    if overall.get('top_metadata') and overall['top_metadata'].get('individual_scores'):
                        top_meta = overall['top_metadata']
                        print("      Individual scores for top model:")
                        for ind_metric, score in top_meta['individual_scores'].items():
                            if score is not None:
                                ind_display = ind_metric.replace('-', ' ').title()
                                print(f"        {ind_display}: {score:.4f}")
                    
                    min_str = overall['min_model']
                    if 'min_models' in overall and overall['min_models']:
                        min_str = ', '.join(overall['min_models'])
                    print(f"      Minimum: {overall['minimum']:.4f} ({min_str})")
                    
                    # Show individual scores for minimum model
                    if overall.get('min_metadata') and overall['min_metadata'].get('individual_scores'):
                        min_meta = overall['min_metadata']
                        print("      Individual scores for minimum model:")
                        for ind_metric, score in min_meta['individual_scores'].items():
                            if score is not None:
                                ind_display = ind_metric.replace('-', ' ').title()
                                print(f"        {ind_display}: {score:.4f}")
                    
                    median_str = overall.get('median_model', 'N/A')
                    if 'median_models' in overall and overall['median_models']:
                        median_str = ', '.join(overall['median_models'])
                    print(f"      Median: {overall['median']:.4f} ({median_str})")
                    
                    # Show individual scores for median model
                    if overall.get('median_metadata') and overall['median_metadata'].get('individual_scores'):
                        median_meta = overall['median_metadata']
                        print("      Individual scores for median model:")
                        for ind_metric, score in median_meta['individual_scores'].items():
                            if score is not None:
                                ind_display = ind_metric.replace('-', ' ').title()
                                print(f"        {ind_display}: {score:.4f}")
                    
                    print(f"      Mean: {overall['mean']:.4f}")
                    print(f"      Count: {overall['count']}")
                else:
                    # This is an individual metric with direct statistics (no 'overall' wrapper)
                    if 'top' in metric_info:
                        # Handle ties - show all models if multiple share the same value
                        top_str = metric_info['top_model']
                        if 'top_models' in metric_info and metric_info['top_models']:
                            top_str = ', '.join(metric_info['top_models'])
                        print(f"      Top: {metric_info['top']:.4f} ({top_str})")
                        
                        min_str = metric_info['min_model']
                        if 'min_models' in metric_info and metric_info['min_models']:
                            min_str = ', '.join(metric_info['min_models'])
                        print(f"      Minimum: {metric_info['minimum']:.4f} ({min_str})")
                        
                        median_str = metric_info.get('median_model', 'N/A')
                        if 'median_models' in metric_info and metric_info['median_models']:
                            median_str = ', '.join(metric_info['median_models'])
                        print(f"      Median: {metric_info['median']:.4f} ({median_str})")
                        print(f"      Mean: {metric_info['mean']:.4f}")
                        print(f"      Count: {metric_info['count']}")
    else:
        print("\n❌ SPIRAL-BENCH: Failed")
        print(f"   Error: {result['spiral_bench'].get('error', 'Unknown')}")
        if 'debug_info' in result['spiral_bench']:
            print(f"   Debug: {result['spiral_bench']['debug_info']}")
    
    # AI Incident DB results
    if result['incident_db'].get('success'):
        incident_data = result['incident_db']
        print("\n\n📋 AI INCIDENT DATABASE RESULTS:")
        print(f"  Total incidents fetched: {incident_data['summary']['total_incidents']}")
        
        if incident_data.get('incidents'):
            print("\n  Recent incidents (first 5):")
            for i, incident in enumerate(incident_data['incidents'][:5], 1):
                print(f"    {i}. {incident.get('title', 'N/A')}")
                print(f"       Date: {incident.get('date_submitted', 'N/A')}")
    else:
        print("\n❌ AI INCIDENT DB: Failed")
        print(f"   Error: {result['incident_db'].get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())
