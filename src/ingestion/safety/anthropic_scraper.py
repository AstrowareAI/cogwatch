"""
Anthropic Alignment Blog Scraper
Scrapes articles from https://alignment.anthropic.com/
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


class AnthropicAlignmentScraper:
    """Scraper for Anthropic Alignment Science Blog articles"""
    
    BASE_URL = "https://alignment.anthropic.com/"
    
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
    
    def parse_article_list(self, html: str, base_url: str) -> List[Dict[str, str]]:
        """
        Parse article links from the main blog page
        
        Returns:
            List of dictionaries with 'url' and 'title' keys
        """
        soup = BeautifulSoup(html, 'html.parser')
        articles = []
        
        # Anthropic blog structure: articles are typically in a list or grid
        # Look for article containers first
        article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and (
            'article' in x.lower() or 
            'post' in x.lower() or
            'entry' in x.lower()
        ))
        
        # If no article containers found, fall back to all links
        if not article_containers:
            article_containers = [soup]
        
        seen_urls = set()
        for container in article_containers:
            links = container.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                title_text = link.get_text(strip=True)
                
                # Skip if no meaningful title or too short
                if not title_text or len(title_text) < 10:
                    continue
                
                # Skip common non-article links
                if any(skip in title_text.lower() for skip in ['read more', 'continue reading', 'home', 'about', 'contact']):
                    continue
                
                # Build full URL
                if href.startswith('http'):
                    full_url = href
                elif href.startswith('/'):
                    full_url = urljoin(base_url, href)
                else:
                    full_url = urljoin(base_url, '/' + href)
                
                # Only include URLs from the same domain
                parsed_base = urlparse(base_url)
                parsed_link = urlparse(full_url)
                
                if parsed_link.netloc != parsed_base.netloc:
                    continue
                
                # Skip root URL, anchor links, and non-article pages
                path_parts = [p for p in parsed_link.path.split('/') if p]
                if (full_url == base_url or 
                    full_url.endswith('#') or 
                    '#' in full_url.split('/')[-1] or
                    len(path_parts) < 1):
                    continue
                
                # Skip common non-article paths
                skip_paths = ['/about', '/contact', '/privacy', '/terms', '/search']
                if any(full_url.startswith(base_url + sp) for sp in skip_paths):
                    continue
                
                # Avoid duplicates
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                
                # Try to find a better title from parent elements
                parent = link.find_parent(['article', 'div', 'li', 'section'])
                if parent:
                    title_elem = parent.find(['h1', 'h2', 'h3', 'h4'], recursive=False)
                    if title_elem:
                        title_text = title_elem.get_text(strip=True)
                
                articles.append({
                    'url': full_url,
                    'title': title_text
                })
        
        return articles
    
    async def scrape_article(self, url: str) -> Optional[Dict]:
        """
        Scrape a single article page
        
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
            'source': 'anthropic',
            'article_type': 'blog'
        }
    
    async def scrape_all_articles(self) -> List[Dict]:
        """
        Scrape all articles from the Anthropic Alignment Blog
        
        Returns:
            List of article dictionaries
        """
        print(f"Scraping Anthropic Alignment Blog from {self.BASE_URL}...")
        
        # Fetch main page
        html = await self.fetch_page(self.BASE_URL)
        if not html:
            print("  ❌ Failed to fetch main page")
            return []
        
        # Parse article links
        article_links = self.parse_article_list(html, self.BASE_URL)
        print(f"  Found {len(article_links)} article links")
        
        if not article_links:
            print("  ⚠ Warning: No article links found")
            return []
        
        # Scrape each article
        articles = []
        for i, link_info in enumerate(article_links, 1):
            url = link_info['url']
            print(f"  [{i}/{len(article_links)}] Scraping: {link_info.get('title', url[:50])}")
            
            article = await self.scrape_article(url)
            if article:
                articles.append(article)
            else:
                print(f"    ⚠ Failed to scrape article")
            
            # Small delay to be respectful
            await asyncio.sleep(0.5)
        
        print(f"  ✓ Successfully scraped {len(articles)}/{len(article_links)} articles")
        return articles


async def main():
    """Test the scraper"""
    scraper = AnthropicAlignmentScraper()
    try:
        articles = await scraper.scrape_all_articles()
        print(f"\nTotal articles scraped: {len(articles)}")
        if articles:
            print("\nFirst article:")
            first = articles[0]
            print(f"  Title: {first['title']}")
            print(f"  URL: {first['url']}")
            print(f"  Date: {first.get('date_published', 'N/A')}")
            print(f"  Author: {first.get('author', 'N/A')}")
            print(f"  Content length: {len(first['content'])} chars")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())

