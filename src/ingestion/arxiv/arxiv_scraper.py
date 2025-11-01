"""
ArXiv Paper Scraper
Searches ArXiv for papers matching cognitive offloading/decline and AI-related terms
"""

import arxiv
from datetime import datetime, timezone
from typing import Dict, List, Optional


class ArxivScraper:
    """Scraper for ArXiv papers related to cognitive effects and AI"""
    
    # ArXiv API supports up to 2,000 results per request theoretically
    # In practice, the arxiv library has pagination issues with max_results > 100
    # We use 100 as the safe default that works reliably
    MAX_PER_REQUEST = 2000  # Theoretical API limit
    MAX_TOTAL = 30000  # Theoretical API limit
    SAFE_MAX_RESULTS = 100  # Safe default that works reliably with arxiv library
    
    def __init__(self, max_results: Optional[int] = None, fetch_all: bool = False):
        """
        Initialize the ArXiv scraper
        
        Args:
            max_results: Maximum number of results to return per search.
                        If None and fetch_all=False, defaults to SAFE_MAX_RESULTS (500).
                        If fetch_all=True, uses SAFE_MAX_RESULTS (500) as a practical limit.
            fetch_all: If True, uses SAFE_MAX_RESULTS to fetch papers (more reliable than very large requests)
        """
        self.fetch_all = fetch_all
        if max_results is None:
            max_results = self.SAFE_MAX_RESULTS
        self.max_results = max_results
    
    def build_search_query(self) -> str:
        """
        Build the ArXiv search query string
        
        Returns:
            Query string for arxiv search
        """
        # Build the query from the user's specification
        cognitive_terms = [
            "cognitive offloading",
            "cognitive decline", 
            "cognitive debt",
            "critical thinking offload",
            "reasoning",
            "decision-making",
            "attention degradation",
            "engagement decline"
        ]
        
        ai_terms = [
            "AI",
            "artificial intelligence",
            "LLM",
            "ChatGPT",
            "generative AI",
            "language model",
            "cognitive load", 
            "automation bias"
        ]
        
        # Format: (term1 OR term2 OR ...) AND (term3 OR term4 OR ...)
        # Use quotes for multi-word phrases, no quotes for single words
        cognitive_parts = []
        for term in cognitive_terms:
            if ' ' in term or '-' in term:
                cognitive_parts.append(f'"{term}"')
            else:
                cognitive_parts.append(term)
        
        ai_parts = []
        for term in ai_terms:
            if ' ' in term or '-' in term:
                ai_parts.append(f'"{term}"')
            else:
                ai_parts.append(term)
        
        cognitive_query = " OR ".join(cognitive_parts)
        ai_query = " OR ".join(ai_parts)
        
        full_query = f"({cognitive_query}) AND ({ai_query})"
        
        return full_query
    
    def search_papers(self, query: Optional[str] = None, max_results: Optional[int] = None, fetch_all: Optional[bool] = None) -> List[Dict]:
        """
        Search ArXiv for papers matching the query
        
        Args:
            query: Custom query string. If None, uses the default cognitive/AI query
            max_results: Maximum number of results. If None, uses self.max_results
            fetch_all: If True, fetches all matching papers using pagination.
                      Overrides max_results if True.
        
        Returns:
            List of paper dictionaries with relevant metadata
        """
        if query is None:
            query = self.build_search_query()
        
        if fetch_all is None:
            fetch_all = self.fetch_all
        
        if fetch_all:
            # Fetch all results using pagination
            return self._search_all_papers(query)
        
        if max_results is None:
            max_results = self.max_results
        
        print(f"  Searching ArXiv with query: {query}")
        print(f"  Max results: {max_results}")
        
        papers = []
        
        try:
            # Search ArXiv
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            print("  Fetching results...")
            results = list(search.results())
            print(f"  Found {len(results)} papers")
            
            # Convert to dictionary format
            for result in results:
                paper_dict = self._result_to_dict(result)
                papers.append(paper_dict)
                
        except Exception as e:
            print(f"  ❌ Error searching ArXiv: {e}")
            raise
        
        return papers
    
    def _search_all_papers(self, query: str) -> List[Dict]:
        """
        Fetch papers using a safe, reliable max_results value
        
        Args:
            query: Search query string
        
        Returns:
            List of paper dictionaries
        """
        print(f"  Searching ArXiv with query: {query}")
        print(f"  Fetching papers with max_results={self.SAFE_MAX_RESULTS} (safe limit)...")
        
        papers = []
        
        try:
            # Use SAFE_MAX_RESULTS (500) for reliability
            # The arxiv library can have pagination issues with very large max_results
            # 500 is a good balance between getting results and reliability
            search = arxiv.Search(
                query=query,
                max_results=self.SAFE_MAX_RESULTS,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )
            
            print("  Fetching results...")
            
            # The results() method returns an iterator
            results = list(search.results())
            
            print(f"  Processing {len(results)} papers...")
            
            # Convert to dictionary format
            for result in results:
                paper_dict = self._result_to_dict(result)
                papers.append(paper_dict)
            
            print(f"  ✓ Total papers found: {len(papers)}")
            
            if len(papers) >= self.SAFE_MAX_RESULTS:
                print(f"  ℹ Note: Result set may contain more papers. Consider:")
                print(f"     - Increasing max_results parameter if you need more")
                print(f"     - Refining your query for better filtering")
            
        except Exception as e:
            print(f"  ❌ Error fetching papers: {e}")
            raise
        
        return papers
    
    def _result_to_dict(self, result: arxiv.Result) -> Dict:
        """
        Convert an arxiv.Result object to a dictionary
        
        Args:
            result: ArXiv result object
            
        Returns:
            Dictionary with paper metadata
        """
        # Extract arxiv ID from entry_id (format: http://arxiv.org/abs/2301.12345v1 -> 2301.12345)
        entry_id = result.entry_id
        arxiv_id = entry_id.split('/')[-1].split('v')[0] if entry_id else None
        
        # Format authors list
        authors = [str(author) for author in result.authors]
        
        # Extract categories (primary and all)
        categories = [str(cat) for cat in result.categories]
        primary_category = str(result.primary_category) if result.primary_category else None
        
        paper_dict = {
            'arxiv_id': arxiv_id,
            'entry_id': entry_id,
            'title': result.title,
            'authors': authors,
            'summary': result.summary,
            'published': result.published.isoformat() if result.published else None,
            'updated': result.updated.isoformat() if result.updated else None,
            'categories': categories,
            'primary_category': primary_category,
            'comment': result.comment if hasattr(result, 'comment') and result.comment else None,
            'journal_ref': result.journal_ref if hasattr(result, 'journal_ref') and result.journal_ref else None,
            'doi': result.doi if hasattr(result, 'doi') and result.doi else None,
            'pdf_url': result.pdf_url if hasattr(result, 'pdf_url') else None,
            'source': 'arxiv',
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }
        
        return paper_dict


def main():
    """Test the ArXiv scraper"""
    scraper = ArxivScraper(max_results=10)
    papers = scraper.search_papers()
    
    print(f"\n📄 Found {len(papers)} papers:")
    for i, paper in enumerate(papers[:3], 1):
        print(f"\n{i}. {paper['title']}")
        print(f"   ArXiv ID: {paper['arxiv_id']}")
        print(f"   Authors: {', '.join(paper['authors'][:3])}")
        if len(paper['authors']) > 3:
            print(f"   ... and {len(paper['authors']) - 3} more")
        print(f"   Published: {paper['published']}")


if __name__ == "__main__":
    main()

