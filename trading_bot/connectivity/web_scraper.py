"""
Elite Trading Bot - Web Scraper

This module provides web scraping capabilities for news and sentiment analysis,
allowing the trading bot to gather market-relevant information from the web.
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse, urljoin

try:
    import aiohttp
except ImportError:
    aiohttp = None
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from .web_client import WebClient, RequestMethod
from .rate_limiter import RateLimiter

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

# Ensure NLTK resources are available
try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)


class WebScraper:
    """
    Web scraper for news and sentiment analysis.
    
    Features:
    - Scraping financial news websites
    - HTML parsing and content extraction
    - Sentiment analysis of news articles
    - Rate limiting to avoid overloading websites
    - Respecting robots.txt
    """
    
    def __init__(self, 
                 rate_limiter: Optional[RateLimiter] = None,
                 user_agent: Optional[str] = None,
                 respect_robots_txt: bool = True):
        """
        Initialize the web scraper.
        
        Args:
            rate_limiter: Optional rate limiter
            user_agent: User agent string for requests
            respect_robots_txt: Whether to respect robots.txt
        """
        self.rate_limiter = rate_limiter
        self.user_agent = user_agent or "EliteTradingBot/1.0 NewsAnalyzer"
        self.respect_robots_txt = respect_robots_txt
        
        # Initialize web client
        self.client = WebClient(
            headers={"User-Agent": self.user_agent}
        )
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Cache for robots.txt
        self.robots_cache: Dict[str, Dict[str, Any]] = {}
        
        logger.info("WebScraper initialized")
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with scraped content
        """
        # Check if we're allowed to scrape this URL
        if self.respect_robots_txt and not await self._can_fetch(url):
            logger.warning(f"Robots.txt disallows scraping {url}")
            return {"error": "Robots.txt disallows scraping this URL"}
        
        # Apply rate limiting if configured
        if self.rate_limiter:
            try:
                domain = urlparse(url).netloc
                await self.rate_limiter.acquire(f"scrape_{domain}")

                # Fetch page content
                response = await self.client.async_get(url)
                html_content = await response.text()

                # Parse HTML
                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract content
                result = self._extract_content(soup, url)

                logger.info(f"Successfully scraped {url}")
                return result

            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                return {"error": str(e)}

    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract content from parsed HTML.
        
        Args:
            soup: BeautifulSoup object
            url: Source URL
            
        Returns:
            Dictionary with extracted content
        """
        # Extract title
        title = soup.title.text.strip() if soup.title else ""
        
        # Extract main content based on common patterns
        content = ""
        
        # Try article tag first
        article = soup.find('article')
        if article:
            content = article.get_text(separator=' ', strip=True)
        else:
            # Try common content div classes/ids
            content_selectors = [
                'div.content', 'div.article-content', 'div.post-content',
                'div.entry-content', 'div.story-content', 'div#content',
                'div.article-body', 'div.story-body'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text(separator=' ', strip=True)
                    break
            
            # If still no content, use main tag
            if not content:
                main = soup.find('main')
                if main:
                    content = main.get_text(separator=' ', strip=True)
        
        # If still no content, use body text but remove scripts, styles, etc.
        if not content:
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.extract()
            content = soup.body.get_text(separator=' ', strip=True) if soup.body else ""
        
        # Extract publish date
        publish_date = None
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\w+ \d{1,2}, \d{4})'  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, str(soup))
            if date_match:
                publish_date = date_match.group(1)
                break
        
        # Extract author
        author = None
        author_selectors = [
            'meta[name="author"]',
            'a[rel="author"]',
            '.author',
            '.byline'
        ]
        
        for selector in author_selectors:
            author_elem = soup.select_one(selector)
            if author_elem:
                if selector == 'meta[name="author"]':
                    author = author_elem.get('content')
                else:
                    author = author_elem.get_text(strip=True)
                break
        
        # Extract keywords/tags
        keywords = []
        keywords_meta = soup.find('meta', {'name': 'keywords'})
        if keywords_meta and keywords_meta.get('content'):
            keywords = [k.strip() for k in keywords_meta['content'].split(',')]
        
        # If no keywords from meta, try to find tag links
        if not keywords:
            tag_links = soup.select('a.tag, a[rel="tag"], .tags a')
            keywords = [tag.get_text(strip=True) for tag in tag_links]
        
        # Analyze sentiment
        sentiment = self._analyze_sentiment(content)
        
        return {
            "url": url,
            "title": title,
            "content": content,
            "publish_date": publish_date,
            "author": author,
            "keywords": keywords,
            "sentiment": sentiment,
            "scraped_at": datetime.now().isoformat()
        }
    
    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment scores
        """
        scores = self.sentiment_analyzer.polarity_scores(text)
        
        return {
            "positive": scores['pos'],
            "negative": scores['neg'],
            "neutral": scores['neu'],
            "compound": scores['compound']
        }
    
    async def _can_fetch(self, url: str) -> bool:
        """
        Check if robots.txt allows fetching a URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed, False otherwise
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Check cache
        if domain in self.robots_cache:
            cache_entry = self.robots_cache[domain]
            
            # Check if cache is expired (24 hours)
            if time.time() - cache_entry['timestamp'] < 86400:
                # Check if path is allowed
                path = parsed_url.path
                for disallowed in cache_entry['disallowed']:
                    if path.startswith(disallowed):
                        return False
                return True
        
        # Fetch robots.txt
        robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
        
        try:
            response = await self.client.async_get(robots_url)
            robots_txt = await response.text()
            
            # Parse robots.txt
            disallowed_paths = []
            user_agent_match = False
            
            for line in robots_txt.splitlines():
                line = line.strip().lower()
                
                if line.startswith('user-agent:'):
                    agent = line[11:].strip()
                    user_agent_match = agent == '*' or self.user_agent.lower().startswith(agent)
                
                elif user_agent_match and line.startswith('disallow:'):
                    path = line[9:].strip()
                    if path:
                        disallowed_paths.append(path)
            
            # Cache result
            self.robots_cache[domain] = {
                'timestamp': time.time(),
                'disallowed': disallowed_paths
            }
            
            # Check if path is allowed
            path = parsed_url.path
            for disallowed in disallowed_paths:
                if path.startswith(disallowed):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching robots.txt for {domain}: {str(e)}")
            return True  # Allow by default if robots.txt can't be fetched
    
    async def scrape_news(self, 
                         sources: List[str], 
                         keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape news from multiple sources.
        
        Args:
            sources: List of news source URLs
            keywords: Optional list of keywords to filter articles
            
        Returns:
            List of news articles
        """
        tasks = [self.scrape_source(source, keywords) for source in sources]
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        articles = []
        for source_articles in results:
            articles.extend(source_articles)
        
        return articles
    
    async def scrape_source(self, 
                           source_url: str, 
                           keywords: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape news from a single source.
        
        Args:
            source_url: News source URL
            keywords: Optional list of keywords to filter articles
            
        Returns:
            List of news articles
        """
        try:
            # Scrape main page
            main_page = await self.scrape_url(source_url)
            
            if 'error' in main_page:
                logger.error(f"Error scraping {source_url}: {main_page['error']}")
                return []
            
            # Extract article links
            soup = BeautifulSoup(main_page.get('content', ''), 'html.parser')
            article_links = self._extract_article_links(soup, source_url)
            
            # Filter by keywords if provided
            if keywords:
                filtered_links = []
                for link in article_links:
                    if any(keyword.lower() in link['title'].lower() for keyword in keywords):
                        filtered_links.append(link)
                article_links = filtered_links
            
            # Limit to 5 articles to avoid overloading
            article_links = article_links[:5]
            
            # Scrape individual articles
            articles = []
            for link in article_links:
                article = await self.scrape_url(link['url'])
                if 'error' not in article:
                    articles.append(article)
                
                # Add delay between requests
                await asyncio.sleep(1)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping source {source_url}: {str(e)}")
            return []
    
    def _extract_article_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """
        Extract article links from a page.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of article links with titles
        """
        links = []
        
        # Find all links
        for a in soup.find_all('a', href=True):
            url = a['href']
            
            # Resolve relative URLs
            if not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            # Skip non-article links
            parsed_url = urlparse(url)
            if parsed_url.netloc != urlparse(base_url).netloc:
                continue
            
            # Skip links to homepage
            if parsed_url.path in ('/', '/index.html'):
                continue
            
            # Get title from text or title attribute
            title = a.get('title', a.get_text(strip=True))
            
            # Skip empty titles or navigation links
            if not title or len(title) < 10:
                continue
            
            # Add to list if not already present
            link_info = {'url': url, 'title': title}
            if link_info not in links:
                links.append(link_info)
        
        return links
    
    async def analyze_market_sentiment(self, 
                                     symbols: List[str], 
                                     sources: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze market sentiment for specific symbols.
        
        Args:
            symbols: List of market symbols (e.g., "BTC", "AAPL")
            sources: List of news sources
            
        Returns:
            Dictionary of sentiment analysis by symbol
        """
        results = {}
        
        for symbol in symbols:
            # Scrape news related to this symbol
            articles = await self.scrape_news(sources, [symbol])
            
            if not articles:
                results[symbol] = {
                    "sentiment": {
                        "positive": 0.0,
                        "negative": 0.0,
                        "neutral": 0.0,
                        "compound": 0.0
                    },
                    "article_count": 0,
                    "latest_articles": []
                }
                continue
            
            # Aggregate sentiment
            positive = 0.0
            negative = 0.0
            neutral = 0.0
            compound = 0.0
            
            for article in articles:
                sentiment = article.get('sentiment', {})
                positive += sentiment.get('positive', 0.0)
                negative += sentiment.get('negative', 0.0)
                neutral += sentiment.get('neutral', 0.0)
                compound += sentiment.get('compound', 0.0)
            
            # Calculate average
            count = len(articles)
            avg_sentiment = {
                "positive": positive / count if count > 0 else 0.0,
                "negative": negative / count if count > 0 else 0.0,
                "neutral": neutral / count if count > 0 else 0.0,
                "compound": compound / count if count > 0 else 0.0
            }
            
            # Prepare result
            results[symbol] = {
                "sentiment": avg_sentiment,
                "article_count": count,
                "latest_articles": [
                    {
                        "title": article.get('title', ''),
                        "url": article.get('url', ''),
                        "publish_date": article.get('publish_date', ''),
                        "sentiment": article.get('sentiment', {})
                    }
                    for article in articles[:3]  # Include top 3 articles
                ]
            }
        
        return results


class FinancialNewsScraper(WebScraper):
    """Specialized scraper for financial news websites."""
    
    def __init__(self, **kwargs):
        """
        Initialize financial news scraper.
        
        Args:
            **kwargs: Additional scraper parameters
        """
        super().__init__(**kwargs)
        
        # Common financial news sources
        self.common_sources = [
            "https://www.reuters.com/markets",
            "https://www.bloomberg.com/markets",
            "https://www.cnbc.com/markets",
            "https://www.ft.com/markets",
            "https://www.wsj.com/news/markets"
        ]
    
    async def get_market_news(self, market_type: str = "crypto") -> List[Dict[str, Any]]:
        """
        Get news for a specific market type.
        
        Args:
            market_type: Market type ("crypto", "stocks", "forex", "commodities")
            
        Returns:
            List of news articles
        """
        sources = self._get_sources_for_market(market_type)
        return await self.scrape_news(sources)
    
    def _get_sources_for_market(self, market_type: str) -> List[str]:
        """
        Get news sources for a specific market type.
        
        Args:
            market_type: Market type
            
        Returns:
            List of news source URLs
        """
        if market_type == "crypto":
            return [
                "https://www.coindesk.com",
                "https://cointelegraph.com",
                "https://decrypt.co"
            ]
        elif market_type == "stocks":
            return [
                "https://www.cnbc.com/markets",
                "https://www.marketwatch.com",
                "https://www.investors.com"
            ]
        elif market_type == "forex":
            return [
                "https://www.dailyfx.com",
                "https://www.fxstreet.com",
                "https://www.forexlive.com"
            ]
        elif market_type == "commodities":
            return [
                "https://www.kitco.com",
                "https://www.investing.com/commodities",
                "https://www.spglobal.com/commodityinsights"
            ]
        else:
            return self.common_sources
