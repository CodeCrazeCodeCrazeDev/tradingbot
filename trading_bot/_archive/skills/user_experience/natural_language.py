"""
Skill #93: Natural Language Interface
=====================================

Enables natural language queries for trading operations.
"""

from dataclasses import dataclass
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class NLPResult:
    """Natural language processing result."""
    intent: str
    entities: Dict[str, str]
    confidence: float
    response: str
    trading_signal: str


class NaturalLanguageInterface:
    """Natural language interface for trading."""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.intents = {
            'buy': ['buy', 'purchase', 'long', 'acquire'],
            'sell': ['sell', 'short', 'exit', 'close'],
            'status': ['status', 'position', 'portfolio', 'holdings'],
            'analyze': ['analyze', 'check', 'review', 'look at'],
        }
        logger.info("NaturalLanguageInterface initialized")
    
    def process(self, query: str) -> NLPResult:
        """Process natural language query."""
        query_lower = query.lower()
        
        # Detect intent
        detected_intent = "unknown"
        confidence = 0.0
        
        for intent, keywords in self.intents.items():
            for keyword in keywords:
                if keyword in query_lower:
                    detected_intent = intent
                    confidence = 0.8
                    break
        
        # Extract entities (simplified)
        entities = {}
        words = query_lower.split()
        for i, word in enumerate(words):
            if word.isupper() and len(word) <= 5:
                entities['symbol'] = word
            if word.isdigit():
                entities['quantity'] = word
        
        response = self._generate_response(detected_intent, entities)
        
        return NLPResult(
            intent=detected_intent, entities=entities, confidence=confidence,
            response=response, trading_signal=f"NLP: {detected_intent} detected"
        )
    
    def _generate_response(self, intent: str, entities: Dict) -> str:
        """Generate response."""
        if intent == "buy":
            return f"Ready to buy {entities.get('symbol', 'asset')}"
        elif intent == "sell":
            return f"Ready to sell {entities.get('symbol', 'asset')}"
        elif intent == "status":
            return "Fetching portfolio status..."
        return "I didn't understand that. Try: buy, sell, or status"
