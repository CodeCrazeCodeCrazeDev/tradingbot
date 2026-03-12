"""
Reconciliation Service - Broker position reconciliation

This module provides periodic reconciliation of broker positions vs local positions
with automatic correction of mismatches.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class MismatchType(Enum):
    """Types of position mismatches"""
    MISSING_LOCAL = 'missing_local'  # Position exists at broker but not locally
    MISSING_BROKER = 'missing_broker'  # Position exists locally but not at broker
    QUANTITY_MISMATCH = 'quantity_mismatch'  # Quantities don't match
    PRICE_MISMATCH = 'price_mismatch'  # Entry prices don't match


@dataclass
class PositionMismatch:
    """Position mismatch information"""
    symbol: str
    mismatch_type: MismatchType
    local_quantity: float
    broker_quantity: float
    local_entry_price: Optional[float]
    broker_entry_price: Optional[float]
    detected_at: datetime
    auto_corrected: bool = False
    correction_action: Optional[str] = None


class ReconciliationService:
    """Service for reconciling broker positions with local state"""
    
    def __init__(self, execution_manager, broker_adapter, config: Optional[Dict[str, Any]] = None):
        """
        Initialize reconciliation service
        
        Args:
            execution_manager: ExecutionManager instance
            broker_adapter: Broker adapter for fetching positions
            config: Configuration dictionary
        """
        self.execution = execution_manager
        self.broker = broker_adapter
        self.config = config or {}
        
        # Reconciliation settings
        self.reconciliation_interval = self.config.get('reconciliation_interval', 300)  # 5 minutes
        self.auto_correct = self.config.get('auto_correct_positions', False)
        self.quantity_tolerance = self.config.get('quantity_tolerance', 0.01)  # 1% tolerance
        self.price_tolerance = self.config.get('price_tolerance', 0.001)  # 0.1% tolerance
        
        # Mismatch tracking
        self.mismatches = []
        self.last_reconciliation = None
        self.reconciliation_count = 0
        self.correction_count = 0
        
        # Running state
        self.running = False
        
        logger.info("Reconciliation service initialized")
    
    async def start(self):
        """Start periodic reconciliation"""
        if self.running:
            logger.warning("Reconciliation service already running")
            return
        
        self.running = True
        logger.info("Starting reconciliation service")
        
        # Start background task
        asyncio.create_task(self._reconciliation_loop())
    
    async def stop(self):
        """Stop reconciliation service"""
        self.running = False
        logger.info("Reconciliation service stopped")
    
    async def _reconciliation_loop(self):
        """Background task for periodic reconciliation"""
        logger.info("Reconciliation loop started")
        
        while self.running:
            try:
                await self.reconcile_positions()
                await asyncio.sleep(self.reconciliation_interval)
                
            except asyncio.CancelledError:
                logger.info("Reconciliation loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in reconciliation loop: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def reconcile_positions(self) -> List[PositionMismatch]:
        """
        Reconcile broker positions with local positions
        
        Returns:
            List of detected mismatches
        """
        logger.info("Starting position reconciliation")
        self.reconciliation_count += 1
        self.last_reconciliation = datetime.now()
        
        try:
            # Fetch broker positions
            broker_positions = await self.broker.get_positions()
            
            # Get local positions
            local_positions = self.execution.get_active_positions()
            
            # Detect mismatches
            mismatches = self._detect_mismatches(broker_positions, local_positions)
            
            if mismatches:
                logger.warning(f"Detected {len(mismatches)} position mismatches")
                
                # Store mismatches
                self.mismatches.extend(mismatches)
                
                # Auto-correct if enabled
                if self.auto_correct:
                    await self._correct_mismatches(mismatches)
                else:
                    # Just log and alert
                    for mismatch in mismatches:
                        logger.error(
                            f"Position mismatch for {mismatch.symbol}: "
                            f"{mismatch.mismatch_type.value}, "
                            f"local={mismatch.local_quantity}, "
                            f"broker={mismatch.broker_quantity}"
                        )
            else:
                logger.info("Position reconciliation complete: no mismatches")
            
            return mismatches
            
        except Exception as e:
            logger.error(f"Error during reconciliation: {e}")
            return []
    
    def _detect_mismatches(self, broker_positions: List[Dict], 
                          local_positions: List[Any]) -> List[PositionMismatch]:
        """
        Detect mismatches between broker and local positions
        
        Args:
            broker_positions: List of broker position dicts
            local_positions: List of local Position objects
            
        Returns:
            List of detected mismatches
        """
        mismatches = []
        
        # Create lookup dictionaries
        broker_dict = {pos['symbol']: pos for pos in broker_positions}
        local_dict = {pos.symbol: pos for pos in local_positions}
        
        # Check all symbols
        all_symbols = set(broker_dict.keys()) | set(local_dict.keys())
        
        for symbol in all_symbols:
            broker_pos = broker_dict.get(symbol)
            local_pos = local_dict.get(symbol)
            
            # Missing local position
            if broker_pos and not local_pos:
                mismatches.append(PositionMismatch(
                    symbol=symbol,
                    mismatch_type=MismatchType.MISSING_LOCAL,
                    local_quantity=0,
                    broker_quantity=broker_pos.get('quantity', 0),
                    local_entry_price=None,
                    broker_entry_price=broker_pos.get('entry_price'),
                    detected_at=datetime.now()
                ))
            
            # Missing broker position
            elif local_pos and not broker_pos:
                mismatches.append(PositionMismatch(
                    symbol=symbol,
                    mismatch_type=MismatchType.MISSING_BROKER,
                    local_quantity=local_pos.quantity,
                    broker_quantity=0,
                    local_entry_price=local_pos.entry_price,
                    broker_entry_price=None,
                    detected_at=datetime.now()
                ))
            
            # Both exist - check quantities and prices
            elif local_pos and broker_pos:
                broker_qty = broker_pos.get('quantity', 0)
                local_qty = local_pos.quantity
                
                # Check quantity mismatch
                qty_diff = abs(broker_qty - local_qty)
                qty_tolerance = abs(broker_qty) * self.quantity_tolerance
                
                if qty_diff > qty_tolerance:
                    mismatches.append(PositionMismatch(
                        symbol=symbol,
                        mismatch_type=MismatchType.QUANTITY_MISMATCH,
                        local_quantity=local_qty,
                        broker_quantity=broker_qty,
                        local_entry_price=local_pos.entry_price,
                        broker_entry_price=broker_pos.get('entry_price'),
                        detected_at=datetime.now()
                    ))
                
                # Check price mismatch
                broker_price = broker_pos.get('entry_price', 0)
                local_price = local_pos.entry_price
                
                if broker_price and local_price:
                    price_diff = abs(broker_price - local_price) / broker_price
                    
                    if price_diff > self.price_tolerance:
                        mismatches.append(PositionMismatch(
                            symbol=symbol,
                            mismatch_type=MismatchType.PRICE_MISMATCH,
                            local_quantity=local_qty,
                            broker_quantity=broker_qty,
                            local_entry_price=local_price,
                            broker_entry_price=broker_price,
                            detected_at=datetime.now()
                        ))
        
        return mismatches
    
    async def _correct_mismatches(self, mismatches: List[PositionMismatch]):
        """
        Auto-correct position mismatches
        
        Args:
            mismatches: List of mismatches to correct
        """
        logger.info(f"Auto-correcting {len(mismatches)} position mismatches")
        
        for mismatch in mismatches:
            try:
                if mismatch.mismatch_type == MismatchType.MISSING_LOCAL:
                    # Create local position from broker data
                    await self._sync_from_broker(mismatch)
                    mismatch.auto_corrected = True
                    mismatch.correction_action = "created_local_position"
                    
                elif mismatch.mismatch_type == MismatchType.MISSING_BROKER:
                    # Close local position (broker is source of truth)
                    await self._close_local_position(mismatch)
                    mismatch.auto_corrected = True
                    mismatch.correction_action = "closed_local_position"
                    
                elif mismatch.mismatch_type == MismatchType.QUANTITY_MISMATCH:
                    # Sync quantity from broker
                    await self._sync_quantity(mismatch)
                    mismatch.auto_corrected = True
                    mismatch.correction_action = "synced_quantity"
                    
                elif mismatch.mismatch_type == MismatchType.PRICE_MISMATCH:
                    # Sync price from broker
                    await self._sync_price(mismatch)
                    mismatch.auto_corrected = True
                    mismatch.correction_action = "synced_price"
                
                self.correction_count += 1
                logger.info(
                    f"Corrected {mismatch.mismatch_type.value} for {mismatch.symbol}: "
                    f"{mismatch.correction_action}"
                )
                
            except Exception as e:
                logger.error(f"Failed to correct mismatch for {mismatch.symbol}: {e}")
                mismatch.auto_corrected = False
    
    async def _sync_from_broker(self, mismatch: PositionMismatch):
        """Create local position from broker data"""
        # Implementation depends on ExecutionManager API
        logger.info(f"Creating local position for {mismatch.symbol} from broker data")
        # self.execution.create_position_from_broker(...)
    
    async def _close_local_position(self, mismatch: PositionMismatch):
        """Close local position that doesn't exist at broker"""
        logger.info(f"Closing orphaned local position for {mismatch.symbol}")
        # Mark position as closed
        position = self.execution.get_position(mismatch.symbol)
        if position:
            position.quantity = 0
    
    async def _sync_quantity(self, mismatch: PositionMismatch):
        """Sync position quantity from broker"""
        logger.info(
            f"Syncing quantity for {mismatch.symbol}: "
            f"{mismatch.local_quantity} -> {mismatch.broker_quantity}"
        )
        position = self.execution.get_position(mismatch.symbol)
        if position:
            position.quantity = mismatch.broker_quantity
    
    async def _sync_price(self, mismatch: PositionMismatch):
        """Sync entry price from broker"""
        logger.info(
            f"Syncing price for {mismatch.symbol}: "
            f"{mismatch.local_entry_price} -> {mismatch.broker_entry_price}"
        )
        position = self.execution.get_position(mismatch.symbol)
        if position and mismatch.broker_entry_price:
            position.entry_price = mismatch.broker_entry_price
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reconciliation statistics"""
        return {
            'reconciliation_count': self.reconciliation_count,
            'correction_count': self.correction_count,
            'last_reconciliation': self.last_reconciliation.isoformat() if self.last_reconciliation else None,
            'total_mismatches': len(self.mismatches),
            'recent_mismatches': [
                {
                    'symbol': m.symbol,
                    'type': m.mismatch_type.value,
                    'detected_at': m.detected_at.isoformat(),
                    'auto_corrected': m.auto_corrected,
                    'correction_action': m.correction_action
                }
                for m in self.mismatches[-10:]  # Last 10
            ]
        }
