"""
AlphaAlgo Core - Integration Module

Provides integration points between the AlphaAlgo Core capital governance system
and the existing trading system components:
- MasterOrchestrator
- PortfolioRiskManager
- TradingEngine

This module ensures that the capital governance rules are enforced throughout
the trading system, with no exceptions or overrides.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from .alphaalgo_core import AlphaAlgoCore, create_alphaalgo_core
from .capital_governance import CapitalGovernanceResult

logger = logging.getLogger(__name__)


class MasterOrchestratorIntegration:
    """
    Integration with the MasterOrchestrator component.
    
    Ensures that all trading decisions are filtered through the capital governance system.
    """
    
    def __init__(self, alphaalgo_core: AlphaAlgoCore):
        try:
            self.alphaalgo_core = alphaalgo_core
            logger.info("MasterOrchestrator integration initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def filter_opportunities(
        self,
        opportunities: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Filter trading opportunities based on capital governance rules.
        
        Args:
            opportunities: List of trading opportunities
            market_data: Current market data
            
        Returns:
            Filtered list of opportunities
        """
        try:
            filtered_opportunities = []
        
            for opportunity in opportunities:
                # Extract strategy ID and symbol
                strategy_id = opportunity.get("strategy_id", "unknown")
                symbol = opportunity.get("symbol", "unknown")
            
                # Evaluate tradability
                result = await self.alphaalgo_core.evaluate_tradability(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    market_data=market_data
                )
            
                if result.is_tradable:
                    # Apply exposure limit
                    opportunity["max_exposure"] = result.max_exposure
                    filtered_opportunities.append(opportunity)
                else:
                    logger.info(f"Opportunity filtered out: {strategy_id} on {symbol} - {result.reason}")
        
            return filtered_opportunities
        except Exception as e:
            logger.error(f"Error in filter_opportunities: {e}")
            raise
    
    async def validate_decisions(
        self,
        decisions: List[Dict[str, Any]],
        market_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Validate trading decisions based on capital governance rules.
        
        Args:
            decisions: List of trading decisions
            market_data: Current market data
            
        Returns:
            Filtered list of decisions
        """
        try:
            validated_decisions = []
        
            for decision in decisions:
                # Extract strategy ID and symbol
                strategy_id = decision.get("strategy_id", "unknown")
                symbol = decision.get("symbol", "unknown")
            
                # Evaluate tradability
                result = await self.alphaalgo_core.evaluate_tradability(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    market_data=market_data
                )
            
                if result.is_tradable:
                    # Apply exposure limit
                    current_exposure = decision.get("exposure", 0.0)
                    if current_exposure > result.max_exposure:
                        decision["exposure"] = result.max_exposure
                        decision["exposure_limited"] = True
                        decision["exposure_reason"] = result.reason
                
                    validated_decisions.append(decision)
                else:
                    logger.info(f"Decision rejected: {strategy_id} on {symbol} - {result.reason}")
        
            return validated_decisions
        except Exception as e:
            logger.error(f"Error in validate_decisions: {e}")
            raise
    
    def register_strategies(self, strategies: Dict[str, Dict[str, Any]]) -> None:
        """
        Register strategies with the AlphaAlgo Core system.
        
        Args:
            strategies: Dictionary of strategy configurations keyed by strategy ID
        """
        try:
            for strategy_id, strategy_config in strategies.items():
                self.alphaalgo_core.register_strategy(strategy_id, strategy_config)
        except Exception as e:
            logger.error(f"Error in register_strategies: {e}")
            raise


class PortfolioRiskManagerIntegration:
    """
    Integration with the PortfolioRiskManager component.
    
    Ensures that risk management is aligned with capital governance rules.
    """
    
    def __init__(self, alphaalgo_core: AlphaAlgoCore):
        try:
            self.alphaalgo_core = alphaalgo_core
            logger.info("PortfolioRiskManager integration initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def validate_trade(
        self,
        trade: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Tuple[bool, str, float]:
        """
        Validate a trade based on capital governance rules.
        
        Args:
            trade: Trade details
            market_data: Current market data
            
        Returns:
            Tuple of (is_valid, reason, max_exposure)
        """
        # Extract strategy ID and symbol
        try:
            strategy_id = trade.get("strategy_id", "unknown")
            symbol = trade.get("symbol", "unknown")
        
            # Evaluate tradability
            result = await self.alphaalgo_core.evaluate_tradability(
                strategy_id=strategy_id,
                symbol=symbol,
                market_data=market_data
            )
        
            return result.is_tradable, result.reason, result.max_exposure
        except Exception as e:
            logger.error(f"Error in validate_trade: {e}")
            raise
    
    async def adjust_position_size(
        self,
        position_size: float,
        strategy_id: str,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> float:
        """
        Adjust position size based on capital governance rules.
        
        Args:
            position_size: Original position size
            strategy_id: Strategy identifier
            symbol: Market symbol
            market_data: Current market data
            
        Returns:
            Adjusted position size
        """
        # Evaluate tradability
        try:
            result = await self.alphaalgo_core.evaluate_tradability(
                strategy_id=strategy_id,
                symbol=symbol,
                market_data=market_data
            )
        
            if not result.is_tradable:
                return 0.0
        
            # Calculate maximum position size based on exposure limit
            max_position = position_size * result.max_exposure
        
            return min(position_size, max_position)
        except Exception as e:
            logger.error(f"Error in adjust_position_size: {e}")
            raise


class TradingEngineIntegration:
    """
    Integration with the TradingEngine component.
    
    Ensures that all signals are validated through the capital governance system.
    """
    
    def __init__(self, alphaalgo_core: AlphaAlgoCore):
        try:
            self.alphaalgo_core = alphaalgo_core
            logger.info("TradingEngine integration initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def validate_signal(
        self,
        signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Tuple[bool, str, float]:
        """
        Validate a trading signal based on capital governance rules.
        
        Args:
            signal: Signal details
            market_data: Current market data
            
        Returns:
            Tuple of (is_valid, reason, max_exposure)
        """
        # Extract strategy ID and symbol
        try:
            strategy_id = signal.get("strategy_id", "unknown")
            symbol = signal.get("symbol", "unknown")
        
            # Evaluate tradability
            result = await self.alphaalgo_core.evaluate_tradability(
                strategy_id=strategy_id,
                symbol=symbol,
                market_data=market_data
            )
        
            return result.is_tradable, result.reason, result.max_exposure
        except Exception as e:
            logger.error(f"Error in validate_signal: {e}")
            raise
    
    async def process_market_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a market event through the anti-learning firewall.
        
        Args:
            event: Market event data
            
        Returns:
            bool: True if the event should be included in learning, False if it should be excluded
        """
        return await self.alphaalgo_core.process_market_event(event)
    
    async def update_behavior(
        self,
        strategy_id: str,
        behavior_data: Dict[str, Any]
    ) -> None:
        """
        Update behavior data for continuous validity monitoring.
        
        Args:
            strategy_id: Strategy identifier
            behavior_data: Behavior metrics
        """
        try:
            await self.alphaalgo_core.update_behavior(strategy_id, behavior_data)
        except Exception as e:
            logger.error(f"Error in update_behavior: {e}")
            raise


class AlphaAlgoCoreIntegration:
    """
    Main integration class for the AlphaAlgo Core system.
    
    Provides access to all integration points.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Create AlphaAlgo Core instance
        try:
            self.alphaalgo_core = create_alphaalgo_core(config_path)
        
            # Create integration components
            self.master_orchestrator = MasterOrchestratorIntegration(self.alphaalgo_core)
            self.portfolio_risk_manager = PortfolioRiskManagerIntegration(self.alphaalgo_core)
            self.trading_engine = TradingEngineIntegration(self.alphaalgo_core)
        
            logger.info("AlphaAlgo Core integration initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the AlphaAlgo Core system.
        
        Returns:
            Dict with system status information
        """
        return self.alphaalgo_core.get_status()


# Factory function for creating integration instance
def create_integration(config_path: Optional[str] = None) -> AlphaAlgoCoreIntegration:
    """
    Create an AlphaAlgo Core integration instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        AlphaAlgoCoreIntegration instance
    """
    return AlphaAlgoCoreIntegration(config_path)
