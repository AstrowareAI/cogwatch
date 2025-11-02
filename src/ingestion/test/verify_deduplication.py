"""
Quick verification script to test deduplication
Shows that rerunning with no new articles will insert 0 articles
"""

import asyncio
from src.ingestion.safety import SafetyDataCollector
from src.db.mongodb import get_collection

async def verify_deduplication():
    """Verify that rerunning with existing articles inserts 0 new articles"""
    
    print("="*70)
    print("VERIFYING DEDUPLICATION LOGIC")
    print("="*70)
    
    collector = SafetyDataCollector(collection_name='safety_depth_articles')
    collection = collector.sync.collection
    
    # Get current count
    initial_count = collection.count_documents({})
    print(f"\n📊 Current articles in MongoDB: {initial_count}")
    
    # Run collector again (should skip all existing articles)
    print("\n🔄 Running collector again (should skip all existing articles)...")
    print("-"*70)
    
    result = await collector.scrape_all()
    
    # Check results
    inserted = result['sync'].get('inserted', 0)
    skipped = result['sync'].get('skipped', 0)
    final_count = collection.count_documents({})
    
    print("\n" + "="*70)
    print("RESULTS:")
    print("="*70)
    print(f"  Initial count: {initial_count}")
    print(f"  Final count: {final_count}")
    print(f"  Articles inserted: {inserted}")
    print(f"  Articles skipped: {skipped}")
    print(f"  Articles scraped (Anthropic): {result['anthropic'].get('articles_found', 0)}")
    print(f"  Articles scraped (Apollo): {result['apollo'].get('articles_found', 0)}")
    
    # Verification
    print("\n" + "="*70)
    if inserted == 0:
        print("✅ VERIFICATION PASSED: No new articles inserted (as expected)")
        print("   All existing articles were correctly skipped!")
    else:
        print(f"⚠️  WARNING: {inserted} new articles were inserted")
        print("   This means new articles were found (or deduplication has an issue)")
    
    if final_count == initial_count:
        print("✅ VERIFICATION PASSED: Database count unchanged")
        print("   This confirms no duplicates were created!")
    else:
        print(f"⚠️  WARNING: Count changed from {initial_count} to {final_count}")
    
    print("="*70)
    
    return inserted == 0 and final_count == initial_count

if __name__ == "__main__":
    success = asyncio.run(verify_deduplication())
    exit(0 if success else 1)

