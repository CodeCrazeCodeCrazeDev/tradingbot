"""Book Knowledge Acquisition for Self-Improving Trading Bot.

This module implements the acquisition of knowledge from books, academic papers,
and other written sources.
"""

import os
import re
import uuid
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
try:
    import requests
except ImportError:
    requests = None
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import AutoTokenizer, AutoModel
try:
    import torch
except ImportError:
    torch = None
from pathlib import Path

from .knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, KnowledgeStatus
import numpy

# Ensure NLTK resources are downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)


class BookSource(Enum):
    """Types of book sources."""
    TEXTBOOK = "textbook"
    ACADEMIC_PAPER = "academic_paper"
    TRADING_BOOK = "trading_book"
    RESEARCH_PAPER = "research_paper"
    BLOG_ARTICLE = "blog_article"
    DOCUMENTATION = "documentation"


@dataclass
class BookKnowledge:
    """Knowledge extracted from a book or written source."""
    title: str
    content: str
    source: BookSource
    author: str
    publication_date: Optional[datetime] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    isbn: Optional[str] = None
    pages: Optional[str] = None
    chapter: Optional[str] = None
    summary: Optional[str] = None
    key_concepts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.8
    metadata: Dict[str, Any] = field(default_factory=dict)


class BookKnowledgeAcquisition:
    """System for acquiring knowledge from books and written sources."""
    
    def __init__(self, knowledge_base: KnowledgeBase, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """Initialize the book knowledge acquisition system.
        
        Args:
            knowledge_base: Knowledge base to store acquired knowledge
            model_name: Name of the transformer model for text embedding
        """
        self.knowledge_base = knowledge_base
        self.model_name = model_name
        
        # Initialize NLP components
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        # Initialize transformer model for semantic understanding
        self.tokenizer = None
        self.model = None
        self._load_transformer_model()
        
        # Cache for document embeddings
        self.embedding_cache = {}
        
        logger.info("Book knowledge acquisition system initialized")
    
    def _load_transformer_model(self):
        """Load the transformer model for text embedding."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            logger.info(f"Loaded transformer model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load transformer model: {e}")
            logger.warning("Falling back to TF-IDF vectorization only")
    
    def extract_from_text(self, text: str, title: str, source_type: BookSource, 
                         author: str, metadata: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        """Extract knowledge items from text.
        
        Args:
            text: Text content to extract knowledge from
            title: Title of the source
            source_type: Type of source
            author: Author of the source
            metadata: Additional metadata
            
        Returns:
            List of extracted knowledge items
        """
        logger.info(f"Extracting knowledge from text: {title}")
        
        # Extract key concepts and segments
        segments = self._segment_text(text)
        key_concepts = self._extract_key_concepts(text)
        
        # Create knowledge items
        knowledge_items = []
        
        # Process each segment
        for i, segment in enumerate(segments):
            if len(segment.strip()) < 100:  # Skip very short segments
                continue
                
            # Generate a title for the segment
            segment_title = self._generate_segment_title(segment, i, title)
            
            # Extract tags for this segment
            segment_tags = self._extract_tags(segment)
            
            # Combine with key concepts
            all_tags = list(set(segment_tags + key_concepts[:5]))
            
            # Create metadata
            item_metadata = {
                "source_title": title,
                "author": author,
                "source_type": source_type.value,
                "segment_index": i,
            }
            if metadata:
                item_metadata.update(metadata)
            
            # Create knowledge item
            item = KnowledgeItem(
                id=str(uuid.uuid4()),
                title=segment_title,
                content=segment,
                knowledge_type=KnowledgeType.BOOK,
                source=f"{source_type.value}:{title}",
                tags=all_tags,
                confidence=0.8,  # Default confidence for book knowledge
                acquisition_date=datetime.now(),
                status=KnowledgeStatus.UNVERIFIED,
                metadata=item_metadata
            )
            
            knowledge_items.append(item)
        
        logger.info(f"Extracted {len(knowledge_items)} knowledge items from: {title}")
        return knowledge_items
    
    def extract_from_file(self, file_path: str, source_type: BookSource, 
                         author: str, metadata: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        """Extract knowledge from a text file.
        
        Args:
            file_path: Path to the file
            source_type: Type of source
            author: Author of the source
            metadata: Additional metadata
            
        Returns:
            List of extracted knowledge items
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
        
        title = os.path.basename(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return self.extract_from_text(text, title, source_type, author, metadata)
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from file {file_path}: {e}")
            return []
    
    def extract_from_url(self, url: str, source_type: BookSource, 
                        author: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> List[KnowledgeItem]:
        """Extract knowledge from a URL.
        
        Args:
            url: URL to extract from
            source_type: Type of source
            author: Author of the source (if known)
            metadata: Additional metadata
            
        Returns:
            List of extracted knowledge items
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.title.string if soup.title else url
            
            # Extract author if not provided
            if not author:
                author_meta = soup.find('meta', {'name': 'author'})
                if author_meta:
                    author = author_meta.get('content', 'Unknown')
                else:
                    author = 'Unknown'
            
            # Extract main content
            main_content = ""
            
            # Try to find main content container
            article = soup.find('article')
            if article:
                main_content = article.get_text()
            else:
                # Try common content containers
                for container in ['main', 'div.content', 'div.post', 'div.article']:
                    content_div = soup.select_one(container)
                    if content_div:
                        main_content = content_div.get_text()
                        break
            
            # If still no content, use body text
            if not main_content:
                main_content = soup.get_text()
            
            # Clean up text
            main_content = re.sub(r'\s+', ' ', main_content).strip()
            
            # Add URL to metadata
            if metadata is None:
                metadata = {}
            metadata['url'] = url
            
            return self.extract_from_text(main_content, title, source_type, author, metadata)
            
        except Exception as e:
            logger.error(f"Error extracting knowledge from URL {url}: {e}")
            return []
    
    def store_knowledge_items(self, items: List[KnowledgeItem]) -> List[str]:
        """Store knowledge items in the knowledge base.
        
        Args:
            items: Knowledge items to store
            
        Returns:
            List of stored item IDs
        """
        stored_ids = []
        
        for item in items:
            # Check for duplicates
            similar_items = self._find_similar_items(item)
            
            if similar_items:
                # Update existing item instead of creating a duplicate
                existing_item = similar_items[0]
                logger.info(f"Found similar item: {existing_item.title} (ID: {existing_item.id})")
                
                # Merge tags
                existing_item.tags = list(set(existing_item.tags + item.tags))
                
                # Update confidence if new item has higher confidence
                if item.confidence > existing_item.confidence:
                    existing_item.confidence = item.confidence
                
                # Update metadata
                existing_item.metadata.update(item.metadata)
                
                # Store updated item
                self.knowledge_base.update_item(existing_item)
                stored_ids.append(existing_item.id)
                
            else:
                # Store new item
                item_id = self.knowledge_base.add_item(item)
                stored_ids.append(item_id)
        
        return stored_ids
    
    def _segment_text(self, text: str) -> List[str]:
        """Segment text into meaningful chunks.
        
        Args:
            text: Text to segment
            
        Returns:
            List of text segments
        """
        # First try to split by section headers
        sections = re.split(r'\n\s*#{1,6}\s+|\n\s*[A-Z][A-Z\s]+\n', text)
        
        # If we have reasonable sections, use them
        if len(sections) > 1 and all(len(s.strip()) > 200 for s in sections):
            return [s.strip() for s in sections]
        
        # Otherwise split by paragraphs and group them
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Group paragraphs into segments of reasonable size
        segments = []
        current_segment = ""
        
        for paragraph in paragraphs:
            if len(current_segment) + len(paragraph) < 2000:
                current_segment += paragraph + "\n\n"
            else:
                segments.append(current_segment.strip())
                current_segment = paragraph + "\n\n"
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text.
        
        Args:
            text: Text to extract concepts from
            
        Returns:
            List of key concepts
        """
        # Tokenize and clean text
        words = word_tokenize(text.lower())
        words = [w for w in words if w.isalnum() and w not in self.stop_words]
        
        # Extract single-word concepts using TF-IDF
        tfidf_matrix = self.vectorizer.fit_transform([text])
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Get top TF-IDF scores
        scores = zip(feature_names, tfidf_matrix.toarray()[0])
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Extract single-word concepts
        single_word_concepts = [word for word, score in sorted_scores[:20]]
        
        # Extract multi-word concepts using n-grams
        bigrams = list(nltk.bigrams(words))
        trigrams = list(nltk.trigrams(words))
        
        # Count n-grams
        bigram_counts = {}
        for bg in bigrams:
            bigram = ' '.join(bg)
            bigram_counts[bigram] = bigram_counts.get(bigram, 0) + 1
        
        trigram_counts = {}
        for tg in trigrams:
            trigram = ' '.join(tg)
            trigram_counts[trigram] = trigram_counts.get(trigram, 0) + 1
        
        # Get top n-grams
        top_bigrams = sorted(bigram_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_trigrams = sorted(trigram_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Combine all concepts
        all_concepts = single_word_concepts + [bg[0] for bg in top_bigrams] + [tg[0] for tg in top_trigrams]
        
        return all_concepts
    
    def _generate_segment_title(self, segment: str, index: int, source_title: str) -> str:
        """Generate a title for a text segment.
        
        Args:
            segment: Text segment
            index: Segment index
            source_title: Title of the source
            
        Returns:
            Generated title
        """
        # Try to find a header in the segment
        header_match = re.search(r'^#{1,6}\s+(.+)$', segment, re.MULTILINE)
        if header_match:
            return header_match.group(1).strip()
        
        # Try to find a capitalized line that could be a title
        lines = segment.split('\n')
        for line in lines[:3]:  # Check first few lines
            if line.isupper() or (line.strip() and line[0].isupper() and len(line) < 100):
                return line.strip()
        
        # Extract first sentence and use as title if it's not too long
        sentences = sent_tokenize(segment)
        if sentences and len(sentences[0]) < 100:
            return sentences[0]
        
        # Fall back to generic title
        return f"{source_title} - Section {index + 1}"
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text.
        
        Args:
            text: Text to extract tags from
            
        Returns:
            List of tags
        """
        # Use TF-IDF to find important terms
        tfidf_matrix = self.vectorizer.fit_transform([text])
        feature_names = self.vectorizer.get_feature_names_out()
        
        # Get top TF-IDF scores
        scores = zip(feature_names, tfidf_matrix.toarray()[0])
        sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
        
        # Extract top terms as tags
        tags = [word for word, score in sorted_scores[:10] if len(word) > 3]
        
        # Add trading-specific tags if they appear in the text
        trading_terms = [
            "trading", "market", "stock", "forex", "cryptocurrency", "technical", "fundamental",
            "analysis", "indicator", "strategy", "risk", "volatility", "trend", "momentum",
            "arbitrage", "algorithm", "backtest", "optimization", "machine learning", "ai"
        ]
        
        for term in trading_terms:
            if term in text.lower() and term not in tags:
                tags.append(term)
        
        return tags[:15]  # Limit to 15 tags
    
    def _find_similar_items(self, item: KnowledgeItem) -> List[KnowledgeItem]:
        """Find similar items in the knowledge base.
        
        Args:
            item: Knowledge item to find similar items for
            
        Returns:
            List of similar knowledge items
        """
        # First check for items with the same title
        title_matches = self.knowledge_base.search(query=item.title, limit=5)
        
        # If we have title matches, check content similarity
        if title_matches:
            similar_items = []
            for match in title_matches:
                similarity = self._calculate_text_similarity(item.content, match.content)
                if similarity > 0.7:  # High similarity threshold
                    similar_items.append(match)
            
            if similar_items:
                return similar_items
        
        # If no title matches or no similar content, check by tags
        if item.tags:
            tag_matches = self.knowledge_base.search(tags=item.tags[:3], limit=5)
            
            similar_items = []
            for match in tag_matches:
                similarity = self._calculate_text_similarity(item.content, match.content)
                if similarity > 0.6:  # Slightly lower threshold for tag matches
                    similar_items.append(match)
            
            if similar_items:
                return similar_items
        
        return []
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Use transformer model if available
        if self.model and self.tokenizer:
            return self._calculate_semantic_similarity(text1, text2)
        
        # Fall back to TF-IDF similarity
        return self._calculate_tfidf_similarity(text1, text2)
    
    def _calculate_tfidf_similarity(self, text1: str, text2: str) -> float:
        """Calculate TF-IDF cosine similarity between texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
        return (tfidf_matrix * tfidf_matrix.T).toarray()[0, 1]
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using transformer model.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Get or compute embeddings
        embedding1 = self._get_text_embedding(text1)
        embedding2 = self._get_text_embedding(text2)
        
        # Calculate cosine similarity
        similarity = torch.nn.functional.cosine_similarity(
            embedding1.unsqueeze(0), embedding2.unsqueeze(0)
        ).item()
        
        return max(0, similarity)  # Ensure non-negative
    
    def _get_text_embedding(self, text: str) -> torch.Tensor:
        """Get embedding for text using transformer model.
        
        Args:
            text: Text to embed
            
        Returns:
            Text embedding
        """
        # Check cache first
        text_hash = hash(text)
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        # Truncate text if too long
        max_length = self.tokenizer.model_max_length
        tokens = self.tokenizer(text, truncation=True, max_length=max_length, return_tensors="pt")
        
        # Generate embedding
        with torch.no_grad():
            outputs = self.model(**tokens)
        
        # Use mean pooling to get text embedding
        embedding = outputs.last_hidden_state.mean(dim=1).squeeze()
        
        # Cache embedding
        self.embedding_cache[text_hash] = embedding
        
        return embedding
