"""
7-Dimensional Omniscient Signal Integration
Complete market awareness across all critical dimensions
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import numpy
import pandas

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime classification"""
    GOLDILOCKS = "goldilocks"  # Low inflation, strong growth
    STAGFLATION = "stagflation"  # High inflation, weak growth
    RECESSION = "recession"  # Negative growth
    RECOVERY = "recovery"  # Accelerating growth
    CRISIS = "crisis"  # Systemic stress


class VolatilityRegime(Enum):
    """Volatility state"""
    LOW = "low"  # VIX < 15
    RISING = "rising"  # VIX 15-25, increasing
    HIGH = "high"  # VIX 25-40
    EXTREME = "extreme"  # VIX > 40


class LiquidityPhase(Enum):
    """Liquidity cycle phase"""
    EXPANSION = "expansion"  # Central banks adding liquidity
    PEAK = "peak"  # Maximum liquidity
    CONTRACTION = "contraction"  # QT, rate hikes
    TROUGH = "trough"  # Minimum liquidity


@dataclass
class DimensionalSignal:
    """Signal from a specific dimension"""
    dimension: str
    signal: str  # BULLISH, BEARISH, NEUTRAL
    strength: float  # 0-1
    confidence: float  # 0-1
    evidence: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class OmniscientAnalysis:
    """Complete 7-dimensional market analysis"""
    primary_signal: str
    conviction: float  # 0-100
    dimension_signals: Dict[str, DimensionalSignal]
    confluence_score: float  # 0-100
    risk_level: str
    recommended_action: str
    position_size_multiplier: float
    key_risks: List[str]
    synthesis: str
    timestamp: datetime = field(default_factory=datetime.now)


class MacroeconomicLayer:
    """Dimension 1: Macroeconomic Intelligence"""
    
    def __init__(self):
        try:
            self.fed_policy_prob = {}
            self.economic_data = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """Comprehensive macro analysis"""
        
        try:
            evidence = []
            bullish_factors = 0
            bearish_factors = 0
        
            # Growth/Inflation Matrix
            growth = data.get('gdp_growth', 2.0)
            inflation = data.get('cpi', 3.0)
        
            if growth > 2.5 and inflation < 3.0:
                regime = MarketRegime.GOLDILOCKS
                bullish_factors += 2
                evidence.append("Goldilocks regime: Strong growth, low inflation")
            elif growth < 0:
                regime = MarketRegime.RECESSION
                bearish_factors += 2
                evidence.append("Recession: Negative growth")
            elif inflation > 5.0 and growth < 2.0:
                regime = MarketRegime.STAGFLATION
                bearish_factors += 2
                evidence.append("Stagflation: High inflation, weak growth")
            else:
                regime = MarketRegime.RECOVERY
                bullish_factors += 1
                evidence.append("Recovery phase")
        
            # Fed Policy Analysis
            fed_stance = data.get('fed_stance', 'neutral')
            if fed_stance == 'dovish':
                bullish_factors += 1
                evidence.append("Fed dovish: Supportive policy")
            elif fed_stance == 'hawkish':
                bearish_factors += 1
                evidence.append("Fed hawkish: Tightening policy")
        
            # Liquidity Cycle
            liquidity = data.get('liquidity_phase', LiquidityPhase.EXPANSION)
            if liquidity == LiquidityPhase.EXPANSION:
                bullish_factors += 1
                evidence.append("Liquidity expanding")
            elif liquidity == LiquidityPhase.CONTRACTION:
                bearish_factors += 1
                evidence.append("Liquidity contracting")
        
            # Determine signal
            net_score = bullish_factors - bearish_factors
            if net_score >= 2:
                signal = "BULLISH"
                strength = min(net_score / 4.0, 1.0)
            elif net_score <= -2:
                signal = "BEARISH"
                strength = min(abs(net_score) / 4.0, 1.0)
            else:
                signal = "NEUTRAL"
                strength = 0.5
        
            return DimensionalSignal(
                dimension="Macroeconomic",
                signal=signal,
                strength=strength,
                confidence=0.85,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class MicrostructureLayer:
    """Dimension 2: Market Microstructure Intelligence"""
    
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """Order flow and microstructure analysis"""
        
        try:
            evidence = []
            score = 0.0
        
            # Volume Profile Analysis
            vpoc = data.get('vpoc', 0)
            current_price = data.get('price', 0)
            if current_price > vpoc:
                score += 0.2
                evidence.append(f"Price above VPOC ({vpoc}): Bullish structure")
            else:
                score -= 0.2
                evidence.append(f"Price below VPOC ({vpoc}): Bearish structure")
        
            # Order Book Analysis
            bid_ask_ratio = data.get('bid_ask_ratio', 1.0)
            if bid_ask_ratio > 1.5:
                score += 0.3
                evidence.append(f"Strong bid support (ratio: {bid_ask_ratio:.2f})")
            elif bid_ask_ratio < 0.67:
                score -= 0.3
                evidence.append(f"Heavy ask pressure (ratio: {bid_ask_ratio:.2f})")
        
            # Delta Analysis
            cumulative_delta = data.get('cumulative_delta', 0)
            if cumulative_delta > 0:
                score += 0.25
                evidence.append(f"Positive cumulative delta: Aggressive buying")
            else:
                score -= 0.25
                evidence.append(f"Negative cumulative delta: Aggressive selling")
        
            # Liquidity Analysis
            liquidity_score = data.get('liquidity_score', 0.5)
            if liquidity_score > 0.7:
                evidence.append("High liquidity: Low execution risk")
            elif liquidity_score < 0.3:
                score -= 0.15
                evidence.append("Low liquidity: High execution risk")
        
            # Determine signal
            if score > 0.3:
                signal = "BULLISH"
            elif score < -0.3:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
            return DimensionalSignal(
                dimension="Microstructure",
                signal=signal,
                strength=min(abs(score), 1.0),
                confidence=0.80,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class SentimentLayer:
    """Dimension 3: Sentiment Intelligence"""
    
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """Multi-source sentiment analysis"""
        
        try:
            evidence = []
            sentiment_score = 0.0
        
            # Put/Call Ratio (contrarian)
            put_call = data.get('put_call_ratio', 1.0)
            if put_call > 1.5:
                sentiment_score += 0.3  # Extreme fear = contrarian bullish
                evidence.append(f"Put/Call ratio {put_call:.2f}: Extreme fear (contrarian bullish)")
            elif put_call < 0.5:
                sentiment_score -= 0.3  # Extreme greed = contrarian bearish
                evidence.append(f"Put/Call ratio {put_call:.2f}: Extreme greed (contrarian bearish)")
        
            # VIX Analysis
            vix = data.get('vix', 15)
            if vix > 30:
                sentiment_score += 0.25  # High fear = opportunity
                evidence.append(f"VIX {vix}: High fear, potential bottom")
            elif vix < 12:
                sentiment_score -= 0.25  # Complacency = risk
                evidence.append(f"VIX {vix}: Complacency, potential top")
        
            # Retail vs Institutional Divergence
            retail_sentiment = data.get('retail_sentiment', 0.5)
            institutional_flow = data.get('institutional_flow', 0)
        
            if retail_sentiment > 0.8 and institutional_flow < 0:
                sentiment_score -= 0.3  # Fade retail euphoria
                evidence.append("Retail euphoric while institutions sell: Bearish divergence")
            elif retail_sentiment < 0.2 and institutional_flow > 0:
                sentiment_score += 0.3  # Follow institutions
                evidence.append("Retail fearful while institutions buy: Bullish divergence")
        
            # Social Media Sentiment
            social_sentiment = data.get('social_sentiment', 0.0)
            if abs(social_sentiment) > 0.7:
                # Extreme sentiment is contrarian
                sentiment_score -= social_sentiment * 0.2
                evidence.append(f"Extreme social sentiment ({social_sentiment:.2f}): Contrarian signal")
        
            # Determine signal
            if sentiment_score > 0.3:
                signal = "BULLISH"
            elif sentiment_score < -0.3:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
            return DimensionalSignal(
                dimension="Sentiment",
                signal=signal,
                strength=min(abs(sentiment_score), 1.0),
                confidence=0.70,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class AlternativeDataLayer:
    """Dimension 4: Alternative Data Intelligence"""
    
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """Alternative data analysis"""
        
        try:
            evidence = []
            alt_score = 0.0
        
            # Satellite Imagery
            parking_lot_fullness = data.get('parking_lot_fullness', 0.5)
            if parking_lot_fullness > 0.7:
                alt_score += 0.25
                evidence.append(f"Satellite: High parking lot activity ({parking_lot_fullness:.0%})")
            elif parking_lot_fullness < 0.3:
                alt_score -= 0.25
                evidence.append(f"Satellite: Low parking lot activity ({parking_lot_fullness:.0%})")
        
            # Credit Card Data
            cc_spending = data.get('credit_card_spending_change', 0.0)
            if cc_spending > 0.05:
                alt_score += 0.3
                evidence.append(f"Credit card spending up {cc_spending:.1%}: Strong consumer")
            elif cc_spending < -0.05:
                alt_score -= 0.3
                evidence.append(f"Credit card spending down {cc_spending:.1%}: Weak consumer")
        
            # Web Traffic
            web_traffic_change = data.get('web_traffic_change', 0.0)
            if web_traffic_change > 0.1:
                alt_score += 0.2
                evidence.append(f"Web traffic up {web_traffic_change:.1%}: Strong demand")
        
            # Insider Activity
            insider_buying = data.get('insider_buying_ratio', 1.0)
            if insider_buying > 2.0:
                alt_score += 0.25
                evidence.append(f"Heavy insider buying (ratio: {insider_buying:.1f})")
            elif insider_buying < 0.5:
                alt_score -= 0.25
                evidence.append(f"Heavy insider selling (ratio: {insider_buying:.1f})")
        
            # Determine signal
            if alt_score > 0.3:
                signal = "BULLISH"
            elif alt_score < -0.3:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
            return DimensionalSignal(
                dimension="AlternativeData",
                signal=signal,
                strength=min(abs(alt_score), 1.0),
                confidence=0.75,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class BlockchainLayer:
    """Dimension 5: Blockchain & Crypto Flow Intelligence"""
    
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """On-chain and crypto market analysis"""
        
        try:
            evidence = []
            crypto_score = 0.0
        
            # Stablecoin Flows
            stablecoin_mints = data.get('stablecoin_net_mints', 0)
            if stablecoin_mints > 1e9:  # $1B+ mints
                crypto_score += 0.3
                evidence.append(f"${stablecoin_mints/1e9:.1f}B stablecoin mints: Capital inflow")
            elif stablecoin_mints < -1e9:
                crypto_score -= 0.3
                evidence.append(f"${abs(stablecoin_mints)/1e9:.1f}B stablecoin burns: Capital outflow")
        
            # Exchange Flows
            btc_exchange_flow = data.get('btc_exchange_net_flow', 0)
            if btc_exchange_flow < -1000:  # BTC leaving exchanges
                crypto_score += 0.25
                evidence.append(f"{abs(btc_exchange_flow):.0f} BTC leaving exchanges: Accumulation")
            elif btc_exchange_flow > 1000:
                crypto_score -= 0.25
                evidence.append(f"{btc_exchange_flow:.0f} BTC to exchanges: Distribution")
        
            # Whale Activity
            whale_transactions = data.get('whale_transactions', 0)
            whale_direction = data.get('whale_direction', 'neutral')
            if whale_transactions > 100 and whale_direction == 'accumulation':
                crypto_score += 0.2
                evidence.append(f"{whale_transactions} whale transactions: Accumulation phase")
        
            # DeFi TVL
            defi_tvl_change = data.get('defi_tvl_change', 0.0)
            if defi_tvl_change > 0.1:
                crypto_score += 0.15
                evidence.append(f"DeFi TVL up {defi_tvl_change:.1%}: Risk appetite rising")
            elif defi_tvl_change < -0.1:
                crypto_score -= 0.15
                evidence.append(f"DeFi TVL down {defi_tvl_change:.1%}: Risk appetite falling")
        
            # Cross-Asset Correlation
            btc_correlation = data.get('btc_stock_correlation', 0.5)
            if btc_correlation > 0.8:
                evidence.append(f"High BTC-stock correlation ({btc_correlation:.2f}): Risk-on/off regime")
        
            # Determine signal
            if crypto_score > 0.3:
                signal = "BULLISH"
            elif crypto_score < -0.3:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
            return DimensionalSignal(
                dimension="Blockchain",
                signal=signal,
                strength=min(abs(crypto_score), 1.0),
                confidence=0.65,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class SocialGraphLayer:
    """Dimension 6: Social Graph & Influence Mapping"""
    
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """Social network and influence analysis"""
        
        try:
            evidence = []
            social_score = 0.0
        
            # Key Opinion Leader Sentiment
            kol_sentiment = data.get('kol_sentiment', 0.0)
            kol_confidence = data.get('kol_confidence', 0.5)
        
            weighted_kol = kol_sentiment * kol_confidence
            social_score += weighted_kol * 0.3
        
            if abs(kol_sentiment) > 0.6:
                evidence.append(f"Key influencers {kol_sentiment:+.2f} sentiment (conf: {kol_confidence:.2f})")
        
            # Information Cascade Detection
            cascade_strength = data.get('cascade_strength', 0.0)
            if cascade_strength > 0.7:
                # Strong cascades can be self-fulfilling
                social_score += 0.25
                evidence.append(f"Strong information cascade detected ({cascade_strength:.2f})")
        
            # Echo Chamber vs Genuine Sentiment
            echo_chamber_score = data.get('echo_chamber_score', 0.5)
            if echo_chamber_score > 0.8:
                # High echo chamber = discount sentiment
                social_score *= 0.5
                evidence.append(f"High echo chamber effect ({echo_chamber_score:.2f}): Discount sentiment")
        
            # Bot Detection
            bot_activity = data.get('bot_activity_ratio', 0.1)
            if bot_activity > 0.3:
                social_score *= 0.6
                evidence.append(f"High bot activity ({bot_activity:.1%}): Artificial sentiment")
        
            # Hedge Fund Letter Sentiment
            hf_sentiment = data.get('hedge_fund_letter_sentiment', 0.0)
            if abs(hf_sentiment) > 0.5:
                social_score += hf_sentiment * 0.2
                evidence.append(f"Hedge fund letters {hf_sentiment:+.2f} sentiment")
        
            # Determine signal
            if social_score > 0.3:
                signal = "BULLISH"
            elif social_score < -0.3:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
            return DimensionalSignal(
                dimension="SocialGraph",
                signal=signal,
                strength=min(abs(social_score), 1.0),
                confidence=0.60,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class PsychologicalLayer:
    """Dimension 7: Psychological Factor Analysis"""
    
    def analyze(self, data: Dict[str, Any]) -> DimensionalSignal:
        """Behavioral finance and market psychology"""
        
        try:
            evidence = []
            psych_score = 0.0
        
            # Herd Behavior Detection
            herd_score = data.get('herd_behavior_score', 0.0)
            if herd_score > 0.7:
                psych_score -= 0.3  # Extreme herding = contrarian signal
                evidence.append(f"Extreme herd behavior ({herd_score:.2f}): Contrarian bearish")
        
            # Market Emotion
            emotion = data.get('market_emotion', 'neutral')
            if emotion == 'panic':
                psych_score += 0.4  # Panic = opportunity
                evidence.append("Market panic detected: Contrarian buying opportunity")
            elif emotion == 'euphoria':
                psych_score -= 0.4  # Euphoria = danger
                evidence.append("Market euphoria detected: Contrarian selling opportunity")
            elif emotion == 'complacency':
                psych_score -= 0.2
                evidence.append("Market complacency: Pre-shock environment")
        
            # Loss Aversion Patterns
            support_defense = data.get('support_defense_strength', 0.5)
            if support_defense > 0.8:
                evidence.append(f"Strong support defense ({support_defense:.2f}): Heavy trapped longs")
        
            # Recency Bias
            recency_bias = data.get('recency_bias_score', 0.5)
            if recency_bias > 0.7:
                psych_score -= 0.15  # Overweighting recent events
                evidence.append(f"High recency bias ({recency_bias:.2f}): Market overreacting")
        
            # Confirmation Bias
            confirmation_bias = data.get('confirmation_bias_score', 0.5)
            if confirmation_bias > 0.8:
                psych_score -= 0.2  # Market ignoring contradictory data
                evidence.append(f"Strong confirmation bias ({confirmation_bias:.2f}): Ignoring warnings")
        
            # Fear & Greed Index
            fear_greed = data.get('fear_greed_index', 50)
            if fear_greed < 20:
                psych_score += 0.3  # Extreme fear
                evidence.append(f"Fear & Greed Index {fear_greed}: Extreme fear")
            elif fear_greed > 80:
                psych_score -= 0.3  # Extreme greed
                evidence.append(f"Fear & Greed Index {fear_greed}: Extreme greed")
        
            # Determine signal
            if psych_score > 0.3:
                signal = "BULLISH"
            elif psych_score < -0.3:
                signal = "BEARISH"
            else:
                signal = "NEUTRAL"
        
            return DimensionalSignal(
                dimension="Psychological",
                signal=signal,
                strength=min(abs(psych_score), 1.0),
                confidence=0.70,
                evidence=evidence
            )
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise


class SevenDimensionalAwareness:
    """
    Omniscient market intelligence integrating all 7 dimensions
    """
    
    def __init__(self):
        try:
            self.macro_layer = MacroeconomicLayer()
            self.micro_layer = MicrostructureLayer()
            self.sentiment_layer = SentimentLayer()
            self.alt_data_layer = AlternativeDataLayer()
            self.blockchain_layer = BlockchainLayer()
            self.social_layer = SocialGraphLayer()
            self.psych_layer = PsychologicalLayer()
        
            self.analysis_history: List[OmniscientAnalysis] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def analyze_market(self, data: Dict[str, Any]) -> OmniscientAnalysis:
        """
        Comprehensive 7-dimensional market analysis
        """
        
        # Analyze each dimension
        try:
            dimension_signals = {
                'macro': self.macro_layer.analyze(data.get('macro', {})),
                'microstructure': self.micro_layer.analyze(data.get('microstructure', {})),
                'sentiment': self.sentiment_layer.analyze(data.get('sentiment', {})),
                'alternative_data': self.alt_data_layer.analyze(data.get('alternative_data', {})),
                'blockchain': self.blockchain_layer.analyze(data.get('blockchain', {})),
                'social_graph': self.social_layer.analyze(data.get('social_graph', {})),
                'psychological': self.psych_layer.analyze(data.get('psychological', {}))
            }
        
            # Calculate confluence score
            confluence = self._calculate_confluence(dimension_signals)
        
            # Synthesize primary signal
            primary_signal, conviction = self._synthesize_signal(dimension_signals, confluence)
        
            # Assess risk level
            risk_level = self._assess_risk(dimension_signals, confluence)
        
            # Generate recommendation
            recommendation = self._generate_recommendation(primary_signal, conviction, risk_level)
        
            # Calculate position size multiplier
            size_multiplier = self._calculate_position_size(conviction, confluence, risk_level)
        
            # Identify key risks
            key_risks = self._identify_risks(dimension_signals)
        
            # Generate synthesis narrative
            synthesis = self._generate_synthesis(dimension_signals, primary_signal, conviction)
        
            analysis = OmniscientAnalysis(
                primary_signal=primary_signal,
                conviction=conviction,
                dimension_signals=dimension_signals,
                confluence_score=confluence,
                risk_level=risk_level,
                recommended_action=recommendation,
                position_size_multiplier=size_multiplier,
                key_risks=key_risks,
                synthesis=synthesis
            )
        
            self.analysis_history.append(analysis)
        
            return analysis
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            raise
    
    def _calculate_confluence(self, signals: Dict[str, DimensionalSignal]) -> float:
        """Calculate signal confluence (0-100)"""
        
        # Weight each dimension
        try:
            weights = {
                'macro': 20,
                'microstructure': 15,
                'sentiment': 15,
                'alternative_data': 10,
                'blockchain': 10,
                'social_graph': 15,
                'psychological': 15
            }
        
            # Count agreements
            bullish_weight = 0
            bearish_weight = 0
            neutral_weight = 0
        
            for dim, signal in signals.items():
                weight = weights.get(dim, 10) * signal.confidence
            
                if signal.signal == "BULLISH":
                    bullish_weight += weight
                elif signal.signal == "BEARISH":
                    bearish_weight += weight
                else:
                    neutral_weight += weight
        
            total_weight = bullish_weight + bearish_weight + neutral_weight
        
            # Confluence is the dominance of the strongest signal
            max_weight = max(bullish_weight, bearish_weight, neutral_weight)
            confluence = (max_weight / total_weight * 100) if total_weight > 0 else 0
        
            return confluence
        except Exception as e:
            logger.error(f"Error in _calculate_confluence: {e}")
            raise
    
    def _synthesize_signal(self, signals: Dict[str, DimensionalSignal], 
                          confluence: float) -> Tuple[str, float]:
        """Synthesize primary signal and conviction"""
        
        try:
            bullish_score = 0
            bearish_score = 0
        
            for signal in signals.values():
                weighted_strength = signal.strength * signal.confidence
            
                if signal.signal == "BULLISH":
                    bullish_score += weighted_strength
                elif signal.signal == "BEARISH":
                    bearish_score += weighted_strength
        
            # Determine primary signal
            if bullish_score > bearish_score * 1.3:
                primary = "BULLISH"
                conviction = min((bullish_score / (bullish_score + bearish_score)) * 100, 100)
            elif bearish_score > bullish_score * 1.3:
                primary = "BEARISH"
                conviction = min((bearish_score / (bullish_score + bearish_score)) * 100, 100)
            else:
                primary = "NEUTRAL"
                conviction = 50
        
            # Adjust conviction by confluence
            conviction = (conviction + confluence) / 2
        
            return primary, conviction
        except Exception as e:
            logger.error(f"Error in _synthesize_signal: {e}")
            raise
    
    def _assess_risk(self, signals: Dict[str, DimensionalSignal], 
                    confluence: float) -> str:
        """Assess overall risk level"""
        
        # Check for conflicting signals
        try:
            signal_types = [s.signal for s in signals.values()]
            unique_signals = len(set(signal_types))
        
            if unique_signals == 3:  # All three types present
                return "HIGH"
            elif confluence < 50:
                return "ELEVATED"
            elif confluence > 75:
                return "LOW"
            else:
                return "MODERATE"
        except Exception as e:
            logger.error(f"Error in _assess_risk: {e}")
            raise
    
    def _generate_recommendation(self, signal: str, conviction: float, 
                                risk: str) -> str:
        """Generate trading recommendation"""
        
        try:
            if conviction >= 80 and risk in ["LOW", "MODERATE"]:
                if signal == "BULLISH":
                    return "STRONG BUY"
                elif signal == "BEARISH":
                    return "STRONG SELL"
            elif conviction >= 65:
                if signal == "BULLISH":
                    return "BUY"
                elif signal == "BEARISH":
                    return "SELL"
            elif conviction >= 50:
                if signal == "BULLISH":
                    return "WEAK BUY"
                elif signal == "BEARISH":
                    return "WEAK SELL"
        
            return "HOLD"
        except Exception as e:
            logger.error(f"Error in _generate_recommendation: {e}")
            raise
    
    def _calculate_position_size(self, conviction: float, confluence: float, 
                                risk: str) -> float:
        """Calculate position size multiplier (0-1.5)"""
        
        try:
            base_size = (conviction / 100) * (confluence / 100)
        
            # Adjust for risk
            risk_multipliers = {
                "LOW": 1.5,
                "MODERATE": 1.0,
                "ELEVATED": 0.5,
                "HIGH": 0.25
            }
        
            multiplier = base_size * risk_multipliers.get(risk, 0.5)
        
            return min(multiplier, 1.5)
        except Exception as e:
            logger.error(f"Error in _calculate_position_size: {e}")
            raise
    
    def _identify_risks(self, signals: Dict[str, DimensionalSignal]) -> List[str]:
        """Identify key risks from dimensional analysis"""
        
        try:
            risks = []
        
            for dim, signal in signals.items():
                # Look for bearish evidence even in bullish signals
                for evidence in signal.evidence:
                    if any(word in evidence.lower() for word in 
                          ['risk', 'stress', 'fear', 'weak', 'declining', 'negative']):
                        risks.append(f"{dim.title()}: {evidence}")
        
            return risks[:5]  # Top 5 risks
        except Exception as e:
            logger.error(f"Error in _identify_risks: {e}")
            raise
    
    def _generate_synthesis(self, signals: Dict[str, DimensionalSignal],
                           primary_signal: str, conviction: float) -> str:
        """Generate comprehensive narrative synthesis"""
        
        try:
            parts = [f"7-Dimensional Analysis: {primary_signal} with {conviction:.0f}% conviction."]
        
            # Add key supporting evidence from each dimension
            for dim, signal in signals.items():
                if signal.signal == primary_signal and signal.evidence:
                    parts.append(f"{dim.title()}: {signal.evidence[0]}")
        
            return " ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_synthesis: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize system
    awareness = SevenDimensionalAwareness()
    
    # Simulate market data
    market_data = {
        'macro': {
            'gdp_growth': 3.0,
            'cpi': 2.5,
            'fed_stance': 'dovish',
            'liquidity_phase': LiquidityPhase.EXPANSION
        },
        'microstructure': {
            'vpoc': 4500,
            'price': 4520,
            'bid_ask_ratio': 1.6,
            'cumulative_delta': 5000,
            'liquidity_score': 0.8
        },
        'sentiment': {
            'put_call_ratio': 1.2,
            'vix': 16,
            'retail_sentiment': 0.6,
            'institutional_flow': 1000000,
            'social_sentiment': 0.3
        },
        'alternative_data': {
            'parking_lot_fullness': 0.75,
            'credit_card_spending_change': 0.08,
            'web_traffic_change': 0.12,
            'insider_buying_ratio': 1.8
        },
        'blockchain': {
            'stablecoin_net_mints': 2e9,
            'btc_exchange_net_flow': -1500,
            'whale_transactions': 150,
            'whale_direction': 'accumulation',
            'defi_tvl_change': 0.15
        },
        'social_graph': {
            'kol_sentiment': 0.6,
            'kol_confidence': 0.8,
            'cascade_strength': 0.6,
            'echo_chamber_score': 0.4,
            'bot_activity_ratio': 0.15
        },
        'psychological': {
            'herd_behavior_score': 0.5,
            'market_emotion': 'neutral',
            'fear_greed_index': 60,
            'recency_bias_score': 0.5,
            'confirmation_bias_score': 0.5
        }
    }
    
    # Analyze
    analysis = awareness.analyze_market(market_data)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"OMNISCIENT MARKET ANALYSIS")
    logger.info(f"{'='*80}")
    logger.info(f"\nPrimary Signal: {analysis.primary_signal}")
    logger.info(f"Conviction: {analysis.conviction:.1f}%")
    logger.info(f"Confluence Score: {analysis.confluence_score:.1f}%")
    logger.info(f"Risk Level: {analysis.risk_level}")
    logger.info(f"Recommendation: {analysis.recommended_action}")
    logger.info(f"Position Size Multiplier: {analysis.position_size_multiplier:.2f}x")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"DIMENSIONAL BREAKDOWN")
    logger.info(f"{'='*80}")
    
    for dim, signal in analysis.dimension_signals.items():
        logger.info(f"\n{dim.upper()}:")
        logger.info(f"  Signal: {signal.signal} (Strength: {signal.strength:.2f}, Confidence: {signal.confidence:.2f})")
        for evidence in signal.evidence:
            logger.info(f"  • {evidence}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"KEY RISKS")
    logger.info(f"{'='*80}")
    for risk in analysis.key_risks:
        logger.info(f"  ⚠ {risk}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"SYNTHESIS")
    logger.info(f"{'='*80}")
    logger.info(f"{analysis.synthesis}")
