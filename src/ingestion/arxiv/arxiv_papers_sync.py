"""
ArXiv Papers MongoDB Sync
Handles syncing ArXiv papers to MongoDB with arxiv_id-based deduplication
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import sys
import os

# For relative imports from sibling directories
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from db.mongodb import get_collection


class ArxivPapersSync:
    """Handles syncing ArXiv papers to MongoDB with deduplication"""
    
    def __init__(self, collection_name: str = 'arxiv_papers'):
        self.collection = get_collection(collection_name)
    
    def create_indexes(self):
        """Create indexes for efficient querying and deduplication"""
        # Index on arxiv_id (unique identifier to prevent duplicates)
        self.collection.create_index('arxiv_id', unique=True)
        
        # Index on entry_id as backup unique identifier
        self.collection.create_index('entry_id', unique=True)
        
        # Index on published date for date-based queries
        self.collection.create_index('published')
        
        # Index on scraped_at for tracking
        self.collection.create_index('scraped_at')
        
        # Index on categories for filtering
        self.collection.create_index('categories')
        
        # Index on primary_category for filtering
        self.collection.create_index('primary_category')
        
        # Index on unprocessed for finding papers to process
        self.collection.create_index('unprocessed')
        
        print(f"Created indexes on collection: {self.collection.name}")
    
    def prepare_paper_for_db(self, paper: Dict) -> Dict:
        """
        Prepare paper document for MongoDB storage
        
        Args:
            paper: Raw paper dictionary from scraper
            
        Returns:
            Document ready for MongoDB insertion
        """
        doc = {
            **paper,
            'unprocessed': True,  # New papers default to unprocessed
        }
        
        # Ensure scraped_at is set if not already present
        if 'scraped_at' not in doc:
            doc['scraped_at'] = datetime.now(timezone.utc).isoformat()
        
        return doc
    
    def get_existing_arxiv_ids(self, arxiv_ids: List[str]) -> set:
        """
        Get set of ArXiv IDs that already exist in the database
        
        Args:
            arxiv_ids: List of ArXiv IDs to check
            
        Returns:
            Set of ArXiv IDs that exist in the database
        """
        existing = self.collection.find(
            {'arxiv_id': {'$in': arxiv_ids}},
            {'arxiv_id': 1}
        )
        return {doc['arxiv_id'] for doc in existing if doc.get('arxiv_id')}
    
    def get_all_existing_arxiv_ids(self) -> set:
        """
        Get all ArXiv IDs currently in the database
        Useful for avoiding unnecessary searches if we already have all papers
        
        Returns:
            Set of all ArXiv IDs in the database
        """
        existing = self.collection.find(
            {},
            {'arxiv_id': 1}
        )
        return {doc['arxiv_id'] for doc in existing if doc.get('arxiv_id')}
    
    def upsert_paper(self, paper: Dict) -> Dict:
        """
        Upsert a single paper into MongoDB (only inserts if arxiv_id is new)
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Dictionary with status: 'inserted', 'skipped' (already exists), or 'error'
        """
        try:
            prepared = self.prepare_paper_for_db(paper)
            arxiv_id = prepared.get('arxiv_id')
            
            if not arxiv_id:
                return {'status': 'error', 'reason': 'Missing arxiv_id'}
            
            # Check if paper already exists
            existing = self.collection.find_one({'arxiv_id': arxiv_id})
            
            if existing:
                # Paper already exists, skip to avoid duplicates
                return {
                    'status': 'skipped',
                    'reason': 'Already exists',
                    'arxiv_id': arxiv_id
                }
            
            # Insert new paper
            result = self.collection.insert_one(prepared)
            
            if result.acknowledged:
                return {
                    'status': 'inserted',
                    'arxiv_id': arxiv_id,
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
                    'arxiv_id': arxiv_id
                }
            return {
                'status': 'error',
                'reason': str(e),
                'arxiv_id': paper.get('arxiv_id', 'unknown')
            }
    
    def sync_papers(self, papers: List[Dict]) -> Dict:
        """
        Sync papers to MongoDB, only inserting new ones
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            Dictionary with sync statistics
        """
        if not papers:
            return {
                'success': True,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_papers': 0,
                'inserted': 0,
                'skipped': 0,
                'errors': 0
            }
        
        # Ensure indexes exist
        self.create_indexes()
        
        # Filter out papers without arxiv_id
        valid_papers = [p for p in papers if p.get('arxiv_id')]
        if len(valid_papers) < len(papers):
            print(f"  ⚠ Warning: {len(papers) - len(valid_papers)} papers missing arxiv_id")
        
        # Get existing ArXiv IDs for batch check (optimization)
        arxiv_ids = [p['arxiv_id'] for p in valid_papers]
        existing_arxiv_ids = self.get_existing_arxiv_ids(arxiv_ids)
        
        print(f"  Checking {len(valid_papers)} papers...")
        print(f"  Found {len(existing_arxiv_ids)} existing papers in database")
        
        # Upsert papers
        inserted = 0
        skipped = 0
        errors = 0
        
        for paper in valid_papers:
            arxiv_id = paper['arxiv_id']
            
            # Quick check: skip if we know it already exists
            if arxiv_id in existing_arxiv_ids:
                skipped += 1
                continue
            
            # Attempt upsert
            result = self.upsert_paper(paper)
            
            if result['status'] == 'inserted':
                inserted += 1
            elif result['status'] == 'skipped':
                skipped += 1
                # Add to existing_arxiv_ids to avoid duplicate checks
                existing_arxiv_ids.add(arxiv_id)
            else:
                errors += 1
                print(f"    ⚠ Error inserting {arxiv_id}: {result.get('reason', 'Unknown')}")
        
        return {
            'success': True,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_papers': len(valid_papers),
            'inserted': inserted,
            'skipped': skipped,
            'errors': errors
        }
    
    def get_unprocessed_papers(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get papers that are marked as unprocessed
        
        Args:
            limit: Maximum number of papers to return (None for all)
            
        Returns:
            List of unprocessed paper documents
        """
        query = {'unprocessed': True}
        cursor = self.collection.find(query).sort('scraped_at', 1)
        
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def mark_as_processed(self, arxiv_id: str) -> bool:
        """
        Mark a paper as processed
        
        Args:
            arxiv_id: ArXiv ID of the paper
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {'arxiv_id': arxiv_id},
                {'$set': {'unprocessed': False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error marking paper {arxiv_id} as processed: {e}")
            return False


def main():
    """Test the sync functionality"""
    sync = ArxivPapersSync()
    
    # Test with sample papers
    test_papers = [
        {
            'arxiv_id': '2301.12345',
            'entry_id': 'http://arxiv.org/abs/2301.12345v1',
            'title': 'Test Paper 1',
            'authors': ['Author One', 'Author Two'],
            'summary': 'This is a test paper about cognitive offloading and AI.',
            'published': '2023-01-01T00:00:00Z',
            'categories': ['cs.AI'],
            'primary_category': 'cs.AI',
            'source': 'arxiv'
        },
        {
            'arxiv_id': '2302.67890',
            'entry_id': 'http://arxiv.org/abs/2302.67890v1',
            'title': 'Test Paper 2',
            'authors': ['Author Three'],
            'summary': 'Another test paper about cognitive decline and LLMs.',
            'published': '2023-02-01T00:00:00Z',
            'categories': ['cs.CL'],
            'primary_category': 'cs.CL',
            'source': 'arxiv'
        }
    ]
    
    result = sync.sync_papers(test_papers)
    print("\nSync Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

