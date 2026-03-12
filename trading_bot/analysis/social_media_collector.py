"""
Social Media Collector for Financial Sentiment Analysis
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
import base64
import hmac
import hashlib
from urllib.parse import urlencode
import numpy
import pandas

logger = logging.getLogger(__name__)


class SocialMediaCollector:
    """
    Social media collector for financial sentiment analysis
    
    Features:
    - Multiple social media platforms
    - Async collection
    - Rate limiting
    - Content filtering
    - Duplicate detection
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # API keys
        self.api_keys = self.config.get('api_keys', {})
        
        # Social media platforms
        self.platforms = self.config.get('platforms', [
            'twitter',
            'reddit',
            'stocktwits',
            'tradingview',
            'discord'
        ])
        
        # Rate limiting
        self.rate_limits = self.config.get('rate_limits', {
            'twitter': 450,  # requests per 15 minutes
            'reddit': 60,    # requests per minute
            'stocktwits': 200,  # requests per hour
            'tradingview': 20,  # requests per minute
            'discord': 50,   # requests per second
            'default': 10    # requests per minute
        })
        
        # Request timestamps for rate limiting
        self.request_timestamps = {platform: [] for platform in self.platforms}
        
        # Duplicate detection
        self.seen_ids = set()
        self.seen_texts = set()
        
        # User agent rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        logger.info("Social Media Collector initialized")
    
    async def collect_posts(self, tickers: List[str] = None, 
                          keywords: List[str] = None,
                          max_age_hours: int = 24,
                          platforms: List[str] = None) -> List[Dict[str, Any]]:
        """
        Collect social media posts for tickers and keywords
        
        Args:
            tickers: List of ticker symbols
            keywords: List of keywords
            max_age_hours: Maximum age of posts in hours
            platforms: List of platforms to collect from (default: all)
            
        Returns:
            List of social media posts
        """
        if not tickers and not keywords:
            logger.warning("No tickers or keywords provided")
            return []
        
        tickers = tickers or []
        keywords = keywords or []
        platforms = platforms or self.platforms
        
        # Combine tickers and keywords for search
        search_terms = tickers + keywords
        
        # Collect posts from all platforms
        all_posts = []
        
        # Create tasks for each platform
        tasks = []
        for platform in platforms:
            if platform in self.platforms and hasattr(self, f"_collect_from_{platform}"):
                tasks.append(getattr(self, f"_collect_from_{platform}")(search_terms, max_age_hours))
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error collecting posts: {result}")
            elif isinstance(result, list):
                all_posts.extend(result)
        
        # Remove duplicates
        unique_posts = self._remove_duplicates(all_posts)
        
        # Sort by date (newest first)
        unique_posts.sort(key=lambda x: x.get('created_at', datetime.now()), reverse=True)
        
        return unique_posts
    
    async def _collect_from_twitter(self, search_terms: List[str], 
                                  max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect posts from Twitter"""
        api_key = self.api_keys.get('twitter', {}).get('api_key')
        api_secret = self.api_keys.get('twitter', {}).get('api_secret')
        bearer_token = self.api_keys.get('twitter', {}).get('bearer_token')
        
        if not (api_key and api_secret) and not bearer_token:
            logger.warning("No API credentials for Twitter")
            return []
        
        posts = []
        
        # Check rate limit
        if not self._check_rate_limit('twitter'):
            logger.warning("Rate limit exceeded for Twitter")
            return []
        try:
        
            # Get bearer token if not provided
            if not bearer_token:
                bearer_token = await self._get_twitter_bearer_token(api_key, api_secret)
            
            # Record request timestamp
            self._record_request('twitter')
            
            # Search for each term
            for term in search_terms:
                # Format search query
                query = f"{term} -is:retweet lang:en"
                
                # Calculate start time
                start_time = (datetime.now() - timedelta(hours=max_age_hours)).isoformat() + 'Z'
                
                # Make API request
                url = "https://api.twitter.com/2/tweets/search/recent"
                params = {
                    'query': query,
                    'max_results': 100,
                    'tweet.fields': 'created_at,public_metrics,entities',
                    'start_time': start_time
                }
                
                headers = {
                    'Authorization': f'Bearer {bearer_token}'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract tweets
                            tweets = data.get('data', [])
                            
                            for tweet in tweets:
                                # Extract data
                                created_at = datetime.fromisoformat(tweet.get('created_at', '').replace('Z', '+00:00'))
                                
                                # Extract mentioned tickers
                                mentioned_tickers = []
                                entities = tweet.get('entities', {})
                                hashtags = entities.get('hashtags', [])
                                
                                for hashtag in hashtags:
                                    tag = hashtag.get('tag', '')
                                    if tag.startswith('$'):
                                        mentioned_tickers.append(tag[1:])
                                
                                # Extract metrics
                                metrics = tweet.get('public_metrics', {})
                                
                                post = {
                                    'id': tweet.get('id', ''),
                                    'text': tweet.get('text', ''),
                                    'created_at': created_at,
                                    'platform': 'twitter',
                                    'user': '',  # Not available in recent search API
                                    'likes': metrics.get('like_count', 0),
                                    'retweets': metrics.get('retweet_count', 0),
                                    'replies': metrics.get('reply_count', 0),
                                    'mentions': mentioned_tickers,
                                    'collected_at': datetime.now()
                                }
                                
                                posts.append(post)
                        else:
                            logger.warning(f"Error from Twitter API: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error collecting from Twitter: {e}")
        
        return posts
    
    async def _get_twitter_bearer_token(self, api_key: str, api_secret: str) -> str:
        """Get Twitter bearer token"""
        try:
            # Encode credentials
            credentials = f"{api_key}:{api_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Make token request
            url = "https://api.twitter.com/oauth2/token"
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
            }
            data = {'grant_type': 'client_credentials'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('access_token', '')
                    else:
                        logger.warning(f"Error getting Twitter bearer token: {response.status}")
                        return ''
        except Exception as e:
            logger.error(f"Error getting Twitter bearer token: {e}")
            return ''
    
    async def _collect_from_reddit(self, search_terms: List[str], 
                                 max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect posts from Reddit"""
        client_id = self.api_keys.get('reddit', {}).get('client_id')
        client_secret = self.api_keys.get('reddit', {}).get('client_secret')
        
        if not client_id or not client_secret:
            logger.warning("No API credentials for Reddit")
            return []
        
        posts = []
        
        # Check rate limit
        if not self._check_rate_limit('reddit'):
            logger.warning("Rate limit exceeded for Reddit")
            return []
        try:
        
            # Get access token
            token = await self._get_reddit_token(client_id, client_secret)
            if not token:
                return []
            
            # Search for each term
            for term in search_terms:
                # Record request timestamp
                self._record_request('reddit')
                
                # Make API request
                url = f"https://oauth.reddit.com/search"
                params = {
                    'q': term,
                    't': 'day',  # Time filter: hour, day, week, month, year, all
                    'sort': 'new',
                    'limit': 100
                }
                
                headers = {
                    'Authorization': f'bearer {token}',
                    'User-Agent': random.choice(self.user_agents)
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract posts
                            items = data.get('data', {}).get('children', [])
                            
                            for item in items:
                                post_data = item.get('data', {})
                                
                                # Extract data
                                created_utc = post_data.get('created_utc', 0)
                                created_at = datetime.fromtimestamp(created_utc)
                                
                                # Check age
                                if datetime.now() - created_at > timedelta(hours=max_age_hours):
                                    continue
                                
                                # Extract mentioned tickers
                                mentioned_tickers = []
                                text = post_data.get('title', '') + ' ' + post_data.get('selftext', '')
                                
                                # Look for cashtags ($AAPL)
                                cashtags = re.findall(r'\$([A-Za-z]+)', text)
                                mentioned_tickers.extend(cashtags)
                                
                                post = {
                                    'id': post_data.get('id', ''),
                                    'title': post_data.get('title', ''),
                                    'text': post_data.get('selftext', ''),
                                    'created_at': created_at,
                                    'platform': 'reddit',
                                    'subreddit': post_data.get('subreddit', ''),
                                    'user': post_data.get('author', ''),
                                    'upvotes': post_data.get('ups', 0),
                                    'comments': post_data.get('num_comments', 0),
                                    'url': f"https://www.reddit.com{post_data.get('permalink', '')}",
                                    'mentions': mentioned_tickers,
                                    'collected_at': datetime.now()
                                }
                                
                                posts.append(post)
                        else:
                            logger.warning(f"Error from Reddit API: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error collecting from Reddit: {e}")
        
        return posts
    
    async def _get_reddit_token(self, client_id: str, client_secret: str) -> str:
        """Get Reddit access token"""
        try:
            # Encode credentials
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            
            # Make token request
            url = "https://www.reddit.com/api/v1/access_token"
            headers = {
                'Authorization': f'Basic {auth}',
                'User-Agent': random.choice(self.user_agents)
            }
            data = {'grant_type': 'client_credentials'}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('access_token', '')
                    else:
                        logger.warning(f"Error getting Reddit token: {response.status}")
                        return ''
        except Exception as e:
            logger.error(f"Error getting Reddit token: {e}")
            return ''
    
    async def _collect_from_stocktwits(self, search_terms: List[str], 
                                     max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect posts from StockTwits"""
        api_key = self.api_keys.get('stocktwits')
        
        posts = []
        
        # Check rate limit
        if not self._check_rate_limit('stocktwits'):
            logger.warning("Rate limit exceeded for StockTwits")
            return []
        try:
        
            # Search for each term
            for term in search_terms:
                # Record request timestamp
                self._record_request('stocktwits')
                
                # Format search query (StockTwits uses symbols like $AAPL)
                symbol = term
                if not symbol.startswith('$'):
                    symbol = f"${symbol}"
                
                # Make API request
                url = f"https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"
                params = {}
                
                if api_key:
                    params['access_token'] = api_key
                
                headers = {
                    'User-Agent': random.choice(self.user_agents)
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract messages
                            messages = data.get('messages', [])
                            
                            for message in messages:
                                # Extract data
                                created_at_str = message.get('created_at', '')
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                                
                                # Check age
                                if datetime.now() - created_at > timedelta(hours=max_age_hours):
                                    continue
                                
                                # Extract user
                                user = message.get('user', {})
                                
                                # Extract symbols
                                symbols = message.get('symbols', [])
                                mentioned_tickers = [s.get('symbol', '').replace('$', '') for s in symbols]
                                
                                post = {
                                    'id': message.get('id', ''),
                                    'text': message.get('body', ''),
                                    'created_at': created_at,
                                    'platform': 'stocktwits',
                                    'user': user.get('username', ''),
                                    'followers': user.get('followers', 0),
                                    'sentiment': message.get('entities', {}).get('sentiment', {}).get('basic', ''),
                                    'mentions': mentioned_tickers,
                                    'collected_at': datetime.now()
                                }
                                
                                posts.append(post)
                        else:
                            logger.warning(f"Error from StockTwits API: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error collecting from StockTwits: {e}")
        
        return posts
    
    async def _collect_from_tradingview(self, search_terms: List[str], 
                                      max_age_hours: int) -> List[Dict[str, Any]]:
        """Collect posts from TradingView"""
        posts = []
        
        # Check rate limit
        if not self._check_rate_limit('tradingview'):
            logger.warning("Rate limit exceeded for TradingView")
            return []
        try:
        
            # Search for each term
            for term in search_terms:
                # Record request timestamp
                self._record_request('tradingview')
                
                # Make API request (TradingView doesn't have an official API, so we scrape the ideas page)
                url = f"https://www.tradingview.com/ideas/search/{term}/"
                headers = {
                    'User-Agent': random.choice(self.user_agents)
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            html = await response.text()
                            
                            # Parse HTML
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find idea cards
                            idea_cards = soup.select('div.tv-card-container')
                            
                            for card in idea_cards:
                                try:
                                    # Extract data
                                    title_elem = card.select_one('div.tv-widget-idea__title')
                                    content_elem = card.select_one('p.tv-widget-idea__description-row')
                                    time_elem = card.select_one('span.tv-widget-idea__time')
                                    user_elem = card.select_one('span.tv-widget-idea__author')
                                    symbol_elem = card.select_one('div.tv-widget-idea__symbol-info')
                                    
                                    if not title_elem:
                                        continue
                                    
                                    title = title_elem.text.strip()
                                    content = content_elem.text.strip() if content_elem else ''
                                    
                                    # Parse time
                                    time_text = time_elem.text.strip() if time_elem else ''
                                    created_at = self._parse_relative_time(time_text)
                                    
                                    # Check age
                                    if datetime.now() - created_at > timedelta(hours=max_age_hours):
                                        continue
                                    
                                    # Extract user
                                    user = user_elem.text.strip() if user_elem else ''
                                    
                                    # Extract symbol
                                    symbol = symbol_elem.text.strip() if symbol_elem else ''
                                    
                                    # Extract sentiment from title and content
                                    text = title + ' ' + content
                                    sentiment = 'neutral'
                                    
                                    if re.search(r'buy|long|bullish|upside|breakout|support', text, re.IGNORECASE):
                                        sentiment = 'bullish'
                                    elif re.search(r'sell|short|bearish|downside|breakdown|resistance', text, re.IGNORECASE):
                                        sentiment = 'bearish'
                                    
                                    post = {
                                        'id': '',  # No ID available from scraping
                                        'title': title,
                                        'text': content,
                                        'created_at': created_at,
                                        'platform': 'tradingview',
                                        'user': user,
                                        'symbol': symbol,
                                        'sentiment': sentiment,
                                        'mentions': [symbol] if symbol else [],
                                        'collected_at': datetime.now()
                                    }
                                    
                                    posts.append(post)
                                    
                                except Exception as e:
                                    logger.warning(f"Error parsing TradingView idea card: {e}")
                        else:
                            logger.warning(f"Error from TradingView: {response.status}")
                
                # Respect rate limit
                await asyncio.sleep(3)
                
        except Exception as e:
            logger.error(f"Error collecting from TradingView: {e}")
        
        return posts
    
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
    
    def _check_rate_limit(self, platform: str) -> bool:
        """Check if rate limit allows a request"""
        timestamps = self.request_timestamps.get(platform, [])
        
        # Get rate limit for platform
        rate_limit = self.rate_limits.get(platform, self.rate_limits.get('default', 10))
        
        # Remove old timestamps
        now = time.time()
        
        # Different time windows for different platforms
        if platform == 'twitter':
            # 15 minutes window
            timestamps = [ts for ts in timestamps if now - ts < 15 * 60]
        elif platform == 'stocktwits':
            # 1 hour window
            timestamps = [ts for ts in timestamps if now - ts < 60 * 60]
        else:
            # 1 minute window
            timestamps = [ts for ts in timestamps if now - ts < 60]
        
        # Update timestamps
        self.request_timestamps[platform] = timestamps
        
        # Check if under limit
        return len(timestamps) < rate_limit
    
    def _record_request(self, platform: str):
        """Record a request timestamp for rate limiting"""
        if platform not in self.request_timestamps:
            self.request_timestamps[platform] = []
        
        self.request_timestamps[platform].append(time.time())
    
    def _remove_duplicates(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts"""
        unique_posts = []
        
        for post in posts:
            post_id = post.get('id', '')
            text = post.get('text', '')
            
            # Generate hash for text to detect near-duplicates
            text_hash = None
            if text:
                text_hash = hash(text[:100])  # Use first 100 chars for hash
            
            # Skip if ID or text already seen
            if (post_id and post_id in self.seen_ids) or (text_hash and text_hash in self.seen_texts):
                continue
            
            # Add to seen sets
            if post_id:
                self.seen_ids.add(post_id)
            if text_hash:
                self.seen_texts.add(text_hash)
            
            unique_posts.append(post)
        
        return unique_posts


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create collector
    collector = SocialMediaCollector({
        'api_keys': {
            'twitter': {
                'api_key': 'YOUR_API_KEY',
                'api_secret': 'YOUR_API_SECRET'
            },
            'reddit': {
                'client_id': 'YOUR_CLIENT_ID',
                'client_secret': 'YOUR_CLIENT_SECRET'
            }
        }
    })
    
    # Run async collection
    async def main():
        posts = await collector.collect_posts(
            tickers=['AAPL', 'TSLA', 'BTC'],
            keywords=['tech stocks', 'earnings'],
            max_age_hours=24
        )
        
        logger.info(f"Collected {len(posts)} social media posts")
        
        for post in posts[:5]:  # Print first 5
            logger.info(f"Platform: {post['platform']}")
            logger.info(f"Text: {post['text'][:100]}...")
            logger.info(f"Created: {post['created_at']}")
            logger.info(f"Mentions: {post['mentions']}")
            print()
    
    asyncio.run(main())
