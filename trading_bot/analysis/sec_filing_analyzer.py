"""
SEC Filing Analyzer
Advanced analysis of SEC filings for alpha generation
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
try:
    import requests
except ImportError:
    requests = None
import json
import re
from datetime import datetime, timedelta
import logging
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False
    textstat = None
from collections import Counter

# Initialize logging
logger = logging.getLogger(__name__)

# Try to download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)


@dataclass
class FilingSignal:
    """Signal generated from SEC filing analysis"""
    ticker: str
    filing_type: str  # 10-K, 10-Q, 8-K, etc.
    filing_date: datetime
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    key_metrics: Dict[str, Any]
    key_changes: List[str]
    sentiment_score: float
    risk_factors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'ticker': self.ticker,
            'filing_type': self.filing_type,
            'filing_date': self.filing_date.isoformat(),
            'signal_type': self.signal_type,
            'strength': self.strength,
            'confidence': self.confidence,
            'key_metrics': self.key_metrics,
            'key_changes': self.key_changes,
            'sentiment_score': self.sentiment_score,
            'risk_factors': self.risk_factors
        }


class SECFilingAnalyzer:
    """
    Advanced analysis of SEC filings for trading signals
    
    Features:
    - Sentiment analysis of MD&A sections
    - Year-over-year financial metric comparison
    - Risk factor analysis and change detection
    - Management language complexity analysis
    - Insider transaction correlation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # SEC API configuration
        self.sec_api_key = self.config.get('sec_api_key', '')
        self.sec_base_url = self.config.get('sec_base_url', 'https://www.sec.gov/Archives/')
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Financial metrics to track
        self.key_metrics = [
            'revenue', 'net_income', 'eps', 'operating_income',
            'gross_margin', 'operating_margin', 'cash', 'debt',
            'assets', 'liabilities', 'equity', 'capex',
            'free_cash_flow', 'inventory', 'accounts_receivable'
        ]
        
        # Risk factor keywords
        self.risk_keywords = [
            'litigation', 'lawsuit', 'regulatory', 'investigation',
            'cybersecurity', 'breach', 'competition', 'disruption',
            'supply chain', 'inflation', 'recession', 'pandemic',
            'climate', 'environmental', 'labor', 'shortage'
        ]
        
        # Positive and negative word lists
        self.positive_words = set([
            'growth', 'increase', 'improved', 'positive', 'strong',
            'opportunity', 'exceed', 'success', 'favorable', 'gain',
            'profitable', 'advantage', 'efficient', 'innovative'
        ])
        
        self.negative_words = set([
            'decline', 'decrease', 'loss', 'negative', 'weak',
            'challenge', 'below', 'fail', 'adverse', 'risk',
            'uncertain', 'difficult', 'delay', 'litigation'
        ])
        
        # Filing cache
        self.filing_cache = {}
        
        logger.info("SEC Filing Analyzer initialized")
    
    def analyze_filing(self, ticker: str, filing_type: str, filing_url: str) -> Optional[FilingSignal]:
        """
        Analyze an SEC filing to generate trading signals
        
        Args:
            ticker: Company ticker symbol
            filing_type: Type of filing (10-K, 10-Q, 8-K)
            filing_url: URL to the filing
            
        Returns:
            Filing signal or None if analysis fails
        """
        try:
            # Get filing content
            filing_content = self._get_filing_content(filing_url)
            if not filing_content:
                return None
            
            # Parse filing date
            filing_date = self._extract_filing_date(filing_content)
            
            # Extract sections
            sections = self._extract_sections(filing_content, filing_type)
            
            # Extract financial metrics
            metrics = self._extract_financial_metrics(sections, filing_type)
            
            # Calculate year-over-year changes
            changes = self._calculate_changes(ticker, filing_type, metrics)
            
            # Analyze sentiment
            sentiment_score = self._analyze_sentiment(sections)
            
            # Extract risk factors
            risk_factors = self._extract_risk_factors(sections)
            
            # Analyze management discussion complexity
            complexity = self._analyze_complexity(sections.get('mda', ''))
            
            # Generate signal
            signal = self._generate_signal(
                ticker, filing_type, filing_date, metrics, 
                changes, sentiment_score, risk_factors, complexity
            )
            
            # Cache metrics for future comparison
            self._cache_metrics(ticker, filing_type, filing_date, metrics)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing {filing_type} for {ticker}: {e}")
            return None
    
    def _get_filing_content(self, filing_url: str) -> str:
        """Get filing content from URL"""
        try:
            headers = {'User-Agent': 'Financial Analysis Bot'}
            response = requests.get(filing_url, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to get filing: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error fetching filing: {e}")
            return ""
    
    def _extract_filing_date(self, content: str) -> datetime:
        """Extract filing date from content"""
        # Look for CONFORMED PERIOD OF REPORT pattern
        match = re.search(r'CONFORMED PERIOD OF REPORT:\s*(\d{8})', content)
        if match:
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y%m%d')
        
        # Look for FILED AS OF DATE pattern
        match = re.search(r'FILED AS OF DATE:\s*(\d{8})', content)
        if match:
            date_str = match.group(1)
            return datetime.strptime(date_str, '%Y%m%d')
        
        # Default to current date if not found
        return datetime.now()
    
    def _extract_sections(self, content: str, filing_type: str) -> Dict[str, str]:
        """Extract relevant sections from filing"""
        sections = {}
        
        # Extract Management's Discussion and Analysis
        mda_pattern = re.compile(
            r"item\s*[7\.]*\s*management\'?s?\s*discussion\s*and\s*analysis.*?item\s*[7A\.]*",
            re.IGNORECASE | re.DOTALL
        )
        mda_match = mda_pattern.search(content)
        if mda_match:
            sections['mda'] = mda_match.group(0)
        
        # Extract Risk Factors
        risk_pattern = re.compile(
            r"item\s*[1A\.]*\s*risk\s*factors.*?item\s*[1B\.]*",
            re.IGNORECASE | re.DOTALL
        )
        risk_match = risk_pattern.search(content)
        if risk_match:
            sections['risk_factors'] = risk_match.group(0)
        
        # Extract Financial Statements
        fin_pattern = re.compile(
            r"item\s*[8\.]*\s*financial\s*statements.*?item\s*[9\.]*",
            re.IGNORECASE | re.DOTALL
        )
        fin_match = fin_pattern.search(content)
        if fin_match:
            sections['financials'] = fin_match.group(0)
        
        return sections
    
    def _extract_financial_metrics(self, sections: Dict[str, str], filing_type: str) -> Dict[str, float]:
        """Extract financial metrics from filing sections"""
        metrics = {}
        
        # This is a simplified implementation
        # In a real system, this would use more sophisticated parsing
        
        financials = sections.get('financials', '')
        mda = sections.get('mda', '')
        
        # Look for revenue
        revenue_pattern = re.compile(r'(revenue|net\s+sales)\s*[of]*\s*[\$]?(\d+[\.\,]?\d*)\s*(billion|million|thousand|[mb])?', re.IGNORECASE)
        revenue_match = revenue_pattern.search(mda) or revenue_pattern.search(financials)
        if revenue_match:
            value = self._parse_numeric_value(revenue_match.group(2), revenue_match.group(3))
            metrics['revenue'] = value
        
        # Look for net income
        income_pattern = re.compile(r'(net\s+income|profit)\s*[of]*\s*[\$]?(\d+[\.\,]?\d*)\s*(billion|million|thousand|[mb])?', re.IGNORECASE)
        income_match = income_pattern.search(mda) or income_pattern.search(financials)
        if income_match:
            value = self._parse_numeric_value(income_match.group(2), income_match.group(3))
            metrics['net_income'] = value
        
        # Look for EPS
        eps_pattern = re.compile(r'(earnings\s+per\s+share|eps)\s*[of]*\s*[\$]?(\d+[\.\,]?\d*)', re.IGNORECASE)
        eps_match = eps_pattern.search(mda) or eps_pattern.search(financials)
        if eps_match:
            metrics['eps'] = float(eps_match.group(2).replace(',', ''))
        
        # Add more metric extraction as needed
        
        return metrics
    
    def _parse_numeric_value(self, value_str: str, unit: Optional[str] = None) -> float:
        """Parse numeric value with unit"""
        value = float(value_str.replace(',', ''))
        
        if unit:
            unit = unit.lower()
            if 'billion' in unit or 'b' in unit:
                value *= 1_000_000_000
            elif 'million' in unit or 'm' in unit:
                value *= 1_000_000
            elif 'thousand' in unit or 'k' in unit:
                value *= 1_000
        
        return value
    
    def _calculate_changes(self, ticker: str, filing_type: str, 
                         current_metrics: Dict[str, float]) -> List[str]:
        """Calculate year-over-year changes in metrics"""
        changes = []
        
        # Get previous metrics from cache
        prev_metrics = self._get_previous_metrics(ticker, filing_type)
        if not prev_metrics:
            return changes
        
        # Calculate changes for each metric
        for metric, current_value in current_metrics.items():
            if metric in prev_metrics:
                prev_value = prev_metrics[metric]
                if prev_value != 0:
                    pct_change = (current_value - prev_value) / abs(prev_value) * 100
                    
                    # Format change description
                    if abs(pct_change) >= 10:
                        direction = "increased" if pct_change > 0 else "decreased"
                        changes.append(f"{metric.replace('_', ' ').title()} {direction} by {abs(pct_change):.1f}%")
        
        return changes
    
    def _get_previous_metrics(self, ticker: str, filing_type: str) -> Dict[str, float]:
        """Get previous metrics from cache"""
        cache_key = f"{ticker}_{filing_type}"
        if cache_key in self.filing_cache:
            # Sort by date and get the most recent
            filings = sorted(self.filing_cache[cache_key], key=lambda x: x['date'], reverse=True)
            if filings:
                return filings[0]['metrics']
        return {}
    
    def _cache_metrics(self, ticker: str, filing_type: str, 
                     filing_date: datetime, metrics: Dict[str, float]):
        """Cache metrics for future comparison"""
        cache_key = f"{ticker}_{filing_type}"
        if cache_key not in self.filing_cache:
            self.filing_cache[cache_key] = []
        
        self.filing_cache[cache_key].append({
            'date': filing_date,
            'metrics': metrics
        })
        
        # Keep only last 4 filings
        self.filing_cache[cache_key] = sorted(
            self.filing_cache[cache_key], 
            key=lambda x: x['date'], 
            reverse=True
        )[:4]
    
    def _analyze_sentiment(self, sections: Dict[str, str]) -> float:
        """Analyze sentiment of filing sections"""
        # Focus on Management Discussion and Analysis
        mda = sections.get('mda', '')
        if not mda:
            return 0.0
        
        # Use VADER sentiment analyzer
        sentiment = self.sentiment_analyzer.polarity_scores(mda)
        
        # Return compound score (-1 to 1)
        return sentiment['compound']
    
    def _extract_risk_factors(self, sections: Dict[str, str]) -> List[str]:
        """Extract key risk factors"""
        risk_factors = []
        risk_section = sections.get('risk_factors', '')
        
        if not risk_section:
            return risk_factors
        
        # Look for paragraphs containing risk keywords
        paragraphs = re.split(r'\n\s*\n', risk_section)
        
        for paragraph in paragraphs:
            for keyword in self.risk_keywords:
                if keyword.lower() in paragraph.lower():
                    # Extract a concise version of the risk
                    sentences = nltk.sent_tokenize(paragraph)
                    if sentences:
                        risk = sentences[0]
                        if len(risk) > 100:
                            risk = risk[:97] + '...'
                        risk_factors.append(risk)
                        break
        
        # Return top risks (limit to 5)
        return risk_factors[:5]
    
    def _analyze_complexity(self, text: str) -> Dict[str, float]:
        """Analyze text complexity"""
        if not text:
            return {'readability': 0, 'avg_sentence_length': 0, 'word_complexity': 0}
        
        # Calculate readability score
        readability = textstat.flesch_reading_ease(text)
        
        # Calculate average sentence length
        sentences = nltk.sent_tokenize(text)
        words = nltk.word_tokenize(text)
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        # Calculate word complexity (average word length)
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        
        return {
            'readability': readability,
            'avg_sentence_length': avg_sentence_length,
            'word_complexity': avg_word_length
        }
    
    def _generate_signal(self, ticker: str, filing_type: str, filing_date: datetime,
                       metrics: Dict[str, float], changes: List[str],
                       sentiment_score: float, risk_factors: List[str],
                       complexity: Dict[str, float]) -> FilingSignal:
        """Generate trading signal from analysis"""
        # Calculate signal type and strength
        signal_factors = []
        
        # Factor 1: Sentiment score
        if sentiment_score > 0.2:
            signal_factors.append(('bullish', min(sentiment_score * 2, 1.0)))
        elif sentiment_score < -0.1:
            signal_factors.append(('bearish', min(abs(sentiment_score) * 2, 1.0)))
        
        # Factor 2: Key metric changes
        metric_signal = self._evaluate_metric_changes(changes)
        if metric_signal:
            signal_factors.append(metric_signal)
        
        # Factor 3: Risk factors
        if len(risk_factors) >= 3:
            signal_factors.append(('bearish', 0.6))
        
        # Calculate overall signal
        if not signal_factors:
            signal_type = 'neutral'
            strength = 0.5
            confidence = 0.3
        else:
            # Count signals by type
            bullish_count = sum(1 for s in signal_factors if s[0] == 'bullish')
            bearish_count = sum(1 for s in signal_factors if s[0] == 'bearish')
            
            if bullish_count > bearish_count:
                signal_type = 'bullish'
                # Average strength of bullish signals
                strength = sum(s[1] for s in signal_factors if s[0] == 'bullish') / bullish_count
            elif bearish_count > bullish_count:
                signal_type = 'bearish'
                # Average strength of bearish signals
                strength = sum(s[1] for s in signal_factors if s[0] == 'bearish') / bearish_count
            else:
                signal_type = 'neutral'
                strength = 0.5
            
            # Confidence based on number of factors
            confidence = min(0.3 + 0.2 * len(signal_factors), 0.9)
        
        return FilingSignal(
            ticker=ticker,
            filing_type=filing_type,
            filing_date=filing_date,
            signal_type=signal_type,
            strength=strength,
            confidence=confidence,
            key_metrics=metrics,
            key_changes=changes,
            sentiment_score=sentiment_score,
            risk_factors=risk_factors
        )
    
    def _evaluate_metric_changes(self, changes: List[str]) -> Optional[Tuple[str, float]]:
        """Evaluate metric changes to determine signal"""
        if not changes:
            return None
        
        positive_changes = 0
        negative_changes = 0
        
        for change in changes:
            if 'increased' in change.lower():
                if any(pos in change.lower() for pos in ['revenue', 'income', 'profit', 'margin', 'eps']):
                    positive_changes += 1
                elif any(neg in change.lower() for neg in ['cost', 'expense', 'debt', 'liability']):
                    negative_changes += 1
            elif 'decreased' in change.lower():
                if any(pos in change.lower() for pos in ['revenue', 'income', 'profit', 'margin', 'eps']):
                    negative_changes += 1
                elif any(neg in change.lower() for neg in ['cost', 'expense', 'debt', 'liability']):
                    positive_changes += 1
        
        if positive_changes > negative_changes:
            strength = min(0.5 + 0.1 * (positive_changes - negative_changes), 1.0)
            return ('bullish', strength)
        elif negative_changes > positive_changes:
            strength = min(0.5 + 0.1 * (negative_changes - positive_changes), 1.0)
            return ('bearish', strength)
        
        return None
    
    def get_recent_filings(self, ticker: str, days_back: int = 30) -> List[Dict[str, Any]]:
        """
        Get recent SEC filings for a company
        
        Args:
            ticker: Company ticker symbol
            days_back: Number of days to look back
            
        Returns:
            List of filing information
        """
        # In a real implementation, this would use the SEC EDGAR API
        # This is a simplified placeholder
        
        # Example response structure
        return [
            {
                'ticker': ticker,
                'filing_type': '10-Q',
                'filing_date': (datetime.now() - timedelta(days=5)).isoformat(),
                'filing_url': f'https://www.sec.gov/Archives/edgar/data/123456/{ticker}_10Q_20230331.htm'
            },
            {
                'ticker': ticker,
                'filing_type': '8-K',
                'filing_date': (datetime.now() - timedelta(days=15)).isoformat(),
                'filing_url': f'https://www.sec.gov/Archives/edgar/data/123456/{ticker}_8K_20230315.htm'
            }
        ]
