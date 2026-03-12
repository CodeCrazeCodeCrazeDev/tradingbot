"""
Position Reconciliation System

Ensures local position state matches broker state:
- Periodic reconciliation checks
- Discrepancy detection and alerting
- Automatic correction (configurable)
- Audit trail of all reconciliations
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ReconciliationStatus(Enum):
    """Reconciliation result status"""
    MATCHED = "matched"
    DISCREPANCY_FOUND = "discrepancy_found"
    CORRECTED = "corrected"
    CORRECTION_FAILED = "correction_failed"
    BROKER_ERROR = "broker_error"
    SKIPPED = "skipped"


class DiscrepancyType(Enum):
    """Types of position discrepancies"""
    MISSING_LOCAL = "missing_local"  # Position exists at broker but not locally
    MISSING_BROKER = "missing_broker"  # Position exists locally but not at broker
    QUANTITY_MISMATCH = "quantity_mismatch"
    PRICE_MISMATCH = "price_mismatch"
    SIDE_MISMATCH = "side_mismatch"


@dataclass
class PositionDiscrepancy:
    """Details of a position discrepancy"""
    symbol: str
    discrepancy_type: DiscrepancyType
    local_value: Any
    broker_value: Any
    severity: str  # 'critical', 'warning', 'info'
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_notes: str = ""


@dataclass
class ReconciliationResult:
    """Result of a reconciliation check"""
    timestamp: datetime
    status: ReconciliationStatus
    positions_checked: int
    discrepancies: List[PositionDiscrepancy]
    corrections_made: int
    duration_ms: float
    notes: str = ""
    
    @property
    def has_discrepancies(self) -> bool:
        return len(self.discrepancies) > 0
    
    @property
    def critical_discrepancies(self) -> List[PositionDiscrepancy]:
        return [d for d in self.discrepancies if d.severity == 'critical']


class PositionReconciler:
    """
    Reconciles local position state with broker state.
    
    Features:
    - Periodic automatic reconciliation
    - Discrepancy detection and classification
    - Optional automatic correction
    - Comprehensive audit trail
    - Alerting on critical discrepancies
    """
    
    def __init__(
        self,
        broker_adapter,
        local_position_manager,
        config: Optional[Dict[str, Any]] = None,
        on_discrepancy: Optional[callable] = None,
        on_correction: Optional[callable] = None
    ):
        """
        Initialize position reconciler.
        
        Args:
            broker_adapter: Broker adapter for fetching positions
            local_position_manager: Local position manager
            config: Configuration dictionary
            on_discrepancy: Callback when discrepancy found
            on_correction: Callback when correction made
        """
        self.broker = broker_adapter
        self.local_manager = local_position_manager
        self.config = config or {}
        
        # Callbacks
        self.on_discrepancy = on_discrepancy
        self.on_correction = on_correction
        
        # Configuration
        self.reconciliation_interval = self.config.get('reconciliation_interval', 60)  # seconds
        self.auto_correct = self.config.get('auto_correct', False)
        self.price_tolerance_pct = self.config.get('price_tolerance_pct', 0.1)  # 0.1%
        self.quantity_tolerance = self.config.get('quantity_tolerance', 0.0001)
        
        # State
        self._running = False
        self._reconciliation_task: Optional[asyncio.Task] = None
        
        # History
        self.reconciliation_history: List[ReconciliationResult] = []
        self._max_history = self.config.get('max_history', 1000)
        
        # Statistics
        self.stats = {
            'total_reconciliations': 0,
            'total_discrepancies': 0,
            'total_corrections': 0,
            'last_reconciliation': None,
            'last_discrepancy': None
        }
        
        logger.info("Position reconciler initialized")
    
    async def start(self):
        """Start periodic reconciliation"""
        if self._running:
            logger.warning("Reconciler already running")
            return
        
        self._running = True
        self._reconciliation_task = asyncio.create_task(self._reconciliation_loop())
        logger.info(f"Position reconciliation started (interval: {self.reconciliation_interval}s)")
    
    async def stop(self):
        """Stop periodic reconciliation"""
        self._running = False
        
        if self._reconciliation_task:
            self._reconciliation_task.cancel()
            try:
                await self._reconciliation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Position reconciliation stopped")
    
    async def _reconciliation_loop(self):
        """Background reconciliation loop"""
        while self._running:
            try:
                await asyncio.sleep(self.reconciliation_interval)
                
                if not self._running:
                    break
                
                result = await self.reconcile()
                
                if result.has_discrepancies:
                    logger.warning(
                        f"Reconciliation found {len(result.discrepancies)} discrepancies "
                        f"({len(result.critical_discrepancies)} critical)"
                    )
                    
                    # Alert on critical discrepancies
                    if result.critical_discrepancies and self.on_discrepancy:
                        for discrepancy in result.critical_discrepancies:
                            try:
                                if asyncio.iscoroutinefunction(self.on_discrepancy):
                                    await self.on_discrepancy(discrepancy)
                                else:
                                    self.on_discrepancy(discrepancy)
                            except Exception as e:
                                logger.error(f"Discrepancy callback error: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reconciliation loop error: {e}")
    
    async def reconcile(self) -> ReconciliationResult:
        """
        Perform position reconciliation.
        
        Returns:
            ReconciliationResult with details
        """
        start_time = datetime.now()
        discrepancies: List[PositionDiscrepancy] = []
        corrections_made = 0
        
        try:
            # Get broker positions
            broker_positions = await self.broker.get_positions()
            broker_positions_dict = {p.symbol: p for p in broker_positions}
            
            # Get local positions
            local_positions = self._get_local_positions()
            local_positions_dict = {p['symbol']: p for p in local_positions}
            
            # Check all symbols
            all_symbols = set(broker_positions_dict.keys()) | set(local_positions_dict.keys())
            
            for symbol in all_symbols:
                broker_pos = broker_positions_dict.get(symbol)
                local_pos = local_positions_dict.get(symbol)
                
                # Check for discrepancies
                symbol_discrepancies = self._check_position(symbol, local_pos, broker_pos)
                discrepancies.extend(symbol_discrepancies)
                
                # Auto-correct if enabled
                if symbol_discrepancies and self.auto_correct:
                    for discrepancy in symbol_discrepancies:
                        if await self._correct_discrepancy(discrepancy):
                            corrections_made += 1
                            discrepancy.resolved = True
            
            # Determine status
            if not discrepancies:
                status = ReconciliationStatus.MATCHED
            elif corrections_made == len(discrepancies):
                status = ReconciliationStatus.CORRECTED
            elif corrections_made > 0:
                status = ReconciliationStatus.DISCREPANCY_FOUND
            else:
                status = ReconciliationStatus.DISCREPANCY_FOUND
            
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ReconciliationResult(
                timestamp=start_time,
                status=status,
                positions_checked=len(all_symbols),
                discrepancies=discrepancies,
                corrections_made=corrections_made,
                duration_ms=duration_ms
            )
            
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            result = ReconciliationResult(
                timestamp=start_time,
                status=ReconciliationStatus.BROKER_ERROR,
                positions_checked=0,
                discrepancies=[],
                corrections_made=0,
                duration_ms=duration_ms,
                notes=str(e)
            )
        
        # Update statistics
        self.stats['total_reconciliations'] += 1
        self.stats['total_discrepancies'] += len(discrepancies)
        self.stats['total_corrections'] += corrections_made
        self.stats['last_reconciliation'] = start_time
        
        if discrepancies:
            self.stats['last_discrepancy'] = start_time
        
        # Store in history
        self.reconciliation_history.append(result)
        if len(self.reconciliation_history) > self._max_history:
            self.reconciliation_history = self.reconciliation_history[-self._max_history:]
        
        logger.info(
            f"Reconciliation complete: {result.positions_checked} positions, "
            f"{len(result.discrepancies)} discrepancies, {result.corrections_made} corrections, "
            f"{result.duration_ms:.1f}ms"
        )
        
        return result
    
    def _get_local_positions(self) -> List[Dict[str, Any]]:
        """Get positions from local manager"""
        try:
            # Try different methods to get positions
            if hasattr(self.local_manager, 'get_all_positions'):
                positions = self.local_manager.get_all_positions()
            elif hasattr(self.local_manager, 'get_positions'):
                positions = self.local_manager.get_positions()
            elif hasattr(self.local_manager, 'positions'):
                positions = list(self.local_manager.positions.values())
            else:
                logger.warning("Could not get local positions - no suitable method found")
                return []
            
            # Normalize to dict format
            result = []
            for pos in positions:
                if isinstance(pos, dict):
                    result.append(pos)
                elif hasattr(pos, '__dict__'):
                    result.append({
                        'symbol': getattr(pos, 'symbol', ''),
                        'quantity': getattr(pos, 'quantity', 0),
                        'side': getattr(pos, 'side', 'buy' if getattr(pos, 'quantity', 0) > 0 else 'sell'),
                        'entry_price': getattr(pos, 'entry_price', 0),
                        'current_price': getattr(pos, 'current_price', 0)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting local positions: {e}")
            return []
    
    def _check_position(
        self,
        symbol: str,
        local_pos: Optional[Dict[str, Any]],
        broker_pos: Any
    ) -> List[PositionDiscrepancy]:
        """
        Check for discrepancies between local and broker position.
        
        Returns:
            List of discrepancies found
        """
        discrepancies = []
        
        # Position exists only at broker
        if broker_pos and not local_pos:
            discrepancies.append(PositionDiscrepancy(
                symbol=symbol,
                discrepancy_type=DiscrepancyType.MISSING_LOCAL,
                local_value=None,
                broker_value={
                    'quantity': broker_pos.quantity,
                    'side': broker_pos.side,
                    'entry_price': broker_pos.entry_price
                },
                severity='critical'
            ))
            return discrepancies
        
        # Position exists only locally
        if local_pos and not broker_pos:
            # Only flag if quantity is non-zero
            if local_pos.get('quantity', 0) != 0:
                discrepancies.append(PositionDiscrepancy(
                    symbol=symbol,
                    discrepancy_type=DiscrepancyType.MISSING_BROKER,
                    local_value={
                        'quantity': local_pos.get('quantity'),
                        'side': local_pos.get('side'),
                        'entry_price': local_pos.get('entry_price')
                    },
                    broker_value=None,
                    severity='critical'
                ))
            return discrepancies
        
        # Both exist - compare values
        if local_pos and broker_pos:
            # Quantity check
            local_qty = local_pos.get('quantity', 0)
            broker_qty = broker_pos.quantity
            
            if abs(local_qty - broker_qty) > self.quantity_tolerance:
                discrepancies.append(PositionDiscrepancy(
                    symbol=symbol,
                    discrepancy_type=DiscrepancyType.QUANTITY_MISMATCH,
                    local_value=local_qty,
                    broker_value=broker_qty,
                    severity='critical'
                ))
            
            # Side check
            local_side = local_pos.get('side', 'buy' if local_qty > 0 else 'sell')
            broker_side = broker_pos.side
            
            if local_side != broker_side:
                discrepancies.append(PositionDiscrepancy(
                    symbol=symbol,
                    discrepancy_type=DiscrepancyType.SIDE_MISMATCH,
                    local_value=local_side,
                    broker_value=broker_side,
                    severity='critical'
                ))
            
            # Entry price check (warning only)
            local_price = local_pos.get('entry_price', 0)
            broker_price = broker_pos.entry_price
            
            if local_price > 0 and broker_price > 0:
                price_diff_pct = abs(local_price - broker_price) / broker_price * 100
                if price_diff_pct > self.price_tolerance_pct:
                    discrepancies.append(PositionDiscrepancy(
                        symbol=symbol,
                        discrepancy_type=DiscrepancyType.PRICE_MISMATCH,
                        local_value=local_price,
                        broker_value=broker_price,
                        severity='warning'
                    ))
        
        return discrepancies
    
    async def _correct_discrepancy(self, discrepancy: PositionDiscrepancy) -> bool:
        """
        Attempt to correct a discrepancy.
        
        Returns:
            True if correction was successful
        """
        try:
            if discrepancy.discrepancy_type == DiscrepancyType.MISSING_LOCAL:
                # Add missing position to local state
                broker_data = discrepancy.broker_value
                if hasattr(self.local_manager, 'update_position'):
                    self.local_manager.update_position(
                        discrepancy.symbol,
                        broker_data['quantity'],
                        broker_data['entry_price']
                    )
                    discrepancy.resolution_notes = "Added missing position to local state"
                    logger.info(f"Corrected MISSING_LOCAL for {discrepancy.symbol}")
                    
                    if self.on_correction:
                        try:
                            if asyncio.iscoroutinefunction(self.on_correction):
                                await self.on_correction(discrepancy)
                            else:
                                self.on_correction(discrepancy)
                        except Exception as e:
                            logger.error(f"Correction callback error: {e}")
                    
                    return True
            
            elif discrepancy.discrepancy_type == DiscrepancyType.MISSING_BROKER:
                # Position exists locally but not at broker - clear local
                if hasattr(self.local_manager, 'positions'):
                    if discrepancy.symbol in self.local_manager.positions:
                        del self.local_manager.positions[discrepancy.symbol]
                        discrepancy.resolution_notes = "Removed orphan position from local state"
                        logger.info(f"Corrected MISSING_BROKER for {discrepancy.symbol}")
                        
                        if self.on_correction:
                            try:
                                if asyncio.iscoroutinefunction(self.on_correction):
                                    await self.on_correction(discrepancy)
                                else:
                                    self.on_correction(discrepancy)
                            except Exception as e:
                                logger.error(f"Correction callback error: {e}")
                        
                        return True
            
            elif discrepancy.discrepancy_type == DiscrepancyType.QUANTITY_MISMATCH:
                # Update local quantity to match broker
                if hasattr(self.local_manager, 'positions'):
                    if discrepancy.symbol in self.local_manager.positions:
                        self.local_manager.positions[discrepancy.symbol]['quantity'] = discrepancy.broker_value
                        discrepancy.resolution_notes = f"Updated quantity from {discrepancy.local_value} to {discrepancy.broker_value}"
                        logger.info(f"Corrected QUANTITY_MISMATCH for {discrepancy.symbol}")
                        
                        if self.on_correction:
                            try:
                                if asyncio.iscoroutinefunction(self.on_correction):
                                    await self.on_correction(discrepancy)
                                else:
                                    self.on_correction(discrepancy)
                            except Exception as e:
                                logger.error(f"Correction callback error: {e}")
                        
                        return True
            
            elif discrepancy.discrepancy_type == DiscrepancyType.PRICE_MISMATCH:
                # Update local price to match broker
                if hasattr(self.local_manager, 'positions'):
                    if discrepancy.symbol in self.local_manager.positions:
                        self.local_manager.positions[discrepancy.symbol]['entry_price'] = discrepancy.broker_value
                        discrepancy.resolution_notes = f"Updated entry price from {discrepancy.local_value} to {discrepancy.broker_value}"
                        logger.info(f"Corrected PRICE_MISMATCH for {discrepancy.symbol}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to correct discrepancy: {e}")
            discrepancy.resolution_notes = f"Correction failed: {e}"
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reconciliation statistics"""
        return {
            **self.stats,
            'history_count': len(self.reconciliation_history),
            'auto_correct_enabled': self.auto_correct,
            'reconciliation_interval': self.reconciliation_interval
        }
    
    def get_recent_discrepancies(self, limit: int = 10) -> List[PositionDiscrepancy]:
        """Get recent discrepancies"""
        all_discrepancies = []
        for result in reversed(self.reconciliation_history):
            all_discrepancies.extend(result.discrepancies)
            if len(all_discrepancies) >= limit:
                break
        return all_discrepancies[:limit]
