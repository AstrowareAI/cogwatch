"""
Test script for Safety Depth Data Collector
Tests first-time load, deduplication, and incremental updates
"""

import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.ingestion.safety import SafetyDataCollector
from src.db.mongodb import get_collection


async def test_safety_collector(clear_db: bool = False):
    """Test the complete safety data collection flow"""
    
    print("="*70)
    print("SAFETY DEPTH DATA COLLECTOR - COMPREHENSIVE TEST")
    print("="*70)
    
    collector = SafetyDataCollector(collection_name='safety_depth_articles')
    collection = collector.sync.collection
    
    # Optionally clear database for fresh test
    if clear_db:
        print("\n🗑️  Clearing database for fresh test...")
        collection.delete_many({})
        print("  ✓ Database cleared")
    
    # Get initial count
    initial_count = collection.count_documents({})
    print(f"\n📊 Initial MongoDB count: {initial_count} articles")
    
    # Test 1: First-time load (or incremental update if DB not empty)
    print("\n" + "="*70)
    if initial_count == 0:
        print("TEST 1: FIRST-TIME LOAD")
    else:
        print("TEST 1: INCREMENTAL UPDATE (Database not empty)")
    print("="*70)
    
    result1 = await collector.scrape_all()
    
    after_first_count = collection.count_documents({})
    inserted_first = result1['sync'].get('inserted', 0)
    skipped_first = result1['sync'].get('skipped', 0)
    articles_scraped = result1['anthropic'].get('articles_found', 0) + result1['apollo'].get('articles_found', 0)
    
    print(f"\n✓ First run complete:")
    print(f"  - Articles scraped (Anthropic): {result1['anthropic'].get('articles_found', 0)}")
    print(f"  - Articles scraped (Apollo): {result1['apollo'].get('articles_found', 0)}")
    print(f"  - Total articles in MongoDB: {after_first_count}")
    print(f"  - New articles inserted: {inserted_first}")
    print(f"  - Articles skipped (existing): {skipped_first}")
    
    assert after_first_count == initial_count + inserted_first, "MongoDB count mismatch!"
    
    if initial_count == 0:
        # First-time load: should insert all articles
        assert inserted_first > 0, "Should insert articles on first run!"
        assert skipped_first == 0, "Should not skip any articles on first run!"
    else:
        # Incremental update: should skip existing articles
        assert inserted_first == 0 or inserted_first < articles_scraped, "Should skip most articles if they exist!"
        assert skipped_first > 0, "Should skip existing articles!"
    
    # Test 2: Second run - should skip all existing articles
    print("\n" + "="*70)
    print("TEST 2: SECOND RUN - DEDUPLICATION TEST")
    print("="*70)
    print("Running collector again immediately (should skip all articles)...")
    
    result2 = await collector.scrape_all()
    
    after_second_count = collection.count_documents({})
    inserted_second = result2['sync'].get('inserted', 0)
    skipped_second = result2['sync'].get('skipped', 0)
    
    print(f"\n✓ Second run complete:")
    print(f"  - Articles scraped (Anthropic): {result2['anthropic'].get('articles_found', 0)}")
    print(f"  - Articles scraped (Apollo): {result2['apollo'].get('articles_found', 0)}")
    print(f"  - Total articles in MongoDB: {after_second_count}")
    print(f"  - New articles inserted (should be 0): {inserted_second}")
    print(f"  - Articles skipped (should equal scraped): {skipped_second}")
    
    assert after_second_count == after_first_count, "MongoDB count should not change!"
    assert inserted_second == 0, "Should not insert any articles on second run!"
    assert skipped_second > 0, "Should skip existing articles!"
    
    # Test 3: Verify unprocessed flag
    print("\n" + "="*70)
    print("TEST 3: VERIFY UNPROCESSED FLAG")
    print("="*70)
    
    unprocessed_count = collection.count_documents({'unprocessed': True})
    total_count = collection.count_documents({})
    
    print(f"\n✓ Unprocessed check:")
    print(f"  - Total articles: {total_count}")
    print(f"  - Articles with unprocessed=true: {unprocessed_count}")
    print(f"  - Articles with unprocessed=false: {total_count - unprocessed_count}")
    
    assert unprocessed_count == total_count, "All new articles should have unprocessed=true!"
    
    # Test 4: Verify article structure
    print("\n" + "="*70)
    print("TEST 4: VERIFY ARTICLE STRUCTURE")
    print("="*70)
    
    sample_article = collection.find_one({})
    if sample_article:
        print(f"\n✓ Sample article structure:")
        print(f"  - URL: {sample_article.get('url', 'N/A')[:60]}...")
        print(f"  - Title: {sample_article.get('title', 'N/A')[:60]}...")
        print(f"  - Source: {sample_article.get('source', 'N/A')}")
        print(f"  - Article type: {sample_article.get('article_type', 'N/A')}")
        print(f"  - Date published: {sample_article.get('date_published', 'N/A')}")
        print(f"  - Author: {sample_article.get('author', 'N/A')}")
        print(f"  - Content length: {len(sample_article.get('content', ''))} chars")
        print(f"  - Unprocessed: {sample_article.get('unprocessed', 'N/A')}")
        print(f"  - Scraped at: {sample_article.get('scraped_at', 'N/A')}")
        
        # Verify required fields
        required_fields = ['url', 'title', 'content', 'source', 'unprocessed', 'scraped_at']
        missing_fields = [f for f in required_fields if f not in sample_article]
        assert not missing_fields, f"Missing required fields: {missing_fields}"
    
    # Test 5: Verify unique URLs
    print("\n" + "="*70)
    print("TEST 5: VERIFY NO DUPLICATE URLS")
    print("="*70)
    
    pipeline = [
        {'$group': {'_id': '$url', 'count': {'$sum': 1}}},
        {'$match': {'count': {'$gt': 1}}}
    ]
    duplicates = list(collection.aggregate(pipeline))
    
    if duplicates:
        print(f"\n❌ Found {len(duplicates)} duplicate URLs!")
        for dup in duplicates[:5]:
            print(f"  - {dup['_id']}: {dup['count']} occurrences")
        assert False, "Found duplicate URLs!"
    else:
        print(f"\n✓ No duplicate URLs found - deduplication working correctly!")
    
    # Summary
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED!")
    print("="*70)
    print(f"\n📊 Final Statistics:")
    print(f"  - Total articles in database: {after_second_count}")
    print(f"  - Articles from Anthropic: {collection.count_documents({'source': 'anthropic'})}")
    print(f"  - Articles from Apollo: {collection.count_documents({'source': 'apollo'})}")
    print(f"  - Research articles: {collection.count_documents({'article_type': 'research'})}")
    print(f"  - Blog articles: {collection.count_documents({'article_type': 'blog'})}")
    print(f"  - Unprocessed articles: {unprocessed_count}")
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_safety_collector())
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

