"""
Decision Layer Persistence

Saves and loads decisions, concept weights, and performance metrics.

Author: AlphaAlgo Integration Team
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .core_types import AggregatedDecision, DecisionResult, DecisionAction, DecisionCategory

logger = logging.getLogger(__name__)


class DecisionPersistence:
    """
    Persistence layer for decision layer.
    
    Stores:
    - Decision history
    - Concept weights
    - Concept performance
    - Configuration
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or "decision_layer_data/decisions.db"
        self.db_dir = Path(self.db_path).parent
        self.db_dir.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        
        logger.info(f"DecisionPersistence initialized: {self.db_path}")
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Decisions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                consensus_level REAL NOT NULL,
                position_size REAL,
                contributing_count INTEGER,
                dissenting_count INTEGER,
                reasoning TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Concept weights table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_weights (
                concept_id INTEGER PRIMARY KEY,
                concept_name TEXT NOT NULL,
                category TEXT NOT NULL,
                weight REAL NOT NULL,
                enabled INTEGER NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Concept performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS concept_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                success INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Decision results table (individual concept results)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decision_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_id INTEGER NOT NULL,
                concept_id INTEGER NOT NULL,
                concept_name TEXT NOT NULL,
                category TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                urgency TEXT NOT NULL,
                reasoning TEXT,
                factors TEXT,
                FOREIGN KEY (decision_id) REFERENCES decisions(id)
            )
        ''')
        
        # Create indices
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decisions_symbol ON decisions(symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_concept_performance_concept_id ON concept_performance(concept_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_decision_results_decision_id ON decision_results(decision_id)')
        
        conn.commit()
        conn.close()
    
    def save_decision(self, decision: AggregatedDecision, symbol: Optional[str] = None) -> int:
        """
        Save aggregated decision to database.
        
        Returns:
            decision_id
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Save main decision
            cursor.execute('''
                INSERT INTO decisions (
                    timestamp, symbol, action, confidence, consensus_level,
                    position_size, contributing_count, dissenting_count, reasoning, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision.timestamp.isoformat(),
                symbol,
                decision.final_action.value,
                decision.final_confidence,
                decision.consensus_level,
                decision.position_size_multiplier,
                len(decision.contributing_concepts),
                len(decision.dissenting_concepts),
                json.dumps(decision.reasoning_chain),
                json.dumps({
                    'risk_adjusted_action': decision.risk_adjusted_action.value
                })
            ))
            
            decision_id = cursor.lastrowid
            
            # Save contributing concept results
            for result in decision.contributing_concepts:
                self._save_decision_result(cursor, decision_id, result)
            
            # Save dissenting concept results
            for result in decision.dissenting_concepts:
                self._save_decision_result(cursor, decision_id, result)
            
            conn.commit()
            return decision_id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving decision: {e}")
            raise
        finally:
            conn.close()
    
    def _save_decision_result(self, cursor, decision_id: int, result: DecisionResult):
        """Save individual concept result"""
        cursor.execute('''
            INSERT INTO decision_results (
                decision_id, concept_id, concept_name, category,
                action, confidence, urgency, reasoning, factors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            decision_id,
            result.concept_id,
            result.concept_name,
            result.category.value,
            result.action.value,
            result.confidence,
            result.urgency.value,
            result.reasoning,
            json.dumps(result.factors)
        ))
    
    def save_concept_weights(self, concepts: List[Any]):
        """Save concept weights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for concept in concepts:
                cursor.execute('''
                    INSERT OR REPLACE INTO concept_weights (
                        concept_id, concept_name, category, weight, enabled, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    concept.concept_id,
                    concept.name,
                    concept.category.value,
                    concept.weight,
                    1 if concept.enabled else 0,
                    datetime.utcnow().isoformat()
                ))
            
            conn.commit()
            logger.info(f"Saved weights for {len(concepts)} concepts")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error saving concept weights: {e}")
            raise
        finally:
            conn.close()
    
    def load_concept_weights(self) -> Dict[int, Dict[str, Any]]:
        """Load concept weights"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT concept_id, weight, enabled FROM concept_weights')
        rows = cursor.fetchall()
        conn.close()
        
        weights = {}
        for concept_id, weight, enabled in rows:
            weights[concept_id] = {
                'weight': weight,
                'enabled': bool(enabled)
            }
        
        logger.info(f"Loaded weights for {len(weights)} concepts")
        return weights
    
    def save_concept_performance(self, concept_id: int, success: bool):
        """Save concept performance result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO concept_performance (concept_id, timestamp, success)
            VALUES (?, ?, ?)
        ''', (
            concept_id,
            datetime.utcnow().isoformat(),
            1 if success else 0
        ))
        
        conn.commit()
        conn.close()
    
    def get_concept_performance(self, concept_id: int, limit: int = 100) -> List[bool]:
        """Get recent performance for a concept"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT success FROM concept_performance
            WHERE concept_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (concept_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [bool(row[0]) for row in rows]
    
    def get_decision_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get decision history with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM decisions WHERE 1=1'
        params = []
        
        if symbol:
            query += ' AND symbol = ?'
            params.append(symbol)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date.isoformat())
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date.isoformat())
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        decisions = []
        for row in rows:
            decision = dict(zip(columns, row))
            # Parse JSON fields
            if decision.get('reasoning'):
                decision['reasoning'] = json.loads(decision['reasoning'])
            if decision.get('metadata'):
                decision['metadata'] = json.loads(decision['metadata'])
            decisions.append(decision)
        
        return decisions
    
    def get_concept_statistics(self) -> Dict[int, Dict[str, Any]]:
        """Get statistics for all concepts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                concept_id,
                COUNT(*) as total,
                SUM(success) as successes,
                AVG(success) as accuracy
            FROM concept_performance
            GROUP BY concept_id
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for concept_id, total, successes, accuracy in rows:
            stats[concept_id] = {
                'total': total,
                'successes': successes,
                'accuracy': accuracy,
                'failures': total - successes
            }
        
        return stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total decisions
        cursor.execute('SELECT COUNT(*) FROM decisions')
        total_decisions = cursor.fetchone()[0]
        
        # Average confidence
        cursor.execute('SELECT AVG(confidence) FROM decisions')
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Average consensus
        cursor.execute('SELECT AVG(consensus_level) FROM decisions')
        avg_consensus = cursor.fetchone()[0] or 0.0
        
        # Action distribution
        cursor.execute('''
            SELECT action, COUNT(*) as count
            FROM decisions
            GROUP BY action
        ''')
        action_dist = dict(cursor.fetchall())
        
        # Recent performance (last 100 decisions)
        cursor.execute('''
            SELECT concept_id, AVG(success) as accuracy
            FROM (
                SELECT concept_id, success
                FROM concept_performance
                ORDER BY timestamp DESC
                LIMIT 100
            )
            GROUP BY concept_id
            ORDER BY accuracy DESC
            LIMIT 10
        ''')
        top_concepts = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_decisions': total_decisions,
            'avg_confidence': avg_confidence,
            'avg_consensus': avg_consensus,
            'action_distribution': action_dist,
            'top_concepts': [
                {'concept_id': cid, 'accuracy': acc}
                for cid, acc in top_concepts
            ]
        }
    
    def cleanup_old_data(self, days: int = 90):
        """Remove data older than specified days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.utcnow().replace(day=datetime.utcnow().day - days)
        cutoff_str = cutoff.isoformat()
        
        # Delete old decisions
        cursor.execute('DELETE FROM decisions WHERE timestamp < ?', (cutoff_str,))
        decisions_deleted = cursor.rowcount
        
        # Delete old performance records
        cursor.execute('DELETE FROM concept_performance WHERE timestamp < ?', (cutoff_str,))
        performance_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {decisions_deleted} decisions and {performance_deleted} performance records")
        
        return {
            'decisions_deleted': decisions_deleted,
            'performance_deleted': performance_deleted
        }
    
    def export_to_json(self, output_path: str, limit: int = 1000):
        """Export decisions to JSON file"""
        decisions = self.get_decision_history(limit=limit)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(decisions, f, indent=2, default=str)
        
        logger.info(f"Exported {len(decisions)} decisions to {output_path}")
        
        return len(decisions)
