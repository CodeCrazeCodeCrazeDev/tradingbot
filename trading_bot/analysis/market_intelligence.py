"""
Market Intelligence System
Advanced market analysis and intelligence gathering.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

try:
    from trading_bot.market_intelligence.technical_analysis import TechnicalAnalyzer
except ImportError:
    TechnicalAnalyzer = None

try:
    from trading_bot.analysis.sentiment_analysis import SentimentAnalyzer
except ImportError:
    SentimentAnalyzer = None

try:
    from trading_bot.analysis.alternative_data import AlternativeDataIntegrator
except ImportError:
    AlternativeDataIntegrator = None

try:
    from trading_bot.analysis.market_regime import MarketRegimeDetector
except ImportError:
    MarketRegimeDetector = None

try:
    from trading_bot.analysis.order_flow import OrderFlowAnalyzer
except ImportError:
    OrderFlowAnalyzer = None

try:
    from trading_bot.analysis.liquidity_analysis import LiquidityAnalyzer
except ImportError:
    LiquidityAnalyzer = None

try:
    from trading_bot.analysis.anomaly_detection import AdvancedAnomalyDetector
except ImportError:
    AdvancedAnomalyDetector = None

logger = logging.getLogger(__name__)


@dataclass
class MarketInsight:
    """Market insight with analysis and confidence."""
    timestamp: datetime
    insight_type: str
    symbol: str
    timeframe: str
    value: Any
    confidence: float
    source: str
    metadata: Dict[str, Any]


class MarketIntelligenceSystem:
    """
    Comprehensive market intelligence system.
    
    Features:
    - Multi-source data integration
    - Real-time analysis
    - Machine learning insights
    - Adaptive intelligence
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize market intelligence system."""
        self.config = config or {}
        
        # Initialize analyzers (with None checks)
        self.technical_analyzer = TechnicalAnalyzer(self.config.get('technical_config')) if TechnicalAnalyzer else None
        self.sentiment_analyzer = SentimentAnalyzer(self.config.get('sentiment_config')) if SentimentAnalyzer else None
        self.alternative_data = AlternativeDataIntegrator(self.config.get('alternative_data_config')) if AlternativeDataIntegrator else None
        self.regime_detector = MarketRegimeDetector(self.config.get('regime_config')) if MarketRegimeDetector else None
        self.order_flow_analyzer = OrderFlowAnalyzer(self.config.get('order_flow_config')) if OrderFlowAnalyzer else None
        self.liquidity_analyzer = LiquidityAnalyzer(self.config.get('liquidity_config')) if LiquidityAnalyzer else None
        self.anomaly_detector = AdvancedAnomalyDetector(self.config.get('anomaly_config')) if AdvancedAnomalyDetector else None
        
        # Analysis state
        self.insights: List[MarketInsight] = []
        self.current_regime = None
        self.anomaly_signals = []
        
        # Thread pool for parallel analysis
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info("Market Intelligence System initialized")
    
    async def analyze_market(self, 
                           market_data: pd.DataFrame,
                           symbol: str,
                           timeframe: str) -> Dict[str, Any]:
        """
        Perform comprehensive market analysis.
        
        Args:
            market_data: OHLCV market data
            symbol: Trading symbol
            timeframe: Analysis timeframe
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Run analyses in parallel
            analysis_tasks = [
                self._run_technical_analysis(market_data, symbol, timeframe),
                self._run_sentiment_analysis(symbol),
                self._run_alternative_analysis(symbol),
                self._run_regime_analysis(market_data, timeframe),
                self._run_order_flow_analysis(market_data, symbol),
                self._run_liquidity_analysis(market_data, symbol),
                self._run_anomaly_detection(market_data)
            ]
            
            # Gather results
            results = await asyncio.gather(*analysis_tasks)
            
            # Combine results
            analysis = {
                'technical': results[0],
                'sentiment': results[1],
                'alternative': results[2],
                'regime': results[3],
                'order_flow': results[4],
                'liquidity': results[5],
                'anomalies': results[6]
            }
            
            # Generate insights
            insights = self._generate_insights(analysis, symbol, timeframe)
            self.insights.extend(insights)
            
            # Limit insight history
            if len(self.insights) > 1000:
                self.insights = self.insights[-1000:]
            
            # Update state
            self.current_regime = analysis['regime'].get('current_regime')
            self.anomaly_signals = analysis['anomalies']
            
            return {
                'analysis': analysis,
                'insights': insights,
                'regime': self.current_regime,
                'anomalies': self.anomaly_signals
            }
            
        except Exception as e:
            logger.error(f"Error in market analysis: {e}")
            return {}
    
    async def _run_technical_analysis(self, data: pd.DataFrame,
                                   symbol: str, timeframe: str) -> Dict[str, Any]:
        """Run technical analysis."""
        try:
            return await self.technical_analyzer.analyze(data, symbol, timeframe)
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
            return {}
    
    async def _run_sentiment_analysis(self, symbol: str) -> Dict[str, Any]:
        """Run sentiment analysis."""
        try:
            return await self.sentiment_analyzer.analyze_sentiment(symbol)
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {}
    
    async def _run_alternative_analysis(self, symbol: str) -> Dict[str, Any]:
        """Run alternative data analysis."""
        try:
            return await self.alternative_data.analyze(symbol)
        except Exception as e:
            logger.error(f"Alternative data analysis error: {e}")
            return {}
    
    async def _run_regime_analysis(self, data: pd.DataFrame,
                                timeframe: str) -> Dict[str, Any]:
        """Run regime analysis."""
        try:
            return await self.regime_detector.detect_regime(data, timeframe)
        except Exception as e:
            logger.error(f"Regime analysis error: {e}")
            return {}
    
    async def _run_order_flow_analysis(self, data: pd.DataFrame,
                                    symbol: str) -> Dict[str, Any]:
        """Run order flow analysis."""
        try:
            return await self.order_flow_analyzer.analyze_flow(data, symbol)
        except Exception as e:
            logger.error(f"Order flow analysis error: {e}")
            return {}
    
    async def _run_liquidity_analysis(self, data: pd.DataFrame,
                                   symbol: str) -> Dict[str, Any]:
        """Run liquidity analysis."""
        try:
            return await self.liquidity_analyzer.analyze_liquidity(data, symbol)
        except Exception as e:
            logger.error(f"Liquidity analysis error: {e}")
            return {}
    
    async def _run_anomaly_detection(self, data: pd.DataFrame) -> List[Dict]:
        """Run anomaly detection."""
        try:
            return self.anomaly_detector.detect_anomalies(data)
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return []
    
    def _generate_insights(self, analysis: Dict[str, Any],
                        symbol: str, timeframe: str) -> List[MarketInsight]:
        """Generate market insights from analysis results."""
        insights = []
        current_time = datetime.now()
        
        # Technical insights
        if technical := analysis.get('technical'):
            for signal_type, signal in technical.items():
                if isinstance(signal, dict) and signal.get('value') is not None:
                    insights.append(MarketInsight(
                        timestamp=current_time,
                        insight_type='technical',
                        symbol=symbol,
                        timeframe=timeframe,
                        value=signal['value'],
                        confidence=signal.get('confidence', 0.5),
                        source=signal_type,
                        metadata=signal
                    ))
        
        # Sentiment insights
        if sentiment := analysis.get('sentiment'):
            insights.append(MarketInsight(
                timestamp=current_time,
                insight_type='sentiment',
                symbol=symbol,
                timeframe=timeframe,
                value=sentiment.get('sentiment', 'neutral'),
                confidence=sentiment.get('confidence', 0.5),
                source='sentiment_analysis',
                metadata=sentiment
            ))
        
        # Alternative data insights
        if alternative := analysis.get('alternative'):
            for source, data in alternative.items():
                if isinstance(data, dict) and data.get('signal'):
                    insights.append(MarketInsight(
                        timestamp=current_time,
                        insight_type='alternative',
                        symbol=symbol,
                        timeframe=timeframe,
                        value=data['signal'],
                        confidence=data.get('confidence', 0.5),
                        source=source,
                        metadata=data
                    ))
        
        # Regime insights
        if regime := analysis.get('regime'):
            insights.append(MarketInsight(
                timestamp=current_time,
                insight_type='regime',
                symbol=symbol,
                timeframe=timeframe,
                value=regime.get('current_regime', 'unknown'),
                confidence=regime.get('regime_probability', 0.5),
                source='regime_detection',
                metadata=regime
            ))
        
        # Order flow insights
        if order_flow := analysis.get('order_flow'):
            for signal_type, signal in order_flow.items():
                if isinstance(signal, dict) and signal.get('value'):
                    insights.append(MarketInsight(
                        timestamp=current_time,
                        insight_type='order_flow',
                        symbol=symbol,
                        timeframe=timeframe,
                        value=signal['value'],
                        confidence=signal.get('confidence', 0.5),
                        source=signal_type,
                        metadata=signal
                    ))
        
        # Liquidity insights
        if liquidity := analysis.get('liquidity'):
            for zone_type, zones in liquidity.items():
                if isinstance(zones, list):
                    for zone in zones:
                        insights.append(MarketInsight(
                            timestamp=current_time,
                            insight_type='liquidity',
                            symbol=symbol,
                            timeframe=timeframe,
                            value=zone.get('price', 0),
                            confidence=zone.get('strength', 0.5),
                            source=zone_type,
                            metadata=zone
                        ))
        
        # Anomaly insights
        if anomalies := analysis.get('anomalies'):
            for anomaly in anomalies:
                insights.append(MarketInsight(
                    timestamp=current_time,
                    insight_type='anomaly',
                    symbol=symbol,
                    timeframe=timeframe,
                    value=anomaly.get('type', 'unknown'),
                    confidence=anomaly.get('confidence', 0.5),
                    source='anomaly_detection',
                    metadata=anomaly
                ))
        
        return insights
    
    def get_active_insights(self, max_age_minutes: int = 60) -> List[MarketInsight]:
        """Get currently active insights."""
        current_time = datetime.now()
        active_insights = []
        
        for insight in self.insights:
            age_minutes = (current_time - insight.timestamp).total_seconds() / 60
            if age_minutes <= max_age_minutes:
                active_insights.append(insight)
        
        return active_insights
    
    def save_state(self, filepath: str):
        """Save system state to file."""
        try:
            state = {
                'insights': [insight.__dict__ for insight in self.insights],
                'current_regime': self.current_regime,
                'anomaly_signals': self.anomaly_signals,
                'config': self.config
            }
            
            with open(filepath, 'w') as f:
                json.dump(state, f, default=str, indent=2)
            
            logger.info(f"System state saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving system state: {e}")
    
    def load_state(self, filepath: str):
        """Load system state from file."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # Reconstruct insights
            self.insights = [
                MarketInsight(**insight) for insight in state['insights']
            ]
            self.current_regime = state['current_regime']
            self.anomaly_signals = state['anomaly_signals']
            self.config = state['config']
            
            logger.info(f"System state loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading system state: {e}")
    
    def get_market_summary(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market summary."""
        active_insights = self.get_active_insights()
        symbol_insights = [i for i in active_insights if i.symbol == symbol]
        
        summary = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'regime': self.current_regime,
            'anomalies': len(self.anomaly_signals),
            'insights': {
                'technical': [],
                'sentiment': [],
                'alternative': [],
                'order_flow': [],
                'liquidity': [],
                'anomaly': []
            }
        }
        
        # Group insights by type
        for insight in symbol_insights:
            if insight.insight_type in summary['insights']:
                summary['insights'][insight.insight_type].append({
                    'value': insight.value,
                    'confidence': insight.confidence,
                    'source': insight.source,
                    'metadata': insight.metadata
                })
        
        return summary
