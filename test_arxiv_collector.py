"""
Test script for ArXiv data collector
Tests searching ArXiv and syncing to MongoDB with deduplication
"""

from src.ingestion.arxiv import ArxivDataCollector


def main():
    """Test the ArXiv data collector"""
    print("="*70)
    print("TESTING ARXIV DATA COLLECTOR")
    print("="*70)
    
    # Initialize collector - by default fetch_all=True to get all papers
    # For testing, we can limit results if needed
    collector = ArxivDataCollector(max_results=50, fetch_all=False)
    
    # Run search and sync
    result = collector.search_and_sync()
    
    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    # Search results
    search = result.get('search', {})
    if search.get('success'):
        print(f"\n✓ ArXiv Search: SUCCESS")
        print(f"  Papers found: {search.get('papers_found', 0)}")
    else:
        print(f"\n❌ ArXiv Search: FAILED")
        print(f"  Error: {search.get('error', 'Unknown')}")
        return
    
    # Sync results
    sync = result.get('sync', {})
    if sync.get('success'):
        print(f"\n✓ MongoDB Sync: SUCCESS")
        print(f"  Total papers processed: {sync.get('total_papers', 0)}")
        print(f"  Inserted (new): {sync.get('inserted', 0)}")
        print(f"  Skipped (existing): {sync.get('skipped', 0)}")
        print(f"  Errors: {sync.get('errors', 0)}")
    else:
        print(f"\n❌ MongoDB Sync: FAILED")
        print(f"  Error: {sync.get('error', 'Unknown')}")
    
    # Summary
    summary = result.get('summary', {})
    print(f"\n📊 Summary:")
    print(f"  Total papers searched: {summary.get('total_papers_searched', 0)}")
    print(f"  New papers inserted: {summary.get('total_inserted', 0)}")
    print(f"  Existing papers skipped: {summary.get('total_skipped', 0)}")
    print(f"  Total papers in database: {summary.get('database_total', 0)}")
    
    # Test deduplication by running again
    print("\n" + "="*70)
    print("TESTING DEDUPLICATION - RUNNING AGAIN")
    print("="*70)
    
    result2 = collector.search_and_sync()
    sync2 = result2.get('sync', {})
    
    print(f"\n✓ Second Run Results:")
    print(f"  Papers found: {result2['search'].get('papers_found', 0)}")
    print(f"  Inserted (new): {sync2.get('inserted', 0)}")
    print(f"  Skipped (existing): {sync2.get('skipped', 0)}")
    
    if sync2.get('inserted', 0) == 0:
        print("\n✅ DEDUPLICATION WORKING: No duplicates inserted!")
    else:
        print(f"\n⚠️  WARNING: {sync2.get('inserted', 0)} papers were inserted (may be new papers)")


if __name__ == "__main__":
    main()

