"""
Harm/Misalignment Data Scraper Coordinator for Cogwatch
Coordinates SpiralBench and AI Incident Database scrapers
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict

from .spiralbench_scraper import SpiralBenchScraper
from .incidentdb_sync import IncidentDBSync


class HarmScraper:
    """Coordinator for harm/misalignment data from Spiral-Bench and AI Incident DB"""
    
    def __init__(self):
        self.spiral_bench_scraper = SpiralBenchScraper()
        self.incident_db_sync = IncidentDBSync()
    
    async def scrape(self) -> Dict:
        """
        Main scraping method - fetches both Spiral-Bench and AI Incident DB data
        
        Returns:
            Dictionary with results from both scrapers
        """
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'spiral_bench': {},
            'incident_db': {}
        }
        
        # Scrape Spiral-Bench
        spiral_results = await self.spiral_bench_scraper.scrape()
        results['spiral_bench'] = spiral_results
        
        # Fetch AI Incident DB data from API (using sync's API methods)
        incident_results = await self.incident_db_sync.fetch_recent_from_api()
        results['incident_db'] = incident_results
        
        return results
    
    async def scrape_recent_incidents(self, days: int = 7, limit: int = 100) -> Dict:
        """
        Fetch recent incidents from the last N days (via API)
        
        Args:
            days: Number of days to look back
            limit: Maximum number of incidents to fetch
            
        Returns:
            Dictionary with recent incidents
        """
        return await self.incident_db_sync.fetch_by_date_range(days=days, limit=limit)


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
                    
                    min_str = overall['min_model']
                    if 'min_models' in overall and overall['min_models']:
                        min_str = ', '.join(overall['min_models'])
                    print(f"      Minimum: {overall['minimum']:.4f} ({min_str})")
                    
                    median_str = overall.get('median_model', 'N/A')
                    if 'median_models' in overall and overall['median_models']:
                        median_str = ', '.join(overall['median_models'])
                    print(f"      Median: {overall['median']:.4f} ({median_str})")
                    
                    print(f"      Mean: {overall['mean']:.4f}")
                    print(f"      Count: {overall['count']}")
                else:
                    # This is an individual metric
                    if 'top' in metric_info:
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
    
    # AI Incident DB results
    if result['incident_db'].get('success'):
        incident_data = result['incident_db']
        summary = incident_data['summary']
        print("\n\n📋 AI INCIDENT DATABASE RESULTS:")
        print(f"  Total incidents fetched: {summary['total_incidents']}")
        print(f"  Total reports: {summary['total_reports']}")
        print(f"  Incidents with classifications: {summary.get('incidents_with_classifications', 0)}")
        
        if incident_data.get('incidents'):
            print("\n  Recent incidents (first 5):")
            for i, incident in enumerate(incident_data['incidents'][:5], 1):
                print(f"\n    {i}. {incident.get('title', 'N/A')}")
                print(f"       Incident ID: {incident.get('incident_id', 'N/A')}")
                print(f"       Date: {incident.get('date', 'N/A')}")
                print(f"       Date Modified: {incident.get('date_modified', 'N/A')}")
                print(f"       Report Count: {incident.get('report_count', 0)}")
                
                # Show classifications if available
                classifications = incident.get('classifications', [])
                if classifications:
                    cls_str = ', '.join([f"{c.get('namespace', '')}:{c.get('attribute', '')}" 
                                        for c in classifications[:3]])
                    print(f"       Classifications: {cls_str}")
                
                # Show entities if available
                entities = incident.get('entities', [])
                if entities:
                    entity_str = ', '.join([f"{e.get('name', '')} ({e.get('role', '')})" 
                                           for e in entities[:3]])
                    print(f"       Entities: {entity_str}")
                
                # Show first report URL if available
                reports = incident.get('reports', [])
                if reports and reports[0].get('url'):
                    print(f"       First Report URL: {reports[0].get('url')}")
    else:
        print("\n❌ AI INCIDENT DB: Failed")
        print(f"   Error: {result['incident_db'].get('error', 'Unknown')}")


if __name__ == "__main__":
    asyncio.run(main())

