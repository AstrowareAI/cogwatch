"""
PubMed Papers MongoDB Sync
Handles syncing PubMed papers to MongoDB with pmid-based deduplication
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import sys
import os

# For relative imports from sibling directories
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from db.mongodb import get_collection


class PubmedPapersSync:
    """Handles syncing PubMed papers to MongoDB with deduplication"""
    
    def __init__(self, collection_name: str = 'pubmed_papers'):
        self.collection = get_collection(collection_name)
    
    def create_indexes(self):
        """Create indexes for efficient querying and deduplication"""
        # Index on pmid (unique identifier to prevent duplicates)
        self.collection.create_index('pmid', unique=True)
        
        # Index on publication_date for date-based queries
        self.collection.create_index('publication_date')
        
        # Index on scraped_at for tracking
        self.collection.create_index('scraped_at')
        
        # Index on journal for filtering
        self.collection.create_index('journal')
        
        # Index on keywords for filtering
        self.collection.create_index('keywords')
        
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
    
    def get_existing_pmids(self, pmids: List[str]) -> set:
        """
        Get set of PubMed IDs that already exist in the database
        
        Args:
            pmids: List of PubMed IDs to check
            
        Returns:
            Set of PubMed IDs that exist in the database
        """
        existing = self.collection.find(
            {'pmid': {'$in': pmids}},
            {'pmid': 1}
        )
        return {doc['pmid'] for doc in existing if doc.get('pmid')}
    
    def get_all_existing_pmids(self) -> set:
        """
        Get all PubMed IDs currently in the database
        
        Returns:
            Set of all PubMed IDs in the database
        """
        existing = self.collection.find(
            {},
            {'pmid': 1}
        )
        return {doc['pmid'] for doc in existing if doc.get('pmid')}
    
    def upsert_paper(self, paper: Dict) -> Dict:
        """
        Upsert a single paper into MongoDB (only inserts if pmid is new)
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Dictionary with status: 'inserted', 'skipped' (already exists), or 'error'
        """
        try:
            prepared = self.prepare_paper_for_db(paper)
            pmid = prepared.get('pmid')
            
            if not pmid:
                return {'status': 'error', 'reason': 'Missing pmid'}
            
            # Check if paper already exists
            existing = self.collection.find_one({'pmid': pmid})
            
            if existing:
                # Paper already exists, skip to avoid duplicates
                return {
                    'status': 'skipped',
                    'reason': 'Already exists',
                    'pmid': pmid
                }
            
            # Insert new paper
            result = self.collection.insert_one(prepared)
            
            if result.acknowledged:
                return {
                    'status': 'inserted',
                    'pmid': pmid,
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
                    'pmid': pmid
                }
            return {
                'status': 'error',
                'reason': str(e),
                'pmid': paper.get('pmid', 'unknown')
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
        
        # Filter out papers without pmid
        valid_papers = [p for p in papers if p.get('pmid')]
        if len(valid_papers) < len(papers):
            print(f"  ⚠ Warning: {len(papers) - len(valid_papers)} papers missing pmid")
        
        # Get existing PubMed IDs for batch check (optimization)
        pmids = [p['pmid'] for p in valid_papers]
        existing_pmids = self.get_existing_pmids(pmids)
        
        print(f"  Checking {len(valid_papers)} papers...")
        print(f"  Found {len(existing_pmids)} existing papers in database")
        
        # Upsert papers
        inserted = 0
        skipped = 0
        errors = 0
        
        for paper in valid_papers:
            pmid = paper['pmid']
            
            # Quick check: skip if we know it already exists
            if pmid in existing_pmids:
                skipped += 1
                continue
            
            # Attempt upsert
            result = self.upsert_paper(paper)
            
            if result['status'] == 'inserted':
                inserted += 1
            elif result['status'] == 'skipped':
                skipped += 1
                # Add to existing_pmids to avoid duplicate checks
                existing_pmids.add(pmid)
            else:
                errors += 1
                print(f"    ⚠ Error inserting {pmid}: {result.get('reason', 'Unknown')}")
        
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
    
    def mark_as_processed(self, pmid: str) -> bool:
        """
        Mark a paper as processed
        
        Args:
            pmid: PubMed ID of the paper
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.collection.update_one(
                {'pmid': pmid},
                {'$set': {'unprocessed': False}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error marking paper {pmid} as processed: {e}")
            return False


def main():
    """Test the sync functionality"""
    sync = PubmedPapersSync()
    
    # Test with sample papers
    test_papers = [
        {
            'pmid': '12345678',
            'title': 'Test Paper 1',
            'authors': ['Author One', 'Author Two'],
            'abstract': 'This is a test paper about cognitive offloading and AI.',
            'publication_date': '2023-01-01',
            'journal': 'Test Journal',
            'source': 'pubmed'
        },
        {
            'pmid': '87654321',
            'title': 'Test Paper 2',
            'authors': ['Author Three'],
            'abstract': 'Another test paper about cognitive decline and LLMs.',
            'publication_date': '2023-02-01',
            'journal': 'Another Journal',
            'source': 'pubmed'
        }
    ]
    
    result = sync.sync_papers(test_papers)
    print("\nSync Result:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()

