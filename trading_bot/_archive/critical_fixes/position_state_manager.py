"""
Position State Manager - Answers Q22, Q21, Q2
=============================================

Critical Question Q22: How do you reconcile internal position state with broker-reported positions?
Critical Question Q21: Where is position state stored, and what happens if that storage becomes unavailable?
Critical Question Q2: How do you guarantee that no two modules can simultaneously believe they own the same position?

This module provides:
1. Single source of truth for position state
2. Automatic reconciliation with broker
3. Discrepancy detection and alerting
4. Thread-safe position access
5. Persistent state with recovery
6. Position locking to prevent race conditions
"""

import asyncio
import logging
import threading
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PositionStatus(Enum):
    """Position status"""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_CLOSED = "partially_closed"
    CLOSED = "closed"
    ERROR = "error"
    RECONCILING = "reconciling"


class ReconciliationAction(Enum):
    """Actions taken during reconciliation"""
    NONE = "none"
    ADDED_LOCAL = "added_local"
    REMOVED_LOCAL = "removed_local"
    UPDATED_QUANTITY = "updated_quantity"
    UPDATED_PRICE = "updated_price"
    FLAGGED_DISCREPANCY = "flagged_discrepancy"


@dataclass
class PositionState:
    """Immutable position state snapshot"""
    position_id: str
    symbol: str
    direction: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    opened_at: datetime
    last_updated: datetime
    status: PositionStatus
    broker_ticket: Optional[str] = None
    strategy_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['opened_at'] = self.opened_at.isoformat()
        d['last_updated'] = self.last_updated.isoformat()
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'PositionState':
        d['opened_at'] = datetime.fromisoformat(d['opened_at'])
        d['last_updated'] = datetime.fromisoformat(d['last_updated'])
        d['status'] = PositionStatus(d['status'])
        return cls(**d)
    
    def checksum(self) -> str:
        """Generate checksum for integrity verification"""
        data = f"{self.position_id}:{self.symbol}:{self.quantity}:{self.entry_price}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class ReconciliationResult:
    """Result of position reconciliation"""
    timestamp: datetime
    local_positions: int
    broker_positions: int
    matched: int
    discrepancies: List[Dict]
    actions_taken: List[Dict]
    success: bool
    duration_ms: float
    error: Optional[str] = None


class PositionLock:
    """Thread-safe position locking mechanism"""
    
    def __init__(self):
        self._locks: Dict[str, threading.RLock] = {}
        self._global_lock = threading.RLock()
        self._lock_owners: Dict[str, str] = {}
    
    @contextmanager
    def acquire(self, position_id: str, owner: str, timeout: float = 5.0):
        """Acquire lock for a position"""
        with self._global_lock:
            if position_id not in self._locks:
                self._locks[position_id] = threading.RLock()
        
        lock = self._locks[position_id]
        acquired = lock.acquire(timeout=timeout)
        
        if not acquired:
            try:
                current_owner = self._lock_owners.get(position_id, 'unknown')
                raise TimeoutError(
                    f"Failed to acquire lock for position {position_id}. "
                    f"Currently held by: {current_owner}"
                )

                self._lock_owners[position_id] = owner
                yield
            finally:
                self._lock_owners.pop(position_id, None)
                lock.release()

    def is_locked(self, position_id: str) -> bool:
        """Check if position is locked"""
        with self._global_lock:
            if position_id not in self._locks:
                return False
            return self._locks[position_id].locked()


class PositionStateManager:
    """
    Single source of truth for position state.
    
    Addresses critical questions:
    - Q22: Reconciliation with broker
    - Q21: Persistent storage with recovery
    - Q2: Thread-safe access preventing race conditions
    
    Features:
    - Thread-safe position access with locking
    - Automatic broker reconciliation
    - Persistent SQLite storage
    - Discrepancy detection and alerting
    - Position integrity verification
    - Audit trail of all changes
    """
    
    def __init__(
        self,
        broker_adapter,
        db_path: str = "position_state.db",
        reconciliation_interval: int = 30,
        auto_correct: bool = False,
        on_discrepancy: Optional[callable] = None
    ):
        """
        Initialize position state manager.
        
        Args:
            broker_adapter: Adapter for broker API
            db_path: Path to SQLite database
            reconciliation_interval: Seconds between reconciliations
            auto_correct: Whether to auto-correct discrepancies
            on_discrepancy: Callback when discrepancy detected
        """
        self.broker = broker_adapter
        self.db_path = Path(db_path)
        self.reconciliation_interval = reconciliation_interval
        self.auto_correct = auto_correct
        self.on_discrepancy = on_discrepancy
        
        # Position storage
        self._positions: Dict[str, PositionState] = {}
        self._position_lock = PositionLock()
        self._global_lock = threading.RLock()
        
        # Reconciliation state
        self._running = False
        self._reconciliation_task: Optional[asyncio.Task] = None
        self._last_reconciliation: Optional[datetime] = None
        self._reconciliation_history: List[ReconciliationResult] = []
        
        # Statistics
        self.stats = {
            'total_reconciliations': 0,
            'total_discrepancies': 0,
            'total_corrections': 0,
            'last_discrepancy': None,
            'uptime_start': datetime.now()
        }
        
        # Initialize database
        self._init_database()
        
        # Load persisted state
        self._load_state()
        
        logger.info(f"PositionStateManager initialized with {len(self._positions)} positions")
    
    def _init_database(self):
        """Initialize SQLite database for persistent storage"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS positions (
                    position_id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    entry_price REAL NOT NULL,
                    current_price REAL NOT NULL,
                    unrealized_pnl REAL DEFAULT 0,
                    realized_pnl REAL DEFAULT 0,
                    stop_loss REAL,
                    take_profit REAL,
                    opened_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    status TEXT NOT NULL,
                    broker_ticket TEXT,
                    strategy_id TEXT,
                    metadata TEXT,
                    checksum TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS position_audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    reason TEXT,
                    actor TEXT,
                    timestamp TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reconciliation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    local_count INTEGER,
                    broker_count INTEGER,
                    matched INTEGER,
                    discrepancies TEXT,
                    actions TEXT,
                    success INTEGER,
                    duration_ms REAL,
                    error TEXT
                )
            """)
            
            conn.commit()
    
    def _load_state(self):
        """Load persisted position state from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM positions WHERE status != 'closed'"
                )
                
                for row in cursor:
                    try:
                        position = PositionState(
                            position_id=row['position_id'],
                            symbol=row['symbol'],
                            direction=row['direction'],
                            quantity=row['quantity'],
                            entry_price=row['entry_price'],
                            current_price=row['current_price'],
                            unrealized_pnl=row['unrealized_pnl'],
                            realized_pnl=row['realized_pnl'],
                            stop_loss=row['stop_loss'],
                            take_profit=row['take_profit'],
                            opened_at=datetime.fromisoformat(row['opened_at']),
                            last_updated=datetime.fromisoformat(row['last_updated']),
                            status=PositionStatus(row['status']),
                            broker_ticket=row['broker_ticket'],
                            strategy_id=row['strategy_id'],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {}
                        )
                        
                        # Verify checksum
                        if row['checksum'] and position.checksum() != row['checksum']:
                            logger.warning(
                                f"Position {position.position_id} checksum mismatch - "
                                f"possible corruption"
                            )
                        
                        self._positions[position.position_id] = position
                        
                    except Exception as e:
                        logger.error(f"Error loading position: {e}")
                
                logger.info(f"Loaded {len(self._positions)} positions from database")
                
        except Exception as e:
            logger.error(f"Error loading state from database: {e}")
    
    def _persist_position(self, position: PositionState, action: str = "update"):
        """Persist position to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO positions
                    (position_id, symbol, direction, quantity, entry_price, current_price,
                     unrealized_pnl, realized_pnl, stop_loss, take_profit, opened_at,
                     last_updated, status, broker_ticket, strategy_id, metadata, checksum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    position.position_id,
                    position.symbol,
                    position.direction,
                    position.quantity,
                    position.entry_price,
                    position.current_price,
                    position.unrealized_pnl,
                    position.realized_pnl,
                    position.stop_loss,
                    position.take_profit,
                    position.opened_at.isoformat(),
                    position.last_updated.isoformat(),
                    position.status.value,
                    position.broker_ticket,
                    position.strategy_id,
                    json.dumps(position.metadata),
                    position.checksum()
                ))
                
                # Audit trail
                conn.execute("""
                    INSERT INTO position_audit
                    (position_id, action, new_value, reason, actor, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    position.position_id,
                    action,
                    json.dumps(position.to_dict()),
                    f"Position {action}",
                    "system",
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error persisting position: {e}")
            raise
    
    def get_position(self, position_id: str) -> Optional[PositionState]:
        """Get position by ID (thread-safe)"""
        with self._global_lock:
            return self._positions.get(position_id)
    
    def get_all_positions(self) -> List[PositionState]:
        """Get all open positions (thread-safe)"""
        with self._global_lock:
            return [
                p for p in self._positions.values()
                if p.status in (PositionStatus.OPEN, PositionStatus.PARTIALLY_CLOSED)
            ]
    
    def get_positions_by_symbol(self, symbol: str) -> List[PositionState]:
        """Get positions for a symbol (thread-safe)"""
        with self._global_lock:
            return [
                p for p in self._positions.values()
                if p.symbol == symbol and p.status == PositionStatus.OPEN
            ]
    
    def add_position(
        self,
        position: PositionState,
        owner: str = "system"
    ) -> bool:
        """
        Add a new position (thread-safe with locking).
        
        Args:
            position: Position to add
            owner: Owner requesting the add
            
        Returns:
            True if added successfully
        """
        try:
            with self._position_lock.acquire(position.position_id, owner):
                with self._global_lock:
                    if position.position_id in self._positions:
                        logger.warning(f"Position {position.position_id} already exists")
                        return False
                    
                    self._positions[position.position_id] = position
                    self._persist_position(position, "create")
                    
                    logger.info(f"Added position {position.position_id}: {position.symbol}")
                    return True
                    
        except TimeoutError as e:
            logger.error(f"Lock timeout adding position: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding position: {e}")
            return False
    
    def update_position(
        self,
        position_id: str,
        updates: Dict[str, Any],
        owner: str = "system"
    ) -> bool:
        """
        Update a position (thread-safe with locking).
        
        Args:
            position_id: Position to update
            updates: Dictionary of updates
            owner: Owner requesting the update
            
        Returns:
            True if updated successfully
        """
        try:
            with self._position_lock.acquire(position_id, owner):
                with self._global_lock:
                    if position_id not in self._positions:
                        logger.warning(f"Position {position_id} not found")
                        return False
                    
                    old_position = self._positions[position_id]
                    
                    # Create updated position
                    position_dict = old_position.to_dict()
                    position_dict.update(updates)
                    position_dict['last_updated'] = datetime.now()
                    
                    new_position = PositionState.from_dict(position_dict)
                    self._positions[position_id] = new_position
                    self._persist_position(new_position, "update")
                    
                    logger.debug(f"Updated position {position_id}")
                    return True
                    
        except TimeoutError as e:
            logger.error(f"Lock timeout updating position: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating position: {e}")
            return False
    
    def close_position(
        self,
        position_id: str,
        close_price: float,
        realized_pnl: float,
        owner: str = "system"
    ) -> bool:
        """
        Close a position (thread-safe with locking).
        
        Args:
            position_id: Position to close
            close_price: Closing price
            realized_pnl: Realized P&L
            owner: Owner requesting the close
            
        Returns:
            True if closed successfully
        """
        return self.update_position(
            position_id,
            {
                'status': PositionStatus.CLOSED.value,
                'current_price': close_price,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': 0
            },
            owner
        )
    
    async def start_reconciliation(self):
        """Start automatic reconciliation loop"""
        if self._running:
            logger.warning("Reconciliation already running")
            return
        
        self._running = True
        self._reconciliation_task = asyncio.create_task(self._reconciliation_loop())
        logger.info(f"Position reconciliation started (interval: {self.reconciliation_interval}s)")
    
    async def stop_reconciliation(self):
        """Stop automatic reconciliation"""
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
                
                if result.discrepancies:
                    logger.warning(
                        f"Reconciliation found {len(result.discrepancies)} discrepancies"
                    )
                    
                    if self.on_discrepancy:
                        for discrepancy in result.discrepancies:
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
        Reconcile local positions with broker positions.
        
        This is the answer to Q22: How do you reconcile internal position
        state with broker-reported positions?
        
        Returns:
            ReconciliationResult with details
        """
        start_time = datetime.now()
        discrepancies = []
        actions_taken = []
        error = None
        
        try:
            # Get broker positions
            broker_positions = await self._get_broker_positions()
            
            # Get local positions
            with self._global_lock:
                local_positions = {
                    p.broker_ticket: p for p in self._positions.values()
                    if p.status == PositionStatus.OPEN and p.broker_ticket
                }
            
            broker_tickets = set(broker_positions.keys())
            local_tickets = set(local_positions.keys())
            
            matched = 0
            
            # Check for positions in broker but not local
            for ticket in broker_tickets - local_tickets:
                broker_pos = broker_positions[ticket]
                discrepancies.append({
                    'type': 'missing_local',
                    'broker_ticket': ticket,
                    'symbol': broker_pos.get('symbol'),
                    'quantity': broker_pos.get('quantity'),
                    'severity': 'critical'
                })
                
                if self.auto_correct:
                    # Add missing position locally
                    await self._add_from_broker(broker_pos)
                    actions_taken.append({
                        'action': ReconciliationAction.ADDED_LOCAL.value,
                        'ticket': ticket
                    })
            
            # Check for positions in local but not broker
            for ticket in local_tickets - broker_tickets:
                local_pos = local_positions[ticket]
                discrepancies.append({
                    'type': 'missing_broker',
                    'broker_ticket': ticket,
                    'symbol': local_pos.symbol,
                    'quantity': local_pos.quantity,
                    'severity': 'critical'
                })
                
                if self.auto_correct:
                    # Mark local position as closed (broker closed it)
                    self.update_position(
                        local_pos.position_id,
                        {'status': PositionStatus.CLOSED.value},
                        'reconciliation'
                    )
                    actions_taken.append({
                        'action': ReconciliationAction.REMOVED_LOCAL.value,
                        'ticket': ticket
                    })
            
            # Check matching positions for discrepancies
            for ticket in broker_tickets & local_tickets:
                broker_pos = broker_positions[ticket]
                local_pos = local_positions[ticket]
                
                # Check quantity
                broker_qty = broker_pos.get('quantity', 0)
                if abs(local_pos.quantity - broker_qty) > 0.0001:
                    discrepancies.append({
                        'type': 'quantity_mismatch',
                        'broker_ticket': ticket,
                        'symbol': local_pos.symbol,
                        'local_quantity': local_pos.quantity,
                        'broker_quantity': broker_qty,
                        'severity': 'warning'
                    })
                    
                    if self.auto_correct:
                        self.update_position(
                            local_pos.position_id,
                            {'quantity': broker_qty},
                            'reconciliation'
                        )
                        actions_taken.append({
                            'action': ReconciliationAction.UPDATED_QUANTITY.value,
                            'ticket': ticket
                        })
                else:
                    matched += 1
            
            # Update statistics
            self.stats['total_reconciliations'] += 1
            self.stats['total_discrepancies'] += len(discrepancies)
            self.stats['total_corrections'] += len(actions_taken)
            if discrepancies:
                self.stats['last_discrepancy'] = datetime.now()
            
            self._last_reconciliation = datetime.now()
            
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")
            error = str(e)
        
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        result = ReconciliationResult(
            timestamp=datetime.now(),
            local_positions=len(local_positions) if 'local_positions' in dir() else 0,
            broker_positions=len(broker_positions) if 'broker_positions' in dir() else 0,
            matched=matched if 'matched' in dir() else 0,
            discrepancies=discrepancies,
            actions_taken=actions_taken,
            success=error is None,
            duration_ms=duration_ms,
            error=error
        )
        
        # Log to database
        self._log_reconciliation(result)
        
        self._reconciliation_history.append(result)
        if len(self._reconciliation_history) > 1000:
            self._reconciliation_history = self._reconciliation_history[-500:]
        
        return result
    
    async def _get_broker_positions(self) -> Dict[str, Dict]:
        """Get positions from broker"""
        positions = {}
        
        try:
            if hasattr(self.broker, 'get_positions'):
                broker_positions = await self.broker.get_positions()
                for pos in broker_positions:
                    ticket = str(pos.get('ticket', pos.get('id', '')))
                    positions[ticket] = pos
            elif hasattr(self.broker, 'positions_get'):
                # MT5 style
                broker_positions = self.broker.positions_get()
                if broker_positions:
                    for pos in broker_positions:
                        positions[str(pos.ticket)] = {
                            'ticket': pos.ticket,
                            'symbol': pos.symbol,
                            'quantity': pos.volume,
                            'direction': 'long' if pos.type == 0 else 'short',
                            'entry_price': pos.price_open,
                            'current_price': pos.price_current,
                            'profit': pos.profit
                        }
        except Exception as e:
            logger.error(f"Error getting broker positions: {e}")
            raise
        
        return positions
    
    async def _add_from_broker(self, broker_pos: Dict):
        """Add a position from broker data"""
        position = PositionState(
            position_id=f"reconciled_{broker_pos.get('ticket')}",
            symbol=broker_pos.get('symbol', ''),
            direction=broker_pos.get('direction', 'long'),
            quantity=broker_pos.get('quantity', 0),
            entry_price=broker_pos.get('entry_price', 0),
            current_price=broker_pos.get('current_price', 0),
            unrealized_pnl=broker_pos.get('profit', 0),
            realized_pnl=0,
            stop_loss=broker_pos.get('sl'),
            take_profit=broker_pos.get('tp'),
            opened_at=datetime.now(),
            last_updated=datetime.now(),
            status=PositionStatus.OPEN,
            broker_ticket=str(broker_pos.get('ticket')),
            metadata={'source': 'reconciliation'}
        )
        
        self.add_position(position, 'reconciliation')
    
    def _log_reconciliation(self, result: ReconciliationResult):
        """Log reconciliation result to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO reconciliation_log
                    (timestamp, local_count, broker_count, matched, discrepancies,
                     actions, success, duration_ms, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.timestamp.isoformat(),
                    result.local_positions,
                    result.broker_positions,
                    result.matched,
                    json.dumps(result.discrepancies),
                    json.dumps(result.actions_taken),
                    1 if result.success else 0,
                    result.duration_ms,
                    result.error
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging reconciliation: {e}")
    
    def get_reconciliation_status(self) -> Dict:
        """Get current reconciliation status"""
        return {
            'last_reconciliation': self._last_reconciliation.isoformat() if self._last_reconciliation else None,
            'is_running': self._running,
            'interval_seconds': self.reconciliation_interval,
            'auto_correct': self.auto_correct,
            'statistics': self.stats,
            'recent_discrepancies': [
                r.discrepancies for r in self._reconciliation_history[-5:]
                if r.discrepancies
            ]
        }
    
    def force_reconcile_now(self) -> asyncio.Task:
        """Force immediate reconciliation"""
        return asyncio.create_task(self.reconcile())
