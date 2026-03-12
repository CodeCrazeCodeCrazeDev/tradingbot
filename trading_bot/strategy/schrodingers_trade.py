"""
Schrödinger's Trade Mode

For every live trade, runs a parallel simulation in real-time:
"What if we used a different TP level? A different SL?"

This continuous, real-time back-testing provides immediate feedback
on the quality of the current decision and can be used to dynamically
manage the trade.

Features:
- Parallel trade simulations
- Alternative scenario testing
- Real-time feedback
- Dynamic trade management
- Optimal exit discovery
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import statistics
import copy

logger = logging.getLogger(__name__)


class TradeOutcome(Enum):
    """Possible trade outcomes."""
    OPEN = "open"
    TAKE_PROFIT = "take_profit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TIME_EXIT = "time_exit"
    MANUAL_EXIT = "manual_exit"


class ScenarioType(Enum):
    """Types of alternative scenarios."""
    TIGHTER_STOP = "tighter_stop"
    WIDER_STOP = "wider_stop"
    TIGHTER_TARGET = "tighter_target"
    WIDER_TARGET = "wider_target"
    TRAILING_STOP = "trailing_stop"
    BREAKEVEN_STOP = "breakeven_stop"
    PARTIAL_EXIT = "partial_exit"
    TIME_BASED_EXIT = "time_based_exit"


@dataclass
class TradeParameters:
    """Parameters for a trade."""
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    direction: str  # 'LONG' or 'SHORT'
    entry_time: datetime
    
    @property
    def risk(self) -> float:
        """Calculate risk in price units."""
        return abs(self.entry_price - self.stop_loss)
    
    @property
    def reward(self) -> float:
        """Calculate reward in price units."""
        return abs(self.take_profit - self.entry_price)
    
    @property
    def risk_reward_ratio(self) -> float:
        """Calculate R:R ratio."""
        try:
            if self.risk > 0:
                return self.reward / self.risk
            return 0
        except Exception as e:
            logger.error(f"Error in risk_reward_ratio: {e}")
            raise


@dataclass
class AlternativeScenario:
    """Alternative trade scenario."""
    scenario_id: str
    scenario_type: ScenarioType
    parameters: TradeParameters
    description: str
    
    # Simulation results
    current_pnl: float = 0
    max_pnl: float = 0
    min_pnl: float = 0
    outcome: TradeOutcome = TradeOutcome.OPEN
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type.value,
            'description': self.description,
            'stop_loss': self.parameters.stop_loss,
            'take_profit': self.parameters.take_profit,
            'current_pnl': self.current_pnl,
            'max_pnl': self.max_pnl,
            'min_pnl': self.min_pnl,
            'outcome': self.outcome.value,
            'exit_price': self.exit_price
        }


@dataclass
class SchrodingerTrade:
    """
    A trade with parallel alternative scenarios.
    """
    trade_id: str
    symbol: str
    actual_trade: TradeParameters
    scenarios: List[AlternativeScenario]
    
    # Actual trade tracking
    current_price: float = 0
    actual_pnl: float = 0
    actual_max_pnl: float = 0
    actual_min_pnl: float = 0
    actual_outcome: TradeOutcome = TradeOutcome.OPEN
    
    # Analysis
    best_scenario: Optional[str] = None
    worst_scenario: Optional[str] = None
    optimal_exit_price: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'actual_pnl': self.actual_pnl,
            'actual_outcome': self.actual_outcome.value,
            'scenarios_count': len(self.scenarios),
            'best_scenario': self.best_scenario,
            'worst_scenario': self.worst_scenario,
            'optimal_exit_price': self.optimal_exit_price
        }


@dataclass
class TradeRecommendation:
    """Recommendation based on scenario analysis."""
    action: str  # 'HOLD', 'MOVE_STOP', 'TAKE_PARTIAL', 'EXIT'
    confidence: float
    reasoning: str
    suggested_stop: Optional[float] = None
    suggested_target: Optional[float] = None
    suggested_exit_pct: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action': self.action,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'suggested_stop': self.suggested_stop,
            'suggested_target': self.suggested_target,
            'suggested_exit_pct': self.suggested_exit_pct
        }


class ScenarioGenerator:
    """
    Generates alternative scenarios for a trade.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Scenario multipliers
            self.stop_multipliers = self.config.get('stop_multipliers', [0.5, 0.75, 1.25, 1.5])
            self.target_multipliers = self.config.get('target_multipliers', [0.5, 0.75, 1.25, 1.5, 2.0])
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate(self, trade: TradeParameters) -> List[AlternativeScenario]:
        """Generate alternative scenarios."""
        try:
            scenarios = []
            scenario_num = 0
        
            # Stop loss variations
            for mult in self.stop_multipliers:
                scenario_num += 1
                new_stop = self._adjust_stop(trade, mult)
            
                scenario_type = ScenarioType.TIGHTER_STOP if mult < 1 else ScenarioType.WIDER_STOP
            
                scenarios.append(AlternativeScenario(
                    scenario_id=f"S{scenario_num}",
                    scenario_type=scenario_type,
                    parameters=TradeParameters(
                        entry_price=trade.entry_price,
                        stop_loss=new_stop,
                        take_profit=trade.take_profit,
                        position_size=trade.position_size,
                        direction=trade.direction,
                        entry_time=trade.entry_time
                    ),
                    description=f"Stop at {mult:.0%} of original ({new_stop:.5f})"
                ))
        
            # Take profit variations
            for mult in self.target_multipliers:
                scenario_num += 1
                new_target = self._adjust_target(trade, mult)
            
                scenario_type = ScenarioType.TIGHTER_TARGET if mult < 1 else ScenarioType.WIDER_TARGET
            
                scenarios.append(AlternativeScenario(
                    scenario_id=f"S{scenario_num}",
                    scenario_type=scenario_type,
                    parameters=TradeParameters(
                        entry_price=trade.entry_price,
                        stop_loss=trade.stop_loss,
                        take_profit=new_target,
                        position_size=trade.position_size,
                        direction=trade.direction,
                        entry_time=trade.entry_time
                    ),
                    description=f"Target at {mult:.0%} of original ({new_target:.5f})"
                ))
        
            # Trailing stop scenario
            scenario_num += 1
            scenarios.append(AlternativeScenario(
                scenario_id=f"S{scenario_num}",
                scenario_type=ScenarioType.TRAILING_STOP,
                parameters=TradeParameters(
                    entry_price=trade.entry_price,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit * 2,  # Extended target
                    position_size=trade.position_size,
                    direction=trade.direction,
                    entry_time=trade.entry_time
                ),
                description="Trailing stop (1R trail after 1R profit)"
            ))
        
            # Breakeven stop scenario
            scenario_num += 1
            scenarios.append(AlternativeScenario(
                scenario_id=f"S{scenario_num}",
                scenario_type=ScenarioType.BREAKEVEN_STOP,
                parameters=TradeParameters(
                    entry_price=trade.entry_price,
                    stop_loss=trade.stop_loss,
                    take_profit=trade.take_profit,
                    position_size=trade.position_size,
                    direction=trade.direction,
                    entry_time=trade.entry_time
                ),
                description="Move to breakeven at 1R profit"
            ))
        
            # Partial exit scenario
            scenario_num += 1
            partial_target = trade.entry_price + (trade.take_profit - trade.entry_price) * 0.5
            if trade.direction == 'SHORT':
                partial_target = trade.entry_price - (trade.entry_price - trade.take_profit) * 0.5
        
            scenarios.append(AlternativeScenario(
                scenario_id=f"S{scenario_num}",
                scenario_type=ScenarioType.PARTIAL_EXIT,
                parameters=TradeParameters(
                    entry_price=trade.entry_price,
                    stop_loss=trade.stop_loss,
                    take_profit=partial_target,
                    position_size=trade.position_size * 0.5,  # 50% position
                    direction=trade.direction,
                    entry_time=trade.entry_time
                ),
                description="50% exit at 50% of target"
            ))
        
            return scenarios
        except Exception as e:
            logger.error(f"Error in generate: {e}")
            raise
    
    def _adjust_stop(self, trade: TradeParameters, multiplier: float) -> float:
        """Adjust stop loss by multiplier."""
        try:
            risk = trade.risk
            new_risk = risk * multiplier
        
            if trade.direction == 'LONG':
                return trade.entry_price - new_risk
            else:
                return trade.entry_price + new_risk
        except Exception as e:
            logger.error(f"Error in _adjust_stop: {e}")
            raise
    
    def _adjust_target(self, trade: TradeParameters, multiplier: float) -> float:
        """Adjust take profit by multiplier."""
        try:
            reward = trade.reward
            new_reward = reward * multiplier
        
            if trade.direction == 'LONG':
                return trade.entry_price + new_reward
            else:
                return trade.entry_price - new_reward
        except Exception as e:
            logger.error(f"Error in _adjust_target: {e}")
            raise


class ScenarioSimulator:
    """
    Simulates scenarios in real-time.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(
        self,
        scenario: AlternativeScenario,
        current_price: float,
        high_price: float,
        low_price: float
    ):
        """
        Update scenario with new price data.
        
        Args:
            scenario: Scenario to update
            current_price: Current price
            high_price: High since last update
            low_price: Low since last update
        """
        try:
            if scenario.outcome != TradeOutcome.OPEN:
                return  # Already closed
        
            params = scenario.parameters
        
            # Calculate current P&L
            if params.direction == 'LONG':
                scenario.current_pnl = (current_price - params.entry_price) * params.position_size
            
                # Check stop loss (using low)
                if low_price <= params.stop_loss:
                    scenario.outcome = TradeOutcome.STOP_LOSS
                    scenario.exit_price = params.stop_loss
                    scenario.exit_time = datetime.now()
                    scenario.current_pnl = (params.stop_loss - params.entry_price) * params.position_size
            
                # Check take profit (using high)
                elif high_price >= params.take_profit:
                    scenario.outcome = TradeOutcome.TAKE_PROFIT
                    scenario.exit_price = params.take_profit
                    scenario.exit_time = datetime.now()
                    scenario.current_pnl = (params.take_profit - params.entry_price) * params.position_size
        
            else:  # SHORT
                scenario.current_pnl = (params.entry_price - current_price) * params.position_size
            
                # Check stop loss (using high)
                if high_price >= params.stop_loss:
                    scenario.outcome = TradeOutcome.STOP_LOSS
                    scenario.exit_price = params.stop_loss
                    scenario.exit_time = datetime.now()
                    scenario.current_pnl = (params.entry_price - params.stop_loss) * params.position_size
            
                # Check take profit (using low)
                elif low_price <= params.take_profit:
                    scenario.outcome = TradeOutcome.TAKE_PROFIT
                    scenario.exit_price = params.take_profit
                    scenario.exit_time = datetime.now()
                    scenario.current_pnl = (params.entry_price - params.take_profit) * params.position_size
        
            # Update max/min P&L
            scenario.max_pnl = max(scenario.max_pnl, scenario.current_pnl)
            scenario.min_pnl = min(scenario.min_pnl, scenario.current_pnl)
        
            # Handle special scenarios
            self._handle_special_scenarios(scenario, current_price, high_price, low_price)
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _handle_special_scenarios(
        self,
        scenario: AlternativeScenario,
        current_price: float,
        high_price: float,
        low_price: float
    ):
        """Handle special scenario types."""
        try:
            params = scenario.parameters
        
            # Trailing stop
            if scenario.scenario_type == ScenarioType.TRAILING_STOP:
                if params.direction == 'LONG':
                    # Trail stop if in profit
                    if scenario.max_pnl > params.risk * params.position_size:
                        trail_stop = high_price - params.risk
                        if trail_stop > params.stop_loss:
                            params.stop_loss = trail_stop
                else:
                    if scenario.max_pnl > params.risk * params.position_size:
                        trail_stop = low_price + params.risk
                        if trail_stop < params.stop_loss:
                            params.stop_loss = trail_stop
        
            # Breakeven stop
            elif scenario.scenario_type == ScenarioType.BREAKEVEN_STOP:
                if params.direction == 'LONG':
                    if scenario.max_pnl >= params.risk * params.position_size:
                        params.stop_loss = max(params.stop_loss, params.entry_price)
                else:
                    if scenario.max_pnl >= params.risk * params.position_size:
                        params.stop_loss = min(params.stop_loss, params.entry_price)
        except Exception as e:
            logger.error(f"Error in _handle_special_scenarios: {e}")
            raise


class SchrodingerTradeManager:
    """
    Main Schrödinger's Trade management system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Components
            self.scenario_generator = ScenarioGenerator(config)
            self.simulator = ScenarioSimulator(config)
        
            # Active trades
            self.active_trades: Dict[str, SchrodingerTrade] = {}
        
            # History
            self.completed_trades: deque = deque(maxlen=100)
        
            logger.info("SchrodingerTradeManager initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def open_trade(
        self,
        trade_id: str,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        direction: str
    ) -> SchrodingerTrade:
        """
        Open a new Schrödinger trade with parallel scenarios.
        
        Returns:
            SchrodingerTrade with all scenarios
        """
        # Create actual trade parameters
        try:
            actual_trade = TradeParameters(
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                direction=direction,
                entry_time=datetime.now()
            )
        
            # Generate alternative scenarios
            scenarios = self.scenario_generator.generate(actual_trade)
        
            # Create Schrödinger trade
            schrodinger_trade = SchrodingerTrade(
                trade_id=trade_id,
                symbol=symbol,
                actual_trade=actual_trade,
                scenarios=scenarios,
                current_price=entry_price
            )
        
            self.active_trades[trade_id] = schrodinger_trade
        
            logger.info(
                f"Opened Schrödinger trade {trade_id} with {len(scenarios)} parallel scenarios"
            )
        
            return schrodinger_trade
        except Exception as e:
            logger.error(f"Error in open_trade: {e}")
            raise
    
    def update_price(
        self,
        trade_id: str,
        current_price: float,
        high_price: Optional[float] = None,
        low_price: Optional[float] = None
    ):
        """
        Update trade with new price data.
        
        Args:
            trade_id: Trade ID
            current_price: Current price
            high_price: High since last update
            low_price: Low since last update
        """
        try:
            if trade_id not in self.active_trades:
                return
        
            trade = self.active_trades[trade_id]
        
            high = high_price or current_price
            low = low_price or current_price
        
            trade.current_price = current_price
        
            # Update actual trade
            params = trade.actual_trade
            if params.direction == 'LONG':
                trade.actual_pnl = (current_price - params.entry_price) * params.position_size
            
                if low <= params.stop_loss:
                    trade.actual_outcome = TradeOutcome.STOP_LOSS
                elif high >= params.take_profit:
                    trade.actual_outcome = TradeOutcome.TAKE_PROFIT
            else:
                trade.actual_pnl = (params.entry_price - current_price) * params.position_size
            
                if high >= params.stop_loss:
                    trade.actual_outcome = TradeOutcome.STOP_LOSS
                elif low <= params.take_profit:
                    trade.actual_outcome = TradeOutcome.TAKE_PROFIT
        
            trade.actual_max_pnl = max(trade.actual_max_pnl, trade.actual_pnl)
            trade.actual_min_pnl = min(trade.actual_min_pnl, trade.actual_pnl)
        
            # Update all scenarios
            for scenario in trade.scenarios:
                self.simulator.update(scenario, current_price, high, low)
        
            # Analyze scenarios
            self._analyze_scenarios(trade)
        except Exception as e:
            logger.error(f"Error in update_price: {e}")
            raise
    
    def _analyze_scenarios(self, trade: SchrodingerTrade):
        """Analyze scenario performance."""
        try:
            if not trade.scenarios:
                return
        
            # Find best and worst scenarios
            best_pnl = float('-inf')
            worst_pnl = float('inf')
            best_scenario = None
            worst_scenario = None
        
            for scenario in trade.scenarios:
                if scenario.current_pnl > best_pnl:
                    best_pnl = scenario.current_pnl
                    best_scenario = scenario.scenario_id
                if scenario.current_pnl < worst_pnl:
                    worst_pnl = scenario.current_pnl
                    worst_scenario = scenario.scenario_id
        
            trade.best_scenario = best_scenario
            trade.worst_scenario = worst_scenario
        
            # Find optimal exit price
            profitable_exits = [
                s.exit_price for s in trade.scenarios
                if s.outcome == TradeOutcome.TAKE_PROFIT and s.exit_price
            ]
        
            if profitable_exits:
                trade.optimal_exit_price = statistics.mean(profitable_exits)
        except Exception as e:
            logger.error(f"Error in _analyze_scenarios: {e}")
            raise
    
    def get_recommendation(self, trade_id: str) -> TradeRecommendation:
        """
        Get recommendation based on scenario analysis.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            TradeRecommendation
        """
        try:
            if trade_id not in self.active_trades:
                return TradeRecommendation(
                    action='HOLD',
                    confidence=0.5,
                    reasoning="Trade not found"
                )
        
            trade = self.active_trades[trade_id]
        
            # Analyze scenario outcomes
            tp_count = sum(1 for s in trade.scenarios if s.outcome == TradeOutcome.TAKE_PROFIT)
            sl_count = sum(1 for s in trade.scenarios if s.outcome == TradeOutcome.STOP_LOSS)
            open_count = sum(1 for s in trade.scenarios if s.outcome == TradeOutcome.OPEN)
        
            total = len(trade.scenarios)
        
            # Calculate average P&L by scenario type
            tighter_stop_pnl = [
                s.current_pnl for s in trade.scenarios
                if s.scenario_type == ScenarioType.TIGHTER_STOP
            ]
            wider_stop_pnl = [
                s.current_pnl for s in trade.scenarios
                if s.scenario_type == ScenarioType.WIDER_STOP
            ]
        
            # Generate recommendation
            if sl_count > total * 0.6:
                # Most scenarios hit stop loss
                return TradeRecommendation(
                    action='EXIT',
                    confidence=0.8,
                    reasoning=f"{sl_count}/{total} scenarios hit stop loss - consider exiting"
                )
        
            if tp_count > total * 0.5:
                # Many scenarios hit take profit
                return TradeRecommendation(
                    action='TAKE_PARTIAL',
                    confidence=0.7,
                    reasoning=f"{tp_count}/{total} scenarios hit target - consider partial exit",
                    suggested_exit_pct=0.5
                )
        
            # Check if tighter stops performed better
            if tighter_stop_pnl and wider_stop_pnl:
                avg_tighter = statistics.mean(tighter_stop_pnl)
                avg_wider = statistics.mean(wider_stop_pnl)
            
                if avg_tighter > avg_wider * 1.2:
                    # Tighter stops better
                    tighter_scenarios = [
                        s for s in trade.scenarios
                        if s.scenario_type == ScenarioType.TIGHTER_STOP
                    ]
                    if tighter_scenarios:
                        best_tighter = max(tighter_scenarios, key=lambda s: s.current_pnl)
                        return TradeRecommendation(
                            action='MOVE_STOP',
                            confidence=0.65,
                            reasoning="Tighter stop scenarios performing better",
                            suggested_stop=best_tighter.parameters.stop_loss
                        )
        
            # Check breakeven scenario
            be_scenarios = [
                s for s in trade.scenarios
                if s.scenario_type == ScenarioType.BREAKEVEN_STOP
            ]
            if be_scenarios and trade.actual_pnl > 0:
                be = be_scenarios[0]
                if be.current_pnl > trade.actual_pnl:
                    return TradeRecommendation(
                        action='MOVE_STOP',
                        confidence=0.6,
                        reasoning="Breakeven stop scenario outperforming",
                        suggested_stop=trade.actual_trade.entry_price
                    )
        
            return TradeRecommendation(
                action='HOLD',
                confidence=0.5,
                reasoning=f"Scenarios mixed: {tp_count} TP, {sl_count} SL, {open_count} open"
            )
        except Exception as e:
            logger.error(f"Error in get_recommendation: {e}")
            raise
    
    def close_trade(self, trade_id: str, exit_price: float) -> Optional[Dict[str, Any]]:
        """
        Close a trade and get final analysis.
        
        Returns:
            Analysis of actual vs scenarios
        """
        try:
            if trade_id not in self.active_trades:
                return None
        
            trade = self.active_trades[trade_id]
        
            # Final update
            self.update_price(trade_id, exit_price)
        
            # Calculate final P&L
            params = trade.actual_trade
            if params.direction == 'LONG':
                final_pnl = (exit_price - params.entry_price) * params.position_size
            else:
                final_pnl = (params.entry_price - exit_price) * params.position_size
        
            trade.actual_pnl = final_pnl
            trade.actual_outcome = TradeOutcome.MANUAL_EXIT
        
            # Compare with scenarios
            better_scenarios = [
                s for s in trade.scenarios
                if s.current_pnl > final_pnl
            ]
        
            worse_scenarios = [
                s for s in trade.scenarios
                if s.current_pnl < final_pnl
            ]
        
            analysis = {
                'trade_id': trade_id,
                'actual_pnl': final_pnl,
                'scenarios_that_beat_actual': len(better_scenarios),
                'scenarios_worse_than_actual': len(worse_scenarios),
                'best_scenario': trade.best_scenario,
                'best_scenario_pnl': max(s.current_pnl for s in trade.scenarios) if trade.scenarios else 0,
                'optimal_exit_was': trade.optimal_exit_price,
                'lessons': self._extract_lessons(trade, final_pnl)
            }
        
            # Move to completed
            self.completed_trades.append(trade)
            del self.active_trades[trade_id]
        
            return analysis
        except Exception as e:
            logger.error(f"Error in close_trade: {e}")
            raise
    
    def _extract_lessons(self, trade: SchrodingerTrade, actual_pnl: float) -> List[str]:
        """Extract lessons from scenario comparison."""
        try:
            lessons = []
        
            # Find best performing scenario type
            type_performance: Dict[ScenarioType, List[float]] = {}
            for s in trade.scenarios:
                if s.scenario_type not in type_performance:
                    type_performance[s.scenario_type] = []
                type_performance[s.scenario_type].append(s.current_pnl)
        
            best_type = None
            best_avg = float('-inf')
            for stype, pnls in type_performance.items():
                avg = statistics.mean(pnls)
                if avg > best_avg:
                    best_avg = avg
                    best_type = stype
        
            if best_type and best_avg > actual_pnl:
                lessons.append(f"Consider using {best_type.value} approach next time")
        
            # Check if trailing stop would have helped
            trailing = [s for s in trade.scenarios if s.scenario_type == ScenarioType.TRAILING_STOP]
            if trailing and trailing[0].current_pnl > actual_pnl * 1.2:
                lessons.append("Trailing stop would have captured more profit")
        
            # Check if partial exit would have helped
            partial = [s for s in trade.scenarios if s.scenario_type == ScenarioType.PARTIAL_EXIT]
            if partial and partial[0].current_pnl > actual_pnl:
                lessons.append("Partial exit strategy would have been beneficial")
        
            return lessons
        except Exception as e:
            logger.error(f"Error in _extract_lessons: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            'active_trades': len(self.active_trades),
            'completed_trades': len(self.completed_trades),
            'active_trade_ids': list(self.active_trades.keys()),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_schrodinger_manager(config: Optional[Dict] = None) -> SchrodingerTradeManager:
    """Create SchrodingerTradeManager instance."""
    return SchrodingerTradeManager(config)


# Example usage
if __name__ == "__main__":
    import random
    
    manager = create_schrodinger_manager()
    
    print("=" * 60)
    print("SCHRÖDINGER'S TRADE MODE")
    print("=" * 60)
    
    # Open a trade
    trade = manager.open_trade(
        trade_id="TRADE001",
        symbol="EURUSD",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        position_size=10000,
        direction='LONG'
    )
    
    print(f"\nOpened trade: {trade.trade_id}")
    print(f"Entry: {trade.actual_trade.entry_price}")
    print(f"Stop Loss: {trade.actual_trade.stop_loss}")
    print(f"Take Profit: {trade.actual_trade.take_profit}")
    print(f"R:R Ratio: {trade.actual_trade.risk_reward_ratio:.2f}")
    print(f"\nParallel Scenarios: {len(trade.scenarios)}")
    
    for scenario in trade.scenarios:
        print(f"  {scenario.scenario_id}: {scenario.description}")
    
    # Simulate price movement
    print("\n" + "=" * 60)
    print("SIMULATING PRICE MOVEMENT...")
    print("=" * 60)
    
    price = 1.1000
    for i in range(20):
        # Random walk with slight upward bias
        change = random.uniform(-0.0015, 0.0020)
        price += change
        
        high = price + random.uniform(0, 0.0010)
        low = price - random.uniform(0, 0.0010)
        
        manager.update_price("TRADE001", price, high, low)
        
        if i % 5 == 0:
            trade = manager.active_trades.get("TRADE001")
            if trade:
                print(f"\nBar {i}: Price={price:.5f}")
                print(f"  Actual P&L: ${trade.actual_pnl:.2f}")
                print(f"  Best Scenario: {trade.best_scenario}")
                
                # Get recommendation
                rec = manager.get_recommendation("TRADE001")
                print(f"  Recommendation: {rec.action} ({rec.confidence:.0%})")
                print(f"  Reasoning: {rec.reasoning}")
    
    # Close trade
    print("\n" + "=" * 60)
    print("CLOSING TRADE")
    print("=" * 60)
    
    analysis = manager.close_trade("TRADE001", price)
    
    if analysis:
        print(f"\nFinal Analysis:")
        print(f"  Actual P&L: ${analysis['actual_pnl']:.2f}")
        print(f"  Scenarios that beat actual: {analysis['scenarios_that_beat_actual']}")
        print(f"  Scenarios worse than actual: {analysis['scenarios_worse_than_actual']}")
        print(f"  Best scenario P&L: ${analysis['best_scenario_pnl']:.2f}")
        
        if analysis['lessons']:
            print(f"\n  Lessons Learned:")
            for lesson in analysis['lessons']:
                print(f"    - {lesson}")
