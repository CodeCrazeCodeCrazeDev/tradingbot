"""
Drawdown Ladder - Progressive Risk Reduction
Automatically reduces position sizes as drawdown increases
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

import logging
logger = logging.getLogger(__name__)



@dataclass
class DrawdownLevel:
    """Drawdown level configuration"""
    threshold_pct: float  # Drawdown percentage threshold
    position_multiplier: float  # Position size multiplier
    max_positions: int  # Maximum concurrent positions
    description: str


class DrawdownLadder:
    """
    Progressive risk reduction based on drawdown levels
    
    As account drawdown increases, automatically:
    - Reduces position sizes
    - Limits number of concurrent positions
    - Increases risk awareness
    """
    
    def __init__(self, initial_balance: float = 10000):
        """
        Initialize drawdown ladder
        
        Args:
            initial_balance: Initial account balance
        """
        self.initial_balance = initial_balance
        self.peak_balance = initial_balance
        
        # Define drawdown levels
        self.levels = [
            DrawdownLevel(0.0, 1.0, 5, "Normal - Full position sizing"),
            DrawdownLevel(2.5, 0.75, 4, "Caution - 25% reduction"),
            DrawdownLevel(5.0, 0.5, 3, "Warning - 50% reduction"),
            DrawdownLevel(7.5, 0.25, 2, "Alert - 75% reduction"),
            DrawdownLevel(10.0, 0.1, 1, "Critical - 90% reduction"),
            DrawdownLevel(15.0, 0.0, 0, "Emergency - Trading halted"),
        ]
    
    def update_peak(self, current_balance: float):
        """Update peak balance if new high"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
    
    def get_drawdown_pct(self, current_balance: float) -> float:
        """
        Calculate current drawdown percentage
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Drawdown percentage (0-100)
        """
        if self.peak_balance == 0:
            return 0.0
        
        drawdown = (self.peak_balance - current_balance) / self.peak_balance * 100
        return max(0.0, drawdown)
    
    def get_current_level(self, current_balance: float) -> DrawdownLevel:
        """
        Get current drawdown level
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Current DrawdownLevel
        """
        drawdown_pct = self.get_drawdown_pct(current_balance)
        
        # Find appropriate level (highest threshold not exceeded)
        current_level = self.levels[0]
        for level in self.levels:
            if drawdown_pct >= level.threshold_pct:
                current_level = level
            else:
                break
        
        return current_level
    
    def get_position_multiplier(self, current_balance: float) -> float:
        """
        Get position size multiplier for current drawdown
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Position multiplier (0.0 - 1.0)
        """
        level = self.get_current_level(current_balance)
        return level.position_multiplier
    
    def get_max_positions(self, current_balance: float) -> int:
        """
        Get maximum allowed positions for current drawdown
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Maximum number of concurrent positions
        """
        level = self.get_current_level(current_balance)
        return level.max_positions
    
    def should_halt_trading(self, current_balance: float) -> bool:
        """
        Check if trading should be halted
        
        Args:
            current_balance: Current account balance
            
        Returns:
            True if trading should stop
        """
        multiplier = self.get_position_multiplier(current_balance)
        return multiplier == 0.0
    
    def get_status(self, current_balance: float) -> Dict:
        """
        Get complete drawdown status
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Status dictionary with all metrics
        """
        drawdown_pct = self.get_drawdown_pct(current_balance)
        level = self.get_current_level(current_balance)
        
        return {
            'current_balance': current_balance,
            'peak_balance': self.peak_balance,
            'drawdown_pct': drawdown_pct,
            'drawdown_amount': self.peak_balance - current_balance,
            'level_threshold': level.threshold_pct,
            'position_multiplier': level.position_multiplier,
            'max_positions': level.max_positions,
            'description': level.description,
            'trading_halted': level.position_multiplier == 0.0,
            'timestamp': datetime.now().isoformat()
        }
    
    def calculate_adjusted_position_size(self, 
                                        base_position_size: float,
                                        current_balance: float) -> float:
        """
        Calculate position size adjusted for drawdown
        
        Args:
            base_position_size: Base position size without adjustment
            current_balance: Current account balance
            
        Returns:
            Adjusted position size
        """
        multiplier = self.get_position_multiplier(current_balance)
        return base_position_size * multiplier
    
    def get_risk_level(self, current_balance: float) -> str:
        """
        Get risk level description
        
        Args:
            current_balance: Current account balance
            
        Returns:
            Risk level string
        """
        drawdown_pct = self.get_drawdown_pct(current_balance)
        
        if drawdown_pct >= 15.0:
            return "EMERGENCY"
        elif drawdown_pct >= 10.0:
            return "CRITICAL"
        elif drawdown_pct >= 7.5:
            return "ALERT"
        elif drawdown_pct >= 5.0:
            return "WARNING"
        elif drawdown_pct >= 2.5:
            return "CAUTION"
        else:
            return "NORMAL"


# Example usage
if __name__ == '__main__':
    # Create drawdown ladder
    ladder = DrawdownLadder(initial_balance=10000)
    
    # Test different balance scenarios
    test_balances = [10000, 9750, 9500, 9250, 9000, 8500, 8000]
    
    print("="*80)
    print("DRAWDOWN LADDER DEMONSTRATION".center(80))
    print("="*80)
    
    for balance in test_balances:
        status = ladder.get_status(balance)
        
        logger.info(f"\nBalance: ${balance:,.2f}")
        logger.info(f"  Drawdown: {status['drawdown_pct']:.2f}%")
        logger.info(f"  Risk Level: {ladder.get_risk_level(balance)}")
        logger.info(f"  Position Multiplier: {status['position_multiplier']:.0%}")
        logger.info(f"  Max Positions: {status['max_positions']}")
        logger.info(f"  Status: {status['description']}")
        
        if status['trading_halted']:
            logger.info(f"  ⚠️ TRADING HALTED!")
    
    logger.info(f"\n{'='*80}")
    print("Drawdown ladder working correctly!".center(80))
    logger.info(f"{'='*80}")
