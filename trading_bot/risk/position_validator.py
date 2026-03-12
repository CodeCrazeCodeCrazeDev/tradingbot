
import logging
from typing import Dict, List, Optional, Any, Tuple
logger = logging.getLogger(__name__)

"""
Position Size Validator
Ensures position sizes are within acceptable limits
"""

class PositionSizeValidator:
    """Validates and caps position sizes for safety"""
    
    def __init__(self, max_lots: float = 1.0, max_risk_pct: float = 2.0):
        """
        Initialize validator
        
        Args:
            max_lots: Maximum position size in lots (default: 1.0)
            max_risk_pct: Maximum risk per trade as % of account (default: 2.0%)
        """
        try:
            self.max_lots = max_lots
            self.max_risk_pct = max_risk_pct
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(self, lot_size: float, account_equity: float, 
                 stop_loss_pips: float, pip_value: float = 10.0) -> float:
        """
        Validate and cap position size
        
        Args:
            lot_size: Calculated lot size
            account_equity: Current account equity
            stop_loss_pips: Stop loss in pips
            pip_value: Value of 1 pip per lot (default: $10 for EURUSD)
        
        Returns:
            Validated lot size (capped if necessary)
        """
        # Cap by maximum lots
        try:
            if lot_size > self.max_lots:
                logger.info(f"[VALIDATOR] Position size {lot_size:.2f} lots exceeds max {self.max_lots} lots - capping")
                lot_size = self.max_lots
        
            # Cap by maximum risk percentage
            risk_usd = lot_size * stop_loss_pips * pip_value
            risk_pct = (risk_usd / account_equity) * 100
        
            if risk_pct > self.max_risk_pct:
                max_risk_usd = account_equity * (self.max_risk_pct / 100)
                max_lot_size = max_risk_usd / (stop_loss_pips * pip_value)
                logger.info(f"[VALIDATOR] Risk {risk_pct:.2f}% exceeds max {self.max_risk_pct}% - capping to {max_lot_size:.2f} lots")
                lot_size = max_lot_size
        
            # Minimum position size
            if lot_size < 0.01:
                logger.info(f"[VALIDATOR] Position size {lot_size:.4f} lots below minimum 0.01 lots - setting to 0.01")
                lot_size = 0.01
        
            return lot_size
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
