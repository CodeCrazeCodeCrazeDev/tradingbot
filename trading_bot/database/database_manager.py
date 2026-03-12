"""
Database Manager for Trading Bot
Stores trade history, performance metrics, and analytics
"""

import sqlite3
import asyncio
# Using synchronous sqlite3 instead of aiosqlite
import pandas as pd
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import pandas

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages all database operations for the trading bot
    """
    
    def __init__(self, db_path: str = "trading_bot.db"):
        try:
            self.db_path = db_path
            self.connection = None
        
            # Ensure database directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def initialize(self):
        """Initialize database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as db:
                # Create tables
                self._create_tables(db)
                db.commit()
            
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def _create_tables(self, db):
        """Create all required tables"""
        
        # Trades table
        try:
            db.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT UNIQUE,
                    timestamp DATETIME,
                    symbol TEXT,
                    exchange TEXT,
                    side TEXT,
                    quantity REAL,
                    entry_price REAL,
                    exit_price REAL,
                    pnl REAL,
                    fees REAL,
                    strategy TEXT,
                    opportunity_type TEXT,
                    confidence REAL,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
            # Opportunities table
            db.execute("""
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    opportunity_id TEXT UNIQUE,
                    timestamp DATETIME,
                    type TEXT,
                    symbol TEXT,
                    confidence REAL,
                    expected_return REAL,
                    risk_score REAL,
                    executed BOOLEAN DEFAULT 0,
                    trade_id TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
            # Performance metrics table
            db.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    metric_type TEXT,
                    value REAL,
                    period TEXT,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
            # Market data table (for analysis)
            db.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    exchange TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
            # Alerts table
            db.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    timestamp DATETIME,
                    type TEXT,
                    severity TEXT,
                    message TEXT,
                    acknowledged BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        
            # Create indexes for performance
            db.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp ON opportunities(timestamp)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp ON market_data(symbol, timestamp)")
        except Exception as e:
            logger.error(f"Error in _create_tables: {e}")
            raise
    
    def save_trade(self, trade: Dict):
        """Save trade to database"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT OR REPLACE INTO trades 
                    (trade_id, timestamp, symbol, exchange, side, quantity, 
                     entry_price, exit_price, pnl, fees, strategy, 
                     opportunity_type, confidence, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.get('trade_id', str(datetime.now().timestamp())),
                    trade.get('timestamp', datetime.now()),
                    trade.get('symbol'),
                    trade.get('exchange', 'unknown'),
                    trade.get('side'),
                    trade.get('quantity'),
                    trade.get('entry_price'),
                    trade.get('exit_price'),
                    trade.get('pnl', 0),
                    trade.get('fees', 0),
                    trade.get('strategy'),
                    trade.get('opportunity_type'),
                    trade.get('confidence'),
                    json.dumps(trade.get('metadata', {}))
                ))
                db.commit()
        except Exception as e:
            logger.error(f"Error in save_trade: {e}")
            raise
    
    def save_opportunity(self, opportunity: Dict):
        """Save opportunity to database"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT OR REPLACE INTO opportunities 
                    (opportunity_id, timestamp, type, symbol, confidence, 
                     expected_return, risk_score, executed, trade_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opportunity.get('opportunity_id', str(datetime.now().timestamp())),
                    opportunity.get('timestamp', datetime.now()),
                    opportunity.get('type'),
                    opportunity.get('symbol'),
                    opportunity.get('confidence'),
                    opportunity.get('expected_return'),
                    opportunity.get('risk_score'),
                    opportunity.get('executed', False),
                    opportunity.get('trade_id'),
                    json.dumps(opportunity.get('metadata', {}))
                ))
                db.commit()
        except Exception as e:
            logger.error(f"Error in save_opportunity: {e}")
            raise
    
    def save_performance_metric(self, metric: Dict):
        """Save performance metric"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, metric_type, value, period, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    metric.get('timestamp', datetime.now()),
                    metric.get('metric_type'),
                    metric.get('value'),
                    metric.get('period', 'daily'),
                    json.dumps(metric.get('metadata', {}))
                ))
                db.commit()
        except Exception as e:
            logger.error(f"Error in save_performance_metric: {e}")
            raise
    
    def save_market_data(self, data: Dict):
        """Save market data point"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT INTO market_data 
                    (timestamp, symbol, exchange, open, high, low, close, volume)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('timestamp', datetime.now()),
                    data.get('symbol'),
                    data.get('exchange', 'unknown'),
                    data.get('open'),
                    data.get('high'),
                    data.get('low'),
                    data.get('close'),
                    data.get('volume')
                ))
                db.commit()
        except Exception as e:
            logger.error(f"Error in save_market_data: {e}")
            raise
    
    def save_alert(self, alert: Dict):
        """Save alert to database"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute("""
                    INSERT OR REPLACE INTO alerts 
                    (alert_id, timestamp, type, severity, message, acknowledged, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.get('alert_id', str(datetime.now().timestamp())),
                    alert.get('timestamp', datetime.now()),
                    alert.get('type'),
                    alert.get('severity'),
                    alert.get('message'),
                    alert.get('acknowledged', False),
                    json.dumps(alert.get('metadata', {}))
                ))
                db.commit()
        except Exception as e:
            logger.error(f"Error in save_alert: {e}")
            raise
    
    def get_trades(self, symbol: str = None, start_date: datetime = None, 
                        end_date: datetime = None) -> List[Dict]:
        """Get trades from database"""
        try:
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
        
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
        
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
        
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
        
            query += " ORDER BY timestamp DESC"
        
            with sqlite3.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                cursor = db.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error in get_trades: {e}")
            raise
    
    def get_performance_metrics(self, metric_type: str = None, 
                                     period: str = None) -> List[Dict]:
        """Get performance metrics"""
        try:
            query = "SELECT * FROM performance_metrics WHERE 1=1"
            params = []
        
            if metric_type:
                query += " AND metric_type = ?"
                params.append(metric_type)
        
            if period:
                query += " AND period = ?"
                params.append(period)
        
            query += " ORDER BY timestamp DESC"
        
            with sqlite3.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                cursor = db.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error in get_performance_metrics: {e}")
            raise
    
    def get_trade_statistics(self, start_date: datetime = None, 
                                  end_date: datetime = None) -> Dict:
        """Calculate trade statistics"""
        try:
            trades = self.get_trades(start_date=start_date, end_date=end_date)
        
            if not trades:
                return {
                    'total_trades': 0,
                    'winning_trades': 0,
                    'losing_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'average_pnl': 0,
                    'best_trade': 0,
                    'worst_trade': 0
                }
        
            df = pd.DataFrame(trades)
        
            return {
                'total_trades': len(df),
                'winning_trades': len(df[df['pnl'] > 0]),
                'losing_trades': len(df[df['pnl'] <= 0]),
                'win_rate': len(df[df['pnl'] > 0]) / len(df) if len(df) > 0 else 0,
                'total_pnl': df['pnl'].sum(),
                'average_pnl': df['pnl'].mean(),
                'best_trade': df['pnl'].max(),
                'worst_trade': df['pnl'].min(),
                'by_symbol': df.groupby('symbol')['pnl'].sum().to_dict(),
                'by_strategy': df.groupby('strategy')['pnl'].sum().to_dict() if 'strategy' in df else {}
            }
        except Exception as e:
            logger.error(f"Error in get_trade_statistics: {e}")
            raise
    
    def get_unacknowledged_alerts(self) -> List[Dict]:
        """Get unacknowledged alerts"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.row_factory = sqlite3.Row
                cursor = db.execute(
                    "SELECT * FROM alerts WHERE acknowledged = 0 ORDER BY timestamp DESC"
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Error in get_unacknowledged_alerts: {e}")
            raise
    
    def acknowledge_alert(self, alert_id: str):
        """Mark alert as acknowledged"""
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute(
                    "UPDATE alerts SET acknowledged = 1 WHERE alert_id = ?",
                    (alert_id,)
                )
                db.commit()
        except Exception as e:
            logger.error(f"Error in acknowledge_alert: {e}")
            raise
    
    def cleanup_old_data(self, days: int = 90):
        """Clean up old data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
        
            with sqlite3.connect(self.db_path) as db:
                # Clean old market data (keep less history)
                db.execute(
                    "DELETE FROM market_data WHERE timestamp < ?",
                    (cutoff_date,)
                )
            
                # Clean old acknowledged alerts
                db.execute(
                    "DELETE FROM alerts WHERE acknowledged = 1 AND timestamp < ?",
                    (cutoff_date,)
                )
            
                db.commit()
            
            logger.info(f"Cleaned up data older than {days} days")
        except Exception as e:
            logger.error(f"Error in cleanup_old_data: {e}")
            raise
