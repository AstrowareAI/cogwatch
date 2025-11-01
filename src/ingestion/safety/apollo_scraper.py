"""
Apollo Research Scraper
Scrapes articles from https://www.apolloresearch.ai/research/ and https://www.apolloresearch.ai/blog/
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Try to use crawl4ai for JavaScript rendering if available
try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False


class ApolloResearchScraper:
    """Scraper for Apollo Research articles (research and blog pages)"""
    
    RESEARCH_URL = "https://www.apolloresearch.ai/research/"
    BLOG_URL = "https://www.apolloresearch.ai/blog/"
    BASE_URL = "https://www.apolloresearch.ai"
    
    def __init__(self):
        self.session = None
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def fetch_page(self, url: str, use_js_rendering: bool = False) -> Optional[str]:
        """
        Fetch HTML content from a URL
        
        Args:
            url: URL to fetch
            use_js_rendering: If True and crawl4ai is available, use JavaScript rendering
        """
        # Use crawl4ai for JavaScript-rendered pages if available and requested
        if use_js_rendering and CRAWL4AI_AVAILABLE:
            try:
                async with AsyncWebCrawler(verbose=False) as crawler:
                    result = await crawler.arun(url=url)
                    if result.success:
                        return result.html
            except Exception as e:
                print(f"  ⚠ crawl4ai error for {url}: {e}")
                # Fall back to regular fetch
        
        # Regular HTTP fetch
        try:
            session = await self._get_session()
            async with session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"  ⚠ Failed to fetch {url}: status {response.status}")
                    return None
        except Exception as e:
            print(f"  ⚠ Error fetching {url}: {e}")
            return None
    
    def parse_article_list(self, html: str, base_url: str, article_type: str) -> List[Dict[str, str]]:
        """
        Parse article links from a listing page (research or blog)
        
        Args:
            html: HTML content
            base_url: Base URL for the page
            article_type: 'research' or 'blog'
        
        Returns:
            List of dictionaries with 'url' and 'title' keys
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        seen_urls = set()
        
        # Apollo uses specific structures - find all relevant links
        # Look for links in article containers or with specific classes
        article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and (
            'article' in str(x).lower() or 
            'post' in str(x).lower() or
            'entry' in str(x).lower() or
            'card' in str(x).lower() or
            'featured' in str(x).lower()
        ))
        
        # Also look for links directly in the page that match the pattern
        all_links = soup.find_all('a', href=True)
        
        # Combine both sources
        links_to_check = []
        if article_containers:
            for container in article_containers:
                links_to_check.extend(container.find_all('a', href=True))
        # Also check all links for direct matches
        links_to_check.extend(all_links)
        
        for link in links_to_check:
            href = link.get('href', '')
            if not href:
                continue
            
            # Build full URL
            if href.startswith('http'):
                full_url = href
            elif href.startswith('/'):
                full_url = urljoin(self.BASE_URL, href)
            else:
                full_url = urljoin(base_url, href)
            
            # Only include URLs from the same domain
            parsed_base = urlparse(self.BASE_URL)
            parsed_link = urlparse(full_url)
            
            if parsed_link.netloc != parsed_base.netloc:
                continue
            
            # Check if URL matches the article type (research or blog)
            path_lower = parsed_link.path.lower()
            if article_type == 'research' and '/research/' not in path_lower:
                continue
            if article_type == 'blog' and '/blog/' not in path_lower:
                continue
            
            # Skip root URLs, listing pages, and non-article pages
            path_parts = [p for p in parsed_link.path.split('/') if p]
            if (full_url == base_url or 
                full_url.endswith('#') or 
                '#' in full_url.split('/')[-1] or
                full_url in [self.RESEARCH_URL, self.BLOG_URL] or
                len(path_parts) < 2):  # Need at least /blog/article-name or /research/article-name
                continue
            
            # Skip common non-article paths
            skip_paths = ['/about', '/contact', '/privacy', '/terms', '/search', '/team', '/press', '/careers']
            if any(full_url.startswith(self.BASE_URL + sp) for sp in skip_paths):
                continue
            
            # Avoid duplicates
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            
            # Extract title - try multiple methods
            title_text = None
            
            # Method 1: Link text itself
            title_text = link.get_text(strip=True)
            
            # Method 2: Look in parent for heading
            if not title_text or len(title_text) < 10:
                parent = link.find_parent(['article', 'div', 'li', 'section', 'header'])
                if parent:
                    # Look for headings
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5'])
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
            
            # Method 3: Use URL as fallback if no title found
            if not title_text or len(title_text) < 10:
                # Extract from URL slug
                slug = path_parts[-1] if path_parts else ''
                title_text = slug.replace('-', ' ').title()
            
            # Skip common non-article link texts
            if title_text and len(title_text) >= 10:
                skip_texts = ['read more', 'continue reading', 'home', 'about', 'contact', 
                             'research', 'blog', 'team', 'press', 'careers', 'menu', 'close']
                if any(skip in title_text.lower() for skip in skip_texts):
                    continue
                
                articles.append({
                    'url': full_url,
                    'title': title_text,
                    'article_type': article_type
                })
        
        return articles
    
    async def scrape_article(self, url: str, article_type: str) -> Optional[Dict]:
        """
        Scrape a single article page
        
        Args:
            url: Article URL
            article_type: 'research' or 'blog'
        
        Returns:
            Dictionary with article data: title, date_published, author, content, url
        """
        # Try with JavaScript rendering first (for dynamic content)
        html = await self.fetch_page(url, use_js_rendering=True)
        
        # If content is too short, it might need JS rendering but crawl4ai might not be available
        # So we try regular fetch as fallback
        if not html:
            html = await self.fetch_page(url, use_js_rendering=False)
        
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = None
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract date published
        date_published = None
        # Look for common date patterns
        date_selectors = [
            'time[datetime]',
            'time[pubdate]',
            '.date',
            '.published',
            '[class*="date"]',
            '[class*="published"]',
            '[class*="publish"]',
            'meta[property="article:published_time"]',
            'meta[name="date"]',
            'meta[name="publishdate"]'
        ]
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                if date_elem.name == 'meta':
                    date_str = date_elem.get('content', '').strip()
                else:
                    date_str = date_elem.get('datetime') or date_elem.get('pubdate') or date_elem.get_text(strip=True)
                if date_str:
                    date_published = date_str
                    break
        
        # Try to extract from URL if it contains date (e.g., /2025/01/15/article-name)
        if not date_published:
            url_parts = url.split('/')
            for part in url_parts:
                if part.isdigit() and len(part) == 4:  # Year
                    year = part
                    # Look for month and day in adjacent parts
                    year_idx = url_parts.index(part)
                    if year_idx + 2 < len(url_parts):
                        month = url_parts[year_idx + 1] if url_parts[year_idx + 1].isdigit() else None
                        day = url_parts[year_idx + 2] if year_idx + 2 < len(url_parts) and url_parts[year_idx + 2].isdigit() else None
                        if month and day:
                            date_published = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                            break
        
        # Extract author
        author = None
        author_selectors = [
            '[class*="author"]',
            '[class*="byline"]',
            '.author',
            'meta[property="article:author"]',
            'meta[name="author"]'
        ]
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                if author_elem.name == 'meta':
                    author = author_elem.get('content', '').strip()
                else:
                    author = author_elem.get_text(strip=True)
                if author:
                    break
        
        # Extract main content
        content = None
        
        # Remove unwanted elements first
        for unwanted in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            unwanted.decompose()
        
        # Try common article content selectors
        content_selectors = [
            'main article',
            'article',
            'main',
            '[role="main"]',
            '[class*="content"]',
            '[class*="article"]',
            '[class*="post"]',
            '.post-content',
            '.article-content',
            '[class*="body"]',
            '[class*="prose"]',  # Common in markdown-based blogs
            '[class*="markdown"]'
        ]
        
        for selector in content_selectors:
            try:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Clone to avoid modifying original
                    elem_copy = BeautifulSoup(str(content_elem), 'html.parser')
                    
                    # Remove remaining unwanted elements
                    for tag in elem_copy(['script', 'style', 'nav', 'footer', 'header', 'aside', 'form']):
                        tag.decompose()
                    
                    # Get text with better formatting
                    content = elem_copy.get_text(separator='\n', strip=True)
                    # Clean up excessive whitespace
                    lines = [line.strip() for line in content.split('\n') if line.strip()]
                    content = '\n'.join(lines)
                    
                    if content and len(content) > 100:  # Ensure meaningful content
                        break
            except Exception:
                continue
        
        # Fallback: get body content but exclude common non-content sections
        if not content or len(content) < 100:
            body = soup.find('body')
            if body:
                # Remove common non-content sections
                for section in body.find_all(['header', 'nav', 'footer', 'aside', 'form', 'script', 'style']):
                    section.decompose()
                
                content = body.get_text(separator='\n', strip=True)
                # Clean up excessive whitespace
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                content = '\n'.join(lines)
        
        if not title or not content:
            print(f"  ⚠ Warning: Incomplete article data from {url}")
            return None
        
        return {
            'title': title,
            'date_published': date_published,
            'author': author,
            'content': content,
            'url': url,
            'source': 'apollo',
            'article_type': article_type
        }
    
    async def scrape_research_articles(self) -> List[Dict]:
        """
        Scrape all research articles from Apollo Research
        
        Returns:
            List of article dictionaries
        """
        print(f"Scraping Apollo Research articles from {self.RESEARCH_URL}...")
        
        # Fetch research page (try with JS rendering first for dynamic content)
        html = await self.fetch_page(self.RESEARCH_URL, use_js_rendering=True)
        if not html:
            html = await self.fetch_page(self.RESEARCH_URL, use_js_rendering=False)
        
        if not html:
            print("  ❌ Failed to fetch research page")
            return []
        
        # Parse article links
        article_links = self.parse_article_list(html, self.RESEARCH_URL, 'research')
        print(f"  Found {len(article_links)} research article links")
        
        if not article_links:
            print("  ⚠ Warning: No research article links found")
            return []
        
        # Scrape each article
        articles = []
        for i, link_info in enumerate(article_links, 1):
            url = link_info['url']
            print(f"  [{i}/{len(article_links)}] Scraping: {link_info.get('title', url[:50])}")
            
            article = await self.scrape_article(url, 'research')
            if article:
                articles.append(article)
            else:
                print(f"    ⚠ Failed to scrape article")
            
            # Small delay to be respectful
            await asyncio.sleep(0.5)
        
        print(f"  ✓ Successfully scraped {len(articles)}/{len(article_links)} research articles")
        return articles
    
    async def scrape_blog_articles(self) -> List[Dict]:
        """
        Scrape all blog articles from Apollo Research
        
        Returns:
            List of article dictionaries
        """
        print(f"Scraping Apollo Research blog from {self.BLOG_URL}...")
        
        # Fetch blog page (try with JS rendering first for dynamic content)
        html = await self.fetch_page(self.BLOG_URL, use_js_rendering=True)
        if not html:
            html = await self.fetch_page(self.BLOG_URL, use_js_rendering=False)
        
        if not html:
            print("  ❌ Failed to fetch blog page")
            return []
        
        # Parse article links
        article_links = self.parse_article_list(html, self.BLOG_URL, 'blog')
        print(f"  Found {len(article_links)} blog article links")
        
        if not article_links:
            print("  ⚠ Warning: No blog article links found")
            return []
        
        # Scrape each article
        articles = []
        for i, link_info in enumerate(article_links, 1):
            url = link_info['url']
            print(f"  [{i}/{len(article_links)}] Scraping: {link_info.get('title', url[:50])}")
            
            article = await self.scrape_article(url, 'blog')
            if article:
                articles.append(article)
            else:
                print(f"    ⚠ Failed to scrape article")
            
            # Small delay to be respectful
            await asyncio.sleep(0.5)
        
        print(f"  ✓ Successfully scraped {len(articles)}/{len(article_links)} blog articles")
        return articles
    
    async def scrape_all_articles(self) -> List[Dict]:
        """
        Scrape all articles from both research and blog pages
        
        Returns:
            List of all article dictionaries
        """
        all_articles = []
        
        # Scrape research articles
        research_articles = await self.scrape_research_articles()
        all_articles.extend(research_articles)
        
        # Scrape blog articles
        blog_articles = await self.scrape_blog_articles()
        all_articles.extend(blog_articles)
        
        return all_articles


async def main():
    """Test the scraper"""
    scraper = ApolloResearchScraper()
    try:
        articles = await scraper.scrape_all_articles()
        print(f"\nTotal articles scraped: {len(articles)}")
        if articles:
            print("\nFirst article:")
            first = articles[0]
            print(f"  Title: {first['title']}")
            print(f"  URL: {first['url']}")
            print(f"  Type: {first.get('article_type', 'N/A')}")
            print(f"  Date: {first.get('date_published', 'N/A')}")
            print(f"  Author: {first.get('author', 'N/A')}")
            print(f"  Content length: {len(first['content'])} chars")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())

