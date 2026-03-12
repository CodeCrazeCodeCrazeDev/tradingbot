"""
Phase 6: Multimodal Intelligence - Text Processing
Processes financial news and social media data
"""

import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging

logger = logging.getLogger(__name__)


class NewsEncoder:
    """
    Encodes financial news articles using BERT.
    Fine-tuned for financial domain.
    """
    
    def __init__(
        self,
        model_name: str = "ProsusAI/finbert",
        max_length: int = 512,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(device)
            self.max_length = max_length
            self.device = device
        
            logger.info("✅ News Encoder initialized")
            logger.info(f"   Model: {model_name}")
            logger.info(f"   Device: {device}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def encode(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> torch.Tensor:
        """
        Encode batch of news articles.
        
        Args:
            texts: List of news articles
            batch_size: Batch size for processing
        
        Returns:
            Tensor of encoded articles [num_articles, hidden_dim]
        """
        try:
            all_embeddings = []
        
            # Process in batches
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
            
                # Tokenize
                inputs = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                ).to(self.device)
            
                # Generate embeddings
                with torch.no_grad():
                    outputs = self.model(**inputs)
                
                    # Use CLS token embedding
                    embeddings = outputs.last_hidden_state[:, 0, :]
                    all_embeddings.append(embeddings.cpu())
        
            # Concatenate all embeddings
            return torch.cat(all_embeddings, dim=0)
        except Exception as e:
            logger.error(f"Error in encode: {e}")
            raise
    
    def encode_with_sentiment(
        self,
        texts: List[str]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Encode texts and extract sentiment scores.
        
        Returns:
            Tuple of (embeddings, sentiment_scores)
        """
        try:
            embeddings = self.encode(texts)
        
            # Simple sentiment scoring
            sentiment_scores = torch.zeros(len(texts))
        
            for i, text in enumerate(texts):
                score = self._analyze_sentiment(text)
                sentiment_scores[i] = score
        
            return embeddings, sentiment_scores
        except Exception as e:
            logger.error(f"Error in encode_with_sentiment: {e}")
            raise
    
    def _analyze_sentiment(self, text: str) -> float:
        """Simple rule-based sentiment analysis."""
        # Positive words
        try:
            positive = [
                'bullish', 'positive', 'growth', 'gains', 'profit',
                'increase', 'higher', 'strong', 'rally', 'surge'
            ]
        
            # Negative words
            negative = [
                'bearish', 'negative', 'decline', 'losses', 'risk',
                'decrease', 'lower', 'weak', 'crash', 'plunge'
            ]
        
            # Count sentiment words
            text = text.lower()
            pos_count = sum(1 for word in positive if word in text)
            neg_count = sum(1 for word in negative if word in text)
        
            # Calculate sentiment score [-1, 1]
            total = pos_count + neg_count
            if total == 0:
                return 0.0
        
            return (pos_count - neg_count) / total
        except Exception as e:
            logger.error(f"Error in _analyze_sentiment: {e}")
            raise


class SocialMediaEncoder:
    """
    Processes social media data (Twitter, Reddit, etc.).
    Optimized for short-form financial content.
    """
    
    def __init__(
        self,
        model_name: str = "vinai/bertweet-base",
        max_length: int = 128,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(device)
            self.max_length = max_length
            self.device = device
        
            # Cashtag/hashtag handling
            self.special_tokens = {
                'cashtag': '$',
                'hashtag': '#'
            }
        
            logger.info("✅ Social Media Encoder initialized")
            logger.info(f"   Model: {model_name}")
            logger.info(f"   Device: {device}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def encode(
        self,
        posts: List[str],
        batch_size: int = 64
    ) -> torch.Tensor:
        """
        Encode social media posts.
        
        Args:
            posts: List of social media posts
            batch_size: Batch size for processing
        
        Returns:
            Tensor of encoded posts [num_posts, hidden_dim]
        """
        # Preprocess posts
        try:
            processed_posts = [self._preprocess_post(p) for p in posts]
        
            all_embeddings = []
        
            # Process in batches
            for i in range(0, len(processed_posts), batch_size):
                batch_posts = processed_posts[i:i + batch_size]
            
                # Tokenize
                inputs = self.tokenizer(
                    batch_posts,
                    padding=True,
                    truncation=True,
                    max_length=self.max_length,
                    return_tensors="pt"
                ).to(self.device)
            
                # Generate embeddings
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    embeddings = outputs.last_hidden_state.mean(dim=1)
                    all_embeddings.append(embeddings.cpu())
        
            return torch.cat(all_embeddings, dim=0)
        except Exception as e:
            logger.error(f"Error in encode: {e}")
            raise
    
    def _preprocess_post(self, post: str) -> str:
        """Preprocess social media post."""
        # Handle cashtags and hashtags
        try:
            words = post.split()
            processed_words = []
        
            for word in words:
                if word.startswith('$'):
                    processed_words.append(f"<cashtag>{word[1:]}</cashtag>")
                elif word.startswith('#'):
                    processed_words.append(f"<hashtag>{word[1:]}</hashtag>")
                else:
                    processed_words.append(word)
        
            return ' '.join(processed_words)
        except Exception as e:
            logger.error(f"Error in _preprocess_post: {e}")
            raise
    
    def extract_symbols(self, post: str) -> List[str]:
        """Extract mentioned stock symbols."""
        try:
            symbols = []
        
            words = post.split()
            for word in words:
                if word.startswith('$'):
                    symbol = word[1:].upper()
                    if symbol.isalpha():  # Basic validation
                        symbols.append(symbol)
        
            return symbols
        except Exception as e:
            logger.error(f"Error in extract_symbols: {e}")
            raise
    
    def analyze_sentiment_with_confidence(
        self,
        post: str
    ) -> Tuple[float, float]:
        """
        Analyze sentiment with confidence score.
        
        Returns:
            Tuple of (sentiment_score, confidence)
        """
        # Encode post
        try:
            embedding = self.encode([post])
        
            # Project to sentiment space
            sentiment = torch.tanh(embedding.mean())  # [-1, 1]
        
            # Confidence based on post characteristics
            confidence = self._calculate_confidence(post)
        
            return float(sentiment), confidence
        except Exception as e:
            logger.error(f"Error in analyze_sentiment_with_confidence: {e}")
            raise
    
    def _calculate_confidence(self, post: str) -> float:
        """Calculate confidence in sentiment analysis."""
        try:
            confidence = 0.5  # Base confidence
        
            # Adjust based on characteristics
            if len(post.split()) > 20:  # Longer posts more reliable
                confidence += 0.1
        
            if post.count('$') > 0:  # Contains cashtags
                confidence += 0.1
        
            if any(word in post.lower() for word in ['think', 'believe', 'expect']):
                confidence += 0.1  # Expression of opinion
        
            if post.count('http') > 0:  # Contains links
                confidence += 0.1  # Supporting evidence
        
            return min(confidence, 1.0)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise


class MultiSourceTextProcessor:
    """
    Processes and combines text from multiple sources.
    Handles news, social media, and other text data.
    """
    
    def __init__(self):
        try:
            self.news_encoder = NewsEncoder()
            self.social_encoder = SocialMediaEncoder()
        
            # Source weights
            self.source_weights = {
                'news': 0.6,
                'social': 0.4
            }
        
            logger.info("✅ Multi-Source Text Processor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def process_all_sources(
        self,
        news_articles: List[str],
        social_posts: List[str]
    ) -> Dict:
        """
        Process text from all sources.
        
        Returns:
            Dictionary with embeddings and analysis
        """
        # Process news
        try:
            news_embeddings, news_sentiment = self.news_encoder.encode_with_sentiment(
                news_articles
            )
        
            # Process social media
            social_embeddings = self.social_encoder.encode(social_posts)
        
            # Extract mentioned symbols
            symbols = []
            for post in social_posts:
                symbols.extend(self.social_encoder.extract_symbols(post))
            symbol_counts = {s: symbols.count(s) for s in set(symbols)}
        
            # Analyze social sentiment
            social_sentiment = []
            social_confidence = []
        
            for post in social_posts:
                sentiment, confidence = self.social_encoder.analyze_sentiment_with_confidence(
                    post
                )
                social_sentiment.append(sentiment)
                social_confidence.append(confidence)
        
            # Combine sentiment scores
            combined_sentiment = (
                self.source_weights['news'] * news_sentiment.mean() +
                self.source_weights['social'] * torch.tensor(social_sentiment).mean()
            )
        
            return {
                'news_embeddings': news_embeddings,
                'social_embeddings': social_embeddings,
                'combined_sentiment': float(combined_sentiment),
                'symbol_mentions': symbol_counts,
                'news_sentiment': news_sentiment,
                'social_sentiment': social_sentiment,
                'social_confidence': social_confidence
            }
        except Exception as e:
            logger.error(f"Error in process_all_sources: {e}")
            raise
    
    def update_source_weights(
        self,
        news_accuracy: float,
        social_accuracy: float
    ):
        """Update source weights based on accuracy."""
        try:
            total = news_accuracy + social_accuracy
            if total > 0:
                self.source_weights['news'] = news_accuracy / total
                self.source_weights['social'] = social_accuracy / total
            
                logger.info("📊 Updated source weights:")
                logger.info(f"   News: {self.source_weights['news']:.2f}")
                logger.info(f"   Social: {self.source_weights['social']:.2f}")
        except Exception as e:
            logger.error(f"Error in update_source_weights: {e}")
            raise
    
    def save_state(self, filepath: str):
        """Save processor state."""
        try:
            state = {
                'source_weights': self.source_weights
            }
            torch.save(state, filepath)
            logger.info(f"💾 Text Processor state saved to {filepath}")
        except Exception as e:
            logger.error(f"Error in save_state: {e}")
            raise
    
    def load_state(self, filepath: str):
        """Load processor state."""
        try:
            state = torch.load(filepath)
            self.source_weights = state['source_weights']
            logger.info(f"📂 Text Processor state loaded from {filepath}")
            logger.info(f"   Weights: {self.source_weights}")
        except Exception as e:
            logger.error(f"Error in load_state: {e}")
            raise
