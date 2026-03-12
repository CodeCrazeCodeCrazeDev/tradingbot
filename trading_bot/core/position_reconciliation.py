"""
Position Reconciliation System
Ensures local position state matches broker positions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ReconciliationStatus(Enum):
    """Status of reconciliation."""
    SYNCED = "synced"
    MISMATCH = "mismatch"
    BROKER_ONLY = "broker_only"
    LOCAL_ONLY = "local_only"
    ERROR = "error"


@dataclass
class PositionMismatch:
    """Represents a position mismatch between local and broker."""
    symbol: str
    local_size: Optional[float]
    broker_size: Optional[float]
    local_price: Optional[float]
    broker_price: Optional[float]
    status: ReconciliationStatus
    action_taken: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReconciliationReport:
    """Report of reconciliation results."""
    timestamp: datetime
    total_local_positions: int
    total_broker_positions: int
    synced_count: int
    mismatch_count: int
    broker_only_count: int
    local_only_count: int
    mismatches: List[PositionMismatch]
    actions_taken: List[str]
    success: bool
    error_message: Optional[str] = None


class PositionReconciler:
    """
    Reconciles local position state with broker positions.
    
    Features:
    - Periodic reconciliation
    - Mismatch detection and resolution
    - Ghost position cleanup
    - Missing position recovery
    - Audit trail
    """
    
    def __init__(
        self,
        broker_adapter,
        position_manager,
        config: Optional[Dict] = None
    ):
        self.broker = broker_adapter
        self.position_manager = position_manager
        self.config = config or {}
        
        # Configuration
        self.reconcile_interval_seconds = self.config.get('reconcile_interval_seconds', 60)
        self.auto_fix_mismatches = self.config.get('auto_fix_mismatches', True)
        self.max_size_difference_pct = self.config.get('max_size_difference_pct', 0.01)  # 1%
        self.max_price_difference_pct = self.config.get('max_price_difference_pct', 0.001)  # 0.1%
        
        # State
        self._running = False
        self._last_reconciliation: Optional[datetime] = None
        self._reconciliation_history: List[ReconciliationReport] = []
        self._max_history = 1000
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        logger.info("PositionReconciler initialized")
    
    async def start(self):
        """Start background reconciliation loop."""
        self._running = True
        logger.info("Starting position reconciliation loop")
        
        while self._running:
            try:
                await self.reconcile()
                await asyncio.sleep(self.reconcile_interval_seconds)
            except Exception as e:
                logger.error(f"Error in reconciliation loop: {e}")
                await asyncio.sleep(10)  # Wait before retry
    
    async def stop(self):
        """Stop reconciliation loop."""
        self._running = False
        logger.info("Position reconciliation stopped")
    
    async def reconcile(self) -> ReconciliationReport:
        """
        Perform full position reconciliation.
        
        Returns:
            ReconciliationReport with results
        """
        async with self._lock:
            start_time = datetime.now()
            mismatches: List[PositionMismatch] = []
            actions_taken: List[str] = []
            
            try:
                # Get positions from both sources
                local_positions = await self._get_local_positions()
                broker_positions = await self._get_broker_positions()
                
                # Create lookup dictionaries
                local_by_symbol = {p['symbol']: p for p in local_positions}
                broker_by_symbol = {p['symbol']: p for p in broker_positions}
                
                all_symbols = set(local_by_symbol.keys()) | set(broker_by_symbol.keys())
                
                synced_count = 0
                mismatch_count = 0
                broker_only_count = 0
                local_only_count = 0
                
                for symbol in all_symbols:
                    local_pos = local_by_symbol.get(symbol)
                    broker_pos = broker_by_symbol.get(symbol)
                    
                    if local_pos and broker_pos:
                        # Both exist - check for mismatches
                        mismatch = self._check_mismatch(symbol, local_pos, broker_pos)
                        if mismatch:
                            mismatches.append(mismatch)
                            mismatch_count += 1
                            
                            if self.auto_fix_mismatches:
                                action = await self._fix_mismatch(mismatch)
                                if action:
                                    actions_taken.append(action)
                                    mismatch.action_taken = action
                        else:
                            synced_count += 1
                    
                    elif broker_pos and not local_pos:
                        # Broker has position, local doesn't - add to local
                        broker_only_count += 1
                        mismatch = PositionMismatch(
                            symbol=symbol,
                            local_size=None,
                            broker_size=broker_pos.get('size'),
                            local_price=None,
                            broker_price=broker_pos.get('entry_price'),
                            status=ReconciliationStatus.BROKER_ONLY
                        )
                        mismatches.append(mismatch)
                        
                        if self.auto_fix_mismatches:
                            action = await self._add_missing_local_position(broker_pos)
                            if action:
                                actions_taken.append(action)
                                mismatch.action_taken = action
                    
                    elif local_pos and not broker_pos:
                        # Local has position, broker doesn't - ghost position
                        local_only_count += 1
                        mismatch = PositionMismatch(
                            symbol=symbol,
                            local_size=local_pos.get('size'),
                            broker_size=None,
                            local_price=local_pos.get('entry_price'),
                            broker_price=None,
                            status=ReconciliationStatus.LOCAL_ONLY
                        )
                        mismatches.append(mismatch)
                        
                        if self.auto_fix_mismatches:
                            action = await self._remove_ghost_position(local_pos)
                            if action:
                                actions_taken.append(action)
                                mismatch.action_taken = action
                
                # Create report
                report = ReconciliationReport(
                    timestamp=start_time,
                    total_local_positions=len(local_positions),
                    total_broker_positions=len(broker_positions),
                    synced_count=synced_count,
                    mismatch_count=mismatch_count,
                    broker_only_count=broker_only_count,
                    local_only_count=local_only_count,
                    mismatches=mismatches,
                    actions_taken=actions_taken,
                    success=True
                )
                
                # Log summary
                if mismatches:
                    logger.warning(
                        f"Reconciliation found {len(mismatches)} issues: "
                        f"{mismatch_count} mismatches, {broker_only_count} broker-only, "
                        f"{local_only_count} local-only"
                    )
                else:
                    logger.info(f"Reconciliation complete: {synced_count} positions synced")
                
                # Store in history
                self._reconciliation_history.append(report)
                if len(self._reconciliation_history) > self._max_history:
                    self._reconciliation_history = self._reconciliation_history[-500:]
                
                self._last_reconciliation = datetime.now()
                return report
                
            except Exception as e:
                logger.error(f"Reconciliation failed: {e}")
                return ReconciliationReport(
                    timestamp=start_time,
                    total_local_positions=0,
                    total_broker_positions=0,
                    synced_count=0,
                    mismatch_count=0,
                    broker_only_count=0,
                    local_only_count=0,
                    mismatches=[],
                    actions_taken=[],
                    success=False,
                    error_message=str(e)
                )
    
    async def _get_local_positions(self) -> List[Dict]:
        """Get positions from local position manager."""
        try:
            if hasattr(self.position_manager, 'get_all_positions'):
                positions = await self.position_manager.get_all_positions()
                return [
                    {
                        'symbol': p.symbol if hasattr(p, 'symbol') else p.get('symbol'),
                        'size': p.size if hasattr(p, 'size') else p.get('size'),
                        'entry_price': p.entry_price if hasattr(p, 'entry_price') else p.get('entry_price'),
                        'side': p.side if hasattr(p, 'side') else p.get('side'),
                        'ticket_id': p.ticket_id if hasattr(p, 'ticket_id') else p.get('ticket_id')
                    }
                    for p in positions
                ]
            elif hasattr(self.position_manager, 'positions'):
                return [
                    {
                        'symbol': p.symbol if hasattr(p, 'symbol') else k,
                        'size': p.size if hasattr(p, 'size') else p.get('size'),
                        'entry_price': p.entry_price if hasattr(p, 'entry_price') else p.get('entry_price'),
                        'side': getattr(p, 'side', p.get('side', 'buy')),
                        'ticket_id': getattr(p, 'ticket_id', k)
                    }
                    for k, p in self.position_manager.positions.items()
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting local positions: {e}")
            return []
    
    async def _get_broker_positions(self) -> List[Dict]:
        """Get positions from broker."""
        try:
            if hasattr(self.broker, 'get_positions'):
                positions = await self.broker.get_positions()
                return [
                    {
                        'symbol': p.get('symbol') or getattr(p, 'symbol', ''),
                        'size': p.get('size') or getattr(p, 'size', 0),
                        'entry_price': p.get('entry_price') or getattr(p, 'entry_price', 0),
                        'side': p.get('side') or getattr(p, 'side', 'buy'),
                        'ticket_id': p.get('ticket_id') or getattr(p, 'ticket_id', '')
                    }
                    for p in positions
                ]
            return []
        except Exception as e:
            logger.error(f"Error getting broker positions: {e}")
            return []
    
    def _check_mismatch(
        self,
        symbol: str,
        local_pos: Dict,
        broker_pos: Dict
    ) -> Optional[PositionMismatch]:
        """Check if positions match within tolerance."""
        local_size = local_pos.get('size', 0)
        broker_size = broker_pos.get('size', 0)
        local_price = local_pos.get('entry_price', 0)
        broker_price = broker_pos.get('entry_price', 0)
        
        # Check size difference
        if local_size > 0 and broker_size > 0:
            size_diff_pct = abs(local_size - broker_size) / max(local_size, broker_size)
            if size_diff_pct > self.max_size_difference_pct:
                return PositionMismatch(
                    symbol=symbol,
                    local_size=local_size,
                    broker_size=broker_size,
                    local_price=local_price,
                    broker_price=broker_price,
                    status=ReconciliationStatus.MISMATCH
                )
        
        # Check price difference (informational only)
        if local_price > 0 and broker_price > 0:
            price_diff_pct = abs(local_price - broker_price) / max(local_price, broker_price)
            if price_diff_pct > self.max_price_difference_pct:
                logger.debug(f"Price mismatch for {symbol}: local={local_price}, broker={broker_price}")
        
        return None
    
    async def _fix_mismatch(self, mismatch: PositionMismatch) -> Optional[str]:
        """Fix a position mismatch by updating local to match broker."""
        try:
            # Trust broker as source of truth
            logger.info(f"Fixing mismatch for {mismatch.symbol}: "
                       f"local={mismatch.local_size}, broker={mismatch.broker_size}")
            
            # Update local position size to match broker
            if hasattr(self.position_manager, 'update_position_size'):
                await self.position_manager.update_position_size(
                    mismatch.symbol,
                    mismatch.broker_size
                )
            
            return f"Updated {mismatch.symbol} size from {mismatch.local_size} to {mismatch.broker_size}"
            
        except Exception as e:
            logger.error(f"Error fixing mismatch: {e}")
            return None
    
    async def _add_missing_local_position(self, broker_pos: Dict) -> Optional[str]:
        """Add a position that exists in broker but not locally."""
        try:
            symbol = broker_pos.get('symbol')
            logger.info(f"Adding missing local position: {symbol}")
            
            if hasattr(self.position_manager, 'add_position'):
                # Create position object and add
                from trading_bot.position_manager import Position
                position = Position(
                    ticket_id=broker_pos.get('ticket_id', f"recovered_{symbol}"),
                    symbol=symbol,
                    side=broker_pos.get('side', 'buy'),
                    entry_price=broker_pos.get('entry_price', 0),
                    current_price=broker_pos.get('entry_price', 0),
                    size=broker_pos.get('size', 0),
                    stop_loss=broker_pos.get('stop_loss', 0),
                    take_profit=broker_pos.get('take_profit', 0),
                    entry_time=datetime.now(),
                    entry_confidence=0.5,
                    current_confidence=0.5,
                    unrealized_pnl=0
                )
                await self.position_manager.add_position(position)
            
            return f"Added missing position: {symbol}"
            
        except Exception as e:
            logger.error(f"Error adding missing position: {e}")
            return None
    
    async def _remove_ghost_position(self, local_pos: Dict) -> Optional[str]:
        """Remove a ghost position that doesn't exist in broker."""
        try:
            symbol = local_pos.get('symbol')
            ticket_id = local_pos.get('ticket_id')
            logger.warning(f"Removing ghost position: {symbol}")
            
            if hasattr(self.position_manager, 'remove_position'):
                await self.position_manager.remove_position(ticket_id)
            
            return f"Removed ghost position: {symbol}"
            
        except Exception as e:
            logger.error(f"Error removing ghost position: {e}")
            return None
    
    def get_last_reconciliation(self) -> Optional[ReconciliationReport]:
        """Get the most recent reconciliation report."""
        if self._reconciliation_history:
            return self._reconciliation_history[-1]
        return None
    
    def get_reconciliation_history(self, limit: int = 100) -> List[ReconciliationReport]:
        """Get reconciliation history."""
        return self._reconciliation_history[-limit:]
    
    def get_status(self) -> Dict:
        """Get current reconciliation status."""
        last = self.get_last_reconciliation()
        return {
            'running': self._running,
            'last_reconciliation': self._last_reconciliation.isoformat() if self._last_reconciliation else None,
            'last_success': last.success if last else None,
            'last_mismatch_count': len(last.mismatches) if last else 0,
            'interval_seconds': self.reconcile_interval_seconds,
            'auto_fix_enabled': self.auto_fix_mismatches
        }


# Factory function
def create_position_reconciler(broker_adapter, position_manager, config=None):
    """Create a position reconciler instance."""
    return PositionReconciler(broker_adapter, position_manager, config)


__all__ = [
    'PositionReconciler',
    'ReconciliationReport',
    'PositionMismatch',
    'ReconciliationStatus',
    'create_position_reconciler'
]
