"""
PubMed Data Collector Coordinator for Cogwatch
Coordinates searching and syncing of PubMed papers related to cognitive effects and AI
Uses the same query terms as ArXiv for consistency
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from .pubmed_scraper import PubmedScraper
from .pubmed_papers_sync import PubmedPapersSync


class PubmedDataCollector:
    """Coordinator for PubMed paper collection on cognitive effects and AI"""
    
    def __init__(
        self, 
        collection_name: str = 'pubmed_papers', 
        max_results: Optional[int] = None,
        tool: str = "Cogwatch",
        email: str = "cogwatch@example.com"
    ):
        """
        Initialize the PubMed data collector
        
        Args:
            collection_name: MongoDB collection name
            max_results: Maximum number of results to fetch from PubMed.
                        If None, defaults to 100 (safe limit).
            tool: Tool name for PubMed API (required by PubMed)
            email: Email address for PubMed API (required by PubMed)
        """
        self.scraper = PubmedScraper(max_results=max_results, tool=tool, email=email)
        self.sync = PubmedPapersSync(collection_name=collection_name)
    
    def search_and_sync(self, query: Optional[str] = None, max_results: Optional[int] = None) -> Dict:
        """
        Main method - searches PubMed and syncs papers to MongoDB
        
        Args:
            query: Custom query string. If None, uses the default cognitive/AI query
            max_results: Maximum number of results. If None, uses scraper's default
        
        Returns:
            Dictionary with results from search and sync
        """
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'search': {},
            'sync': {}
        }
        
        # Check existing papers count for reference
        existing_count = self.sync.collection.count_documents({})
        print(f"\n  Current papers in database: {existing_count}")
        
        # Search PubMed
        print("\n" + "="*60)
        print("SEARCHING PUBMED")
        print("="*60)
        try:
            papers = self.scraper.search_papers(query=query, max_results=max_results)
            results['search'] = {
                'success': True,
                'papers_found': len(papers),
                'papers': papers
            }
            print(f"  ✓ Found {len(papers)} papers")
        except Exception as e:
            print(f"  ❌ Error searching PubMed: {e}")
            results['search'] = {
                'success': False,
                'error': str(e),
                'papers_found': 0,
                'papers': []
            }
            return results
        
        # Sync papers to MongoDB
        print("\n" + "="*60)
        print("SYNCING PAPERS TO MONGODB")
        print("="*60)
        
        if papers:
            sync_result = self.sync.sync_papers(papers)
            results['sync'] = sync_result
        else:
            results['sync'] = {
                'success': False,
                'error': 'No papers to sync',
                'total_papers': 0,
                'inserted': 0,
                'skipped': 0,
                'errors': 0
            }
        
        # Summary
        results['summary'] = {
            'total_papers_searched': len(papers),
            'total_inserted': results['sync'].get('inserted', 0),
            'total_skipped': results['sync'].get('skipped', 0),
            'total_errors': results['sync'].get('errors', 0),
            'database_total': self.sync.collection.count_documents({})
        }
        
        return results


def main():
    """Test the PubMed data collector"""
    collector = PubmedDataCollector(max_results=20)
    result = collector.search_and_sync()
    
    print("\n" + "="*60)
    print("PUBMED DATA COLLECTION SUMMARY")
    print("="*60)
    
    # Search results
    if result['search'].get('success'):
        print(f"\n✓ PubMed Search:")
        print(f"  Papers found: {result['search']['papers_found']}")
    else:
        print(f"\n❌ PubMed Search:")
        print(f"  Error: {result['search'].get('error', 'Unknown')}")
    
    # Sync results
    sync = result.get('sync', {})
    if sync.get('success'):
        print(f"\n✓ MongoDB Sync:")
        print(f"  Total papers: {sync.get('total_papers', 0)}")
        print(f"  Inserted (new): {sync.get('inserted', 0)}")
        print(f"  Skipped (existing): {sync.get('skipped', 0)}")
        print(f"  Errors: {sync.get('errors', 0)}")
    else:
        print(f"\n❌ MongoDB Sync:")
        print(f"  Error: {sync.get('error', 'Unknown')}")
    
    # Overall summary
    summary = result.get('summary', {})
    print(f"\n📊 Overall Summary:")
    print(f"  Total papers searched: {summary.get('total_papers_searched', 0)}")
    print(f"  New papers inserted: {summary.get('total_inserted', 0)}")
    print(f"  Existing papers skipped: {summary.get('total_skipped', 0)}")
    print(f"  Total papers in database: {summary.get('database_total', 0)}")


if __name__ == "__main__":
    main()

