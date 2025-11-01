"""
Safety Depth Data Collector Coordinator for Cogwatch
Coordinates scraping and syncing of safety research articles from Anthropic and Apollo Research
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict

from .anthropic_scraper import AnthropicAlignmentScraper
from .apollo_scraper import ApolloResearchScraper
from .safety_articles_sync import SafetyArticlesSync


class SafetyDataCollector:
    """Coordinator for safety depth data from Anthropic and Apollo Research"""
    
    def __init__(self, collection_name: str = 'safety_depth_articles'):
        self.anthropic_scraper = AnthropicAlignmentScraper()
        self.apollo_scraper = ApolloResearchScraper()
        self.sync = SafetyArticlesSync(collection_name=collection_name)
    
    async def scrape_all(self) -> Dict:
        """
        Main scraping method - fetches articles from both sources
        
        Returns:
            Dictionary with results from both scrapers
        """
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'anthropic': {},
            'apollo': {},
            'sync': {}
        }
        
        # Scrape Anthropic articles
        print("\n" + "="*60)
        print("SCRAPING ANTHROPIC ALIGNMENT BLOG")
        print("="*60)
        try:
            anthropic_articles = await self.anthropic_scraper.scrape_all_articles()
            results['anthropic'] = {
                'success': True,
                'articles_found': len(anthropic_articles),
                'articles': anthropic_articles
            }
        except Exception as e:
            print(f"  ❌ Error scraping Anthropic: {e}")
            results['anthropic'] = {
                'success': False,
                'error': str(e),
                'articles_found': 0,
                'articles': []
            }
        finally:
            await self.anthropic_scraper.close()
        
        # Scrape Apollo Research articles
        print("\n" + "="*60)
        print("SCRAPING APOLLO RESEARCH")
        print("="*60)
        try:
            apollo_articles = await self.apollo_scraper.scrape_all_articles()
            results['apollo'] = {
                'success': True,
                'articles_found': len(apollo_articles),
                'articles': apollo_articles
            }
        except Exception as e:
            print(f"  ❌ Error scraping Apollo: {e}")
            results['apollo'] = {
                'success': False,
                'error': str(e),
                'articles_found': 0,
                'articles': []
            }
        finally:
            await self.apollo_scraper.close()
        
        # Sync all articles to MongoDB
        print("\n" + "="*60)
        print("SYNCING ARTICLES TO MONGODB")
        print("="*60)
        
        all_articles = []
        if results['anthropic'].get('success'):
            all_articles.extend(results['anthropic'].get('articles', []))
        if results['apollo'].get('success'):
            all_articles.extend(results['apollo'].get('articles', []))
        
        if all_articles:
            sync_result = self.sync.sync_articles(all_articles)
            results['sync'] = sync_result
        else:
            results['sync'] = {
                'success': False,
                'error': 'No articles to sync',
                'total_articles': 0,
                'inserted': 0,
                'skipped': 0,
                'errors': 0
            }
        
        # Summary
        results['summary'] = {
            'total_articles_scraped': len(all_articles),
            'total_inserted': results['sync'].get('inserted', 0),
            'total_skipped': results['sync'].get('skipped', 0),
            'total_errors': results['sync'].get('errors', 0)
        }
        
        return results


async def main():
    """Test the safety data collector"""
    collector = SafetyDataCollector()
    result = await collector.scrape_all()
    
    print("\n" + "="*60)
    print("SAFETY DEPTH DATA COLLECTION SUMMARY")
    print("="*60)
    
    # Anthropic results
    if result['anthropic'].get('success'):
        print(f"\n✓ Anthropic Alignment Blog:")
        print(f"  Articles scraped: {result['anthropic']['articles_found']}")
    else:
        print(f"\n❌ Anthropic Alignment Blog:")
        print(f"  Error: {result['anthropic'].get('error', 'Unknown')}")
    
    # Apollo results
    if result['apollo'].get('success'):
        print(f"\n✓ Apollo Research:")
        print(f"  Articles scraped: {result['apollo']['articles_found']}")
    else:
        print(f"\n❌ Apollo Research:")
        print(f"  Error: {result['apollo'].get('error', 'Unknown')}")
    
    # Sync results
    sync = result.get('sync', {})
    if sync.get('success'):
        print(f"\n✓ MongoDB Sync:")
        print(f"  Total articles: {sync.get('total_articles', 0)}")
        print(f"  Inserted (new): {sync.get('inserted', 0)}")
        print(f"  Skipped (existing): {sync.get('skipped', 0)}")
        print(f"  Errors: {sync.get('errors', 0)}")
    else:
        print(f"\n❌ MongoDB Sync:")
        print(f"  Error: {sync.get('error', 'Unknown')}")
    
    # Overall summary
    summary = result.get('summary', {})
    print(f"\n📊 Overall Summary:")
    print(f"  Total articles scraped: {summary.get('total_articles_scraped', 0)}")
    print(f"  New articles inserted: {summary.get('total_inserted', 0)}")
    print(f"  Existing articles skipped: {summary.get('total_skipped', 0)}")


if __name__ == "__main__":
    asyncio.run(main())

