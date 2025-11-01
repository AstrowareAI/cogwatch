"""
PubMed Paper Scraper
Searches PubMed for papers matching cognitive offloading/decline and AI-related terms
Uses the same query terms as ArXiv scraper
"""

from pymed import PubMed
from datetime import datetime, timezone
from typing import Dict, List, Optional


class PubmedScraper:
    """Scraper for PubMed papers related to cognitive effects and AI"""
    
    # PubMed API practical limits
    # The pymed library handles batching automatically
    SAFE_MAX_RESULTS = 100  # Safe default that works reliably
    
    def __init__(self, max_results: Optional[int] = None, tool: str = "Cogwatch", email: str = "cogwatch@example.com"):
        """
        Initialize the PubMed scraper
        
        Args:
            max_results: Maximum number of results to return per search.
                        If None, defaults to SAFE_MAX_RESULTS (100).
            tool: Tool name for PubMed API (required by PubMed)
            email: Email address for PubMed API (required by PubMed)
        """
        if max_results is None:
            max_results = self.SAFE_MAX_RESULTS
        self.max_results = max_results
        self.pubmed = PubMed(tool=tool, email=email)
    
    def build_search_query(self) -> str:
        """
        Build the PubMed search query string
        Uses the same query terms as ArXiv for consistency
        
        Returns:
            Query string for PubMed search (PubMed query syntax)
        """
        # Build the query from the same specification as ArXiv
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
        
        # PubMed query syntax uses parentheses and OR/AND operators
        # Terms with spaces should be quoted or use [All Fields] syntax
        # Format: (term1 OR term2 OR ...) AND (term3 OR term4 OR ...)
        cognitive_query = " OR ".join([f'"{term}"' for term in cognitive_terms])
        ai_query = " OR ".join([f'"{term}"' for term in ai_terms])
        
        full_query = f"({cognitive_query}) AND ({ai_query})"
        
        return full_query
    
    def search_papers(self, query: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict]:
        """
        Search PubMed for papers matching the query
        
        Args:
            query: Custom query string. If None, uses the default cognitive/AI query
            max_results: Maximum number of results. If None, uses self.max_results
        
        Returns:
            List of paper dictionaries with relevant metadata
        """
        if query is None:
            query = self.build_search_query()
        
        if max_results is None:
            max_results = self.max_results
        
        print(f"  Searching PubMed with query: {query}")
        print(f"  Max results: {max_results}")
        
        papers = []
        
        try:
            # Search PubMed
            print("  Fetching results...")
            results = list(self.pubmed.query(query, max_results=max_results))
            print(f"  Found {len(results)} papers")
            
            # Convert to dictionary format
            for result in results:
                paper_dict = self._result_to_dict(result)
                papers.append(paper_dict)
                
        except Exception as e:
            print(f"  ❌ Error searching PubMed: {e}")
            raise
        
        return papers
    
    def _result_to_dict(self, result) -> Dict:
        """
        Convert a PubMedArticle object to a dictionary
        
        Args:
            result: PubMedArticle object from pymed
            
        Returns:
            Dictionary with paper metadata
        """
        # Get publication date
        pub_date = None
        if hasattr(result, 'publication_date') and result.publication_date:
            try:
                # publication_date might be a string or date object
                if isinstance(result.publication_date, str):
                    pub_date = result.publication_date
                else:
                    pub_date = result.publication_date.isoformat() if hasattr(result.publication_date, 'isoformat') else str(result.publication_date)
            except:
                pub_date = str(result.publication_date) if result.publication_date else None
        
        # Get authors
        authors = []
        if hasattr(result, 'authors') and result.authors:
            for author in result.authors:
                if isinstance(author, dict):
                    # Format: "Lastname, Firstname" or just name
                    name = author.get('lastname', '')
                    if author.get('firstname'):
                        name = f"{name}, {author.get('firstname')}".strip(', ')
                    authors.append(name if name else str(author))
                else:
                    authors.append(str(author))
        
        # Get journal
        journal = None
        if hasattr(result, 'journal') and result.journal:
            journal = str(result.journal)
        
        # Get keywords
        keywords = []
        if hasattr(result, 'keywords') and result.keywords:
            if isinstance(result.keywords, list):
                keywords = [str(kw) for kw in result.keywords]
            else:
                keywords = [str(result.keywords)]
        
        paper_dict = {
            'pmid': str(result.pubmed_id) if hasattr(result, 'pubmed_id') and result.pubmed_id else None,
            'title': result.title if hasattr(result, 'title') and result.title else None,
            'authors': authors,
            'abstract': result.abstract if hasattr(result, 'abstract') and result.abstract else None,
            'publication_date': pub_date,
            'journal': journal,
            'doi': result.doi if hasattr(result, 'doi') and result.doi else None,
            'keywords': keywords,
            'source': 'pubmed',
            'scraped_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Add optional fields if available
        if hasattr(result, 'conclusions') and result.conclusions:
            paper_dict['conclusions'] = result.conclusions
        if hasattr(result, 'methods') and result.methods:
            paper_dict['methods'] = result.methods
        if hasattr(result, 'results') and result.results:
            paper_dict['results'] = result.results
        
        return paper_dict


def main():
    """Test the PubMed scraper"""
    scraper = PubmedScraper(max_results=10)
    papers = scraper.search_papers()
    
    print(f"\n📄 Found {len(papers)} papers:")
    for i, paper in enumerate(papers[:3], 1):
        print(f"\n{i}. {paper['title'][:60] if paper.get('title') else 'No title'}")
        print(f"   PubMed ID: {paper.get('pmid', 'N/A')}")
        print(f"   Authors: {', '.join(paper['authors'][:2]) if paper.get('authors') else 'N/A'}")
        if paper.get('authors') and len(paper['authors']) > 2:
            print(f"   ... and {len(paper['authors']) - 2} more")
        print(f"   Published: {paper.get('publication_date', 'N/A')}")


if __name__ == "__main__":
    main()

