"""
Production Database Integration

Complete database infrastructure:
- PostgreSQL for relational data
- TimescaleDB for time-series data
- Connection pooling
- Migrations
- Query optimization
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type
from datetime import datetime, timedelta
from dataclasses import dataclass
from contextlib import asynccontextmanager
import json
import os

logger = logging.getLogger(__name__)

# SQLAlchemy imports
try:
    from sqlalchemy import (
        create_engine, Column, Integer, String, Float, DateTime, 
        Boolean, Text, JSON, ForeignKey, Index, func, text
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.pool import QueuePool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy not installed. Install with: pip install sqlalchemy asyncpg")

# Alembic for migrations
try:
    from alembic import command
    from alembic.config import Config
    ALEMBIC_AVAILABLE = True
except ImportError:
    ALEMBIC_AVAILABLE = False

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    # ==========================================
    # ORM Models
    # ==========================================
    
    class TradeRecord(Base):
        """Trade record model"""
        __tablename__ = 'trades'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        trade_id = Column(String(64), unique=True, nullable=False, index=True)
        order_id = Column(String(64), index=True)
        symbol = Column(String(32), nullable=False, index=True)
        side = Column(String(10), nullable=False)
        quantity = Column(Float, nullable=False)
        entry_price = Column(Float, nullable=False)
        exit_price = Column(Float)
        pnl = Column(Float)
        commission = Column(Float, default=0)
        strategy = Column(String(64))
        entry_time = Column(DateTime, nullable=False, index=True)
        exit_time = Column(DateTime)
        status = Column(String(20), default='open', index=True)
        extra_data = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        __table_args__ = (
            Index('ix_trades_symbol_entry_time', 'symbol', 'entry_time'),
        )
    
    class PositionRecord(Base):
        """Position record model"""
        __tablename__ = 'positions'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        position_id = Column(String(64), unique=True, nullable=False, index=True)
        symbol = Column(String(32), nullable=False, index=True)
        side = Column(String(10), nullable=False)
        quantity = Column(Float, nullable=False)
        entry_price = Column(Float, nullable=False)
        current_price = Column(Float)
        unrealized_pnl = Column(Float)
        realized_pnl = Column(Float, default=0)
        stop_loss = Column(Float)
        take_profit = Column(Float)
        opened_at = Column(DateTime, nullable=False)
        closed_at = Column(DateTime)
        status = Column(String(20), default='open', index=True)
        extra_data = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    class OrderRecord(Base):
        """Order record model"""
        __tablename__ = 'orders'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        order_id = Column(String(64), unique=True, nullable=False, index=True)
        client_order_id = Column(String(64), index=True)
        broker_id = Column(String(32))
        symbol = Column(String(32), nullable=False, index=True)
        side = Column(String(10), nullable=False)
        order_type = Column(String(20), nullable=False)
        quantity = Column(Float, nullable=False)
        price = Column(Float)
        stop_price = Column(Float)
        filled_quantity = Column(Float, default=0)
        average_fill_price = Column(Float)
        commission = Column(Float, default=0)
        status = Column(String(20), default='pending', index=True)
        error_message = Column(Text)
        submitted_at = Column(DateTime, nullable=False)
        filled_at = Column(DateTime)
        cancelled_at = Column(DateTime)
        extra_data = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        __table_args__ = (
            Index('ix_orders_symbol_submitted_at', 'symbol', 'submitted_at'),
        )
    
    class AccountSnapshot(Base):
        """Account snapshot model"""
        __tablename__ = 'account_snapshots'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        snapshot_time = Column(DateTime, nullable=False, index=True)
        balance = Column(Float, nullable=False)
        equity = Column(Float, nullable=False)
        margin = Column(Float)
        free_margin = Column(Float)
        margin_level = Column(Float)
        unrealized_pnl = Column(Float)
        realized_pnl = Column(Float)
        open_positions = Column(Integer)
        currency = Column(String(10))
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class MetricRecord(Base):
        """Performance metric model"""
        __tablename__ = 'metrics'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        metric_time = Column(DateTime, nullable=False, index=True)
        metric_name = Column(String(64), nullable=False, index=True)
        metric_value = Column(Float, nullable=False)
        labels = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        __table_args__ = (
            Index('ix_metrics_name_time', 'metric_name', 'metric_time'),
        )
    
    class SignalRecord(Base):
        """Trading signal model"""
        __tablename__ = 'signals'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        signal_id = Column(String(64), unique=True, nullable=False, index=True)
        symbol = Column(String(32), nullable=False, index=True)
        direction = Column(String(10), nullable=False)
        strength = Column(Float)
        confidence = Column(Float)
        source = Column(String(64))
        generated_at = Column(DateTime, nullable=False, index=True)
        expires_at = Column(DateTime)
        executed = Column(Boolean, default=False)
        order_id = Column(String(64))
        extra_data = Column(JSON)
        created_at = Column(DateTime, default=datetime.utcnow)
    
    class AuditLog(Base):
        """Audit log model"""
        __tablename__ = 'audit_logs'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        event_id = Column(String(64), unique=True, nullable=False, index=True)
        event_type = Column(String(64), nullable=False, index=True)
        user_id = Column(String(64), index=True)
        ip_address = Column(String(45))
        resource = Column(String(256))
        action = Column(String(256), nullable=False)
        status = Column(String(20), nullable=False)
        details = Column(JSON)
        timestamp = Column(DateTime, nullable=False, index=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        
        __table_args__ = (
            Index('ix_audit_user_timestamp', 'user_id', 'timestamp'),
        )


class DatabaseManager:
    """
    Production database manager with connection pooling.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("SQLAlchemy not installed")
        
        self.config = config or {}
        
        # Database URL
        self.database_url = self.config.get(
            'database_url',
            os.getenv('DATABASE_URL', 'postgresql://localhost/alphaalgo')
        )
        
        # Convert to async URL if needed
        if self.database_url.startswith('postgresql://'):
            self.async_database_url = self.database_url.replace(
                'postgresql://', 'postgresql+asyncpg://'
            )
        else:
            self.async_database_url = self.database_url
        
        # Connection pool settings
        self.pool_size = self.config.get('pool_size', 10)
        self.max_overflow = self.config.get('max_overflow', 20)
        self.pool_timeout = self.config.get('pool_timeout', 30)
        
        # Engines
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        
        logger.info("DatabaseManager initialized")
    
    async def connect(self):
        """Initialize database connections"""
        try:
            # Sync engine (for migrations)
            self.engine = create_engine(
                self.database_url,
                poolclass=QueuePool,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_pre_ping=True
            )
            
            # Async engine
            self.async_engine = create_async_engine(
                self.async_database_url,
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
                pool_pre_ping=True
            )
            
            # Session factories
            self.SessionLocal = sessionmaker(bind=self.engine)
            self.AsyncSessionLocal = sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database connected successfully")
            
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.async_engine:
            await self.async_engine.dispose()
        if self.engine:
            self.engine.dispose()
        logger.info("Database disconnected")
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session"""
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # ==========================================
    # Trade Operations
    # ==========================================
    
    async def save_trade(self, trade_data: Dict[str, Any]) -> str:
        """Save trade record"""
        async with self.get_session() as session:
            trade = TradeRecord(
                trade_id=trade_data.get('trade_id', str(uuid.uuid4())),
                order_id=trade_data.get('order_id'),
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                quantity=trade_data['quantity'],
                entry_price=trade_data['entry_price'],
                exit_price=trade_data.get('exit_price'),
                pnl=trade_data.get('pnl'),
                commission=trade_data.get('commission', 0),
                strategy=trade_data.get('strategy'),
                entry_time=trade_data['entry_time'],
                exit_time=trade_data.get('exit_time'),
                status=trade_data.get('status', 'open'),
                metadata=trade_data.get('metadata')
            )
            session.add(trade)
            await session.flush()
            return trade.trade_id
    
    async def get_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get trade records"""
        async with self.get_session() as session:
            query = session.query(TradeRecord)
            
            if symbol:
                query = query.filter(TradeRecord.symbol == symbol)
            if start_time:
                query = query.filter(TradeRecord.entry_time >= start_time)
            if end_time:
                query = query.filter(TradeRecord.entry_time <= end_time)
            if status:
                query = query.filter(TradeRecord.status == status)
            
            query = query.order_by(TradeRecord.entry_time.desc()).limit(limit)
            
            result = await session.execute(query)
            trades = result.scalars().all()
            
            return [self._trade_to_dict(t) for t in trades]
    
    def _trade_to_dict(self, trade: TradeRecord) -> Dict:
        """Convert trade record to dict"""
        return {
            'trade_id': trade.trade_id,
            'order_id': trade.order_id,
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': trade.quantity,
            'entry_price': trade.entry_price,
            'exit_price': trade.exit_price,
            'pnl': trade.pnl,
            'commission': trade.commission,
            'strategy': trade.strategy,
            'entry_time': trade.entry_time.isoformat() if trade.entry_time else None,
            'exit_time': trade.exit_time.isoformat() if trade.exit_time else None,
            'status': trade.status,
            'metadata': trade.metadata
        }
    
    # ==========================================
    # Order Operations
    # ==========================================
    
    async def save_order(self, order_data: Dict[str, Any]) -> str:
        """Save order record"""
        async with self.get_session() as session:
            order = OrderRecord(
                order_id=order_data['order_id'],
                client_order_id=order_data.get('client_order_id'),
                broker_id=order_data.get('broker_id'),
                symbol=order_data['symbol'],
                side=order_data['side'],
                order_type=order_data['order_type'],
                quantity=order_data['quantity'],
                price=order_data.get('price'),
                stop_price=order_data.get('stop_price'),
                filled_quantity=order_data.get('filled_quantity', 0),
                average_fill_price=order_data.get('average_fill_price'),
                commission=order_data.get('commission', 0),
                status=order_data.get('status', 'pending'),
                submitted_at=order_data.get('submitted_at', datetime.utcnow()),
                metadata=order_data.get('metadata')
            )
            session.add(order)
            await session.flush()
            return order.order_id
    
    async def update_order(self, order_id: str, updates: Dict[str, Any]):
        """Update order record"""
        async with self.get_session() as session:
            result = await session.execute(
                session.query(OrderRecord).filter(OrderRecord.order_id == order_id)
            )
            order = result.scalar_one_or_none()
            
            if order:
                for key, value in updates.items():
                    if hasattr(order, key):
                        setattr(order, key, value)
    
    # ==========================================
    # Account Operations
    # ==========================================
    
    async def save_account_snapshot(self, snapshot_data: Dict[str, Any]):
        """Save account snapshot"""
        async with self.get_session() as session:
            snapshot = AccountSnapshot(
                snapshot_time=snapshot_data.get('snapshot_time', datetime.utcnow()),
                balance=snapshot_data['balance'],
                equity=snapshot_data['equity'],
                margin=snapshot_data.get('margin'),
                free_margin=snapshot_data.get('free_margin'),
                margin_level=snapshot_data.get('margin_level'),
                unrealized_pnl=snapshot_data.get('unrealized_pnl'),
                realized_pnl=snapshot_data.get('realized_pnl'),
                open_positions=snapshot_data.get('open_positions'),
                currency=snapshot_data.get('currency')
            )
            session.add(snapshot)
    
    async def get_account_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Get account history"""
        async with self.get_session() as session:
            query = session.query(AccountSnapshot)
            
            if start_time:
                query = query.filter(AccountSnapshot.snapshot_time >= start_time)
            if end_time:
                query = query.filter(AccountSnapshot.snapshot_time <= end_time)
            
            query = query.order_by(AccountSnapshot.snapshot_time.desc()).limit(limit)
            
            result = await session.execute(query)
            snapshots = result.scalars().all()
            
            return [{
                'snapshot_time': s.snapshot_time.isoformat(),
                'balance': s.balance,
                'equity': s.equity,
                'margin': s.margin,
                'free_margin': s.free_margin,
                'unrealized_pnl': s.unrealized_pnl
            } for s in snapshots]
    
    # ==========================================
    # Metrics Operations
    # ==========================================
    
    async def save_metric(
        self,
        metric_name: str,
        metric_value: float,
        labels: Optional[Dict] = None,
        metric_time: Optional[datetime] = None
    ):
        """Save metric record"""
        async with self.get_session() as session:
            metric = MetricRecord(
                metric_time=metric_time or datetime.utcnow(),
                metric_name=metric_name,
                metric_value=metric_value,
                labels=labels
            )
            session.add(metric)
    
    async def get_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Get metric records"""
        async with self.get_session() as session:
            query = session.query(MetricRecord).filter(
                MetricRecord.metric_name == metric_name
            )
            
            if start_time:
                query = query.filter(MetricRecord.metric_time >= start_time)
            if end_time:
                query = query.filter(MetricRecord.metric_time <= end_time)
            
            query = query.order_by(MetricRecord.metric_time.desc()).limit(limit)
            
            result = await session.execute(query)
            metrics = result.scalars().all()
            
            return [{
                'metric_time': m.metric_time.isoformat(),
                'metric_name': m.metric_name,
                'metric_value': m.metric_value,
                'labels': m.labels
            } for m in metrics]
    
    # ==========================================
    # Audit Operations
    # ==========================================
    
    async def save_audit_log(self, event_data: Dict[str, Any]):
        """Save audit log entry"""
        async with self.get_session() as session:
            audit = AuditLog(
                event_id=event_data['event_id'],
                event_type=event_data['event_type'],
                user_id=event_data.get('user_id'),
                ip_address=event_data.get('ip_address'),
                resource=event_data.get('resource'),
                action=event_data['action'],
                status=event_data['status'],
                details=event_data.get('details'),
                timestamp=event_data['timestamp']
            )
            session.add(audit)
    
    # ==========================================
    # Analytics
    # ==========================================
    
    async def get_trade_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get trade statistics"""
        async with self.get_session() as session:
            query = session.query(
                func.count(TradeRecord.id).label('total_trades'),
                func.sum(TradeRecord.pnl).label('total_pnl'),
                func.avg(TradeRecord.pnl).label('avg_pnl'),
                func.sum(func.case((TradeRecord.pnl > 0, 1), else_=0)).label('winning_trades'),
                func.sum(func.case((TradeRecord.pnl <= 0, 1), else_=0)).label('losing_trades')
            ).filter(TradeRecord.status == 'closed')
            
            if start_time:
                query = query.filter(TradeRecord.entry_time >= start_time)
            if end_time:
                query = query.filter(TradeRecord.entry_time <= end_time)
            
            result = await session.execute(query)
            row = result.one()
            
            total = row.total_trades or 0
            winning = row.winning_trades or 0
            
            return {
                'total_trades': total,
                'winning_trades': winning,
                'losing_trades': row.losing_trades or 0,
                'win_rate': (winning / total * 100) if total > 0 else 0,
                'total_pnl': row.total_pnl or 0,
                'average_pnl': row.avg_pnl or 0
            }


# Import uuid for trade_id generation
import uuid

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




# Export
__all__ = [
    'DatabaseManager',
    'TradeRecord',
    'PositionRecord',
    'OrderRecord',
    'AccountSnapshot',
    'MetricRecord',
    'SignalRecord',
    'AuditLog'
]
