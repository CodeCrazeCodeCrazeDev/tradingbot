"""
Database management for AlphaAlgo 2.0
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import sqlite3
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """
    SQLite database manager for persistent storage.
    """
    
    def __init__(self, db_path: str = "data/alphaalgo.db"):
        self.db_path = db_path
        self.conn = None
        
        # Create database directory
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize()
        
        logger.info(f"✅ Database initialized: {db_path}")
    
    def _initialize(self):
        """Initialize database connection and tables."""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                entry_time TIMESTAMP NOT NULL,
                exit_time TIMESTAMP,
                pnl REAL,
                status TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL,
                filled_quantity REAL DEFAULT 0,
                filled_price REAL,
                status TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP NOT NULL,
                equity REAL NOT NULL,
                pnl REAL NOT NULL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                win_rate REAL,
                total_trades INTEGER,
                metadata TEXT
            )
        """)
        
        # Model checkpoints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                version TEXT NOT NULL,
                path TEXT NOT NULL,
                metrics TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.info("✅ Database tables created")
    
    def save_trade(self, trade: Dict):
        """Save trade to database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO trades 
            (trade_id, symbol, side, quantity, entry_price, exit_price, 
             entry_time, exit_time, pnl, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade['trade_id'],
            trade['symbol'],
            trade['side'],
            trade['quantity'],
            trade['entry_price'],
            trade.get('exit_price'),
            trade['entry_time'],
            trade.get('exit_time'),
            trade.get('pnl'),
            trade['status'],
            json.dumps(trade.get('metadata', {}))
        ))
        
        self.conn.commit()
    
    def get_trades(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get trades from database."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM trades WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY entry_time DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        trades = []
        for row in cursor.fetchall():
            trade = dict(row)
            if trade['metadata']:
                trade['metadata'] = json.loads(trade['metadata'])
            trades.append(trade)
        
        return trades
    
    def save_position(self, position: Dict):
        """Save position to database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO positions 
            (symbol, quantity, entry_price, current_price, unrealized_pnl, realized_pnl)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            position['symbol'],
            position['quantity'],
            position['entry_price'],
            position.get('current_price'),
            position.get('unrealized_pnl'),
            position.get('realized_pnl')
        ))
        
        self.conn.commit()
    
    def get_positions(self) -> List[Dict]:
        """Get all positions from database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM positions WHERE quantity != 0")
        
        return [dict(row) for row in cursor.fetchall()]
    
    def save_order(self, order: Dict):
        """Save order to database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO orders 
            (order_id, symbol, side, type, quantity, price, filled_quantity, 
             filled_price, status, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order['order_id'],
            order['symbol'],
            order['side'],
            order['type'],
            order['quantity'],
            order.get('price'),
            order.get('filled_quantity', 0),
            order.get('filled_price'),
            order['status'],
            json.dumps(order.get('metadata', {}))
        ))
        
        self.conn.commit()
    
    def get_orders(
        self,
        symbol: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get orders from database."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM orders WHERE 1=1"
        params = []
        
        if symbol:
            query += " AND symbol = ?"
            params.append(symbol)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        
        orders = []
        for row in cursor.fetchall():
            order = dict(row)
            if order['metadata']:
                order['metadata'] = json.loads(order['metadata'])
            orders.append(order)
        
        return orders
    
    def save_performance(self, performance: Dict):
        """Save performance metrics to database."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO performance 
            (timestamp, equity, pnl, sharpe_ratio, max_drawdown, win_rate, 
             total_trades, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            performance['timestamp'],
            performance['equity'],
            performance['pnl'],
            performance.get('sharpe_ratio'),
            performance.get('max_drawdown'),
            performance.get('win_rate'),
            performance.get('total_trades'),
            json.dumps(performance.get('metadata', {}))
        ))
        
        self.conn.commit()
    
    def get_performance_history(self, days: int = 30) -> List[Dict]:
        """Get performance history."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM performance 
            WHERE timestamp >= datetime('now', '-' || ? || ' days')
            ORDER BY timestamp DESC
        """, (days,))
        
        history = []
        for row in cursor.fetchall():
            perf = dict(row)
            if perf['metadata']:
                perf['metadata'] = json.loads(perf['metadata'])
            history.append(perf)
        
        return history
    
    def save_model_checkpoint(self, checkpoint: Dict):
        """Save model checkpoint metadata."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO model_checkpoints 
            (model_name, version, path, metrics)
            VALUES (?, ?, ?, ?)
        """, (
            checkpoint['model_name'],
            checkpoint['version'],
            checkpoint['path'],
            json.dumps(checkpoint.get('metrics', {}))
        ))
        
        self.conn.commit()
    
    def get_latest_checkpoint(self, model_name: str) -> Optional[Dict]:
        """Get latest model checkpoint."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            SELECT * FROM model_checkpoints 
            WHERE model_name = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (model_name,))
        
        row = cursor.fetchone()
        if row:
            checkpoint = dict(row)
            if checkpoint['metrics']:
                checkpoint['metrics'] = json.loads(checkpoint['metrics'])
            return checkpoint
        
        return None
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")
