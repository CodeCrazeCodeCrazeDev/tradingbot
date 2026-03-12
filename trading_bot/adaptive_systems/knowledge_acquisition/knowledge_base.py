"""Knowledge Base for Self-Improving Trading Bot.

This module implements a comprehensive knowledge base that stores and manages
knowledge acquired from various sources.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class KnowledgeType(Enum):
    """Types of knowledge that can be stored."""
    BOOK = "book"
    HUMAN = "human"
    AI = "ai"
    ALGORITHM = "algorithm"
    GENERATED = "generated"
    HYBRID = "hybrid"


class KnowledgeStatus(Enum):
    """Status of knowledge items."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    APPLIED = "applied"
    REJECTED = "rejected"
    OUTDATED = "outdated"


@dataclass
class KnowledgeItem:
    """A single item of knowledge."""
    id: str
    title: str
    content: str
    knowledge_type: KnowledgeType
    source: str
    tags: List[str]
    confidence: float
    acquisition_date: datetime
    status: KnowledgeStatus = KnowledgeStatus.UNVERIFIED
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_ids: List[str] = field(default_factory=list)
    application_count: int = 0
    last_applied: Optional[datetime] = None
    verification_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "knowledge_type": self.knowledge_type.value,
            "source": self.source,
            "tags": self.tags,
            "confidence": self.confidence,
            "acquisition_date": self.acquisition_date.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
            "related_ids": self.related_ids,
            "application_count": self.application_count,
            "last_applied": self.last_applied.isoformat() if self.last_applied else None,
            "verification_score": self.verification_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeItem':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            knowledge_type=KnowledgeType(data["knowledge_type"]),
            source=data["source"],
            tags=data["tags"],
            confidence=data["confidence"],
            acquisition_date=datetime.fromisoformat(data["acquisition_date"]),
            status=KnowledgeStatus(data["status"]),
            metadata=data["metadata"],
            related_ids=data["related_ids"],
            application_count=data["application_count"],
            last_applied=datetime.fromisoformat(data["last_applied"]) if data["last_applied"] else None,
            verification_score=data["verification_score"]
        )


class KnowledgeBase:
    """Knowledge base for storing and retrieving knowledge items."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize the knowledge base.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or os.path.join(
            Path.home(), ".trading_bot", "knowledge_base.db"
        )
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        logger.info(f"Knowledge base initialized at {self.db_path}")
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create knowledge items table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_items (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            knowledge_type TEXT NOT NULL,
            acquisition_date TEXT NOT NULL,
            status TEXT NOT NULL,
            confidence REAL NOT NULL
        )
        ''')
        
        # Create tags table for efficient searching
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_tags (
            id TEXT NOT NULL,
            tag TEXT NOT NULL,
            PRIMARY KEY (id, tag),
            FOREIGN KEY (id) REFERENCES knowledge_items (id) ON DELETE CASCADE
        )
        ''')
        
        # Create index on knowledge type and status
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type_status ON knowledge_items (knowledge_type, status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags ON knowledge_tags (tag)')
        
        conn.commit()
        conn.close()
    
    def add_item(self, item: KnowledgeItem) -> str:
        """Add a knowledge item to the database.
        
        Args:
            item: Knowledge item to add
            
        Returns:
            ID of the added item
        """
        if not item.id:
            item.id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert knowledge item
            cursor.execute(
                "INSERT INTO knowledge_items (id, data, knowledge_type, acquisition_date, status, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.id,
                    json.dumps(item.to_dict()),
                    item.knowledge_type.value,
                    item.acquisition_date.isoformat(),
                    item.status.value,
                    item.confidence
                )
            )
            
            # Insert tags
            for tag in item.tags:
                cursor.execute(
                    "INSERT INTO knowledge_tags (id, tag) VALUES (?, ?)",
                    (item.id, tag)
                )
            
            conn.commit()
            logger.info(f"Added knowledge item: {item.title} (ID: {item.id})")
            return item.id
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error adding knowledge item: {e}")
            raise
        finally:
            conn.close()
    
    def get_item(self, item_id: str) -> Optional[KnowledgeItem]:
        """Get a knowledge item by ID.
        
        Args:
            item_id: ID of the item to retrieve
            
        Returns:
            Knowledge item if found, None otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT data FROM knowledge_items WHERE id = ?", (item_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return KnowledgeItem.from_dict(json.loads(result[0]))
        return None
    
    def update_item(self, item: KnowledgeItem) -> bool:
        """Update a knowledge item.
        
        Args:
            item: Knowledge item to update
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Update knowledge item
            cursor.execute(
                "UPDATE knowledge_items SET data = ?, knowledge_type = ?, acquisition_date = ?, status = ?, confidence = ? WHERE id = ?",
                (
                    json.dumps(item.to_dict()),
                    item.knowledge_type.value,
                    item.acquisition_date.isoformat(),
                    item.status.value,
                    item.confidence,
                    item.id
                )
            )
            
            # Delete existing tags
            cursor.execute("DELETE FROM knowledge_tags WHERE id = ?", (item.id,))
            
            # Insert new tags
            for tag in item.tags:
                cursor.execute(
                    "INSERT INTO knowledge_tags (id, tag) VALUES (?, ?)",
                    (item.id, tag)
                )
            
            conn.commit()
            logger.info(f"Updated knowledge item: {item.title} (ID: {item.id})")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating knowledge item: {e}")
            return False
        finally:
            conn.close()
    
    def delete_item(self, item_id: str) -> bool:
        """Delete a knowledge item.
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            True if successful, False otherwise
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Delete knowledge item (cascade will delete tags)
            cursor.execute("DELETE FROM knowledge_items WHERE id = ?", (item_id,))
            conn.commit()
            logger.info(f"Deleted knowledge item: {item_id}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting knowledge item: {e}")
            return False
        finally:
            conn.close()
    
    def search(self, 
               query: Optional[str] = None, 
               knowledge_type: Optional[KnowledgeType] = None,
               tags: Optional[List[str]] = None,
               status: Optional[KnowledgeStatus] = None,
               min_confidence: float = 0.0,
               limit: int = 100) -> List[KnowledgeItem]:
        """Search for knowledge items.
        
        Args:
            query: Text search query
            knowledge_type: Filter by knowledge type
            tags: Filter by tags (all tags must match)
            status: Filter by status
            min_confidence: Minimum confidence score
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge items
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        sql = "SELECT data FROM knowledge_items WHERE confidence >= ?"
        params = [min_confidence]
        
        if knowledge_type:
            sql += " AND knowledge_type = ?"
            params.append(knowledge_type.value)
        
        if status:
            sql += " AND status = ?"
            params.append(status.value)
        
        # Handle text search
        if query:
            sql += " AND data LIKE ?"
            params.append(f"%{query}%")
        
        # Handle tag filtering with a subquery
        if tags and len(tags) > 0:
            placeholders = ", ".join(["?"] * len(tags))
            sql += f" AND id IN (SELECT id FROM knowledge_tags WHERE tag IN ({placeholders}) GROUP BY id HAVING COUNT(DISTINCT tag) = ?)"
            params.extend(tags)
            params.append(len(tags))  # Ensure all tags match
        
        sql += " ORDER BY confidence DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        return [KnowledgeItem.from_dict(json.loads(row[0])) for row in results]
    
    def get_related_items(self, item_id: str) -> List[KnowledgeItem]:
        """Get items related to a specific knowledge item.
        
        Args:
            item_id: ID of the item to find related items for
            
        Returns:
            List of related knowledge items
        """
        item = self.get_item(item_id)
        if not item:
            return []
        
        related_items = []
        for related_id in item.related_ids:
            related_item = self.get_item(related_id)
            if related_item:
                related_items.append(related_item)
        
        return related_items
    
    def mark_as_applied(self, item_id: str) -> bool:
        """Mark a knowledge item as applied.
        
        Args:
            item_id: ID of the item to mark
            
        Returns:
            True if successful, False otherwise
        """
        item = self.get_item(item_id)
        if not item:
            return False
        
        item.status = KnowledgeStatus.APPLIED
        item.application_count += 1
        item.last_applied = datetime.now()
        
        return self.update_item(item)
    
    def mark_as_verified(self, item_id: str, verification_score: float) -> bool:
        """Mark a knowledge item as verified.
        
        Args:
            item_id: ID of the item to mark
            verification_score: Verification confidence score (0-1)
            
        Returns:
            True if successful, False otherwise
        """
        item = self.get_item(item_id)
        if not item:
            return False
        
        item.status = KnowledgeStatus.VERIFIED
        item.verification_score = verification_score
        
        return self.update_item(item)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.
        
        Returns:
            Dictionary of statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            "total_items": 0,
            "by_type": {},
            "by_status": {},
            "tags": {},
            "avg_confidence": 0.0
        }
        
        # Total items
        cursor.execute("SELECT COUNT(*) FROM knowledge_items")
        stats["total_items"] = cursor.fetchone()[0]
        
        # Items by type
        cursor.execute("SELECT knowledge_type, COUNT(*) FROM knowledge_items GROUP BY knowledge_type")
        for row in cursor.fetchall():
            stats["by_type"][row[0]] = row[1]
        
        # Items by status
        cursor.execute("SELECT status, COUNT(*) FROM knowledge_items GROUP BY status")
        for row in cursor.fetchall():
            stats["by_status"][row[0]] = row[1]
        
        # Top tags
        cursor.execute("SELECT tag, COUNT(*) FROM knowledge_tags GROUP BY tag ORDER BY COUNT(*) DESC LIMIT 20")
        for row in cursor.fetchall():
            stats["tags"][row[0]] = row[1]
        
        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM knowledge_items")
        stats["avg_confidence"] = cursor.fetchone()[0] or 0.0
        
        conn.close()
        return stats
