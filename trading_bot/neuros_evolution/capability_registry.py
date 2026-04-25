"""
Capability Registry
===================

Persistent storage and management for distilled capabilities.
Tracks task-to-capability mappings, performance metrics, and routing decisions.
"""

import sqlite3
import json
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class CapabilityRecord:
    """Record of a distilled capability in the registry"""
    capability_id: str
    name: str
    task_category: str
    task_tags: List[str]
    source_model: str
    behaviors: List[Dict[str, Any]]
    controls: List[Dict[str, Any]]
    performance_score: float
    latency_ms: float
    reliability_score: float
    usage_count: int = 0
    success_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used: Optional[str] = None
    status: str = "active"  # active, deprecated, failed
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoutingDecision:
    """Record of a routing decision"""
    decision_id: str
    task_hash: str
    task_category: str
    selected_capability: str
    alternative_options: List[str]
    confidence: float
    latency_ms: float
    success: Optional[bool] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class CapabilityRegistry:
    """
    Persistent registry for distilled capabilities.
    
    Provides:
    - SQLite storage for capability records
    - Task-to-capability mappings
    - Performance tracking and statistics
    - Routing history for meta-learning
    """
    
    def __init__(self, db_path: str = "./capability_registry.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"CapabilityRegistry initialized at {db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """Initialize database schema"""
        with self._get_connection() as conn:
            # Capabilities table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS capabilities (
                    capability_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    task_category TEXT NOT NULL,
                    task_tags TEXT,  -- JSON array
                    source_model TEXT,
                    behaviors TEXT,  -- JSON
                    controls TEXT,   -- JSON
                    performance_score REAL DEFAULT 0.0,
                    latency_ms REAL DEFAULT 0.0,
                    reliability_score REAL DEFAULT 0.0,
                    usage_count INTEGER DEFAULT 0,
                    success_count INTEGER DEFAULT 0,
                    created_at TEXT,
                    last_used TEXT,
                    status TEXT DEFAULT 'active',
                    metadata TEXT  -- JSON
                )
            """)
            
            # Routing decisions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    decision_id TEXT PRIMARY KEY,
                    task_hash TEXT NOT NULL,
                    task_category TEXT,
                    selected_capability TEXT,
                    alternative_options TEXT,  -- JSON array
                    confidence REAL,
                    latency_ms REAL,
                    success INTEGER,  -- 0/1/NULL
                    created_at TEXT
                )
            """)
            
            # Performance metrics table (time-series)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    capability_id TEXT,
                    metric_name TEXT,
                    metric_value REAL,
                    recorded_at TEXT
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cap_category ON capabilities(task_category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cap_status ON capabilities(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_route_task ON routing_decisions(task_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_perf_cap ON performance_metrics(capability_id)")
            
            conn.commit()
    
    def register_capability(self, record: CapabilityRecord) -> str:
        """Register a new capability"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO capabilities (
                    capability_id, name, task_category, task_tags, source_model,
                    behaviors, controls, performance_score, latency_ms, reliability_score,
                    usage_count, success_count, created_at, last_used, status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.capability_id,
                record.name,
                record.task_category,
                json.dumps(record.task_tags),
                record.source_model,
                json.dumps(record.behaviors),
                json.dumps(record.controls),
                record.performance_score,
                record.latency_ms,
                record.reliability_score,
                record.usage_count,
                record.success_count,
                record.created_at,
                record.last_used,
                record.status,
                json.dumps(record.metadata)
            ))
            conn.commit()
        
        logger.info(f"Registered capability {record.capability_id} for {record.task_category}")
        return record.capability_id
    
    def get_capability(self, capability_id: str) -> Optional[CapabilityRecord]:
        """Get a capability by ID"""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM capabilities WHERE capability_id = ?",
                (capability_id,)
            ).fetchone()
            
            if row:
                return self._row_to_capability(row)
            return None
    
    def find_capabilities_for_task(self, task_category: str, 
                                    min_score: float = 0.0,
                                    limit: int = 10) -> List[CapabilityRecord]:
        """Find capabilities for a task category, ranked by performance"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM capabilities 
                WHERE task_category = ? 
                AND status = 'active'
                AND performance_score >= ?
                ORDER BY performance_score DESC, reliability_score DESC
                LIMIT ?
            """, (task_category, min_score, limit)).fetchall()
            
            return [self._row_to_capability(row) for row in rows]
    
    def find_capabilities_by_tags(self, tags: List[str], 
                                 min_score: float = 0.0) -> List[CapabilityRecord]:
        """Find capabilities matching any of the given tags"""
        capabilities = []
        
        with self._get_connection() as conn:
            # Get all active capabilities
            rows = conn.execute("""
                SELECT * FROM capabilities 
                WHERE status = 'active'
                AND performance_score >= ?
            """, (min_score,)).fetchall()
            
            for row in rows:
                record = self._row_to_capability(row)
                # Check if any tag matches
                if any(tag in record.task_tags for tag in tags):
                    capabilities.append(record)
        
        # Sort by performance
        capabilities.sort(key=lambda x: x.performance_score, reverse=True)
        return capabilities
    
    def update_capability_performance(self, capability_id: str, 
                                     success: bool,
                                     latency_ms: float,
                                     additional_metrics: Optional[Dict[str, float]] = None):
        """Update capability performance metrics after use"""
        now = datetime.utcnow().isoformat()
        
        with self._get_connection() as conn:
            # Update usage stats
            conn.execute("""
                UPDATE capabilities 
                SET usage_count = usage_count + 1,
                    success_count = success_count + ?,
                    last_used = ?
                WHERE capability_id = ?
            """, (1 if success else 0, now, capability_id))
            
            # Record metrics
            if additional_metrics:
                for metric_name, value in additional_metrics.items():
                    conn.execute("""
                        INSERT INTO performance_metrics 
                        (capability_id, metric_name, metric_value, recorded_at)
                        VALUES (?, ?, ?, ?)
                    """, (capability_id, metric_name, value, now))
            
            conn.commit()
        
        logger.debug(f"Updated performance for {capability_id}: success={success}")
    
    def deprecate_capability(self, capability_id: str, reason: str = ""):
        """Mark a capability as deprecated"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE capabilities 
                SET status = 'deprecated',
                    metadata = json_set(metadata, '$.deprecation_reason', ?)
                WHERE capability_id = ?
            """, (reason, capability_id))
            conn.commit()
        
        logger.info(f"Deprecated capability {capability_id}: {reason}")
    
    def record_routing_decision(self, decision: RoutingDecision):
        """Record a routing decision for meta-learning"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO routing_decisions 
                (decision_id, task_hash, task_category, selected_capability,
                 alternative_options, confidence, latency_ms, success, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision.decision_id,
                decision.task_hash,
                decision.task_category,
                decision.selected_capability,
                json.dumps(decision.alternative_options),
                decision.confidence,
                decision.latency_ms,
                1 if decision.success else 0 if decision.success is False else None,
                decision.created_at
            ))
            conn.commit()
    
    def update_routing_outcome(self, decision_id: str, success: bool):
        """Update the outcome of a routing decision"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE routing_decisions 
                SET success = ?
                WHERE decision_id = ?
            """, (1 if success else 0, decision_id))
            conn.commit()
    
    def get_routing_history(self, task_category: Optional[str] = None,
                           limit: int = 100) -> List[RoutingDecision]:
        """Get routing decision history"""
        with self._get_connection() as conn:
            if task_category:
                rows = conn.execute("""
                    SELECT * FROM routing_decisions 
                    WHERE task_category = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (task_category, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM routing_decisions 
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()
            
            return [self._row_to_routing(row) for row in rows]
    
    def get_capability_stats(self, capability_id: str) -> Dict[str, Any]:
        """Get statistics for a capability"""
        with self._get_connection() as conn:
            # Basic stats
            row = conn.execute("""
                SELECT usage_count, success_count, performance_score, reliability_score
                FROM capabilities WHERE capability_id = ?
            """, (capability_id,)).fetchone()
            
            if not row:
                return {}
            
            # Performance trend
            metrics = conn.execute("""
                SELECT metric_name, metric_value, recorded_at
                FROM performance_metrics
                WHERE capability_id = ?
                ORDER BY recorded_at DESC
                LIMIT 100
            """, (capability_id,)).fetchall()
            
            # Recent routing decisions
            routing = conn.execute("""
                SELECT COUNT(*) as total, SUM(success) as successes
                FROM routing_decisions
                WHERE selected_capability = ?
                AND created_at > datetime('now', '-7 days')
            """, (capability_id,)).fetchone()
            
            return {
                'capability_id': capability_id,
                'total_usage': row['usage_count'],
                'success_rate': row['success_count'] / max(1, row['usage_count']),
                'performance_score': row['performance_score'],
                'reliability_score': row['reliability_score'],
                'recent_routing_total': routing['total'] or 0,
                'recent_routing_success_rate': (routing['successes'] or 0) / max(1, routing['total'] or 1),
                'performance_trend': self._calculate_trend(metrics)
            }
    
    def get_all_capabilities(self, status: Optional[str] = None) -> List[CapabilityRecord]:
        """Get all capabilities, optionally filtered by status"""
        with self._get_connection() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM capabilities WHERE status = ?",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM capabilities").fetchall()
            
            return [self._row_to_capability(row) for row in rows]
    
    def get_leaderboard(self, task_category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get capability leaderboard"""
        with self._get_connection() as conn:
            if task_category:
                rows = conn.execute("""
                    SELECT capability_id, name, task_category, performance_score,
                           reliability_score, usage_count, source_model
                    FROM capabilities
                    WHERE task_category = ? AND status = 'active'
                    ORDER BY performance_score DESC
                """, (task_category,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT capability_id, name, task_category, performance_score,
                           reliability_score, usage_count, source_model
                    FROM capabilities
                    WHERE status = 'active'
                    ORDER BY performance_score DESC
                """).fetchall()
            
            return [{
                'capability_id': row['capability_id'],
                'name': row['name'],
                'task_category': row['task_category'],
                'performance_score': row['performance_score'],
                'reliability_score': row['reliability_score'],
                'usage_count': row['usage_count'],
                'source_model': row['source_model']
            } for row in rows]
    
    def _row_to_capability(self, row: sqlite3.Row) -> CapabilityRecord:
        """Convert database row to CapabilityRecord"""
        return CapabilityRecord(
            capability_id=row['capability_id'],
            name=row['name'],
            task_category=row['task_category'],
            task_tags=json.loads(row['task_tags']) if row['task_tags'] else [],
            source_model=row['source_model'],
            behaviors=json.loads(row['behaviors']) if row['behaviors'] else [],
            controls=json.loads(row['controls']) if row['controls'] else [],
            performance_score=row['performance_score'],
            latency_ms=row['latency_ms'],
            reliability_score=row['reliability_score'],
            usage_count=row['usage_count'],
            success_count=row['success_count'],
            created_at=row['created_at'],
            last_used=row['last_used'],
            status=row['status'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {}
        )
    
    def _row_to_routing(self, row: sqlite3.Row) -> RoutingDecision:
        """Convert database row to RoutingDecision"""
        success_val = row['success']
        success = True if success_val == 1 else False if success_val == 0 else None
        
        return RoutingDecision(
            decision_id=row['decision_id'],
            task_hash=row['task_hash'],
            task_category=row['task_category'],
            selected_capability=row['selected_capability'],
            alternative_options=json.loads(row['alternative_options']) if row['alternative_options'] else [],
            confidence=row['confidence'],
            latency_ms=row['latency_ms'],
            success=success,
            created_at=row['created_at']
        )
    
    def _calculate_trend(self, metrics: List[sqlite3.Row]) -> str:
        """Calculate performance trend from metrics"""
        if len(metrics) < 10:
            return "insufficient_data"
        
        # Get recent vs older values
        recent = [m['metric_value'] for m in metrics[:len(metrics)//2]]
        older = [m['metric_value'] for m in metrics[len(metrics)//2:]]
        
        recent_avg = np.mean(recent) if recent else 0
        older_avg = np.mean(older) if older else 0
        
        diff = recent_avg - older_avg
        if abs(diff) < 0.01:
            return "stable"
        return "improving" if diff > 0 else "declining"
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """Get registry summary statistics"""
        with self._get_connection() as conn:
            # Count by status
            status_counts = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM capabilities
                GROUP BY status
            """).fetchall()
            
            # Count by category
            category_counts = conn.execute("""
                SELECT task_category, COUNT(*) as count
                FROM capabilities
                WHERE status = 'active'
                GROUP BY task_category
            """).fetchall()
            
            # Recent routing decisions
            routing_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
                    AVG(confidence) as avg_confidence
                FROM routing_decisions
                WHERE created_at > datetime('now', '-24 hours')
            """).fetchone()
            
            return {
                'total_capabilities': sum(row['count'] for row in status_counts),
                'by_status': {row['status']: row['count'] for row in status_counts},
                'by_category': {row['task_category']: row['count'] for row in category_counts},
                'recent_routing': {
                    'total': routing_stats['total'] or 0,
                    'success_rate': (routing_stats['successes'] or 0) / max(1, routing_stats['total'] or 1),
                    'avg_confidence': routing_stats['avg_confidence'] or 0
                }
            }


def create_registry(db_path: str = "./capability_registry.db") -> CapabilityRegistry:
    """Factory function to create a capability registry"""
    return CapabilityRegistry(db_path)
