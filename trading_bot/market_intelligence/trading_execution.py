import logging
logger = logging.getLogger(__name__)
"""Trading Execution Framework for the Market Intelligence System."""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger
from enum import Enum
from datetime import datetime, timedelta
import numpy
import pandas


class EntrySignalType(Enum):
    """Types of entry signals."""
    BREAKOUT = "breakout"
    PULLBACK = "pullback"
    REVERSAL = "reversal"
    CONTINUATION = "continuation"
    MEAN_REVERSION = "mean_reversion"


class ExitSignalType(Enum):
    """Types of exit signals."""
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TIME_EXIT = "time_exit"
    SIGNAL_REVERSAL = "signal_reversal"


class EntryStrategy:
    """Advanced entry strategy based on market intelligence."""
    
    def __init__(self):
        try:
            self.entry_signals = []
            self.signal_weights = {
                'structure': 0.25,
                'liquidity': 0.20,
                'volume': 0.15,
                'momentum': 0.15,
                'bias': 0.15,
                'risk': 0.10
            }
            logger.info("Initialized EntryStrategy")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_entry_signals(self, market_analysis: Dict, 
                             current_price: float,
                             symbol: str) -> List[Dict]:
        """Generate entry signals based on comprehensive market analysis.
        
        Args:
            market_analysis: Complete market intelligence analysis
            current_price: Current market price
            symbol: Trading symbol
            
        Returns:
            List of entry signals with confidence scores
        """
        try:
            entry_signals = []
        
            # Structure-based entries
            structure_signals = self._analyze_structure_entries(
                market_analysis.get('market_structure', {}), current_price
            )
            entry_signals.extend(structure_signals)
        
            # Liquidity-based entries
            liquidity_signals = self._analyze_liquidity_entries(
                market_analysis.get('liquidity_analysis', {}), current_price
            )
            entry_signals.extend(liquidity_signals)
        
            # Volume-based entries
            volume_signals = self._analyze_volume_entries(
                market_analysis.get('volume_analysis', {}), current_price
            )
            entry_signals.extend(volume_signals)
        
            # Momentum-based entries
            momentum_signals = self._analyze_momentum_entries(
                market_analysis.get('momentum_indicators', {}), current_price
            )
            entry_signals.extend(momentum_signals)
        
            # Bias confirmation entries
            bias_signals = self._analyze_bias_entries(
                market_analysis.get('bias_analysis', {}), current_price
            )
            entry_signals.extend(bias_signals)
        
            # Calculate composite signals
            composite_signals = self._calculate_composite_signals(entry_signals)
        
            # Filter and rank signals
            filtered_signals = self._filter_and_rank_signals(composite_signals, symbol)
        
            return filtered_signals
        except Exception as e:
            logger.error(f"Error in generate_entry_signals: {e}")
            raise
    
    def _analyze_structure_entries(self, structure_analysis: Dict, 
                                 current_price: float) -> List[Dict]:
        """Analyze structure-based entry opportunities."""
        try:
            signals = []
        
            # Break of Structure entries
            bos_patterns = structure_analysis.get('bos_patterns', [])
            for bos in bos_patterns[-3:]:  # Last 3 BOS patterns
                if bos.get('structure_break', False):
                    entry_price = bos.get('break_level', current_price)
                
                    signals.append({
                        'type': EntrySignalType.BREAKOUT,
                        'direction': 'long' if bos.get('type') == 'bullish_bos' else 'short',
                        'entry_price': entry_price,
                        'confidence': 0.75,
                        'source': 'break_of_structure',
                        'stop_loss': self._calculate_structure_stop_loss(bos, entry_price),
                        'take_profit': self._calculate_structure_take_profit(bos, entry_price)
                    })
        
            # Order block entries
            order_blocks = structure_analysis.get('order_blocks', [])
            for block in order_blocks:
                if not block.get('is_mitigated', True):
                    entry_price = block.get('mitigation_level', current_price)
                
                    signals.append({
                        'type': EntrySignalType.PULLBACK,
                        'direction': 'long' if block.get('type') == 'bullish' else 'short',
                        'entry_price': entry_price,
                        'confidence': 0.70,
                        'source': 'order_block',
                        'stop_loss': self._calculate_order_block_stop_loss(block, entry_price),
                        'take_profit': self._calculate_order_block_take_profit(block, entry_price)
                    })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_structure_entries: {e}")
            raise
    
    def _analyze_liquidity_entries(self, liquidity_analysis: Dict, 
                                 current_price: float) -> List[Dict]:
        """Analyze liquidity-based entry opportunities."""
        try:
            signals = []
        
            # Liquidity pool entries
            liquidity_pools = liquidity_analysis.get('liquidity_pools', [])
            for pool in liquidity_pools:
                if pool.get('strength', 0) >= 3:  # Strong liquidity pools
                    entry_price = pool.get('level', current_price)
                
                    signals.append({
                        'type': EntrySignalType.REVERSAL,
                        'direction': 'short' if pool.get('type') == 'resistance' else 'long',
                        'entry_price': entry_price,
                        'confidence': min(0.8, pool.get('strength', 0) / 5),
                        'source': 'liquidity_pool',
                        'stop_loss': self._calculate_liquidity_stop_loss(pool, entry_price),
                        'take_profit': self._calculate_liquidity_take_profit(pool, entry_price)
                    })
        
            # Fair Value Gap entries
            fvg_patterns = liquidity_analysis.get('fair_value_gaps', [])
            for fvg in fvg_patterns:
                if not fvg.get('is_filled', True):
                    entry_price = (fvg.get('gap_high', 0) + fvg.get('gap_low', 0)) / 2
                
                    signals.append({
                        'type': EntrySignalType.MEAN_REVERSION,
                        'direction': 'long' if fvg.get('type') == 'bullish_fvg' else 'short',
                        'entry_price': entry_price,
                        'confidence': 0.65,
                        'source': 'fair_value_gap',
                        'stop_loss': self._calculate_fvg_stop_loss(fvg, entry_price),
                        'take_profit': self._calculate_fvg_take_profit(fvg, entry_price)
                    })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_liquidity_entries: {e}")
            raise
    
    def _analyze_volume_entries(self, volume_analysis: Dict, 
                              current_price: float) -> List[Dict]:
        """Analyze volume-based entry opportunities."""
        try:
            signals = []
        
            # Volume climax entries
            volume_climax = volume_analysis.get('volume_climax_events', [])
            for climax in volume_climax[-2:]:  # Last 2 climax events
                climax_type = climax.get('climax_type', '')
            
                if 'selling_climax' in climax_type:
                    signals.append({
                        'type': EntrySignalType.REVERSAL,
                        'direction': 'long',
                        'entry_price': current_price,
                        'confidence': 0.70,
                        'source': 'selling_climax',
                        'stop_loss': current_price * 0.995,
                        'take_profit': current_price * 1.015
                    })
                elif 'buying_climax' in climax_type:
                    signals.append({
                        'type': EntrySignalType.REVERSAL,
                        'direction': 'short',
                        'entry_price': current_price,
                        'confidence': 0.70,
                        'source': 'buying_climax',
                        'stop_loss': current_price * 1.005,
                        'take_profit': current_price * 0.985
                    })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_volume_entries: {e}")
            raise
    
    def _analyze_momentum_entries(self, momentum_indicators: Dict, 
                                current_price: float) -> List[Dict]:
        """Analyze momentum-based entry opportunities."""
        try:
            signals = []
        
            # RSI divergence entries
            rsi_value = momentum_indicators.get('rsi', 50)
            if rsi_value < 30:  # Oversold
                signals.append({
                    'type': EntrySignalType.REVERSAL,
                    'direction': 'long',
                    'entry_price': current_price,
                    'confidence': 0.60,
                    'source': 'rsi_oversold',
                    'stop_loss': current_price * 0.99,
                    'take_profit': current_price * 1.02
                })
            elif rsi_value > 70:  # Overbought
                signals.append({
                    'type': EntrySignalType.REVERSAL,
                    'direction': 'short',
                    'entry_price': current_price,
                    'confidence': 0.60,
                    'source': 'rsi_overbought',
                    'stop_loss': current_price * 1.01,
                    'take_profit': current_price * 0.98
                })
        
            # MACD signal entries
            macd_signal = momentum_indicators.get('macd_signal', 0)
            if macd_signal > 0:  # Bullish MACD
                signals.append({
                    'type': EntrySignalType.CONTINUATION,
                    'direction': 'long',
                    'entry_price': current_price,
                    'confidence': 0.55,
                    'source': 'macd_bullish',
                    'stop_loss': current_price * 0.995,
                    'take_profit': current_price * 1.01
                })
            elif macd_signal < 0:  # Bearish MACD
                signals.append({
                    'type': EntrySignalType.CONTINUATION,
                    'direction': 'short',
                    'entry_price': current_price,
                    'confidence': 0.55,
                    'source': 'macd_bearish',
                    'stop_loss': current_price * 1.005,
                    'take_profit': current_price * 0.99
                })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_momentum_entries: {e}")
            raise
    
    def _analyze_bias_entries(self, bias_analysis: Dict, 
                            current_price: float) -> List[Dict]:
        """Analyze bias-based entry opportunities."""
        try:
            signals = []
        
            overall_bias = bias_analysis.get('overall_bias', {})
            bias_direction = overall_bias.get('direction', 'neutral')
            bias_strength = overall_bias.get('strength', 'weak')
        
            if bias_direction == 'bullish' and bias_strength in ['strong', 'extreme']:
                signals.append({
                    'type': EntrySignalType.CONTINUATION,
                    'direction': 'long',
                    'entry_price': current_price,
                    'confidence': 0.65 if bias_strength == 'strong' else 0.75,
                    'source': 'bullish_bias',
                    'stop_loss': current_price * 0.995,
                    'take_profit': current_price * 1.015
                })
            elif bias_direction == 'bearish' and bias_strength in ['strong', 'extreme']:
                signals.append({
                    'type': EntrySignalType.CONTINUATION,
                    'direction': 'short',
                    'entry_price': current_price,
                    'confidence': 0.65 if bias_strength == 'strong' else 0.75,
                    'source': 'bearish_bias',
                    'stop_loss': current_price * 1.005,
                    'take_profit': current_price * 0.985
                })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_bias_entries: {e}")
            raise
    
    def _calculate_composite_signals(self, entry_signals: List[Dict]) -> List[Dict]:
        """Calculate composite signals by combining similar entries."""
        try:
            if not entry_signals:
                return []
        
            # Group signals by direction and type
            signal_groups = {}
        
            for signal in entry_signals:
                key = (signal['direction'], signal['type'])
                if key not in signal_groups:
                    signal_groups[key] = []
                signal_groups[key].append(signal)
        
            composite_signals = []
        
            for (direction, signal_type), signals in signal_groups.items():
                if len(signals) == 1:
                    composite_signals.append(signals[0])
                else:
                    # Combine multiple signals
                    avg_confidence = sum(s['confidence'] for s in signals) / len(signals)
                    avg_entry_price = sum(s['entry_price'] for s in signals) / len(signals)
                
                    # Boost confidence for confluence
                    confluence_boost = min(0.2, (len(signals) - 1) * 0.05)
                    final_confidence = min(0.95, avg_confidence + confluence_boost)
                
                    composite_signal = {
                        'type': signal_type,
                        'direction': direction,
                        'entry_price': avg_entry_price,
                        'confidence': final_confidence,
                        'source': 'composite',
                        'component_signals': [s['source'] for s in signals],
                        'confluence_count': len(signals),
                        'stop_loss': sum(s['stop_loss'] for s in signals) / len(signals),
                        'take_profit': sum(s['take_profit'] for s in signals) / len(signals)
                    }
                
                    composite_signals.append(composite_signal)
        
            return composite_signals
        except Exception as e:
            logger.error(f"Error in _calculate_composite_signals: {e}")
            raise
    
    def _filter_and_rank_signals(self, signals: List[Dict], symbol: str) -> List[Dict]:
        """Filter and rank signals by quality and confidence."""
        # Filter by minimum confidence
        try:
            filtered_signals = [s for s in signals if s['confidence'] >= 0.5]
        
            # Sort by confidence (descending)
            filtered_signals.sort(key=lambda x: x['confidence'], reverse=True)
        
            # Add metadata
            for i, signal in enumerate(filtered_signals):
                signal.update({
                    'signal_id': f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}",
                    'timestamp': datetime.now(),
                    'symbol': symbol,
                    'rank': i + 1
                })
        
            return filtered_signals[:5]  # Return top 5 signals
        except Exception as e:
            logger.error(f"Error in _filter_and_rank_signals: {e}")
            raise
    
    def _calculate_structure_stop_loss(self, bos: Dict, entry_price: float) -> float:
        """Calculate stop loss for structure-based entries."""
        try:
            if bos.get('type') == 'bullish_bos':
                return entry_price * 0.995  # 0.5% below entry
            else:
                return entry_price * 1.005  # 0.5% above entry
        except Exception as e:
            logger.error(f"Error in _calculate_structure_stop_loss: {e}")
            raise
    
    def _calculate_structure_take_profit(self, bos: Dict, entry_price: float) -> float:
        """Calculate take profit for structure-based entries."""
        try:
            if bos.get('type') == 'bullish_bos':
                return entry_price * 1.02  # 2% above entry
            else:
                return entry_price * 0.98  # 2% below entry
        except Exception as e:
            logger.error(f"Error in _calculate_structure_take_profit: {e}")
            raise
    
    def _calculate_order_block_stop_loss(self, block: Dict, entry_price: float) -> float:
        """Calculate stop loss for order block entries."""
        try:
            if block.get('type') == 'bullish':
                return block.get('low', entry_price * 0.995)
            else:
                return block.get('high', entry_price * 1.005)
        except Exception as e:
            logger.error(f"Error in _calculate_order_block_stop_loss: {e}")
            raise
    
    def _calculate_order_block_take_profit(self, block: Dict, entry_price: float) -> float:
        """Calculate take profit for order block entries."""
        try:
            if block.get('type') == 'bullish':
                return entry_price * 1.015  # 1.5% above entry
            else:
                return entry_price * 0.985  # 1.5% below entry
        except Exception as e:
            logger.error(f"Error in _calculate_order_block_take_profit: {e}")
            raise
    
    def _calculate_liquidity_stop_loss(self, pool: Dict, entry_price: float) -> float:
        """Calculate stop loss for liquidity pool entries."""
        try:
            if pool.get('type') == 'resistance':
                return entry_price * 1.005  # 0.5% above entry
            else:
                return entry_price * 0.995  # 0.5% below entry
        except Exception as e:
            logger.error(f"Error in _calculate_liquidity_stop_loss: {e}")
            raise
    
    def _calculate_liquidity_take_profit(self, pool: Dict, entry_price: float) -> float:
        """Calculate take profit for liquidity pool entries."""
        try:
            if pool.get('type') == 'resistance':
                return entry_price * 0.985  # 1.5% below entry
            else:
                return entry_price * 1.015  # 1.5% above entry
        except Exception as e:
            logger.error(f"Error in _calculate_liquidity_take_profit: {e}")
            raise
    
    def _calculate_fvg_stop_loss(self, fvg: Dict, entry_price: float) -> float:
        """Calculate stop loss for FVG entries."""
        try:
            if fvg.get('type') == 'bullish_fvg':
                return fvg.get('gap_low', entry_price * 0.995)
            else:
                return fvg.get('gap_high', entry_price * 1.005)
        except Exception as e:
            logger.error(f"Error in _calculate_fvg_stop_loss: {e}")
            raise
    
    def _calculate_fvg_take_profit(self, fvg: Dict, entry_price: float) -> float:
        """Calculate take profit for FVG entries."""
        try:
            if fvg.get('type') == 'bullish_fvg':
                return entry_price * 1.01  # 1% above entry
            else:
                return entry_price * 0.99  # 1% below entry
        except Exception as e:
            logger.error(f"Error in _calculate_fvg_take_profit: {e}")
            raise


class ManagementStrategy:
    """Position management strategy based on market conditions."""
    
    def __init__(self):
        try:
            self.active_positions = {}
            logger.info("Initialized ManagementStrategy")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def manage_position(self, position: Dict, current_price: float, 
                       market_analysis: Dict) -> Dict:
        """Manage an active position based on current market conditions.
        
        Args:
            position: Position information
            current_price: Current market price
            market_analysis: Current market analysis
            
        Returns:
            Dictionary with management actions
        """
        try:
            management_actions = {
                'hold': True,
                'adjust_stop_loss': False,
                'adjust_take_profit': False,
                'partial_close': False,
                'full_close': False,
                'add_to_position': False
            }
        
            # Calculate current P&L
            entry_price = position.get('entry_price', current_price)
            direction = position.get('direction', 'long')
        
            if direction == 'long':
                pnl_pct = (current_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - current_price) / entry_price
        
            # Dynamic stop loss adjustment
            stop_loss_adjustment = self._calculate_dynamic_stop_loss(
                position, current_price, market_analysis, pnl_pct
            )
        
            if stop_loss_adjustment:
                management_actions.update(stop_loss_adjustment)
        
            # Take profit adjustment
            take_profit_adjustment = self._calculate_dynamic_take_profit(
                position, current_price, market_analysis, pnl_pct
            )
        
            if take_profit_adjustment:
                management_actions.update(take_profit_adjustment)
        
            # Position scaling decisions
            scaling_decision = self._calculate_position_scaling(
                position, current_price, market_analysis, pnl_pct
            )
        
            if scaling_decision:
                management_actions.update(scaling_decision)
        
            return management_actions
        except Exception as e:
            logger.error(f"Error in manage_position: {e}")
            raise
    
    def _calculate_dynamic_stop_loss(self, position: Dict, current_price: float,
                                   market_analysis: Dict, pnl_pct: float) -> Dict:
        """Calculate dynamic stop loss adjustments."""
        try:
            actions = {}
        
            # Trailing stop based on profit
            if pnl_pct > 0.01:  # 1% profit
                direction = position.get('direction', 'long')
                current_stop = position.get('stop_loss', 0)
            
                if direction == 'long':
                    # Trail stop loss upward
                    new_stop = current_price * 0.995  # 0.5% below current price
                    if new_stop > current_stop:
                        actions['adjust_stop_loss'] = True
                        actions['new_stop_loss'] = new_stop
                else:
                    # Trail stop loss downward
                    new_stop = current_price * 1.005  # 0.5% above current price
                    if new_stop < current_stop:
                        actions['adjust_stop_loss'] = True
                        actions['new_stop_loss'] = new_stop
        
            return actions
        except Exception as e:
            logger.error(f"Error in _calculate_dynamic_stop_loss: {e}")
            raise
    
    def _calculate_dynamic_take_profit(self, position: Dict, current_price: float,
                                     market_analysis: Dict, pnl_pct: float) -> Dict:
        """Calculate dynamic take profit adjustments."""
        try:
            actions = {}
        
            # Extend take profit if strong momentum continues
            momentum_indicators = market_analysis.get('momentum_indicators', {})
            rsi = momentum_indicators.get('rsi', 50)
        
            direction = position.get('direction', 'long')
        
            if direction == 'long' and rsi < 80 and pnl_pct > 0.015:
                # Extend take profit for long positions
                new_tp = current_price * 1.025  # 2.5% above current price
                actions['adjust_take_profit'] = True
                actions['new_take_profit'] = new_tp
            elif direction == 'short' and rsi > 20 and pnl_pct > 0.015:
                # Extend take profit for short positions
                new_tp = current_price * 0.975  # 2.5% below current price
                actions['adjust_take_profit'] = True
                actions['new_take_profit'] = new_tp
        
            return actions
        except Exception as e:
            logger.error(f"Error in _calculate_dynamic_take_profit: {e}")
            raise
    
    def _calculate_position_scaling(self, position: Dict, current_price: float,
                                  market_analysis: Dict, pnl_pct: float) -> Dict:
        """Calculate position scaling decisions."""
        try:
            actions = {}
        
            # Partial profit taking
            if pnl_pct > 0.02:  # 2% profit
                actions['partial_close'] = True
                actions['close_percentage'] = 0.5  # Close 50%
        
            # Add to winning positions
            bias_analysis = market_analysis.get('bias_analysis', {})
            overall_bias = bias_analysis.get('overall_bias', {})
            bias_direction = overall_bias.get('direction', 'neutral')
        
            direction = position.get('direction', 'long')
        
            if (pnl_pct > 0.005 and  # 0.5% profit
                ((direction == 'long' and bias_direction == 'bullish') or
                 (direction == 'short' and bias_direction == 'bearish'))):
                actions['add_to_position'] = True
                actions['add_percentage'] = 0.25  # Add 25% to position
        
            return actions
        except Exception as e:
            logger.error(f"Error in _calculate_position_scaling: {e}")
            raise


class ExitStrategy:
    """Advanced exit strategy based on market intelligence."""
    
    def __init__(self):
        try:
            self.exit_rules = {}
            logger.info("Initialized ExitStrategy")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_exit_signals(self, position: Dict, current_price: float,
                            market_analysis: Dict) -> List[Dict]:
        """Generate exit signals for active positions.
        
        Args:
            position: Position information
            current_price: Current market price
            market_analysis: Current market analysis
            
        Returns:
            List of exit signals
        """
        try:
            exit_signals = []
        
            # Technical exit signals
            technical_exits = self._analyze_technical_exits(
                position, current_price, market_analysis
            )
            exit_signals.extend(technical_exits)
        
            # Risk-based exits
            risk_exits = self._analyze_risk_exits(
                position, current_price, market_analysis
            )
            exit_signals.extend(risk_exits)
        
            # Time-based exits
            time_exits = self._analyze_time_exits(position, current_price)
            exit_signals.extend(time_exits)
        
            # Market condition exits
            condition_exits = self._analyze_market_condition_exits(
                position, current_price, market_analysis
            )
            exit_signals.extend(condition_exits)
        
            # Rank and filter exit signals
            ranked_exits = self._rank_exit_signals(exit_signals)
        
            return ranked_exits
        except Exception as e:
            logger.error(f"Error in generate_exit_signals: {e}")
            raise
    
    def _analyze_technical_exits(self, position: Dict, current_price: float,
                               market_analysis: Dict) -> List[Dict]:
        """Analyze technical-based exit signals."""
        try:
            signals = []
        
            # Momentum reversal exits
            momentum_indicators = market_analysis.get('momentum_indicators', {})
            rsi = momentum_indicators.get('rsi', 50)
        
            direction = position.get('direction', 'long')
        
            if direction == 'long' and rsi > 80:
                signals.append({
                    'type': ExitSignalType.SIGNAL_REVERSAL,
                    'reason': 'rsi_overbought',
                    'urgency': 'medium',
                    'confidence': 0.7,
                    'exit_percentage': 0.5
                })
            elif direction == 'short' and rsi < 20:
                signals.append({
                    'type': ExitSignalType.SIGNAL_REVERSAL,
                    'reason': 'rsi_oversold',
                    'urgency': 'medium',
                    'confidence': 0.7,
                    'exit_percentage': 0.5
                })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_technical_exits: {e}")
            raise
    
    def _analyze_risk_exits(self, position: Dict, current_price: float,
                          market_analysis: Dict) -> List[Dict]:
        """Analyze risk-based exit signals."""
        try:
            signals = []
        
            # Calculate current risk
            entry_price = position.get('entry_price', current_price)
            direction = position.get('direction', 'long')
        
            if direction == 'long':
                risk_pct = (entry_price - current_price) / entry_price
            else:
                risk_pct = (current_price - entry_price) / entry_price
        
            # Risk threshold exits
            if risk_pct > 0.02:  # 2% loss
                signals.append({
                    'type': ExitSignalType.STOP_LOSS,
                    'reason': 'risk_threshold_exceeded',
                    'urgency': 'high',
                    'confidence': 0.9,
                    'exit_percentage': 1.0
                })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_risk_exits: {e}")
            raise
    
    def _analyze_time_exits(self, position: Dict, current_price: float) -> List[Dict]:
        """Analyze time-based exit signals."""
        try:
            signals = []
        
            # Position age
            entry_time = position.get('entry_time', datetime.now())
            if isinstance(entry_time, str):
                entry_time = pd.to_datetime(entry_time)
        
            position_age = datetime.now() - entry_time
        
            # Time-based exit after 24 hours
            if position_age > timedelta(hours=24):
                signals.append({
                    'type': ExitSignalType.TIME_EXIT,
                    'reason': 'position_age_limit',
                    'urgency': 'low',
                    'confidence': 0.5,
                    'exit_percentage': 1.0
                })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_time_exits: {e}")
            raise
    
    def _analyze_market_condition_exits(self, position: Dict, current_price: float,
                                      market_analysis: Dict) -> List[Dict]:
        """Analyze market condition-based exits."""
        try:
            signals = []
        
            # Volatility-based exits
            volatility_measures = market_analysis.get('volatility_measures', {})
            volatility_regime = volatility_measures.get('volatility_regime', 'normal')
        
            if volatility_regime == 'high':
                signals.append({
                    'type': ExitSignalType.SIGNAL_REVERSAL,
                    'reason': 'high_volatility_regime',
                    'urgency': 'medium',
                    'confidence': 0.6,
                    'exit_percentage': 0.3
                })
        
            return signals
        except Exception as e:
            logger.error(f"Error in _analyze_market_condition_exits: {e}")
            raise
    
    def _rank_exit_signals(self, exit_signals: List[Dict]) -> List[Dict]:
        """Rank exit signals by urgency and confidence."""
        try:
            if not exit_signals:
                return []
        
            # Define urgency weights
            urgency_weights = {'high': 3, 'medium': 2, 'low': 1}
        
            # Calculate composite score
            for signal in exit_signals:
                urgency_weight = urgency_weights.get(signal.get('urgency', 'low'), 1)
                confidence = signal.get('confidence', 0.5)
                signal['composite_score'] = urgency_weight * confidence
        
            # Sort by composite score (descending)
            exit_signals.sort(key=lambda x: x['composite_score'], reverse=True)
        
            # Add timestamps
            for signal in exit_signals:
                signal['timestamp'] = datetime.now()
        
            return exit_signals
        except Exception as e:
            logger.error(f"Error in _rank_exit_signals: {e}")
            raise
