"""
AADS OpenCLIP Visual Intelligence Pipeline

Inspired by OpenCLIP's vision-language contrastive learning. Financial markets
produce enormous volumes of visual data that traditional NLP cannot process.
Images are treated as first-class alpha signals.

Visual Alpha Sources:
- Chart patterns (head-and-shoulders, breakouts, volume profiles)
- Satellite imagery (parking lots, factories, ports, shipping)
- Earnings presentation slides (charts, tables, body language)
- News article images (protests, disasters, product launches)
- Social media images (conference attendance, product events)

Features:
- Zero-shot visual classification using CLIP embeddings
- Financial-specific category taxonomy
- Sentiment extraction from visual content
- Chart pattern recognition
- Satellite imagery analysis
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import logging
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


class VisualCategory(Enum):
    """Categories of visual signals"""
    CHART_PATTERN = "chart_pattern"
    SATELLITE = "satellite"
    NEWS_EVENT = "news_event"
    EARNINGS = "earnings"
    SOCIAL = "social"
    PRODUCT = "product"
    INFRASTRUCTURE = "infrastructure"


class VisualSentiment(Enum):
    """Sentiment derived from visual analysis"""
    STRONGLY_BULLISH = "strongly_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONGLY_BEARISH = "strongly_bearish"


@dataclass
class VisualSignal:
    """Output from visual analysis pipeline"""
    source: str                         # Image path or URL
    image_hash: str                     # Hash for deduplication
    category: VisualCategory
    top_classification: str             # Best matching category
    confidence: float                   # Classification confidence
    sentiment: VisualSentiment
    sentiment_score: float              # -1 to 1
    
    # Extracted data
    detected_assets: List[str] = field(default_factory=list)
    extracted_text: Optional[str] = None
    extracted_numbers: Dict[str, float] = field(default_factory=dict)
    
    # Embedding for similarity search
    embedding: Optional[np.ndarray] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    processing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'image_hash': self.image_hash,
            'category': self.category.value,
            'top_classification': self.top_classification,
            'confidence': self.confidence,
            'sentiment': self.sentiment.value,
            'sentiment_score': self.sentiment_score,
            'detected_assets': self.detected_assets,
            'extracted_text': self.extracted_text,
            'extracted_numbers': self.extracted_numbers,
            'timestamp': self.timestamp.isoformat()
        }


class OpenCLIPPipeline:
    """
    OpenCLIP-based visual intelligence pipeline for financial signals.
    
    Uses CLIP embedding space where similar financial contexts cluster together,
    enabling zero-shot visual classification.
    """
    
    # Financial-specific classification categories
    FINANCIAL_CATEGORIES = [
        # Chart patterns (bullish)
        "bullish breakout chart pattern with high volume",
        "cup and handle bullish continuation pattern",
        "ascending triangle bullish pattern",
        "golden cross moving average bullish signal",
        "accumulation base forming with increasing volume",
        
        # Chart patterns (bearish)
        "bearish head and shoulders reversal pattern",
        "descending triangle bearish pattern",
        "death cross moving average bearish signal",
        "volume capitulation selling pattern",
        "distribution top forming with decreasing volume",
        
        # Satellite / alternative (bullish)
        "busy parking lot high consumer activity retail",
        "ship congestion port high trade activity",
        "factory lights on high production activity",
        "construction activity new development growth",
        "crowded airport high travel demand",
        
        # Satellite / alternative (bearish)
        "empty parking lot low consumer activity",
        "port congestion supply chain disruption",
        "factory lights off production halt shutdown",
        "abandoned construction stalled development",
        "empty airport low travel demand",
        
        # News / event imagery (bullish)
        "product launch event consumer excitement crowd",
        "executive confident earnings presentation success",
        "ribbon cutting ceremony new store opening",
        "packed conference high industry interest",
        "celebration corporate milestone achievement",
        
        # News / event imagery (bearish)
        "protest crowd political instability unrest",
        "natural disaster flood fire supply chain risk",
        "empty store retail decline bankruptcy",
        "executive nervous uncertain earnings presentation",
        "layoff announcement corporate restructuring",
        
        # Neutral / informational
        "financial chart with technical indicators",
        "corporate office building exterior",
        "warehouse logistics distribution center",
        "data center technology infrastructure",
        "trading floor stock exchange"
    ]
    
    # Category to sentiment mapping
    CATEGORY_SENTIMENT = {
        "bullish breakout chart pattern with high volume": (VisualSentiment.STRONGLY_BULLISH, 0.9),
        "cup and handle bullish continuation pattern": (VisualSentiment.BULLISH, 0.7),
        "ascending triangle bullish pattern": (VisualSentiment.BULLISH, 0.6),
        "golden cross moving average bullish signal": (VisualSentiment.BULLISH, 0.7),
        "accumulation base forming with increasing volume": (VisualSentiment.BULLISH, 0.5),
        
        "bearish head and shoulders reversal pattern": (VisualSentiment.STRONGLY_BEARISH, -0.9),
        "descending triangle bearish pattern": (VisualSentiment.BEARISH, -0.6),
        "death cross moving average bearish signal": (VisualSentiment.BEARISH, -0.7),
        "volume capitulation selling pattern": (VisualSentiment.STRONGLY_BEARISH, -0.8),
        "distribution top forming with decreasing volume": (VisualSentiment.BEARISH, -0.5),
        
        "busy parking lot high consumer activity retail": (VisualSentiment.BULLISH, 0.6),
        "ship congestion port high trade activity": (VisualSentiment.BULLISH, 0.4),
        "factory lights on high production activity": (VisualSentiment.BULLISH, 0.5),
        "construction activity new development growth": (VisualSentiment.BULLISH, 0.4),
        "crowded airport high travel demand": (VisualSentiment.BULLISH, 0.5),
        
        "empty parking lot low consumer activity": (VisualSentiment.BEARISH, -0.6),
        "port congestion supply chain disruption": (VisualSentiment.BEARISH, -0.5),
        "factory lights off production halt shutdown": (VisualSentiment.STRONGLY_BEARISH, -0.8),
        "abandoned construction stalled development": (VisualSentiment.BEARISH, -0.6),
        "empty airport low travel demand": (VisualSentiment.BEARISH, -0.5),
        
        "product launch event consumer excitement crowd": (VisualSentiment.BULLISH, 0.7),
        "executive confident earnings presentation success": (VisualSentiment.BULLISH, 0.6),
        "ribbon cutting ceremony new store opening": (VisualSentiment.BULLISH, 0.4),
        "packed conference high industry interest": (VisualSentiment.BULLISH, 0.3),
        "celebration corporate milestone achievement": (VisualSentiment.BULLISH, 0.5),
        
        "protest crowd political instability unrest": (VisualSentiment.BEARISH, -0.6),
        "natural disaster flood fire supply chain risk": (VisualSentiment.STRONGLY_BEARISH, -0.9),
        "empty store retail decline bankruptcy": (VisualSentiment.STRONGLY_BEARISH, -0.8),
        "executive nervous uncertain earnings presentation": (VisualSentiment.BEARISH, -0.5),
        "layoff announcement corporate restructuring": (VisualSentiment.BEARISH, -0.6),
        
        "financial chart with technical indicators": (VisualSentiment.NEUTRAL, 0.0),
        "corporate office building exterior": (VisualSentiment.NEUTRAL, 0.0),
        "warehouse logistics distribution center": (VisualSentiment.NEUTRAL, 0.0),
        "data center technology infrastructure": (VisualSentiment.NEUTRAL, 0.0),
        "trading floor stock exchange": (VisualSentiment.NEUTRAL, 0.0),
    }
    
    def __init__(self, model_name: str = "ViT-B-32"):
        """
        Initialize the OpenCLIP pipeline.
        
        Args:
            model_name: CLIP model variant to use
        """
        self.model_name = model_name
        self.model = None
        self.preprocess = None
        self.tokenizer = None
        
        # Pre-compute category embeddings
        self.category_embeddings: Dict[str, np.ndarray] = {}
        self._initialize_category_embeddings()
        
        # Cache for processed images
        self.cache: Dict[str, VisualSignal] = {}
        
        logger.info(f"OpenCLIPPipeline initialized with model {model_name}")
    
    def _initialize_category_embeddings(self) -> None:
        """Pre-compute embeddings for all financial categories"""
        for category in self.FINANCIAL_CATEGORIES:
            # Placeholder: generate pseudo-embedding from text hash
            # In production, use actual CLIP text encoder
            embedding = self._text_to_embedding(category)
            self.category_embeddings[category] = embedding
    
    def _text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding (placeholder)"""
        # In production, use CLIP text encoder
        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = np.frombuffer(hash_bytes, dtype=np.float32)[:32]
        return embedding / (np.linalg.norm(embedding) + 1e-10)
    
    def _image_to_embedding(self, image_path: str) -> np.ndarray:
        """Convert image to embedding (placeholder)"""
        # In production, use CLIP image encoder
        # For now, generate pseudo-embedding from path hash
        hash_bytes = hashlib.sha256(image_path.encode()).digest()
        embedding = np.frombuffer(hash_bytes, dtype=np.float32)[:32]
        return embedding / (np.linalg.norm(embedding) + 1e-10)
    
    def _compute_image_hash(self, image_path: str) -> str:
        """Compute hash for image deduplication"""
        return hashlib.md5(image_path.encode()).hexdigest()[:16]
    
    def analyze(self, image_source: str) -> VisualSignal:
        """
        Analyze an image for financial signals.
        
        Args:
            image_source: Path or URL to image
            
        Returns:
            VisualSignal with classification and sentiment
        """
        import time
        start_time = time.time()
        
        # Check cache
        image_hash = self._compute_image_hash(image_source)
        if image_hash in self.cache:
            return self.cache[image_hash]
        
        # Get image embedding
        image_embedding = self._image_to_embedding(image_source)
        
        # Calculate similarity to each financial category
        similarities = {}
        for category, cat_embedding in self.category_embeddings.items():
            similarity = float(np.dot(image_embedding, cat_embedding))
            similarities[category] = similarity
        
        # Find best matching category
        top_category = max(similarities, key=similarities.get)
        confidence = similarities[top_category]
        
        # Normalize confidence to [0, 1]
        confidence = (confidence + 1) / 2  # Assuming cosine similarity in [-1, 1]
        
        # Get sentiment from category
        sentiment_info = self.CATEGORY_SENTIMENT.get(
            top_category,
            (VisualSentiment.NEUTRAL, 0.0)
        )
        sentiment, sentiment_score = sentiment_info
        
        # Determine visual category
        visual_category = self._classify_visual_category(top_category)
        
        # Create signal
        signal = VisualSignal(
            source=image_source,
            image_hash=image_hash,
            category=visual_category,
            top_classification=top_category,
            confidence=confidence,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            embedding=image_embedding,
            processing_time_ms=(time.time() - start_time) * 1000
        )
        
        # Cache result
        self.cache[image_hash] = signal
        
        return signal
    
    def _classify_visual_category(self, top_classification: str) -> VisualCategory:
        """Map classification to visual category"""
        classification_lower = top_classification.lower()
        
        if any(kw in classification_lower for kw in ['chart', 'pattern', 'cross', 'triangle']):
            return VisualCategory.CHART_PATTERN
        elif any(kw in classification_lower for kw in ['parking', 'factory', 'port', 'airport', 'satellite']):
            return VisualCategory.SATELLITE
        elif any(kw in classification_lower for kw in ['protest', 'disaster', 'flood', 'fire']):
            return VisualCategory.NEWS_EVENT
        elif any(kw in classification_lower for kw in ['earnings', 'executive', 'presentation']):
            return VisualCategory.EARNINGS
        elif any(kw in classification_lower for kw in ['launch', 'conference', 'celebration']):
            return VisualCategory.PRODUCT
        else:
            return VisualCategory.INFRASTRUCTURE
    
    def analyze_batch(self, image_sources: List[str]) -> List[VisualSignal]:
        """Analyze multiple images"""
        return [self.analyze(source) for source in image_sources]
    
    def analyze_earnings_slides(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyze earnings presentation slides.
        
        Extracts and analyzes every slide for:
        - Chart sentiment
        - Executive body language
        - Key metrics visibility
        
        Args:
            pdf_path: Path to earnings presentation PDF
            
        Returns:
            Aggregated analysis of all slides
        """
        # In production, convert PDF to images and analyze each
        # For now, return placeholder analysis
        
        # Simulate slide analysis
        num_slides = np.random.randint(10, 30)
        slide_signals = []
        
        for i in range(num_slides):
            # Generate pseudo-signal for each slide
            signal = VisualSignal(
                source=f"{pdf_path}#slide{i}",
                image_hash=f"slide_{i}_{hashlib.md5(pdf_path.encode()).hexdigest()[:8]}",
                category=VisualCategory.EARNINGS,
                top_classification="earnings presentation slide",
                confidence=np.random.uniform(0.6, 0.95),
                sentiment=np.random.choice(list(VisualSentiment)),
                sentiment_score=np.random.uniform(-0.5, 0.5)
            )
            slide_signals.append(signal)
        
        # Aggregate signals
        bullish_count = sum(1 for s in slide_signals if s.sentiment_score > 0.2)
        bearish_count = sum(1 for s in slide_signals if s.sentiment_score < -0.2)
        avg_sentiment = np.mean([s.sentiment_score for s in slide_signals])
        
        return {
            'pdf_path': pdf_path,
            'num_slides': num_slides,
            'bullish_slides': bullish_count,
            'bearish_slides': bearish_count,
            'neutral_slides': num_slides - bullish_count - bearish_count,
            'avg_sentiment_score': avg_sentiment,
            'overall_sentiment': (
                VisualSentiment.BULLISH if avg_sentiment > 0.2
                else VisualSentiment.BEARISH if avg_sentiment < -0.2
                else VisualSentiment.NEUTRAL
            ).value,
            'confidence': np.mean([s.confidence for s in slide_signals]),
            'slide_signals': [s.to_dict() for s in slide_signals[:5]]  # First 5 for brevity
        }
    
    def analyze_satellite_imagery(
        self,
        image_path: str,
        target_type: str,
        baseline_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze satellite imagery for economic signals.
        
        Target types:
        - parking_lot: Retail activity indicator
        - factory: Manufacturing activity
        - port: Trade/shipping activity
        - construction: Development activity
        
        Args:
            image_path: Path to satellite image
            target_type: Type of target to analyze
            baseline_path: Optional baseline image for comparison
            
        Returns:
            Analysis results with activity metrics
        """
        # Analyze current image
        signal = self.analyze(image_path)
        
        # Simulate activity level detection
        # In production, use object detection / segmentation
        activity_level = np.random.uniform(0.3, 0.9)
        
        # Compare to baseline if provided
        change_from_baseline = None
        if baseline_path:
            baseline_activity = np.random.uniform(0.3, 0.9)
            change_from_baseline = activity_level - baseline_activity
        
        # Generate alpha signal
        if target_type == "parking_lot":
            # High parking = high retail activity = bullish for retail
            alpha_signal = (activity_level - 0.5) * 2  # Scale to [-1, 1]
            affected_sectors = ["XRT", "XLY"]  # Retail ETFs
        elif target_type == "factory":
            # Lights on = production = bullish for manufacturing
            alpha_signal = (activity_level - 0.5) * 2
            affected_sectors = ["XLI", "IYT"]  # Industrial ETFs
        elif target_type == "port":
            # High activity = trade flow = mixed signal
            alpha_signal = (activity_level - 0.5) * 1.5
            affected_sectors = ["IYT", "XLI"]
        else:
            alpha_signal = 0.0
            affected_sectors = []
        
        return {
            'image_path': image_path,
            'target_type': target_type,
            'activity_level': activity_level,
            'change_from_baseline': change_from_baseline,
            'alpha_signal': alpha_signal,
            'affected_sectors': affected_sectors,
            'visual_signal': signal.to_dict(),
            'confidence': signal.confidence
        }
    
    def detect_chart_patterns(self, chart_image_path: str) -> Dict[str, Any]:
        """
        Detect technical chart patterns in an image.
        
        Patterns detected:
        - Head and shoulders
        - Double top/bottom
        - Triangle (ascending, descending, symmetric)
        - Cup and handle
        - Breakout patterns
        
        Args:
            chart_image_path: Path to chart image
            
        Returns:
            Detected patterns with confidence scores
        """
        signal = self.analyze(chart_image_path)
        
        # Extract pattern-specific information
        patterns_detected = []
        
        # Check which chart patterns match
        chart_categories = [
            cat for cat in self.FINANCIAL_CATEGORIES
            if 'pattern' in cat.lower() or 'chart' in cat.lower()
        ]
        
        for category in chart_categories:
            similarity = float(np.dot(
                signal.embedding,
                self.category_embeddings[category]
            ))
            if similarity > 0.3:  # Threshold
                patterns_detected.append({
                    'pattern': category,
                    'confidence': (similarity + 1) / 2,
                    'sentiment': self.CATEGORY_SENTIMENT.get(category, (VisualSentiment.NEUTRAL, 0.0))[1]
                })
        
        # Sort by confidence
        patterns_detected.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'chart_image': chart_image_path,
            'patterns_detected': patterns_detected[:3],  # Top 3
            'primary_pattern': patterns_detected[0] if patterns_detected else None,
            'overall_sentiment': signal.sentiment.value,
            'sentiment_score': signal.sentiment_score,
            'confidence': signal.confidence
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        if not self.cache:
            return {'total_processed': 0}
        
        signals = list(self.cache.values())
        
        category_counts = {}
        for cat in VisualCategory:
            category_counts[cat.value] = sum(1 for s in signals if s.category == cat)
        
        sentiment_counts = {}
        for sent in VisualSentiment:
            sentiment_counts[sent.value] = sum(1 for s in signals if s.sentiment == sent)
        
        return {
            'total_processed': len(signals),
            'category_distribution': category_counts,
            'sentiment_distribution': sentiment_counts,
            'avg_confidence': np.mean([s.confidence for s in signals]),
            'avg_processing_time_ms': np.mean([s.processing_time_ms for s in signals])
        }
