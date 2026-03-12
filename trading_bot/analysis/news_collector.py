"""
Financial News Collector for Sentiment Analysis
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from datetime import datetime, timedelta
try:
    import requests
except ImportError:
    requests = None
import json
import re
import asyncio
try:
    import aiohttp
except ImportError:
    aiohttp = None
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urlparse
import numpy
import pandas

logger = logging.getLogger(__name__)


class NewsCollector:
    """
    Financial news collector for sentiment analysis
    
    Features:
    - Multiple news sources
    - Async collection
    - Rate limiting
    - Content extraction
    - Duplicate detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # API keys
        self.api_keys = self.config.get('api_keys', {})
        
        # News sources
        self.sources = self.config.get('sources', [
            'alpha_vantage',
            'newsapi',
            'financial_times',
            'bloomberg',
            'reuters',
            'cnbc',
            'yahoo_finance',
            'seeking_alpha',
            'market_watch'
        ])
        
        # Rate limiting
        self.rate_limits = self.config.get('rate_limits', {
            'alpha_vantage': 5,  # requests per minute
            'newsapi': 100,  # requests per day
            'default': 10  # requests per minute
        })
        
        # Request timestamps for rate limiting
        self.request_timestamps = {source: [] for source in self.sources}
        
        # Duplicate detection
        self.seen_urls = set()
        self.seen_titles = set()
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        logger.info("News Collector initialized")
    
    async def collect_news(self, tickers: List[str] = None, 
                         keywords: List[str] = None,
                         max_age_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Collect financial news for tickers and keywords
        
        Args:
            tickers: List of ticker symbols
            keywords: List of keywords
            max_age_hours: Maximum age of news in hours
            
        Returns:
            List of news articles
        """
        if not tickers and not keywords:
            logger.warning("No tickers or keywords provided")
            return []
        
        tickers = tickers or []
        keywords = keywords or []
        
        # Combine tickers and keywords for search
        search_terms = tickers + keywords
        
        # Collect news from all sources
        all_news = []
        
        # Create tasks for each source
        tasks = []
        for source in self.sources:
            if hasattr(self, f"_collect_from_{source}"):
                tasks.append(getattr(self, f"_collect_from_{source}")(search_terms, max_age_hours))
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error collecting news: {result}")
            elif isinstance(result, list):
                all_news.extend(result)
        
        # Remove duplicates
        unique_news = self._remove_duplicates(all_news)
        
        # Sort by date (newest first)
        unique_news.sort(key=lambda x: x.get('published_at', datetime.now()), reverse=True)
        
        return unique_news
    
    async def _collect_from_alpha_vantage(self, search_terms: List[str], 
                                        max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect news from Alpha Vantage"""
        api_key = self.api_keys.get('alpha_vantage')
        if not api_key:
            logger.warning("No API key for Alpha Vantage")
            return []
        
        news = []
        
        # Check rate limit
        if not self._check_rate_limit('alpha_vantage'):
            logger.warning("Rate limit exceeded for Alpha Vantage")
            return []
        
        # Alpha Vantage only supports one ticker at a time
        for term in search_terms:
            try:
                # Record request timestamp
                self._record_request('alpha_vantage')
                
                # Make API request
                url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={term}&apikey={api_key}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract news items
                            items = data.get('feed', [])
                            
                            for item in items:
                                # Check age
                                published_at = datetime.fromisoformat(item.get('time_published', '').replace('Z', '+00:00'))
                                if datetime.now() - published_at > timedelta(hours=max_age_hours):
                                    continue
                                
                                # Extract data
                                article = {
                                    'title': item.get('title', ''),
                                    'url': item.get('url', ''),
                                    'source': item.get('source', 'Alpha Vantage'),
                                    'published_at': published_at,
                                    'summary': item.get('summary', ''),
                                    'sentiment': item.get('overall_sentiment_score', 0),
                                    'tickers': item.get('ticker_sentiment', []),
                                    'content': '',
                                    'collected_at': datetime.now()
                                }
                                
                                news.append(article)
                        else:
                            logger.warning(f"Error from Alpha Vantage API: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error collecting from Alpha Vantage: {e}")
        
        return news
    
    async def _collect_from_newsapi(self, search_terms: List[str], 
                                  max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect news from NewsAPI"""
        api_key = self.api_keys.get('newsapi')
        if not api_key:
            logger.warning("No API key for NewsAPI")
            return []
        
        news = []
        
        # Check rate limit
        if not self._check_rate_limit('newsapi'):
            logger.warning("Rate limit exceeded for NewsAPI")
            return []
        try:
        
            # Record request timestamp
            self._record_request('newsapi')
            
            # Prepare query
            query = ' OR '.join(search_terms)
            
            # Calculate date range
            from_date = (datetime.now() - timedelta(hours=max_age_hours)).strftime('%Y-%m-%d')
            
            # Make API request
            url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&language=en&sortBy=publishedAt&apiKey={api_key}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract news items
                        items = data.get('articles', [])
                        
                        for item in items:
                            # Extract data
                            published_at = datetime.fromisoformat(item.get('publishedAt', '').replace('Z', '+00:00'))
                            
                            article = {
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'source': item.get('source', {}).get('name', 'NewsAPI'),
                                'published_at': published_at,
                                'summary': item.get('description', ''),
                                'content': item.get('content', ''),
                                'collected_at': datetime.now()
                            }
                            
                            news.append(article)
                    else:
                        logger.warning(f"Error from NewsAPI: {response.status}")
            
        except Exception as e:
            logger.error(f"Error collecting from NewsAPI: {e}")
        
        return news
    
    async def _collect_from_yahoo_finance(self, search_terms: List[str], 
                                        max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect news from Yahoo Finance"""
        news = []
        
        # Check rate limit
        if not self._check_rate_limit('yahoo_finance'):
            logger.warning("Rate limit exceeded for Yahoo Finance")
            return []
        
        # Yahoo Finance supports multiple tickers
        for term in search_terms:
            try:
                # Record request timestamp
                self._record_request('yahoo_finance')
                
                # Make request
                url = f"https://finance.yahoo.com/quote/{term}/news"
                headers = {'User-Agent': random.choice(self.user_agents)}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Parse HTML
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find news items
                            news_items = soup.select(r'div.Ov\(h\) Pend\(44px\)')
                            
                            for item in news_items:
                                try:
                                    # Extract data
                                    title_elem = item.select_one('h3')
                                    link_elem = item.select_one('a')
                                    source_elem = item.select_one(r'div.C\(#959595\)')
                                    time_elem = item.select_one('span')
                                    
                                    if not title_elem or not link_elem:
                                        continue
                                    
                                    title = title_elem.text.strip()
                                    url = 'https://finance.yahoo.com' + link_elem['href']
                                    source = source_elem.text.strip() if source_elem else 'Yahoo Finance'
                                    
                                    # Parse time
                                    time_text = time_elem.text.strip() if time_elem else ''
                                    published_at = self._parse_relative_time(time_text)
                                    
                                    # Check age
                                    if datetime.now() - published_at > timedelta(hours=max_age_hours):
                                        continue
                                    
                                    # Extract article content
                                    article_content = await self._extract_article_content(url)
                                    
                                    article = {
                                        'title': title,
                                        'url': url,
                                        'source': source,
                                        'published_at': published_at,
                                        'summary': '',
                                        'content': article_content,
                                        'collected_at': datetime.now()
                                    }
                                    
                                    news.append(article)
                                    
                                except Exception as e:
                                    logger.warning(f"Error parsing Yahoo Finance news item: {e}")
                        else:
                            logger.warning(f"Error from Yahoo Finance: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error collecting from Yahoo Finance: {e}")
        
        return news
    
    async def _collect_from_seeking_alpha(self, search_terms: List[str], 
                                        max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect news from Seeking Alpha"""
        news = []
        
        # Check rate limit
        if not self._check_rate_limit('seeking_alpha'):
            logger.warning("Rate limit exceeded for Seeking Alpha")
            return []
        
        # Seeking Alpha supports multiple tickers
        for term in search_terms:
            try:
                # Record request timestamp
                self._record_request('seeking_alpha')
                
                # Make request
                url = f"https://seekingalpha.com/symbol/{term}/news"
                headers = {'User-Agent': random.choice(self.user_agents)}
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Parse HTML
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find news items
                            news_items = soup.select('div[data-test-id="post-list-item"]')
                            
                            for item in news_items:
                                try:
                                    # Extract data
                                    title_elem = item.select_one('a[data-test-id="post-list-item-title"]')
                                    time_elem = item.select_one('span[data-test-id="post-list-item-date"]')
                                    
                                    if not title_elem:
                                        continue
                                    
                                    title = title_elem.text.strip()
                                    url = 'https://seekingalpha.com' + title_elem['href']
                                    
                                    # Parse time
                                    time_text = time_elem.text.strip() if time_elem else ''
                                    published_at = self._parse_relative_time(time_text)
                                    
                                    # Check age
                                    if datetime.now() - published_at > timedelta(hours=max_age_hours):
                                        continue
                                    
                                    # Extract article content
                                    article_content = await self._extract_article_content(url)
                                    
                                    article = {
                                        'title': title,
                                        'url': url,
                                        'source': 'Seeking Alpha',
                                        'published_at': published_at,
                                        'summary': '',
                                        'content': article_content,
                                        'collected_at': datetime.now()
                                    }
                                    
                                    news.append(article)
                                    
                                except Exception as e:
                                    logger.warning(f"Error parsing Seeking Alpha news item: {e}")
                        else:
                            logger.warning(f"Error from Seeking Alpha: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(3)
                
            except Exception as e:
                logger.error(f"Error collecting from Seeking Alpha: {e}")
        
        return news
    
    async def _extract_article_content(self, url: str) -> str:
        """Extract content from article URL"""
        try:
            # Check rate limit for the domain
            domain = urlparse(url).netloc
            if not self._check_rate_limit(domain):
                logger.warning(f"Rate limit exceeded for {domain}")
                return ""
            
            # Record request timestamp
            self._record_request(domain)
            
            # Make request
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parse HTML
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Extract text
                        text = soup.get_text(separator=' ', strip=True)
                        
                        # Clean text
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        # Limit length
                        if len(text) > 5000:
                            text = text[:5000] + '...'
                        
                        return text
                    else:
                        logger.warning(f"Error extracting content from {url}: {response.status}")
                        return ""
        except Exception as e:
            logger.warning(f"Error extracting content from {url}: {e}")
            return ""
    
    def _parse_relative_time(self, time_text: str) -> datetime:
        """Parse relative time strings like '2 hours ago'"""
        now = datetime.now()
        
        if not time_text:
            return now
        
        time_text = time_text.lower()
        
        # Parse patterns like "2 hours ago", "5 minutes ago", "yesterday", etc.
        if 'hour' in time_text:
            hours = int(re.search(r'(\d+)', time_text).group(1))
            return now - timedelta(hours=hours)
        elif 'minute' in time_text:
            minutes = int(re.search(r'(\d+)', time_text).group(1))
            return now - timedelta(minutes=minutes)
        elif 'day' in time_text:
            days = int(re.search(r'(\d+)', time_text).group(1))
            return now - timedelta(days=days)
        elif 'yesterday' in time_text:
            return now - timedelta(days=1)
        elif 'week' in time_text:
            weeks = int(re.search(r'(\d+)', time_text).group(1))
            return now - timedelta(weeks=weeks)
        elif 'month' in time_text:
            # Approximate
            months = int(re.search(r'(\d+)', time_text).group(1))
            return now - timedelta(days=30 * months)
        else:
            try:
                # Try to parse absolute date
                # Common formats
                formats = [
                    '%b %d, %Y',  # Jan 1, 2023
                    '%B %d, %Y',  # January 1, 2023
                    '%m/%d/%Y',   # 01/01/2023
                    '%Y-%m-%d'    # 2023-01-01
                ]
                
                for fmt in formats:
                    try:
                        return datetime.strptime(time_text, fmt)
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # Default to current time if parsing fails
        return now
    
    def _check_rate_limit(self, source: str) -> bool:
        """Check if rate limit allows a request"""
        timestamps = self.request_timestamps.get(source, [])
        
        # Get rate limit for source
        rate_limit = self.rate_limits.get(source, self.rate_limits.get('default', 10))
        
        # Remove old timestamps
        now = time.time()
        timestamps = [ts for ts in timestamps if now - ts < 60]  # Keep last minute
        
        # Check if under limit
        return len(timestamps) < rate_limit
    
    def _record_request(self, source: str):
        """Record a request timestamp for rate limiting"""
        if source not in self.request_timestamps:
            self.request_timestamps[source] = []
        
        self.request_timestamps[source].append(time.time())
    
    def _remove_duplicates(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate articles"""
        unique_articles = []
        
        for article in articles:
            url = article.get('url', '')
            title = article.get('title', '')
            
            # Skip if URL or title already seen
            if url in self.seen_urls or title in self.seen_titles:
                continue
            
            # Add to seen sets
            if url:
                self.seen_urls.add(url)
            if title:
                self.seen_titles.add(title)
            
            unique_articles.append(article)
        
        return unique_articles


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create collector
    collector = NewsCollector({
        'api_keys': {
            'alpha_vantage': 'YOUR_API_KEY',
            'newsapi': 'YOUR_API_KEY'
        }
    })
    
    # Run async collection
    async def main():
        news = await collector.collect_news(
            tickers=['AAPL', 'MSFT', 'GOOGL'],
            keywords=['tech stocks', 'earnings'],
            max_age_hours=24
        )
        
        logger.info(f"Collected {len(news)} news articles")
        
        for article in news[:5]:  # Print first 5
            logger.info(f"Title: {article['title']}")
            logger.info(f"Source: {article['source']}")
            logger.info(f"Published: {article['published_at']}")
            logger.info(f"URL: {article['url']}")
            print()
    
    asyncio.run(main())
