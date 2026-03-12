"""
Tier 6: Macroeconomic & Intermarket Analysis
Analyzes macro context and cross-market correlations
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from trading_bot.brain.tier_structure import (
    TierBase, MarketStateVector, OrderFlowIntelligence, 
    MarketGeometryModel, RegimeContextVector, SentimentVector, MacroContext
)

logger = logging.getLogger(__name__)


@dataclass
class MacroFactor:
    """Macroeconomic factor"""
    name: str
    value: float
    impact: float  # -1.0 to 1.0
    confidence: float
    trend: str  # increasing, decreasing, stable
    metadata: Dict[str, Any]


class InterestRateAnalysis:
    """Interest rate differential analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def analyze(self, rates_data: Dict[str, float], 
                base_currency: str, quote_currency: str) -> Dict[str, Any]:
        """Analyze interest rate differentials"""
        if not rates_data or base_currency not in rates_data or quote_currency not in rates_data:
            try:
                return {
                    'differential': 0.0,
                    'trend': 'stable',
                    'carry_score': 0.0
                }

                # Calculate rate differential
                base_rate = rates_data[base_currency]
                quote_rate = rates_data[quote_currency]
                differential = base_rate - quote_rate

                # Calculate carry score (-1 to 1)
                # Positive means favorable for long positions
                carry_score = np.tanh(differential)  # Squash to -1 to 1

                # Determine trend
                if 'historical' in rates_data:
                    hist_diff = rates_data['historical'].get(base_currency, 0) - rates_data['historical'].get(quote_currency, 0)
                    if differential > hist_diff + 0.001:
                        trend = 'increasing'
                    elif differential < hist_diff - 0.001:
                        trend = 'decreasing'
                    else:
                        trend = 'stable'
                else:
                    trend = 'stable'

                return {
                    'differential': differential,
                    'base_rate': base_rate,
                    'quote_rate': quote_rate,
                    'trend': trend,
                    'carry_score': carry_score
                }

            except Exception as e:
                logger.error(f"Error analyzing interest rates: {str(e)}")
                return {
                    'differential': 0.0,
                    'trend': 'stable',
                    'carry_score': 0.0
                }


class YieldCurveAnalysis:
    """Yield curve analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def analyze(self, yield_data: Dict[str, float]) -> Dict[str, Any]:
        """Analyze yield curve"""
        if not yield_data or '2Y' not in yield_data or '10Y' not in yield_data:
            try:
                return {
                    'spread': 0.0,
                    'state': 'normal',
                    'recession_probability': 0.0
                }

                # Calculate 2Y-10Y spread
                spread = yield_data['10Y'] - yield_data['2Y']

                # Determine curve state
                if spread > 0.5:
                    state = 'steep'
                elif spread > 0:
                    state = 'normal'
                elif spread > -0.5:
                    state = 'flat'
                else:
                    state = 'inverted'

                # Calculate recession probability
                # Based on historical evidence that yield curve inversion
                # often precedes recessions
                if spread < 0:
                    recession_prob = min(-spread, 1.0)
                else:
                    recession_prob = 0.0

                return {
                    'spread': spread,
                    'state': state,
                    'recession_probability': recession_prob,
                    'steepness': abs(spread),
                    'inversion_depth': max(-spread, 0.0)
                }

            except Exception as e:
                logger.error(f"Error analyzing yield curve: {str(e)}")
                return {
                    'spread': 0.0,
                    'state': 'normal',
                    'recession_probability': 0.0
                }


class CorrelationAnalysis:
    """Cross-market correlation analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.lookback = self.config.get('lookback', 20)
    
    def analyze(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze cross-market correlations"""
        if not market_data:
            return {
            'correlations': {},
            'strength': 0.0,
            'regime': 'neutral'
            }

            # Calculate returns
            returns = {}
        try:
            for market, data in market_data.items():
                if len(data) >= self.lookback:
                    returns[market] = data['close'].pct_change()
            
            # Calculate correlation matrix
            corr_matrix = pd.DataFrame(returns).corr()
            
            # Calculate average correlation strength
            corr_strength = abs(corr_matrix.values[np.triu_indices_from(corr_matrix, k=1)]).mean()
            
            # Determine correlation regime
            if corr_strength > 0.7:
                regime = 'high_correlation'
            elif corr_strength < 0.3:
                regime = 'low_correlation'
            else:
                regime = 'normal'
            
            # Get specific correlations
            correlations = {}
            for m1 in returns:
                for m2 in returns:
                    if m1 < m2:  # Avoid duplicates
                        corr = corr_matrix.loc[m1, m2]
                        correlations[f"{m1}-{m2}"] = corr
            
            return {
                'correlations': correlations,
                'strength': corr_strength,
                'regime': regime,
                'matrix': corr_matrix.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing correlations: {str(e)}")
            return {
                'correlations': {},
                'strength': 0.0,
                'regime': 'neutral'
            }


class RiskSentimentAnalysis:
    """Global risk sentiment analysis"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def analyze(self, market_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Analyze global risk sentiment"""
        if not market_data or 'VIX' not in market_data:
            try:
                return {
                    'sentiment': 'neutral',
                    'risk_appetite': 0.5,
                    'regime': 'normal'
                }

                # Get VIX data
                vix = market_data['VIX']['close']

                # Calculate VIX percentile
                vix_percentile = pd.Series(vix).rank(pct=True).iloc[-1]

                # Calculate risk appetite (0 to 1)
                # High VIX = Low risk appetite
                risk_appetite = 1.0 - vix_percentile

                # Determine sentiment
                if vix.iloc[-1] > 30:
                    sentiment = 'risk_off'
                elif vix.iloc[-1] < 15:
                    sentiment = 'risk_on'
                else:
                    sentiment = 'neutral'

                # Check for VIX divergence
                if 'SPX' in market_data:
                    spx = market_data['SPX']['close']
                    vix_trend = vix.diff(5).iloc[-1]
                    spx_trend = spx.diff(5).iloc[-1]

                    if vix_trend > 0 and spx_trend > 0:
                        divergence = 'bearish'
                    elif vix_trend < 0 and spx_trend < 0:
                        divergence = 'bullish'
                    else:
                        divergence = 'none'
                else:
                    divergence = 'none'

                return {
                    'sentiment': sentiment,
                    'risk_appetite': risk_appetite,
                    'vix_level': vix.iloc[-1],
                    'vix_percentile': vix_percentile,
                    'divergence': divergence,
                    'regime': 'high_vol' if vix.iloc[-1] > 25 else 'low_vol'
                }

            except Exception as e:
                logger.error(f"Error analyzing risk sentiment: {str(e)}")
                return {
                    'sentiment': 'neutral',
                    'risk_appetite': 0.5,
                    'regime': 'normal'
                }


class Tier6MacroAnalysis(TierBase):
    """
    Tier 6: Macroeconomic & Intermarket Analysis
    
    Analyzes macro context and cross-market relationships:
    - Interest rate differentials
    - Yield curve analysis
    - Cross-market correlations
    - Global risk sentiment
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 6: Macro Analysis", config)
        self.rates_analysis = None
        self.yield_analysis = None
        self.correlation_analysis = None
        self.risk_analysis = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.rates_analysis = InterestRateAnalysis(self.config.get('rates', {}))
        self.yield_analysis = YieldCurveAnalysis(self.config.get('yields', {}))
        self.correlation_analysis = CorrelationAnalysis(self.config.get('correlation', {}))
        self.risk_analysis = RiskSentimentAnalysis(self.config.get('risk', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[SentimentVector] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> MacroContext:
        """
        Process market data and analyze macro context
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 5 (SentimentVector)
            additional_inputs: Dictionary with rates, yields, and market data
            
        Returns:
            MacroContext with macro analysis
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 6")
            return None
        try:
        
            # Get additional data
            rates_data = additional_inputs.get('rates_data', {})
            yield_data = additional_inputs.get('yield_data', {})
            market_data_dict = additional_inputs.get('market_data', {})
            
            # Get currency pair
            base_currency = additional_inputs.get('base_currency', 'USD')
            quote_currency = additional_inputs.get('quote_currency', 'EUR')
            
            # Analyze interest rates
            rates = self.rates_analysis.analyze(rates_data, base_currency, quote_currency)
            
            # Analyze yield curve
            yields = self.yield_analysis.analyze(yield_data)
            
            # Analyze correlations
            correlations = self.correlation_analysis.analyze(market_data_dict)
            
            # Analyze risk sentiment
            risk = self.risk_analysis.analyze(market_data_dict)
            
            # Calculate interest rate differential
            interest_rate_differential = rates['differential']
            
            # Get yield curve slope
            yield_curve_slope = yields['spread']
            
            # Get correlation strength for relevant pairs
            correlation_strength = {
                pair: corr for pair, corr in correlations['correlations'].items()
                if base_currency in pair or quote_currency in pair
            }
            
            # Get risk sentiment
            risk_sentiment = risk['sentiment']
            
            # Determine capital flow direction
            if rates['carry_score'] > 0.2 and risk['risk_appetite'] > 0.6:
                flow_direction = 'into_' + base_currency
            elif rates['carry_score'] < -0.2 and risk['risk_appetite'] > 0.6:
                flow_direction = 'into_' + quote_currency
            else:
                flow_direction = 'neutral'
            
            # Calculate signal value (-1 to 1)
            # Combine carry, yield curve, and risk sentiment
            signal_components = [
                rates['carry_score'],
                -yields['recession_probability'],  # Negative because higher probability is bearish
                (2 * risk['risk_appetite'] - 1)  # Convert 0-1 to -1 to 1
            ]
            
            signal_value = np.mean(signal_components)
            
            # Calculate confidence (0 to 1)
            # Higher when multiple factors align
            confidence_factors = [
                1.0 - yields['recession_probability'],
                risk['risk_appetite'] if signal_value > 0 else (1 - risk['risk_appetite']),
                abs(rates['carry_score'])
            ]
            
            confidence = np.mean(confidence_factors)
            
            # Create metadata
            metadata = {
                'rates': rates,
                'yields': yields,
                'correlations': correlations,
                'risk': risk
            }
            
            # Create macro context
            macro = MacroContext(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                interest_rate_differential=interest_rate_differential,
                yield_curve_slope=yield_curve_slope,
                correlation_strength=correlation_strength,
                risk_sentiment=risk_sentiment,
                capital_flow_direction=flow_direction,
                metadata=metadata
            )
            
            self.last_output = macro
            return macro
            
        except Exception as e:
            logger.error(f"Error processing Tier 6: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Create sample additional inputs
    additional_inputs = {
        'rates_data': {
            'USD': 5.25,
            'EUR': 4.50,
            'historical': {'USD': 5.0, 'EUR': 4.0}
        },
        'yield_data': {
            '2Y': 4.89,
            '10Y': 4.62
        },
        'market_data': {
            'VIX': pd.DataFrame({
                'close': np.random.uniform(15, 25, 250)
            }, index=dates),
            'SPX': pd.DataFrame({
                'close': np.random.randn(250).cumsum() + 4000
            }, index=dates)
        },
        'base_currency': 'USD',
        'quote_currency': 'EUR'
    }
    
    # Initialize and process
    tier6 = Tier6MacroAnalysis()
    tier6.initialize()
    result = tier6.process(df, additional_inputs=additional_inputs)
    
    # Print results
    logger.info("\n=== Tier 6: Macro Analysis Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Rate Differential: {result.interest_rate_differential:.2f}%")
    logger.info(f"Yield Curve Slope: {result.yield_curve_slope:.2f}%")
    logger.info(f"Risk Sentiment: {result.risk_sentiment}")
    logger.info(f"Capital Flow: {result.capital_flow_direction}")
    logger.info("\nCorrelation Strength:")
    for pair, strength in result.correlation_strength.items():
        logger.info(f"- {pair}: {strength:.2f}")


# Alias for backward compatibility - tier_structure.py imports Tier6MacroContext
Tier6MacroContext = Tier6MacroAnalysis
