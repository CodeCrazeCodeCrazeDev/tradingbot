"""
Comprehensive Trading Playbook Module
======================================

Complete trading rules and scenarios:
- Multi-Scenario Trading Rules
- Trade Execution Flow
- Position Management
- Performance Attribution
- A/B Testing Framework
- Model Retraining Schedule
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Trading scenario types"""
    HIGH_CONFIDENCE_BULLISH = "high_confidence_bullish"
    HIGH_CONFIDENCE_BEARISH = "high_confidence_bearish"
    SENTIMENT_DIVERGENCE = "sentiment_divergence"
    LOW_CONFIDENCE_HIGH_VOL = "low_confidence_high_vol"
    MULTIPLE_CONFIRMATIONS = "multiple_confirmations"
    EVENT_DRIVEN = "event_driven"
    REGIME_CHANGE = "regime_change"


class TradeStage(Enum):
    """Trade execution stages"""
    SIGNAL_GENERATION = "signal_generation"
    RISK_ASSESSMENT = "risk_assessment"
    EXECUTION_SELECTION = "execution_selection"
    ORDER_EXECUTION = "order_execution"
    POSITION_MANAGEMENT = "position_management"
    POST_TRADE_ANALYSIS = "post_trade_analysis"


class PositionAction(Enum):
    """Position management actions"""
    HOLD = "hold"
    ADD = "add"  # Pyramid
    REDUCE = "reduce"  # Partial exit
    CLOSE = "close"  # Full exit
    REVERSE = "reverse"  # Close and open opposite


@dataclass
class TradingScenario:
    """Trading scenario definition"""
    scenario_type: ScenarioType
    name: str
    description: str
    
    # Entry conditions
    dc_signal_required: bool
    min_tmv: float
    min_lob_probability: float
    min_lstm_confidence: float
    sentiment_range: Tuple[float, float]  # (min, max)
    volatility_regime: str
    
    # Position sizing
    position_size_multiplier: float
    max_position_pct: float
    
    # Entry parameters
    entry_type: str  # 'limit', 'market', 'twap'
    entry_offset_bps: float
    
    # Exit parameters
    stop_loss_multiplier: float
    take_profit_levels: List[Tuple[float, float]]  # (threshold_mult, exit_pct)
    
    # Expected outcomes
    expected_win_rate: float
    expected_rr_ratio: float
    expected_hold_time_minutes: int


@dataclass
class TradeExecution:
    """Trade execution record"""
    trade_id: str
    timestamp: datetime
    symbol: str
    scenario: ScenarioType
    
    # Entry
    direction: str
    entry_price: float
    position_size: float
    
    # Signals at entry
    dc_signal: Dict[str, Any]
    ml_signal: Dict[str, Any]
    sentiment_signal: Dict[str, Any]
    
    # Exit
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None
    
    # P&L
    realized_pnl: float = 0
    realized_pnl_pct: float = 0
    
    # Attribution
    attribution: Dict[str, float] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    period: str
    
    # P&L
    gross_pnl: float
    net_pnl: float
    transaction_costs: float
    slippage_costs: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    # Returns
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    
    # Risk metrics
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    calmar_ratio: float
    
    # Attribution
    dc_contribution: float
    ml_contribution: float
    sentiment_contribution: float


class TradingPlaybook:
    """
    Comprehensive Trading Playbook
    
    Defines all trading scenarios and rules
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize scenarios
        self.scenarios = self._initialize_scenarios()
        
        # Trade history
        self.trade_history: deque = deque(maxlen=10000)
        
        # Active trades
        self.active_trades: Dict[str, TradeExecution] = {}
    
    def _initialize_scenarios(self) -> Dict[ScenarioType, TradingScenario]:
        """Initialize trading scenarios"""
        return {
            ScenarioType.HIGH_CONFIDENCE_BULLISH: TradingScenario(
                scenario_type=ScenarioType.HIGH_CONFIDENCE_BULLISH,
                name="High-Confidence DC Signal + Bullish Sentiment",
                description="Strong DC reversal with confirming sentiment",
                dc_signal_required=True,
                min_tmv=2.0,
                min_lob_probability=0.75,
                min_lstm_confidence=0.70,
                sentiment_range=(30, 100),
                volatility_regime="low_moderate",
                position_size_multiplier=1.5,
                max_position_pct=0.05,
                entry_type="limit",
                entry_offset_bps=5,
                stop_loss_multiplier=1.5,
                take_profit_levels=[(1.0, 0.5), (2.0, 0.5)],
                expected_win_rate=0.70,
                expected_rr_ratio=2.0,
                expected_hold_time_minutes=45,
            ),
            
            ScenarioType.SENTIMENT_DIVERGENCE: TradingScenario(
                scenario_type=ScenarioType.SENTIMENT_DIVERGENCE,
                name="DC Signal + Negative Sentiment Divergence",
                description="DC signal with conflicting sentiment",
                dc_signal_required=True,
                min_tmv=2.0,
                min_lob_probability=0.60,
                min_lstm_confidence=0.55,
                sentiment_range=(-50, -10),
                volatility_regime="any",
                position_size_multiplier=0.5,
                max_position_pct=0.025,
                entry_type="limit",
                entry_offset_bps=10,
                stop_loss_multiplier=1.0,
                take_profit_levels=[(0.75, 1.0)],
                expected_win_rate=0.55,
                expected_rr_ratio=1.0,
                expected_hold_time_minutes=15,
            ),
            
            ScenarioType.LOW_CONFIDENCE_HIGH_VOL: TradingScenario(
                scenario_type=ScenarioType.LOW_CONFIDENCE_HIGH_VOL,
                name="Low-Confidence + High Volatility",
                description="Unclear signals in volatile conditions - SKIP or minimal",
                dc_signal_required=True,
                min_tmv=2.0,
                min_lob_probability=0.50,
                min_lstm_confidence=0.50,
                sentiment_range=(-20, 20),
                volatility_regime="high",
                position_size_multiplier=0.25,
                max_position_pct=0.01,
                entry_type="market",
                entry_offset_bps=0,
                stop_loss_multiplier=0.75,
                take_profit_levels=[(0.5, 1.0)],
                expected_win_rate=0.50,
                expected_rr_ratio=0.66,
                expected_hold_time_minutes=10,
            ),
            
            ScenarioType.MULTIPLE_CONFIRMATIONS: TradingScenario(
                scenario_type=ScenarioType.MULTIPLE_CONFIRMATIONS,
                name="Multiple Confirmations + Alternative Data",
                description="Strong signals from multiple sources",
                dc_signal_required=True,
                min_tmv=2.5,
                min_lob_probability=0.80,
                min_lstm_confidence=0.78,
                sentiment_range=(-100, -50),
                volatility_regime="any",
                position_size_multiplier=2.0,
                max_position_pct=0.075,
                entry_type="limit",
                entry_offset_bps=2,
                stop_loss_multiplier=2.0,
                take_profit_levels=[(1.5, 0.4), (3.0, 0.4), (0, 0.2)],  # Trail remaining
                expected_win_rate=0.80,
                expected_rr_ratio=3.0,
                expected_hold_time_minutes=120,
            ),
            
            ScenarioType.EVENT_DRIVEN: TradingScenario(
                scenario_type=ScenarioType.EVENT_DRIVEN,
                name="Event-Driven (News/Earnings)",
                description="Trading around major events",
                dc_signal_required=False,
                min_tmv=0,
                min_lob_probability=0.60,
                min_lstm_confidence=0.60,
                sentiment_range=(-100, 100),
                volatility_regime="high",
                position_size_multiplier=0.5,
                max_position_pct=0.02,
                entry_type="market",
                entry_offset_bps=0,
                stop_loss_multiplier=2.0,
                take_profit_levels=[(2.0, 0.5), (4.0, 0.5)],
                expected_win_rate=0.55,
                expected_rr_ratio=2.5,
                expected_hold_time_minutes=60,
            ),
        }
    
    def match_scenario(self, signals: Dict[str, Any]) -> Optional[TradingScenario]:
        """
        Match current signals to a trading scenario
        
        Args:
            signals: Dictionary of current signals
            
        Returns:
            Matching TradingScenario or None
        """
        dc_signal = signals.get('dc', {})
        ml_signal = signals.get('ml', {})
        sentiment = signals.get('sentiment', {})
        regime = signals.get('regime', 'normal')
        
        # Extract values
        has_dc = dc_signal.get('has_signal', False)
        tmv = dc_signal.get('tmv', 0)
        lob_prob = ml_signal.get('probability', 0.5)
        lstm_conf = ml_signal.get('confidence', 0.5)
        sent_score = sentiment.get('score', 0)
        
        # Check each scenario
        for scenario_type, scenario in self.scenarios.items():
            # DC requirement
            if scenario.dc_signal_required and not has_dc:
                continue
            
            # TMV requirement
            if tmv < scenario.min_tmv:
                continue
            
            # ML requirements
            if lob_prob < scenario.min_lob_probability:
                continue
            if lstm_conf < scenario.min_lstm_confidence:
                continue
            
            # Sentiment range
            if not (scenario.sentiment_range[0] <= sent_score <= scenario.sentiment_range[1]):
                continue
            
            # Volatility regime
            if scenario.volatility_regime != "any":
                if scenario.volatility_regime == "high" and regime not in ['high_vol_trending', 'high_vol_ranging']:
                    continue
                if scenario.volatility_regime == "low_moderate" and regime in ['high_vol_trending', 'high_vol_ranging']:
                    continue
            
            # Match found
            return scenario
        
        return None
    
    def create_trade_plan(self, scenario: TradingScenario, signals: Dict[str, Any],
                         current_price: float, capital: float) -> Dict[str, Any]:
        """
        Create detailed trade plan
        
        Args:
            scenario: Matched scenario
            signals: Current signals
            current_price: Current price
            capital: Available capital
            
        Returns:
            Trade plan dictionary
        """
        dc_threshold = signals.get('dc', {}).get('threshold', 0.01)
        
        # Calculate position size
        base_size = capital * scenario.max_position_pct
        adjusted_size = base_size * scenario.position_size_multiplier
        
        # Entry price
        if scenario.entry_type == 'limit':
            if signals.get('direction') == 'long':
                entry_price = current_price * (1 - scenario.entry_offset_bps / 10000)
            else:
                entry_price = current_price * (1 + scenario.entry_offset_bps / 10000)
        else:
            entry_price = current_price
        
        # Stop loss
        stop_distance = dc_threshold * scenario.stop_loss_multiplier
        if signals.get('direction') == 'long':
            stop_loss = entry_price * (1 - stop_distance)
        else:
            stop_loss = entry_price * (1 + stop_distance)
        
        # Take profit levels
        take_profits = []
        for tp_mult, exit_pct in scenario.take_profit_levels:
            if tp_mult == 0:
                # Trailing stop
                take_profits.append({
                    'type': 'trailing',
                    'exit_pct': exit_pct,
                    'trail_distance': dc_threshold,
                })
            else:
                tp_distance = dc_threshold * tp_mult
                if signals.get('direction') == 'long':
                    tp_price = entry_price * (1 + tp_distance)
                else:
                    tp_price = entry_price * (1 - tp_distance)
                
                take_profits.append({
                    'type': 'fixed',
                    'price': tp_price,
                    'exit_pct': exit_pct,
                })
        
        return {
            'scenario': scenario.scenario_type.value,
            'direction': signals.get('direction', 'neutral'),
            'entry_type': scenario.entry_type,
            'entry_price': entry_price,
            'position_size': adjusted_size,
            'stop_loss': stop_loss,
            'take_profits': take_profits,
            'expected_win_rate': scenario.expected_win_rate,
            'expected_rr_ratio': scenario.expected_rr_ratio,
            'expected_hold_time': scenario.expected_hold_time_minutes,
            'risk_per_trade': abs(entry_price - stop_loss) * adjusted_size / entry_price,
        }


class PositionManager:
    """
    Position Management System
    
    Handles cascading, de-cascading, and exit management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Active positions
        self.positions: Dict[str, Dict[str, Any]] = {}
        
        # Position history
        self.position_history: deque = deque(maxlen=1000)
    
    def open_position(self, trade_plan: Dict[str, Any], symbol: str) -> str:
        """Open a new position"""
        position_id = f"POS_{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.positions[position_id] = {
            'id': position_id,
            'symbol': symbol,
            'direction': trade_plan['direction'],
            'entry_price': trade_plan['entry_price'],
            'current_size': trade_plan['position_size'],
            'initial_size': trade_plan['position_size'],
            'stop_loss': trade_plan['stop_loss'],
            'take_profits': trade_plan['take_profits'],
            'cascade_level': 0,
            'partial_exits': [],
            'opened_at': datetime.now(),
            'unrealized_pnl': 0,
            'status': 'open',
        }
        
        return position_id
    
    def update_position(self, position_id: str, current_price: float) -> Dict[str, Any]:
        """
        Update position and determine action
        
        Args:
            position_id: Position ID
            current_price: Current price
            
        Returns:
            Action to take
        """
        if position_id not in self.positions:
            return {'action': PositionAction.HOLD, 'reason': 'Position not found'}
        
        pos = self.positions[position_id]
        
        # Update unrealized P&L
        if pos['direction'] == 'long':
            pos['unrealized_pnl'] = (current_price - pos['entry_price']) / pos['entry_price']
        else:
            pos['unrealized_pnl'] = (pos['entry_price'] - current_price) / pos['entry_price']
        
        # Check stop loss
        if pos['direction'] == 'long' and current_price <= pos['stop_loss']:
            return {
                'action': PositionAction.CLOSE,
                'reason': 'stop_loss',
                'price': current_price,
            }
        elif pos['direction'] == 'short' and current_price >= pos['stop_loss']:
            return {
                'action': PositionAction.CLOSE,
                'reason': 'stop_loss',
                'price': current_price,
            }
        
        # Check take profit levels
        for i, tp in enumerate(pos['take_profits']):
            if tp.get('executed'):
                continue
            
            if tp['type'] == 'fixed':
                if pos['direction'] == 'long' and current_price >= tp['price']:
                    return {
                        'action': PositionAction.REDUCE,
                        'reason': f'take_profit_{i+1}',
                        'exit_pct': tp['exit_pct'],
                        'price': current_price,
                        'tp_index': i,
                    }
                elif pos['direction'] == 'short' and current_price <= tp['price']:
                    return {
                        'action': PositionAction.REDUCE,
                        'reason': f'take_profit_{i+1}',
                        'exit_pct': tp['exit_pct'],
                        'price': current_price,
                        'tp_index': i,
                    }
        
        return {'action': PositionAction.HOLD, 'reason': 'No action required'}
    
    def execute_action(self, position_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute position action"""
        if position_id not in self.positions:
            return {'success': False, 'error': 'Position not found'}
        
        pos = self.positions[position_id]
        
        if action['action'] == PositionAction.CLOSE:
            # Close entire position
            exit_size = pos['current_size']
            pos['current_size'] = 0
            pos['status'] = 'closed'
            pos['closed_at'] = datetime.now()
            pos['exit_price'] = action['price']
            pos['exit_reason'] = action['reason']
            
            # Calculate realized P&L
            if pos['direction'] == 'long':
                realized_pnl = (action['price'] - pos['entry_price']) * exit_size / pos['entry_price']
            else:
                realized_pnl = (pos['entry_price'] - action['price']) * exit_size / pos['entry_price']
            
            pos['realized_pnl'] = realized_pnl
            
            # Move to history
            self.position_history.append(pos.copy())
            del self.positions[position_id]
            
            return {
                'success': True,
                'action': 'closed',
                'exit_size': exit_size,
                'realized_pnl': realized_pnl,
            }
        
        elif action['action'] == PositionAction.REDUCE:
            # Partial exit
            exit_size = pos['current_size'] * action['exit_pct']
            pos['current_size'] -= exit_size
            
            # Mark TP as executed
            if 'tp_index' in action:
                pos['take_profits'][action['tp_index']]['executed'] = True
            
            pos['partial_exits'].append({
                'timestamp': datetime.now(),
                'size': exit_size,
                'price': action['price'],
                'reason': action['reason'],
            })
            
            # Check if fully closed
            if pos['current_size'] <= 0:
                pos['status'] = 'closed'
                pos['closed_at'] = datetime.now()
                self.position_history.append(pos.copy())
                del self.positions[position_id]
            
            return {
                'success': True,
                'action': 'reduced',
                'exit_size': exit_size,
                'remaining_size': pos.get('current_size', 0),
            }
        
        return {'success': True, 'action': 'hold'}


class PerformanceAttributor:
    """
    Performance Attribution System
    
    Attributes P&L to different signal sources
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Trade records
        self.trades: deque = deque(maxlen=10000)
        
        # Daily metrics
        self.daily_metrics: Dict[str, PerformanceMetrics] = {}
    
    def record_trade(self, trade: TradeExecution):
        """Record completed trade"""
        self.trades.append(trade)
    
    def calculate_attribution(self, trade: TradeExecution) -> Dict[str, float]:
        """
        Calculate signal attribution for trade
        
        Args:
            trade: Completed trade
            
        Returns:
            Attribution dictionary
        """
        attribution = {}
        
        # DC contribution
        dc_signal = trade.dc_signal
        if dc_signal.get('has_signal'):
            dc_strength = dc_signal.get('tmv', 0) / 4  # Normalize
            attribution['dc'] = dc_strength * 0.3
        else:
            attribution['dc'] = 0
        
        # ML contribution
        ml_signal = trade.ml_signal
        ml_conf = ml_signal.get('confidence', 0.5)
        attribution['ml'] = (ml_conf - 0.5) * 2 * 0.25  # Normalize to contribution
        
        # Sentiment contribution
        sent_signal = trade.sentiment_signal
        sent_score = sent_signal.get('score', 0)
        # Check if sentiment was confirming
        if trade.direction == 'long' and sent_score > 0:
            attribution['sentiment'] = min(sent_score / 100, 1) * 0.15
        elif trade.direction == 'short' and sent_score < 0:
            attribution['sentiment'] = min(abs(sent_score) / 100, 1) * 0.15
        else:
            attribution['sentiment'] = -0.05  # Penalty for divergence
        
        # Execution contribution (slippage)
        attribution['execution'] = 0.1  # Placeholder
        
        # Normalize
        total = sum(abs(v) for v in attribution.values())
        if total > 0:
            attribution = {k: v / total for k, v in attribution.items()}
        
        return attribution
    
    def calculate_period_metrics(self, start_date: datetime, 
                                end_date: datetime) -> PerformanceMetrics:
        """
        Calculate performance metrics for period
        
        Args:
            start_date: Period start
            end_date: Period end
            
        Returns:
            PerformanceMetrics
        """
        period_trades = [
            t for t in self.trades
            if start_date <= t.timestamp <= end_date
        ]
        
        if not period_trades:
            return PerformanceMetrics(
                period=f"{start_date.date()} to {end_date.date()}",
                gross_pnl=0, net_pnl=0, transaction_costs=0, slippage_costs=0,
                total_trades=0, winning_trades=0, losing_trades=0, win_rate=0,
                avg_win=0, avg_loss=0, profit_factor=0, expectancy=0,
                sharpe_ratio=0, sortino_ratio=0, max_drawdown=0, calmar_ratio=0,
                dc_contribution=0, ml_contribution=0, sentiment_contribution=0,
            )
        
        # Calculate metrics
        pnls = [t.realized_pnl for t in period_trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_trades = len(period_trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        
        gross_pnl = sum(pnls)
        transaction_costs = total_trades * 0.001  # Estimate
        slippage_costs = total_trades * 0.0005  # Estimate
        net_pnl = gross_pnl - transaction_costs - slippage_costs
        
        profit_factor = sum(wins) / abs(sum(losses)) if losses else float('inf')
        expectancy = np.mean(pnls) if pnls else 0
        
        # Risk metrics
        if len(pnls) > 1:
            returns_std = np.std(pnls)
            sharpe_ratio = np.mean(pnls) / returns_std * np.sqrt(252) if returns_std > 0 else 0
            
            downside = [p for p in pnls if p < 0]
            downside_std = np.std(downside) if downside else 1
            sortino_ratio = np.mean(pnls) / downside_std * np.sqrt(252) if downside_std > 0 else 0
            
            # Max drawdown
            cumulative = np.cumsum(pnls)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = running_max - cumulative
            max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
            
            calmar_ratio = net_pnl / max_drawdown if max_drawdown > 0 else 0
        else:
            sharpe_ratio = sortino_ratio = max_drawdown = calmar_ratio = 0
        
        # Attribution
        dc_contrib = np.mean([t.attribution.get('dc', 0) for t in period_trades if t.attribution])
        ml_contrib = np.mean([t.attribution.get('ml', 0) for t in period_trades if t.attribution])
        sent_contrib = np.mean([t.attribution.get('sentiment', 0) for t in period_trades if t.attribution])
        
        return PerformanceMetrics(
            period=f"{start_date.date()} to {end_date.date()}",
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            transaction_costs=transaction_costs,
            slippage_costs=slippage_costs,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            expectancy=expectancy,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            dc_contribution=dc_contrib,
            ml_contribution=ml_contrib,
            sentiment_contribution=sent_contrib,
        )


class ABTestingFramework:
    """
    A/B Testing Framework for Strategy Variations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Active tests
        self.active_tests: Dict[str, Dict[str, Any]] = {}
        
        # Test history
        self.test_history: deque = deque(maxlen=100)
        
        # Allocation
        self.test_allocation = self.config.get('test_allocation', 0.10)  # 10% to test
    
    def create_test(self, test_name: str, control_config: Dict[str, Any],
                   variant_config: Dict[str, Any], duration_days: int = 30) -> str:
        """
        Create new A/B test
        
        Args:
            test_name: Name of test
            control_config: Control (current) configuration
            variant_config: Variant (new) configuration
            duration_days: Test duration
            
        Returns:
            Test ID
        """
        test_id = f"TEST_{test_name}_{datetime.now().strftime('%Y%m%d')}"
        
        self.active_tests[test_id] = {
            'id': test_id,
            'name': test_name,
            'control': control_config,
            'variant': variant_config,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=duration_days),
            'control_trades': [],
            'variant_trades': [],
            'status': 'active',
        }
        
        return test_id
    
    def record_trade(self, test_id: str, is_variant: bool, trade: Dict[str, Any]):
        """Record trade for test"""
        if test_id not in self.active_tests:
            return
        
        test = self.active_tests[test_id]
        
        if is_variant:
            test['variant_trades'].append(trade)
        else:
            test['control_trades'].append(trade)
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze test results
        
        Args:
            test_id: Test ID
            
        Returns:
            Analysis results
        """
        if test_id not in self.active_tests:
            return {'error': 'Test not found'}
        
        test = self.active_tests[test_id]
        
        control_pnls = [t.get('pnl', 0) for t in test['control_trades']]
        variant_pnls = [t.get('pnl', 0) for t in test['variant_trades']]
        
        if not control_pnls or not variant_pnls:
            return {'error': 'Insufficient data'}
        
        # Calculate metrics
        control_sharpe = np.mean(control_pnls) / np.std(control_pnls) if np.std(control_pnls) > 0 else 0
        variant_sharpe = np.mean(variant_pnls) / np.std(variant_pnls) if np.std(variant_pnls) > 0 else 0
        
        control_win_rate = sum(1 for p in control_pnls if p > 0) / len(control_pnls)
        variant_win_rate = sum(1 for p in variant_pnls if p > 0) / len(variant_pnls)
        
        # Statistical significance (simplified)
        from scipy import stats
        try:
            t_stat, p_value = stats.ttest_ind(control_pnls, variant_pnls)
        except Exception:
            t_stat, p_value = 0, 1
        
        is_significant = p_value < 0.05
        variant_better = np.mean(variant_pnls) > np.mean(control_pnls)
        
        return {
            'test_id': test_id,
            'control': {
                'trades': len(control_pnls),
                'total_pnl': sum(control_pnls),
                'sharpe': control_sharpe,
                'win_rate': control_win_rate,
            },
            'variant': {
                'trades': len(variant_pnls),
                'total_pnl': sum(variant_pnls),
                'sharpe': variant_sharpe,
                'win_rate': variant_win_rate,
            },
            'p_value': p_value,
            'is_significant': is_significant,
            'recommendation': 'adopt_variant' if is_significant and variant_better else 'keep_control',
        }


class ModelRetrainingScheduler:
    """
    Model Retraining Schedule Manager
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Retraining schedules
        self.schedules = {
            'sentiment': {'frequency': 'daily', 'last_trained': None},
            'lob_model': {'frequency': 'daily', 'last_trained': None},
            'lstm_trend': {'frequency': 'weekly', 'last_trained': None},
            'volatility_regime': {'frequency': 'weekly', 'last_trained': None},
            'ensemble_meta': {'frequency': 'monthly', 'last_trained': None},
            'risk_params': {'frequency': 'monthly', 'last_trained': None},
            'execution_rl': {'frequency': 'monthly', 'last_trained': None},
        }
        
        # Training history
        self.training_history: deque = deque(maxlen=1000)
    
    def check_retraining_needed(self) -> List[str]:
        """
        Check which models need retraining
        
        Returns:
            List of model names needing retraining
        """
        needs_retraining = []
        now = datetime.now()
        
        for model, schedule in self.schedules.items():
            last_trained = schedule['last_trained']
            
            if last_trained is None:
                needs_retraining.append(model)
                continue
            
            if schedule['frequency'] == 'daily':
                if (now - last_trained).days >= 1:
                    needs_retraining.append(model)
            elif schedule['frequency'] == 'weekly':
                if (now - last_trained).days >= 7:
                    needs_retraining.append(model)
            elif schedule['frequency'] == 'monthly':
                if (now - last_trained).days >= 30:
                    needs_retraining.append(model)
        
        return needs_retraining
    
    def record_training(self, model: str, metrics: Dict[str, Any]):
        """Record model training"""
        if model in self.schedules:
            self.schedules[model]['last_trained'] = datetime.now()
        
        self.training_history.append({
            'model': model,
            'timestamp': datetime.now(),
            'metrics': metrics,
        })
    
    def get_training_schedule(self) -> Dict[str, Any]:
        """Get current training schedule status"""
        return {
            model: {
                'frequency': schedule['frequency'],
                'last_trained': schedule['last_trained'].isoformat() if schedule['last_trained'] else None,
                'next_training': self._calculate_next_training(schedule),
            }
            for model, schedule in self.schedules.items()
        }
    
    def _calculate_next_training(self, schedule: Dict[str, Any]) -> Optional[str]:
        """Calculate next training date"""
        if schedule['last_trained'] is None:
            return 'Now'
        
        freq_days = {'daily': 1, 'weekly': 7, 'monthly': 30}
        days = freq_days.get(schedule['frequency'], 30)
        
        next_date = schedule['last_trained'] + timedelta(days=days)
        return next_date.isoformat()
