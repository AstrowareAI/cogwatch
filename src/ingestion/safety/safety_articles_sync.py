"""
Safety Articles MongoDB Sync
Handles syncing safety research articles to MongoDB with URL-based deduplication
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import sys
import os

# For relative imports from sibling directories
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from db.mongodb import get_collection


class SafetyArticlesSync:
    """Handles syncing safety research articles to MongoDB"""
    
    def __init__(self, collection_name: str = 'safety_depth_articles'):
        self.collection = get_collection(collection_name)
    
    def create_indexes(self):
        """Create indexes for efficient querying"""
        # Index on URL (unique identifier to prevent duplicates)
        self.collection.create_index('url', unique=True)
        
        # Index on source and article_type for filtering
        self.collection.create_index([('source', 1), ('article_type', 1)])
        
        # Index on date_published for date-based queries
        self.collection.create_index('date_published')
        
        # Index on scraped_at for tracking
        self.collection.create_index('scraped_at')
        
        # Index on unprocessed for finding articles to process
        self.collection.create_index('unprocessed')
        
        print(f"Created indexes on collection: {self.collection.name}")
    
    def prepare_article_for_db(self, article: Dict) -> Dict:
        """
        Prepare article document for MongoDB storage
        
        Args:
            article: Raw article dictionary from scraper
            
        Returns:
            Document ready for MongoDB insertion
        """
        doc = {
            **article,
            'unprocessed': True,  # New articles default to unprocessed
            'scraped_at': datetime.now(timezone.utc),
        }
        
        # Ensure date_published is stored as string if it exists
        if doc.get('date_published') and isinstance(doc['date_published'], datetime):
            doc['date_published'] = doc['date_published'].isoformat()
        
        return doc
    
    def get_existing_urls(self, urls: List[str]) -> set:
        """
        Get set of URLs that already exist in the database
        
        Args:
            urls: List of URLs to check
            
        Returns:
            Set of URLs that exist in the database
        """
        existing = self.collection.find(
            {'url': {'$in': urls}},
            {'url': 1}
        )
        return {doc['url'] for doc in existing}
    
    def upsert_article(self, article: Dict) -> Dict:
        """
        Upsert a single article into MongoDB (only inserts if URL is new)
        
        Args:
            article: Article dictionary
            
        Returns:
            Dictionary with status: 'inserted', 'skipped' (already exists), or 'error'
        """
        try:
            prepared = self.prepare_article_for_db(article)
            url = prepared.get('url')
            
            if not url:
                return {'status': 'error', 'reason': 'Missing URL'}
            
            # Check if article already exists
            existing = self.collection.find_one({'url': url})
            
            if existing:
                # Article already exists, skip to avoid duplicates
                return {
                    'status': 'skipped',
                    'reason': 'Already exists',
                    'url': url
                }
            
            # Insert new article
            result = self.collection.insert_one(prepared)
            
            if result.acknowledged:
                return {
                    'status': 'inserted',
                    'url': url,
                    'id': str(result.inserted_id)
                }
            else:
                return {
                    'status': 'error',
                    'reason': 'Insert not acknowledged'
                }
        except Exception as e:
            # Handle duplicate key error gracefully (race condition)
            if 'duplicate key' in str(e).lower() or 'E11000' in str(e):
                return {
                    'status': 'skipped',
                    'reason': 'Duplicate key (concurrent insert)',
                    'url': url
                }
            return {
                'status': 'error',
                'reason': str(e),
                'url': article.get('url', 'unknown')
            }
    
    def sync_articles(self, articles: List[Dict]) -> Dict:
        """
        Sync articles to MongoDB, only inserting new ones
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Dictionary with sync statistics
        """
        if not articles:
            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_articles': 0,
                'inserted': 0,
                'skipped': 0,
                'errors': 0
            }
        
        # Ensure indexes exist
        self.create_indexes()
        
        # Filter out articles without URLs
        valid_articles = [a for a in articles if a.get('url')]
        if len(valid_articles) < len(articles):
            print(f"  ⚠ Warning: {len(articles) - len(valid_articles)} articles missing URLs")
        
        # Get existing URLs for batch check (optimization)
        urls = [a['url'] for a in valid_articles]
        existing_urls = self.get_existing_urls(urls)
        
        print(f"  Checking {len(valid_articles)} articles...")
        print(f"  Found {len(existing_urls)} existing articles in database")
        
        # Upsert articles
        inserted = 0
        skipped = 0
        errors = 0
        
        for article in valid_articles:
            url = article['url']
            
            # Quick check: skip if we know it already exists
            if url in existing_urls:
                skipped += 1
                continue
            
            # Attempt upsert
            result = self.upsert_article(article)
            
            if result['status'] == 'inserted':
                inserted += 1
            elif result['status'] == 'skipped':
                skipped += 1
                # Add to existing_urls to avoid duplicate checks
                existing_urls.add(url)
            else:
                errors += 1
                print(f"    ⚠ Error inserting {url}: {result.get('reason', 'Unknown')}")
        
        return {
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_articles': len(valid_articles),
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors
        }
    
    def get_unprocessed_articles(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get articles that are marked as unprocessed
        
        Args:
            limit: Maximum number of articles to return (None for all)
            
        Returns:
            List of unprocessed article documents
        """
        query = {'unprocessed': True}
        cursor = self.collection.find(query).sort('scraped_at', 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def mark_as_processed(self, url: str) -> bool:
        """
        Mark an article as processed
        
        Args:
            url: Article URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {'url': url},
                {'$set': {'unprocessed': False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error marking article {url} as processed: {e}")
            return False


async def main():
    """Test the sync functionality"""
    sync = SafetyArticlesSync()
    
    # Test with sample articles
    test_articles = [
        {
            'title': 'Test Article 1',
            'date_published': '2025-01-15',
            'author': 'Test Author',
            'content': 'Test content...',
            'url': 'https://example.com/test1',
            'source': 'test',
            'article_type': 'blog'
        },
        {
            'title': 'Test Article 2',
            'date_published': '2025-01-16',
            'author': 'Test Author 2',
            'content': 'Test content 2...',
            'url': 'https://example.com/test2',
            'source': 'test',
            'article_type': 'research'
        }
    ]
    
    result = sync.sync_articles(test_articles)
    print("\nSync Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())

