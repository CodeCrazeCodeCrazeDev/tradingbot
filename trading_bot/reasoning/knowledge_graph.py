"""
Phase 3: Neuro-Symbolic Reasoning - Financial Knowledge Graph
Combines symbolic rules with neural reasoning
"""

import logging
from typing import Dict, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class FinancialKnowledgeGraph:
    """Financial knowledge representation and reasoning."""
    
    def __init__(self):
        # Core financial rules
        try:
            self.rules = {
                'interest_rate_impact': [
                    "IF interest_rates_rise THEN currency_strengthens",
                    "IF interest_rates_fall THEN bonds_rally",
                    "IF interest_rates_rise THEN bond_prices_fall"
                ],
                'correlation_rules': [
                    "IF VIX_spikes THEN equities_fall",
                    "IF dollar_strengthens THEN commodities_weaken",
                    "IF dollar_weakens THEN gold_rises"
                ],
                'technical_patterns': [
                    "IF double_top THEN expect_reversal",
                    "IF golden_cross THEN expect_uptrend",
                    "IF death_cross THEN expect_downtrend"
                ],
                'volatility_rules': [
                    "IF volatility_high THEN reduce_position_size",
                    "IF volatility_increasing THEN widen_stops",
                    "IF volatility_low THEN tighten_stops"
                ],
                'trend_rules': [
                    "IF price_above_200ma AND rsi_above_50 THEN uptrend",
                    "IF price_below_200ma AND rsi_below_50 THEN downtrend",
                    "IF adx_above_25 THEN strong_trend"
                ],
                'risk_rules': [
                    "IF correlation_high THEN reduce_exposure",
                    "IF market_stress_high THEN increase_cash",
                    "IF drawdown_exceeds_threshold THEN reduce_risk"
                ]
            }
        
            # Market regimes and their characteristics
            self.market_regimes = {
                'trending': {
                    'indicators': ['strong_adx', 'directional_movement'],
                    'strategies': ['trend_following', 'breakout'],
                    'risk_profile': 'moderate'
                },
                'ranging': {
                    'indicators': ['bounded_rsi', 'flat_ma'],
                    'strategies': ['mean_reversion', 'range_trading'],
                    'risk_profile': 'low'
                },
                'high_volatility': {
                    'indicators': ['wide_atr', 'vix_high'],
                    'strategies': ['options_based', 'reduced_size'],
                    'risk_profile': 'high'
                },
                'low_volatility': {
                    'indicators': ['narrow_atr', 'vix_low'],
                    'strategies': ['carry_trade', 'yield_seeking'],
                    'risk_profile': 'low'
                }
            }
        
            logger.info("✅ Financial Knowledge Graph initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def reason(self, market_state: Dict) -> Dict:
        """
        Apply logical rules to current market state.
        
        Args:
            market_state: Current market conditions
        
        Returns:
            Dictionary of conclusions and confidence
        """
        try:
            conclusions = []
            confidence_scores = []
        
            # Apply each rule category
            for category, rules in self.rules.items():
                category_conclusions = self._apply_rules(rules, market_state)
                if category_conclusions:
                    conclusions.extend(category_conclusions)
                
                    # Calculate confidence based on rule support
                    confidence = len(category_conclusions) / len(rules)
                    confidence_scores.append(confidence)
        
            # Detect market regime
            regime = self._detect_regime(market_state)
        
            # Combine all insights
            return {
                'conclusions': conclusions,
                'confidence': np.mean(confidence_scores) if confidence_scores else 0.0,
                'market_regime': regime,
                'recommended_strategies': self.market_regimes[regime]['strategies'],
                'risk_profile': self.market_regimes[regime]['risk_profile']
            }
        except Exception as e:
            logger.error(f"Error in reason: {e}")
            raise
    
    def _apply_rules(self, rules: List[str], market_state: Dict) -> List[str]:
        """Apply a set of rules to market state."""
        try:
            conclusions = []
        
            for rule in rules:
                if self._evaluate_rule(rule, market_state):
                    conclusions.append(self._extract_conclusion(rule))
        
            return conclusions
        except Exception as e:
            logger.error(f"Error in _apply_rules: {e}")
            raise
    
    def _evaluate_rule(self, rule: str, market_state: Dict) -> bool:
        """Evaluate if a rule's conditions are met."""
        try:
            condition = rule.split(" THEN ")[0].replace("IF ", "")
        
            # Interest rate rules
            if "interest_rates_rise" in condition:
                return market_state.get('interest_rate_change', 0) > 0
            elif "interest_rates_fall" in condition:
                return market_state.get('interest_rate_change', 0) < 0
        
            # Technical patterns
            elif "double_top" in condition:
                return market_state.get('pattern') == 'double_top'
            elif "golden_cross" in condition:
                sma_50 = market_state.get('sma_50', 0)
                sma_200 = market_state.get('sma_200', 0)
                return sma_50 > sma_200
            elif "death_cross" in condition:
                sma_50 = market_state.get('sma_50', 0)
                sma_200 = market_state.get('sma_200', 0)
                return sma_50 < sma_200
        
            # Trend conditions
            elif "price_above_200ma" in condition:
                price = market_state.get('price', 0)
                sma_200 = market_state.get('sma_200', 0)
                return price > sma_200
            elif "rsi_above_50" in condition:
                return market_state.get('rsi', 0) > 50
            elif "adx_above_25" in condition:
                return market_state.get('adx', 0) > 25
        
            # Volatility conditions
            elif "volatility_high" in condition:
                return market_state.get('volatility', 1.0) > 2.0
            elif "volatility_increasing" in condition:
                vol_change = market_state.get('volatility_change', 0)
                return vol_change > 0.1
            elif "volatility_low" in condition:
                return market_state.get('volatility', 1.0) < 0.5
        
            return False
        except Exception as e:
            logger.error(f"Error in _evaluate_rule: {e}")
            raise
    
    def _extract_conclusion(self, rule: str) -> str:
        """Extract conclusion part from rule."""
        return rule.split(" THEN ")[1]
    
    def _detect_regime(self, market_state: Dict) -> str:
        """Detect current market regime."""
        # Check for trending market
        try:
            adx = market_state.get('adx', 0)
            if adx > 25:
                return 'trending'
        
            # Check volatility
            volatility = market_state.get('volatility', 1.0)
            if volatility > 2.0:
                return 'high_volatility'
            elif volatility < 0.5:
                return 'low_volatility'
        
            # Default to ranging
            return 'ranging'
        except Exception as e:
            logger.error(f"Error in _detect_regime: {e}")
            raise
    
    def add_rule(self, category: str, rule: str):
        """Add new rule to knowledge base."""
        try:
            if category not in self.rules:
                self.rules[category] = []
        
            if rule not in self.rules[category]:
                self.rules[category].append(rule)
                logger.info(f"📚 Added rule to {category}: {rule}")
        except Exception as e:
            logger.error(f"Error in add_rule: {e}")
            raise
    
    def get_regime_characteristics(self, regime: str) -> Dict:
        """Get characteristics of a market regime."""
        return self.market_regimes.get(regime, {
            'indicators': [],
            'strategies': ['default'],
            'risk_profile': 'moderate'
        })
    
    def update_regime_model(self, regime: str, characteristics: Dict):
        """Update market regime model with new characteristics."""
        try:
            if regime in self.market_regimes:
                self.market_regimes[regime].update(characteristics)
                logger.info(f"📊 Updated {regime} regime model")
        except Exception as e:
            logger.error(f"Error in update_regime_model: {e}")
            raise
    
    def explain_reasoning(self, conclusions: List[str]) -> str:
        """Generate human-readable explanation of reasoning."""
        try:
            if not conclusions:
                return "No clear patterns detected in current market conditions."
        
            explanation = "Market analysis based on financial rules:\n\n"
            for i, conclusion in enumerate(conclusions, 1):
                explanation += f"{i}. {conclusion}\n"
        
            return explanation
        except Exception as e:
            logger.error(f"Error in explain_reasoning: {e}")
            raise
