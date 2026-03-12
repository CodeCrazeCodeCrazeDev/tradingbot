"""
Data Warehouse - Parquet Export and Analytics Pipeline
DuckDB/ClickHouse integration for historical analysis
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Try to import data processing libraries
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("Pandas not available")

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    logger.warning("PyArrow not available. Parquet export disabled.")

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    logger.warning("DuckDB not available")


class DataCategory(Enum):
    """Data categories for warehouse"""
    TRADES = "trades"
    ORDERS = "orders"
    POSITIONS = "positions"
    MARKET_DATA = "market_data"
    SIGNALS = "signals"
    PERFORMANCE = "performance"
    RISK_METRICS = "risk_metrics"
    SYSTEM_EVENTS = "system_events"


class ExportFormat(Enum):
    """Export formats"""
    PARQUET = "parquet"
    CSV = "csv"
    JSON = "json"


@dataclass
class DataPartition:
    """Data partition metadata"""
    partition_id: str
    category: DataCategory
    start_date: datetime
    end_date: datetime
    row_count: int
    file_path: str
    file_size_bytes: int
    created_at: datetime
    schema_version: str = "1.0"


@dataclass
class QueryResult:
    """Query result container"""
    query: str
    columns: List[str]
    data: List[List[Any]]
    row_count: int
    execution_time_ms: float
    
    def to_dataframe(self):
        if PANDAS_AVAILABLE:
            return pd.DataFrame(self.data, columns=self.columns)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'query': self.query,
            'columns': self.columns,
            'row_count': self.row_count,
            'execution_time_ms': self.execution_time_ms,
            'data': self.data[:100]  # Limit for serialization
        }


class DataWarehouse:
    """
    Data warehouse for trading analytics
    Supports Parquet export and DuckDB queries
    """
    
    # Schema definitions for each category
    SCHEMAS = {
        DataCategory.TRADES: {
            'trade_id': 'string',
            'timestamp': 'timestamp',
            'symbol': 'string',
            'side': 'string',
            'quantity': 'float64',
            'price': 'float64',
            'commission': 'float64',
            'pnl': 'float64',
            'strategy': 'string',
        },
        DataCategory.ORDERS: {
            'order_id': 'string',
            'timestamp': 'timestamp',
            'symbol': 'string',
            'side': 'string',
            'order_type': 'string',
            'quantity': 'float64',
            'price': 'float64',
            'status': 'string',
            'filled_quantity': 'float64',
            'avg_fill_price': 'float64',
        },
        DataCategory.MARKET_DATA: {
            'timestamp': 'timestamp',
            'symbol': 'string',
            'open': 'float64',
            'high': 'float64',
            'low': 'float64',
            'close': 'float64',
            'volume': 'float64',
            'vwap': 'float64',
        },
        DataCategory.POSITIONS: {
            'timestamp': 'timestamp',
            'symbol': 'string',
            'quantity': 'float64',
            'avg_price': 'float64',
            'market_value': 'float64',
            'unrealized_pnl': 'float64',
            'realized_pnl': 'float64',
        },
        DataCategory.SIGNALS: {
            'signal_id': 'string',
            'timestamp': 'timestamp',
            'symbol': 'string',
            'signal_type': 'string',
            'direction': 'string',
            'strength': 'float64',
            'confidence': 'float64',
            'strategy': 'string',
        },
        DataCategory.PERFORMANCE: {
            'timestamp': 'timestamp',
            'portfolio_value': 'float64',
            'daily_pnl': 'float64',
            'cumulative_pnl': 'float64',
            'sharpe_ratio': 'float64',
            'max_drawdown': 'float64',
            'win_rate': 'float64',
        },
        DataCategory.RISK_METRICS: {
            'timestamp': 'timestamp',
            'var_95': 'float64',
            'var_99': 'float64',
            'expected_shortfall': 'float64',
            'beta': 'float64',
            'correlation': 'float64',
            'volatility': 'float64',
        },
    }
    
    def __init__(self, storage_path: str = "data_warehouse", config: Optional[Dict] = None):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.config = config or {}
        
        # Create category directories
        for category in DataCategory:
            (self.storage_path / category.value).mkdir(exist_ok=True)
            
        # Partition tracking
        self.partitions: Dict[str, DataPartition] = {}
        self._load_partition_metadata()
        
        # DuckDB connection
        self.db_path = self.storage_path / "warehouse.duckdb"
        self.conn = None
        if DUCKDB_AVAILABLE:
            self._init_duckdb()
            
        # Buffer for batch writes
        self.write_buffers: Dict[DataCategory, List[Dict]] = {
            cat: [] for cat in DataCategory
        }
        self.buffer_size = self.config.get('buffer_size', 1000)
        
        logger.info(f"Data warehouse initialized at {self.storage_path}")
        
    def _init_duckdb(self):
        """Initialize DuckDB connection"""
        try:
            self.conn = duckdb.connect(str(self.db_path))
            
            # Create views for parquet files
            for category in DataCategory:
                parquet_path = self.storage_path / category.value / "*.parquet"
                try:
                    self.conn.execute(f"""
                        CREATE OR REPLACE VIEW {category.value} AS 
                        SELECT * FROM read_parquet('{parquet_path}')
                    """)
                except Exception:
                    pass  # No parquet files yet
                    
            logger.info("DuckDB initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DuckDB: {e}")
            self.conn = None
            
    def _load_partition_metadata(self):
        """Load partition metadata from disk"""
        metadata_file = self.storage_path / "partitions.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    for p in data:
                        p['category'] = DataCategory(p['category'])
                        p['start_date'] = datetime.fromisoformat(p['start_date'])
                        p['end_date'] = datetime.fromisoformat(p['end_date'])
                        p['created_at'] = datetime.fromisoformat(p['created_at'])
                        partition = DataPartition(**p)
                        self.partitions[partition.partition_id] = partition
            except Exception as e:
                logger.warning(f"Failed to load partition metadata: {e}")
                
    def _save_partition_metadata(self):
        """Save partition metadata to disk"""
        metadata_file = self.storage_path / "partitions.json"
        data = []
        for p in self.partitions.values():
            d = {
                'partition_id': p.partition_id,
                'category': p.category.value,
                'start_date': p.start_date.isoformat(),
                'end_date': p.end_date.isoformat(),
                'row_count': p.row_count,
                'file_path': p.file_path,
                'file_size_bytes': p.file_size_bytes,
                'created_at': p.created_at.isoformat(),
                'schema_version': p.schema_version
            }
            data.append(d)
            
        with open(metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
            
    def insert(self, category: DataCategory, data: Dict[str, Any]):
        """Insert single record into buffer"""
        self.write_buffers[category].append(data)
        
        if len(self.write_buffers[category]) >= self.buffer_size:
            self.flush(category)
            
    def insert_batch(self, category: DataCategory, records: List[Dict[str, Any]]):
        """Insert batch of records"""
        self.write_buffers[category].extend(records)
        
        if len(self.write_buffers[category]) >= self.buffer_size:
            self.flush(category)
            
    def flush(self, category: Optional[DataCategory] = None):
        """Flush buffer to parquet files"""
        categories = [category] if category else list(DataCategory)
        
        for cat in categories:
            if not self.write_buffers[cat]:
                continue
                
            self._write_parquet(cat, self.write_buffers[cat])
            self.write_buffers[cat] = []
            
    def _write_parquet(self, category: DataCategory, records: List[Dict[str, Any]]):
        """Write records to parquet file"""
        if not PYARROW_AVAILABLE or not PANDAS_AVAILABLE:
            logger.warning("Cannot write parquet: PyArrow or Pandas not available")
            return
            
        if not records:
            return
            
        # Create DataFrame
        df = pd.DataFrame(records)
        
        # Ensure timestamp column
        if 'timestamp' not in df.columns:
            df['timestamp'] = datetime.now()
            
        # Generate partition ID
        min_date = df['timestamp'].min()
        max_date = df['timestamp'].max()
        partition_id = f"{category.value}_{min_date.strftime('%Y%m%d_%H%M%S')}"
        
        # File path
        file_path = self.storage_path / category.value / f"{partition_id}.parquet"
        
        # Write parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, file_path, compression='snappy')
        
        # Update metadata
        file_size = file_path.stat().st_size
        partition = DataPartition(
            partition_id=partition_id,
            category=category,
            start_date=min_date,
            end_date=max_date,
            row_count=len(records),
            file_path=str(file_path),
            file_size_bytes=file_size,
            created_at=datetime.now()
        )
        self.partitions[partition_id] = partition
        self._save_partition_metadata()
        
        logger.info(f"Written {len(records)} records to {file_path}")
        
        # Refresh DuckDB view
        if self.conn:
            try:
                parquet_path = self.storage_path / category.value / "*.parquet"
                self.conn.execute(f"""
                    CREATE OR REPLACE VIEW {category.value} AS 
                    SELECT * FROM read_parquet('{parquet_path}')
                """)
            except Exception:
                pass
                
    def query(self, sql: str) -> Optional[QueryResult]:
        """Execute SQL query"""
        if not self.conn:
            logger.error("DuckDB not available")
            return None
            
        start_time = datetime.now()
        
        try:
            result = self.conn.execute(sql)
            columns = [desc[0] for desc in result.description]
            data = result.fetchall()
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return QueryResult(
                query=sql,
                columns=columns,
                data=[list(row) for row in data],
                row_count=len(data),
                execution_time_ms=execution_time
            )
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return None
            
    def get_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None
    ) -> Optional[QueryResult]:
        """Get trades with filters"""
        conditions = []
        
        if start_date:
            conditions.append(f"timestamp >= '{start_date.isoformat()}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date.isoformat()}'")
        if symbol:
            conditions.append(f"symbol = '{symbol}'")
        if strategy:
            conditions.append(f"strategy = '{strategy}'")
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT * FROM trades
            WHERE {where_clause}
            ORDER BY timestamp DESC
        """
        
        return self.query(sql)
    
    def get_performance_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[Dict[str, Any]]:
        """Get performance summary"""
        conditions = []
        
        if start_date:
            conditions.append(f"timestamp >= '{start_date.isoformat()}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date.isoformat()}'")
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"""
            SELECT 
                COUNT(*) as trade_count,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate,
                MAX(pnl) as best_trade,
                MIN(pnl) as worst_trade
            FROM trades
            WHERE {where_clause}
        """
        
        result = self.query(sql)
        if result and result.data:
            row = result.data[0]
            return {
                'trade_count': row[0],
                'total_pnl': row[1],
                'avg_pnl': row[2],
                'win_rate': row[3],
                'best_trade': row[4],
                'worst_trade': row[5]
            }
        return None
    
    def get_daily_pnl(
        self,
        days: int = 30
    ) -> Optional[QueryResult]:
        """Get daily P&L for last N days"""
        sql = f"""
            SELECT 
                DATE_TRUNC('day', timestamp) as date,
                SUM(pnl) as daily_pnl,
                COUNT(*) as trade_count
            FROM trades
            WHERE timestamp >= CURRENT_DATE - INTERVAL '{days} days'
            GROUP BY DATE_TRUNC('day', timestamp)
            ORDER BY date
        """
        
        return self.query(sql)
    
    def get_symbol_performance(self) -> Optional[QueryResult]:
        """Get performance by symbol"""
        sql = """
            SELECT 
                symbol,
                COUNT(*) as trade_count,
                SUM(pnl) as total_pnl,
                AVG(pnl) as avg_pnl,
                SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as win_rate
            FROM trades
            GROUP BY symbol
            ORDER BY total_pnl DESC
        """
        
        return self.query(sql)
    
    def export_to_parquet(
        self,
        category: DataCategory,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """Export data to single parquet file"""
        if not PYARROW_AVAILABLE:
            logger.error("PyArrow not available for export")
            return False
            
        conditions = []
        if start_date:
            conditions.append(f"timestamp >= '{start_date.isoformat()}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date.isoformat()}'")
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"SELECT * FROM {category.value} WHERE {where_clause}"
        
        try:
            if self.conn:
                self.conn.execute(f"COPY ({sql}) TO '{output_path}' (FORMAT PARQUET)")
                logger.info(f"Exported {category.value} to {output_path}")
                return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            
        return False
    
    def export_to_csv(
        self,
        category: DataCategory,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """Export data to CSV file"""
        conditions = []
        if start_date:
            conditions.append(f"timestamp >= '{start_date.isoformat()}'")
        if end_date:
            conditions.append(f"timestamp <= '{end_date.isoformat()}'")
            
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        sql = f"SELECT * FROM {category.value} WHERE {where_clause}"
        
        try:
            if self.conn:
                self.conn.execute(f"COPY ({sql}) TO '{output_path}' (FORMAT CSV, HEADER)")
                logger.info(f"Exported {category.value} to {output_path}")
                return True
        except Exception as e:
            logger.error(f"Export failed: {e}")
            
        return False
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'total_partitions': len(self.partitions),
            'total_size_bytes': 0,
            'total_rows': 0,
            'by_category': {}
        }
        
        for partition in self.partitions.values():
            stats['total_size_bytes'] += partition.file_size_bytes
            stats['total_rows'] += partition.row_count
            
            cat = partition.category.value
            if cat not in stats['by_category']:
                stats['by_category'][cat] = {
                    'partitions': 0,
                    'rows': 0,
                    'size_bytes': 0
                }
            stats['by_category'][cat]['partitions'] += 1
            stats['by_category'][cat]['rows'] += partition.row_count
            stats['by_category'][cat]['size_bytes'] += partition.file_size_bytes
            
        stats['total_size_mb'] = stats['total_size_bytes'] / (1024 * 1024)
        
        return stats
    
    def vacuum(self, older_than_days: int = 90):
        """Remove old partitions"""
        cutoff = datetime.now() - timedelta(days=older_than_days)
        removed = 0
        
        for partition_id, partition in list(self.partitions.items()):
            if partition.end_date < cutoff:
                try:
                    Path(partition.file_path).unlink()
                    del self.partitions[partition_id]
                    removed += 1
                except Exception as e:
                    logger.warning(f"Failed to remove partition {partition_id}: {e}")
                    
        if removed > 0:
            self._save_partition_metadata()
            logger.info(f"Vacuumed {removed} partitions")
            
        return removed
    
    def close(self):
        """Close warehouse connections"""
        # Flush all buffers
        self.flush()
        
        # Close DuckDB
        if self.conn:
            self.conn.close()
            
        logger.info("Data warehouse closed")
