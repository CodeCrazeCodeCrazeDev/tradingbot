import logging
logger = logging.getLogger(__name__)
"""Adaptive Risk Management System for Market Intelligence."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import numpy
import pandas


class RiskRegime(Enum):
    """Risk regime classifications."""
    LOW_RISK = "low_risk"
    NORMAL_RISK = "normal_risk"
    ELEVATED_RISK = "elevated_risk"
    HIGH_RISK = "high_risk"
    EXTREME_RISK = "extreme_risk"


class AdaptiveRiskManagement:
    """Dynamic risk management that adapts to market conditions."""
    
    def __init__(self):
        try:
            self.risk_history = []
            self.correlation_matrix = {}
            self.volatility_forecasts = {}
            self.drawdown_tracker = {}
            logger.info("Initialized AdaptiveRiskManagement")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_dynamic_position_size(self, symbol: str, 
                                      market_analysis: Dict,
                                      account_balance: float,
                                      base_risk_percent: float = 0.02) -> Dict:
        """Calculate dynamic position size based on market conditions."""
        # Base risk calculation
        try:
            base_risk_amount = account_balance * base_risk_percent
        
            # Risk adjustments based on market analysis
            risk_multiplier = self._calculate_risk_multiplier(market_analysis)
        
            # Volatility adjustment
            volatility_adj = self._calculate_volatility_adjustment(symbol, market_analysis)
        
            # Correlation adjustment
            correlation_adj = self._calculate_correlation_adjustment(symbol)
        
            # Drawdown adjustment
            drawdown_adj = self._calculate_drawdown_adjustment(account_balance)
        
            # Combined adjustment
            final_multiplier = risk_multiplier * volatility_adj * correlation_adj * drawdown_adj
        
            # Calculate final position size
            adjusted_risk_amount = base_risk_amount * final_multiplier
        
            # Get stop loss distance for position sizing
            stop_loss_distance = self._calculate_optimal_stop_loss(symbol, market_analysis)
        
            # Position size calculation
            if stop_loss_distance > 0:
                position_size = adjusted_risk_amount / stop_loss_distance
            else:
                position_size = 0
        
            return {
                'position_size': position_size,
                'risk_amount': adjusted_risk_amount,
                'risk_multiplier': final_multiplier,
                'adjustments': {
                    'market_conditions': risk_multiplier,
                    'volatility': volatility_adj,
                    'correlation': correlation_adj,
                    'drawdown': drawdown_adj
                },
                'stop_loss_distance': stop_loss_distance,
                'risk_regime': self._classify_risk_regime(final_multiplier)
            }
        except Exception as e:
            logger.error(f"Error in calculate_dynamic_position_size: {e}")
            raise
    
    def monitor_portfolio_risk(self, positions: List[Dict], 
                             market_data: Dict) -> Dict:
        """Monitor and assess portfolio-wide risk metrics."""
        try:
            if not positions:
                return {'total_risk': 0, 'risk_concentration': {}}
        
            # Calculate portfolio metrics
            total_exposure = sum(pos.get('notional_value', 0) for pos in positions)
            total_risk = sum(pos.get('risk_amount', 0) for pos in positions)
        
            # Risk concentration by symbol
            symbol_risk = {}
            for pos in positions:
                symbol = pos.get('symbol', 'UNKNOWN')
                symbol_risk[symbol] = symbol_risk.get(symbol, 0) + pos.get('risk_amount', 0)
        
            # Risk concentration by sector/asset class
            sector_risk = self._calculate_sector_risk_concentration(positions)
        
            # Correlation risk
            correlation_risk = self._calculate_portfolio_correlation_risk(positions, market_data)
        
            # Value at Risk (VaR)
            portfolio_var = self._calculate_portfolio_var(positions, market_data)
        
            # Maximum drawdown risk
            max_drawdown_risk = self._calculate_max_drawdown_risk(positions)
        
            return {
                'total_exposure': total_exposure,
                'total_risk': total_risk,
                'risk_percentage': total_risk / max(total_exposure, 1) * 100,
                'symbol_concentration': symbol_risk,
                'sector_concentration': sector_risk,
                'correlation_risk': correlation_risk,
                'portfolio_var_1d': portfolio_var['1d'],
                'portfolio_var_5d': portfolio_var['5d'],
                'max_drawdown_risk': max_drawdown_risk,
                'risk_alerts': self._generate_risk_alerts(total_risk, symbol_risk, correlation_risk)
            }
        except Exception as e:
            logger.error(f"Error in monitor_portfolio_risk: {e}")
            raise
    
    def adaptive_stop_loss_management(self, position: Dict, 
                                    current_price: float,
                                    market_analysis: Dict) -> Dict:
        """Dynamically adjust stop losses based on market conditions."""
        try:
            entry_price = position.get('entry_price', current_price)
            current_stop = position.get('stop_loss', entry_price)
            direction = position.get('direction', 'long')
        
            # Calculate current P&L
            if direction == 'long':
                unrealized_pnl = (current_price - entry_price) / entry_price
            else:
                unrealized_pnl = (entry_price - current_price) / entry_price
        
            # Volatility-based stop adjustment
            volatility = market_analysis.get('volatility_measures', {}).get('current_volatility', 0.02)
            atr_multiplier = max(1.5, min(3.0, volatility * 100))  # 1.5x to 3x ATR
        
            # Trend-based adjustment
            trend_strength = market_analysis.get('bias_analysis', {}).get('overall_bias', {}).get('strength', 'weak')
            trend_multiplier = {'weak': 1.0, 'moderate': 1.2, 'strong': 1.5, 'extreme': 2.0}.get(trend_strength, 1.0)
        
            # Calculate new stop loss
            atr = market_analysis.get('technical_analysis', {}).get('volatility', {}).get('atr', current_price * 0.01)
        
            if direction == 'long':
                # Trailing stop for long positions
                if unrealized_pnl > 0.01:  # 1% profit
                    new_stop = current_price - (atr * atr_multiplier * trend_multiplier)
                    new_stop = max(new_stop, current_stop)  # Only move stop up
                else:
                    new_stop = entry_price - (atr * atr_multiplier)
            else:
                # Trailing stop for short positions
                if unrealized_pnl > 0.01:  # 1% profit
                    new_stop = current_price + (atr * atr_multiplier * trend_multiplier)
                    new_stop = min(new_stop, current_stop)  # Only move stop down
                else:
                    new_stop = entry_price + (atr * atr_multiplier)
        
            return {
                'new_stop_loss': new_stop,
                'stop_adjustment': abs(new_stop - current_stop) / current_price,
                'atr_multiplier': atr_multiplier,
                'trend_multiplier': trend_multiplier,
                'should_update': abs(new_stop - current_stop) / current_price > 0.001  # 0.1% threshold
            }
        except Exception as e:
            logger.error(f"Error in adaptive_stop_loss_management: {e}")
            raise
    
    def _calculate_risk_multiplier(self, market_analysis: Dict) -> float:
        """Calculate risk multiplier based on market conditions."""
        try:
            multiplier = 1.0
        
            # Volatility adjustment
            volatility = market_analysis.get('volatility_measures', {}).get('volatility_regime', 'normal')
            vol_adjustments = {'low': 1.2, 'normal': 1.0, 'high': 0.7, 'extreme': 0.4}
            multiplier *= vol_adjustments.get(volatility, 1.0)
        
            # Market regime adjustment
            regime = market_analysis.get('market_context', {}).get('market_regime', 'normal')
            regime_adjustments = {'bullish': 1.1, 'normal': 1.0, 'bearish': 0.8, 'crisis': 0.5}
            multiplier *= regime_adjustments.get(regime, 1.0)
        
            # Liquidity adjustment
            liquidity_score = market_analysis.get('liquidity_analysis', {}).get('liquidity_score', 0.5)
            if liquidity_score < 0.3:
                multiplier *= 0.7  # Reduce risk in low liquidity
            elif liquidity_score > 0.8:
                multiplier *= 1.1  # Slightly increase risk in high liquidity
        
            return max(0.2, min(2.0, multiplier))  # Cap between 20% and 200%
        except Exception as e:
            logger.error(f"Error in _calculate_risk_multiplier: {e}")
            raise
    
    def _calculate_volatility_adjustment(self, symbol: str, market_analysis: Dict) -> float:
        """Calculate volatility-based risk adjustment."""
        try:
            current_vol = market_analysis.get('volatility_measures', {}).get('current_volatility', 0.02)
            historical_vol = market_analysis.get('volatility_measures', {}).get('historical_volatility', 0.02)
        
            if historical_vol == 0:
                return 1.0
        
            vol_ratio = current_vol / historical_vol
        
            # Inverse relationship: higher volatility = lower position size
            if vol_ratio > 1.5:
                return 0.6  # Reduce by 40%
            elif vol_ratio > 1.2:
                return 0.8  # Reduce by 20%
            elif vol_ratio < 0.8:
                return 1.2  # Increase by 20%
            else:
                return 1.0
        except Exception as e:
            logger.error(f"Error in _calculate_volatility_adjustment: {e}")
            raise
    
    def _calculate_correlation_adjustment(self, symbol: str) -> float:
        """Calculate correlation-based risk adjustment."""
        # Simplified correlation adjustment
        # In practice, this would analyze correlations with existing positions
        
        try:
            if symbol in self.correlation_matrix:
                avg_correlation = np.mean(list(self.correlation_matrix[symbol].values()))
            
                # Higher correlation = lower additional risk
                if avg_correlation > 0.7:
                    return 0.7  # Highly correlated
                elif avg_correlation > 0.5:
                    return 0.85  # Moderately correlated
                else:
                    return 1.0  # Low correlation
        
            return 1.0  # No correlation data
        except Exception as e:
            logger.error(f"Error in _calculate_correlation_adjustment: {e}")
            raise
    
    def _calculate_drawdown_adjustment(self, current_balance: float) -> float:
        """Calculate drawdown-based risk adjustment."""
        try:
            if not self.drawdown_tracker:
                return 1.0
        
            peak_balance = max(self.drawdown_tracker.values()) if self.drawdown_tracker else current_balance
            current_drawdown = (peak_balance - current_balance) / peak_balance
        
            # Reduce risk during drawdowns
            if current_drawdown > 0.15:  # 15% drawdown
                return 0.5
            elif current_drawdown > 0.10:  # 10% drawdown
                return 0.7
            elif current_drawdown > 0.05:  # 5% drawdown
                return 0.85
            else:
                return 1.0
        except Exception as e:
            logger.error(f"Error in _calculate_drawdown_adjustment: {e}")
            raise
    
    def _calculate_optimal_stop_loss(self, symbol: str, market_analysis: Dict) -> float:
        """Calculate optimal stop loss distance."""
        # ATR-based stop loss
        try:
            atr = market_analysis.get('technical_analysis', {}).get('volatility', {}).get('atr', 0.001)
        
            # Support/resistance based adjustment
            structure_analysis = market_analysis.get('advanced_patterns', {}).get('market_structure', {})
            nearest_level = structure_analysis.get('nearest_support_resistance', 0)
        
            # Use larger of ATR-based or structure-based stop
            atr_stop = atr * 2.0  # 2x ATR
            structure_stop = abs(nearest_level) * 0.01 if nearest_level else atr_stop
        
            return max(atr_stop, structure_stop)
        except Exception as e:
            logger.error(f"Error in _calculate_optimal_stop_loss: {e}")
            raise
    
    def _classify_risk_regime(self, risk_multiplier: float) -> RiskRegime:
        """Classify current risk regime."""
        try:
            if risk_multiplier <= 0.4:
                return RiskRegime.EXTREME_RISK
            elif risk_multiplier <= 0.6:
                return RiskRegime.HIGH_RISK
            elif risk_multiplier <= 0.8:
                return RiskRegime.ELEVATED_RISK
            elif risk_multiplier <= 1.2:
                return RiskRegime.NORMAL_RISK
            else:
                return RiskRegime.LOW_RISK
        except Exception as e:
            logger.error(f"Error in _classify_risk_regime: {e}")
            raise
    
    def _calculate_sector_risk_concentration(self, positions: List[Dict]) -> Dict:
        """Calculate risk concentration by sector."""
        try:
            sector_risk = {}
        
            # Simplified sector mapping
            sector_mapping = {
                'EUR': 'currencies', 'GBP': 'currencies', 'JPY': 'currencies',
                'USD': 'currencies', 'AUD': 'currencies', 'CAD': 'currencies',
                'XAU': 'commodities', 'XAG': 'commodities', 'OIL': 'commodities'
            }
        
            for pos in positions:
                symbol = pos.get('symbol', '')
                risk_amount = pos.get('risk_amount', 0)
            
                # Determine sector
                sector = 'unknown'
                for currency, sec in sector_mapping.items():
                    if currency in symbol:
                        sector = sec
                        break
            
                sector_risk[sector] = sector_risk.get(sector, 0) + risk_amount
        
            return sector_risk
        except Exception as e:
            logger.error(f"Error in _calculate_sector_risk_concentration: {e}")
            raise
    
    def _calculate_portfolio_correlation_risk(self, positions: List[Dict], 
                                           market_data: Dict) -> float:
        """Calculate portfolio correlation risk."""
        try:
            if len(positions) < 2:
                return 0.0
        
            # Simplified correlation risk calculation
            symbols = [pos.get('symbol') for pos in positions]
        
            # Estimate correlations (in practice, use historical data)
            total_correlation = 0
            pair_count = 0
        
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    # Simplified correlation estimation
                    if sym1[:3] == sym2[:3] or sym1[3:] == sym2[3:]:  # Same base currency
                        correlation = 0.8
                    else:
                        correlation = 0.3
                
                    total_correlation += abs(correlation)
                    pair_count += 1
        
            return total_correlation / max(pair_count, 1)
        except Exception as e:
            logger.error(f"Error in _calculate_portfolio_correlation_risk: {e}")
            raise
    
    def _calculate_portfolio_var(self, positions: List[Dict], 
                               market_data: Dict) -> Dict:
        """Calculate portfolio Value at Risk."""
        try:
            if not positions:
                return {'1d': 0, '5d': 0}
        
            # Simplified VaR calculation
            total_notional = sum(pos.get('notional_value', 0) for pos in positions)
        
            # Assume 2% daily volatility for simplification
            daily_vol = 0.02
        
            # 95% confidence VaR
            var_1d = total_notional * daily_vol * 1.645  # 95% confidence
            var_5d = var_1d * np.sqrt(5)  # 5-day VaR
        
            return {'1d': var_1d, '5d': var_5d}
        except Exception as e:
            logger.error(f"Error in _calculate_portfolio_var: {e}")
            raise
    
    def _calculate_max_drawdown_risk(self, positions: List[Dict]) -> float:
        """Calculate maximum potential drawdown."""
        try:
            total_risk = sum(pos.get('risk_amount', 0) for pos in positions)
            total_notional = sum(pos.get('notional_value', 0) for pos in positions)
        
            if total_notional == 0:
                return 0.0
        
            # Worst-case scenario: all positions hit stop loss
            max_drawdown = total_risk / total_notional
        
            return max_drawdown
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown_risk: {e}")
            raise
    
    def _generate_risk_alerts(self, total_risk: float, 
                            symbol_risk: Dict, correlation_risk: float) -> List[str]:
        """Generate risk management alerts."""
        try:
            alerts = []
        
            # Total risk alert
            if total_risk > 100000:  # Example threshold
                alerts.append(f"High total portfolio risk: ${total_risk:,.0f}")
        
            # Concentration alerts
            for symbol, risk in symbol_risk.items():
                if risk > total_risk * 0.3:  # More than 30% of total risk
                    alerts.append(f"High concentration in {symbol}: {risk/total_risk*100:.1f}%")
        
            # Correlation alert
            if correlation_risk > 0.7:
                alerts.append(f"High portfolio correlation risk: {correlation_risk:.2f}")
        
            return alerts
        except Exception as e:
            logger.error(f"Error in _generate_risk_alerts: {e}")
            raise


class CorrelationBasedBalancing:
    """Portfolio balancing based on correlation analysis."""
    
    def __init__(self):
        try:
            self.correlation_history = {}
            self.rebalance_thresholds = {'high': 0.8, 'medium': 0.6, 'low': 0.4}
            logger.info("Initialized CorrelationBasedBalancing")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze_portfolio_correlations(self, positions: List[Dict], 
                                     price_data: Dict) -> Dict:
        """Analyze correlations between portfolio positions."""
        try:
            if len(positions) < 2:
                return {'correlations': {}, 'diversification_score': 1.0}
        
            symbols = [pos.get('symbol') for pos in positions]
            correlation_matrix = {}
        
            # Calculate pairwise correlations
            for i, sym1 in enumerate(symbols):
                correlation_matrix[sym1] = {}
                for sym2 in symbols:
                    if sym1 == sym2:
                        correlation_matrix[sym1][sym2] = 1.0
                    else:
                        # Calculate correlation from price data
                        corr = self._calculate_price_correlation(sym1, sym2, price_data)
                        correlation_matrix[sym1][sym2] = corr
        
            # Calculate diversification score
            diversification_score = self._calculate_diversification_score(correlation_matrix)
        
            # Identify highly correlated pairs
            high_corr_pairs = self._identify_high_correlation_pairs(correlation_matrix)
        
            return {
                'correlations': correlation_matrix,
                'diversification_score': diversification_score,
                'high_correlation_pairs': high_corr_pairs,
                'rebalancing_suggestions': self._generate_rebalancing_suggestions(
                    positions, correlation_matrix
                )
            }
        except Exception as e:
            logger.error(f"Error in analyze_portfolio_correlations: {e}")
            raise
    
    def suggest_position_adjustments(self, correlation_analysis: Dict) -> List[Dict]:
        """Suggest position adjustments based on correlation analysis."""
        try:
            suggestions = []
        
            high_corr_pairs = correlation_analysis.get('high_correlation_pairs', [])
            diversification_score = correlation_analysis.get('diversification_score', 1.0)
        
            # If diversification is poor, suggest reducing correlated positions
            if diversification_score < 0.6:
                for pair in high_corr_pairs:
                    suggestions.append({
                        'action': 'reduce_position',
                        'symbols': pair['symbols'],
                        'reason': f"High correlation ({pair['correlation']:.2f})",
                        'suggested_reduction': 0.3  # Reduce by 30%
                    })
        
            return suggestions
        except Exception as e:
            logger.error(f"Error in suggest_position_adjustments: {e}")
            raise
    
    def _calculate_price_correlation(self, sym1: str, sym2: str, 
                                   price_data: Dict) -> float:
        """Calculate correlation between two symbols."""
        # Simplified correlation calculation
        # In practice, use historical price returns
        
        # Currency pair correlation heuristics
        try:
            if sym1[:3] == sym2[:3] or sym1[3:] == sym2[3:]:  # Share base/quote currency
                return np.random.uniform(0.6, 0.9)
            elif 'JPY' in sym1 and 'JPY' in sym2:  # Both JPY pairs
                return np.random.uniform(0.4, 0.7)
            elif 'USD' in sym1 and 'USD' in sym2:  # Both USD pairs
                return np.random.uniform(0.3, 0.6)
            else:
                return np.random.uniform(-0.2, 0.4)
        except Exception as e:
            logger.error(f"Error in _calculate_price_correlation: {e}")
            raise
    
    def _calculate_diversification_score(self, correlation_matrix: Dict) -> float:
        """Calculate portfolio diversification score."""
        try:
            if not correlation_matrix:
                return 1.0
        
            # Average absolute correlation (excluding diagonal)
            correlations = []
            symbols = list(correlation_matrix.keys())
        
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    correlations.append(abs(correlation_matrix[sym1][sym2]))
        
            if not correlations:
                return 1.0
        
            avg_correlation = np.mean(correlations)
        
            # Convert to diversification score (lower correlation = higher diversification)
            return 1.0 - avg_correlation
        except Exception as e:
            logger.error(f"Error in _calculate_diversification_score: {e}")
            raise
    
    def _identify_high_correlation_pairs(self, correlation_matrix: Dict) -> List[Dict]:
        """Identify pairs with high correlation."""
        try:
            high_corr_pairs = []
            symbols = list(correlation_matrix.keys())
        
            for i, sym1 in enumerate(symbols):
                for sym2 in symbols[i+1:]:
                    corr = correlation_matrix[sym1][sym2]
                    if abs(corr) > self.rebalance_thresholds['high']:
                        high_corr_pairs.append({
                            'symbols': [sym1, sym2],
                            'correlation': corr,
                            'risk_level': 'high' if abs(corr) > 0.9 else 'medium'
                        })
        
            return high_corr_pairs
        except Exception as e:
            logger.error(f"Error in _identify_high_correlation_pairs: {e}")
            raise
    
    def _generate_rebalancing_suggestions(self, positions: List[Dict], 
                                        correlation_matrix: Dict) -> List[str]:
        """Generate portfolio rebalancing suggestions."""
        try:
            suggestions = []
        
            # Check for over-concentration
            total_exposure = sum(pos.get('notional_value', 0) for pos in positions)
        
            for pos in positions:
                symbol = pos.get('symbol')
                exposure = pos.get('notional_value', 0)
                concentration = exposure / total_exposure if total_exposure > 0 else 0
            
                if concentration > 0.4:  # More than 40% in single position
                    suggestions.append(f"Reduce {symbol} position - high concentration ({concentration*100:.1f}%)")
        
            return suggestions
        except Exception as e:
            logger.error(f"Error in _generate_rebalancing_suggestions: {e}")
            raise


class DrawdownResponsiveAdjustment:
    """Drawdown-responsive risk adjustment system."""
    
    def __init__(self):
        try:
            self.drawdown_history = []
            self.recovery_tracker = {}
            logger.info("Initialized DrawdownResponsiveAdjustment")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def monitor_drawdown(self, current_balance: float, peak_balance: float) -> Dict:
        """Monitor current drawdown and suggest adjustments."""
        try:
            current_drawdown = (peak_balance - current_balance) / peak_balance
        
            # Classify drawdown severity
            if current_drawdown < 0.02:
                severity = 'minimal'
            elif current_drawdown < 0.05:
                severity = 'minor'
            elif current_drawdown < 0.10:
                severity = 'moderate'
            elif current_drawdown < 0.20:
                severity = 'significant'
            else:
                severity = 'severe'
        
            # Calculate recovery requirements
            recovery_needed = (peak_balance / current_balance - 1) * 100
        
            # Risk adjustment recommendations
            risk_adjustments = self._calculate_drawdown_risk_adjustments(current_drawdown)
        
            return {
                'current_drawdown': current_drawdown,
                'drawdown_amount': peak_balance - current_balance,
                'severity': severity,
                'recovery_needed_percent': recovery_needed,
                'risk_adjustments': risk_adjustments,
                'psychological_impact': self._assess_psychological_impact(current_drawdown),
                'recovery_timeline': self._estimate_recovery_timeline(current_drawdown)
            }
        except Exception as e:
            logger.error(f"Error in monitor_drawdown: {e}")
            raise
    
    def adaptive_position_sizing(self, base_size: float, drawdown_info: Dict) -> float:
        """Adjust position size based on drawdown status."""
        try:
            current_drawdown = drawdown_info.get('current_drawdown', 0)
        
            # Drawdown-based size adjustments
            if current_drawdown > 0.15:  # 15%+ drawdown
                size_multiplier = 0.5
            elif current_drawdown > 0.10:  # 10%+ drawdown
                size_multiplier = 0.7
            elif current_drawdown > 0.05:  # 5%+ drawdown
                size_multiplier = 0.85
            else:
                size_multiplier = 1.0
        
            return base_size * size_multiplier
        except Exception as e:
            logger.error(f"Error in adaptive_position_sizing: {e}")
            raise
    
    def _calculate_drawdown_risk_adjustments(self, drawdown: float) -> Dict:
        """Calculate risk adjustments based on drawdown level."""
        try:
            adjustments = {
                'position_size_multiplier': 1.0,
                'stop_loss_tightening': 1.0,
                'take_profit_adjustment': 1.0,
                'new_position_restriction': False
            }
        
            if drawdown > 0.15:  # Severe drawdown
                adjustments.update({
                    'position_size_multiplier': 0.4,
                    'stop_loss_tightening': 0.7,
                    'take_profit_adjustment': 0.8,
                    'new_position_restriction': True
                })
            elif drawdown > 0.10:  # Significant drawdown
                adjustments.update({
                    'position_size_multiplier': 0.6,
                    'stop_loss_tightening': 0.8,
                    'take_profit_adjustment': 0.9,
                    'new_position_restriction': False
                })
            elif drawdown > 0.05:  # Moderate drawdown
                adjustments.update({
                    'position_size_multiplier': 0.8,
                    'stop_loss_tightening': 0.9,
                    'take_profit_adjustment': 1.0,
                    'new_position_restriction': False
                })
        
            return adjustments
        except Exception as e:
            logger.error(f"Error in _calculate_drawdown_risk_adjustments: {e}")
            raise
    
    def _assess_psychological_impact(self, drawdown: float) -> str:
        """Assess psychological impact of drawdown."""
        try:
            if drawdown > 0.20:
                return 'severe_stress'
            elif drawdown > 0.15:
                return 'high_stress'
            elif drawdown > 0.10:
                return 'moderate_stress'
            elif drawdown > 0.05:
                return 'mild_concern'
            else:
                return 'minimal_impact'
        except Exception as e:
            logger.error(f"Error in _assess_psychological_impact: {e}")
            raise
    
    def _estimate_recovery_timeline(self, drawdown: float) -> str:
        """Estimate recovery timeline based on drawdown severity."""
        # Simplified recovery estimation
        try:
            if drawdown > 0.20:
                return '6-12_months'
            elif drawdown > 0.15:
                return '3-6_months'
            elif drawdown > 0.10:
                return '1-3_months'
            elif drawdown > 0.05:
                return '2-4_weeks'
            else:
                return '1-2_weeks'
        except Exception as e:
            logger.error(f"Error in _estimate_recovery_timeline: {e}")
            raise
