"""
Cognition Store — Embedding-Indexed Knowledge Base
===================================================

The memory backbone of the Cognitive Operating System.

Every piece of knowledge the system accumulates is stored here as a
KnowledgeNode, indexed by embedding for semantic retrieval, tagged by
category for structured access, and scored by validation history for
trust-weighted retrieval.

Key operations:
    - ingest:     Add new knowledge (from research, trades, simulation, meta)
    - recall:     Semantic search — find knowledge relevant to a query
    - validate:   Score a node against reality (confirmation / refutation)
    - consolidate: Decay stale knowledge, promote validated knowledge
    - export:     Serialize for persistence

FAISS is used when available for fast similarity search; falls back to
numpy dot-product when not installed.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import hashlib
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

from .types import KnowledgeNode, KnowledgeCategory, COSConfig

logger = logging.getLogger(__name__)

# Optional FAISS
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.info("FAISS not available — using numpy similarity search")


class CognitionStore:
    """
    Structured, embedding-indexed knowledge base.

    The store is the single source of truth for all accumulated knowledge.
    It supports:
      1. Semantic retrieval (find knowledge similar to a query embedding)
      2. Category filtering (only look at risk insights, or causal relations)
      3. Salience ranking (prioritize recently-validated, high-impact knowledge)
      4. Validation tracking (know which knowledge is confirmed vs. refuted)
    """

    def __init__(self, config: COSConfig):
        self.config = config
        self.embedding_dim = config.embedding_dim
        self.capacity = config.store_capacity

        # In-memory node store: node_id → KnowledgeNode
        self._nodes: Dict[str, KnowledgeNode] = {}

        # Embedding matrix for fast search
        self._embeddings: Optional[np.ndarray] = None  # shape (N, embedding_dim)
        self._node_id_order: List[str] = []             # parallel index for embeddings

        # FAISS index (if available)
        self._faiss_index = None
        if FAISS_AVAILABLE and config.use_faiss:
            self._faiss_index = faiss.IndexFlatIP(config.embedding_dim)

        # Category index: category → set of node_ids
        self._category_index: Dict[KnowledgeCategory, set] = defaultdict(set)

        # Source index: source → set of node_ids
        self._source_index: Dict[str, set] = defaultdict(set)

        # Salience heap for top-k retrieval
        self._salience_dirty = True

        # Persistence
        self._storage_path = Path(config.storage_path) / "cognition_store"
        self._db_path = self._storage_path / "cognition_store.db"

        # Stats
        self._ingest_count = 0
        self._recall_count = 0
        self._validate_count = 0

        logger.info(
            f"CognitionStore initialized | dim={self.embedding_dim} "
            f"| capacity={self.capacity} | faiss={FAISS_AVAILABLE}"
        )

    # ── Ingest ────────────────────────────────────────────────────────────

    def ingest(self, node: KnowledgeNode) -> str:
        """
        Add a knowledge node to the store.

        If a node with the same content hash already exists, merge instead
        of duplicating.
        """
        # Compute embedding if not provided
        if node.embedding is None:
            node.embedding = self._compute_embedding(node)

        # Dedup by content hash
        content_hash = self._content_hash(node)
        existing_id = self._find_by_hash(content_hash)
        if existing_id is not None:
            self._merge_into(existing_id, node)
            return existing_id

        # Enforce capacity
        if len(self._nodes) >= self.capacity:
            self._evict_lowest_salience()

        # Store
        node_id = node.node_id
        self._nodes[node_id] = node
        self._category_index[node.category].add(node_id)
        self._source_index[node.source].add(node_id)

        # Update embedding matrix
        self._add_embedding(node_id, node.embedding)

        self._ingest_count += 1
        self._salience_dirty = True

        logger.debug(f"Ingested node {node_id} | category={node.category.value} | source={node.source}")
        return node_id

    def ingest_batch(self, nodes: List[KnowledgeNode]) -> List[str]:
        """Ingest multiple nodes at once."""
        return [self.ingest(n) for n in nodes]

    # ── Recall ────────────────────────────────────────────────────────────

    def recall(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        category: Optional[KnowledgeCategory] = None,
        source: Optional[str] = None,
        min_salience: float = 0.0,
        min_validation: float = 0.0,
    ) -> List[Tuple[KnowledgeNode, float]]:
        """
        Semantic retrieval: find the top_k most relevant knowledge nodes.

        Returns list of (node, similarity_score) sorted by relevance.
        Relevance = similarity * salience_weight * validation_weight
        """
        self._recall_count += 1

        if len(self._nodes) == 0:
            return []

        # Filter candidates
        candidate_ids = set(self._nodes.keys())
        if category is not None:
            candidate_ids &= self._category_index[category]
        if source is not None:
            candidate_ids &= self._source_index[source]

        # Filter by salience and validation
        candidate_ids = {
            nid for nid in candidate_ids
            if self._nodes[nid].salience >= min_salience
            and self._nodes[nid].validation_score >= min_validation
        }

        if not candidate_ids:
            return []

        # Search
        if self._faiss_index is not None and len(candidate_ids) > 50:
            results = self._faiss_search(query_embedding, top_k * 2, candidate_ids)
        else:
            results = self._numpy_search(query_embedding, top_k * 2, candidate_ids)

        # Re-rank by combined score: similarity * salience * (1 + validation)
        scored = []
        for node_id, sim in results:
            node = self._nodes[node_id]
            validation_weight = 1.0 + max(0, node.validation_score)
            combined = sim * node.salience * validation_weight
            scored.append((node, combined))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Update retrieval counts
        for node, _ in scored[:top_k]:
            node.retrieval_count += 1

        return scored[:top_k]

    def recall_by_category(
        self,
        category: KnowledgeCategory,
        top_k: int = 10,
        sort_by: str = "salience",
    ) -> List[KnowledgeNode]:
        """Retrieve nodes by category, sorted by salience or validation."""
        node_ids = self._category_index[category]
        nodes = [self._nodes[nid] for nid in node_ids if nid in self._nodes]

        if sort_by == "salience":
            nodes.sort(key=lambda n: n.salience, reverse=True)
        elif sort_by == "validation":
            nodes.sort(key=lambda n: n.validation_score, reverse=True)
        elif sort_by == "retrieval":
            nodes.sort(key=lambda n: n.retrieval_count, reverse=True)

        return nodes[:top_k]

    def recall_recent(self, top_k: int = 10) -> List[KnowledgeNode]:
        """Get the most recently created or updated nodes."""
        nodes = list(self._nodes.values())
        nodes.sort(key=lambda n: n.updated_at, reverse=True)
        return nodes[:top_k]

    # ── Validate ──────────────────────────────────────────────────────────

    def validate(self, node_id: str, score: float) -> bool:
        """
        Record a validation result for a node.

        Args:
            node_id: The node to validate
            score:   -1.0 (refuted) to +1.0 (confirmed)

        Returns True if node was found and updated.
        """
        if node_id not in self._nodes:
            return False

        node = self._nodes[node_id]
        node.validation_count += 1

        # Running average of validation scores
        n = node.validation_count
        node.validation_score = (node.validation_score * (n - 1) + score) / n
        node.last_validated_at = datetime.utcnow()

        # Refresh salience on validation
        if self.config.salience_refresh_on_validation:
            node.salience = min(1.0, node.salience + 0.2 * max(0, score))

        self._validate_count += 1
        logger.debug(
            f"Validated node {node_id} | score={score:.2f} "
            f"| avg={node.validation_score:.2f} | count={node.validation_count}"
        )
        return True

    def validate_batch(self, results: List[Tuple[str, float]]) -> int:
        """Validate multiple nodes at once. Returns count of successful validations."""
        return sum(1 for nid, score in results if self.validate(nid, score))

    # ── Consolidate ───────────────────────────────────────────────────────

    def consolidate(self):
        """
        Maintenance pass: decay salience, remove dead nodes, rebuild indices.

        Called periodically to keep the store healthy.
        """
        # Decay salience
        for node in self._nodes.values():
            node.refresh_salience(decay=self.config.salience_decay)

        # Remove nodes with zero salience and negative validation
        dead_ids = [
            nid for nid, node in self._nodes.items()
            if node.salience < 0.01 and node.validation_score < -0.5
        ]
        for nid in dead_ids:
            self._remove_node(nid)

        # Rebuild embedding matrix if dirty
        self._rebuild_embedding_matrix()

        self._salience_dirty = False
        logger.info(
            f"Consolidated store | nodes={len(self._nodes)} "
            f"| evicted={len(dead_ids)}"
        )

    # ── Persistence ───────────────────────────────────────────────────────

    def save(self):
        """Persist all nodes to SQLite."""
        self._storage_path.mkdir(parents=True, exist_ok=True)

        cols = [
            "node_id", "category", "title", "content", "structured_data",
            "embedding", "source", "parent_ids", "created_at", "updated_at",
            "validation_count", "validation_score", "last_validated_at",
            "retrieval_count", "decision_impact_count", "salience",
        ]
        # Build proper typed schema
        typed_cols = []
        for c in cols:
            if c in ("validation_count", "retrieval_count", "decision_impact_count"):
                typed_cols.append(f"{c} INTEGER")
            elif c in ("validation_score", "salience"):
                typed_cols.append(f"{c} REAL")
            elif c == "embedding":
                typed_cols.append(f"{c} BLOB")
            else:
                typed_cols.append(f"{c} TEXT")

        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("DROP TABLE IF EXISTS knowledge_nodes")
            conn.execute(f"CREATE TABLE knowledge_nodes ({', '.join(typed_cols)})")

            placeholders = ", ".join("?" for _ in cols)
            col_names = ", ".join(cols)

            for node in self._nodes.values():
                emb_bytes = node.embedding.tobytes() if node.embedding is not None else None
                conn.execute(
                    f"INSERT INTO knowledge_nodes ({col_names}) VALUES ({placeholders})",
                    (
                        node.node_id,
                        node.category.value,
                        node.title,
                        node.content,
                        json.dumps(node.structured_data),
                        emb_bytes,
                        node.source,
                        json.dumps(node.parent_ids),
                        node.created_at.isoformat(),
                        node.updated_at.isoformat(),
                        node.validation_count,
                        node.validation_score,
                        node.last_validated_at.isoformat() if node.last_validated_at else None,
                        node.retrieval_count,
                        node.decision_impact_count,
                        node.salience,
                    ),
                )

        logger.info(f"Saved {len(self._nodes)} nodes to {self._db_path}")

    def load(self):
        """Load nodes from SQLite."""
        if not self._db_path.exists():
            logger.info("No saved store found — starting fresh")
            return

        with sqlite3.connect(str(self._db_path)) as conn:
            rows = conn.execute("SELECT * FROM knowledge_nodes").fetchall()

        for row in rows:
            (
                node_id, category, title, content, structured_data,
                emb_bytes, source, parent_ids, created_at, updated_at,
                validation_count, validation_score, last_validated_at,
                retrieval_count, decision_impact_count, salience,
            ) = row

            embedding = np.frombuffer(emb_bytes, dtype=np.float32) if emb_bytes else None
            if embedding is not None and len(embedding) != self.embedding_dim:
                embedding = None  # dimension mismatch — skip

            node = KnowledgeNode(
                node_id=node_id,
                category=KnowledgeCategory(category),
                title=title,
                content=content,
                structured_data=json.loads(structured_data) if structured_data else {},
                embedding=embedding,
                source=source,
                parent_ids=json.loads(parent_ids) if parent_ids else [],
                created_at=datetime.fromisoformat(created_at),
                updated_at=datetime.fromisoformat(updated_at),
                validation_count=validation_count,
                validation_score=validation_score,
                last_validated_at=datetime.fromisoformat(last_validated_at) if last_validated_at else None,
                retrieval_count=retrieval_count,
                decision_impact_count=decision_impact_count,
                salience=salience,
            )
            self._nodes[node_id] = node
            self._category_index[node.category].add(node_id)
            self._source_index[node.source].add(node_id)
            if embedding is not None:
                self._add_embedding(node_id, embedding)

        logger.info(f"Loaded {len(self._nodes)} nodes from {self._db_path}")

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return store statistics."""
        category_counts = {cat.value: len(ids) for cat, ids in self._category_index.items()}
        source_counts = {src: len(ids) for src, ids in self._source_index.items()}

        avg_salience = 0.0
        avg_validation = 0.0
        if self._nodes:
            avg_salience = np.mean([n.salience for n in self._nodes.values()])
            avg_validation = np.mean([n.validation_score for n in self._nodes.values()])

        return {
            "total_nodes": len(self._nodes),
            "capacity": self.capacity,
            "embedding_dim": self.embedding_dim,
            "faiss_enabled": self._faiss_index is not None,
            "category_counts": category_counts,
            "source_counts": source_counts,
            "avg_salience": float(avg_salience),
            "avg_validation_score": float(avg_validation),
            "ingest_count": self._ingest_count,
            "recall_count": self._recall_count,
            "validate_count": self._validate_count,
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _compute_embedding(self, node: KnowledgeNode) -> np.ndarray:
        """
        Compute a simple embedding for a knowledge node.

        Uses a deterministic hash-based projection when no neural
        encoder is available. This is a placeholder — in production,
        this would use a sentence transformer or the existing
        EmbeddingEncoder from world_model.experience_replay.
        """
        text = f"{node.title} {node.content} {node.category.value}"
        rng = np.random.RandomState(hash(text) % (2**31))
        emb = rng.randn(self.embedding_dim).astype(np.float32)
        emb /= (np.linalg.norm(emb) + 1e-8)
        return emb

    def _content_hash(self, node: KnowledgeNode) -> str:
        """Deterministic hash of node content for dedup."""
        raw = f"{node.title}|{node.content}|{node.category.value}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _find_by_hash(self, content_hash: str) -> Optional[str]:
        """Find existing node with the same content hash."""
        for nid, node in self._nodes.items():
            if self._content_hash(node) == content_hash:
                return nid
        return None

    def _merge_into(self, existing_id: str, new_node: KnowledgeNode):
        """Merge new node data into an existing node."""
        existing = self._nodes[existing_id]
        existing.updated_at = datetime.utcnow()

        # Merge structured data
        existing.structured_data.update(new_node.structured_data)

        # Boost salience
        existing.salience = min(1.0, existing.salience + 0.1)

        # Merge parent IDs
        for pid in new_node.parent_ids:
            if pid not in existing.parent_ids:
                existing.parent_ids.append(pid)

        # Update embedding if new one is better
        if new_node.embedding is not None:
            if existing.embedding is None:
                existing.embedding = new_node.embedding
                self._update_embedding(existing_id, new_node.embedding)
            else:
                # Average embeddings
                existing.embedding = 0.5 * existing.embedding + 0.5 * new_node.embedding
                norm = np.linalg.norm(existing.embedding)
                if norm > 0:
                    existing.embedding /= norm
                self._update_embedding(existing_id, existing.embedding)

    def _add_embedding(self, node_id: str, embedding: np.ndarray):
        """Add an embedding to the search index."""
        self._node_id_order.append(node_id)

        if self._embeddings is None:
            self._embeddings = embedding.reshape(1, -1).copy()
        else:
            self._embeddings = np.vstack([self._embeddings, embedding.reshape(1, -1)])

        if self._faiss_index is not None:
            self._faiss_index.add(embedding.reshape(1, -1))

    def _update_embedding(self, node_id: str, embedding: np.ndarray):
        """Update an existing embedding in the search index."""
        if node_id in self._node_id_order:
            idx = self._node_id_order.index(node_id)
            self._embeddings[idx] = embedding
            # FAISS doesn't support in-place updates easily; mark dirty
            self._salience_dirty = True

    def _remove_node(self, node_id: str):
        """Remove a node from all indices."""
        if node_id not in self._nodes:
            return

        node = self._nodes.pop(node_id)
        self._category_index[node.category].discard(node_id)
        self._source_index[node.source].discard(node_id)
        self._salience_dirty = True

    def _evict_lowest_salience(self):
        """Remove the lowest-salience node to make room."""
        if not self._nodes:
            return
        worst_id = min(self._nodes, key=lambda nid: self._nodes[nid].salience)
        self._remove_node(worst_id)

    def _rebuild_embedding_matrix(self):
        """Rebuild the embedding matrix and FAISS index from scratch."""
        self._node_id_order = []
        self._embeddings = None

        if self._faiss_index is not None:
            self._faiss_index = faiss.IndexFlatIP(self.embedding_dim)

        for nid, node in self._nodes.items():
            if node.embedding is not None:
                self._add_embedding(nid, node.embedding)

    def _faiss_search(
        self,
        query: np.ndarray,
        top_k: int,
        candidate_ids: set,
    ) -> List[Tuple[str, float]]:
        """Search using FAISS inner-product index."""
        q = query.reshape(1, -1).astype(np.float32)
        scores, indices = self._faiss_index.search(q, min(top_k, len(self._nodes)))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            if idx < len(self._node_id_order):
                nid = self._node_id_order[idx]
                if nid in candidate_ids:
                    results.append((nid, float(score)))
        return results

    def _numpy_search(
        self,
        query: np.ndarray,
        top_k: int,
        candidate_ids: set,
    ) -> List[Tuple[str, float]]:
        """Fallback similarity search using numpy dot-product."""
        if self._embeddings is None:
            return []

        # Filter to candidates
        candidate_indices = [
            i for i, nid in enumerate(self._node_id_order)
            if nid in candidate_ids
        ]
        if not candidate_indices:
            return []

        candidate_embs = self._embeddings[candidate_indices]
        candidate_nids = [self._node_id_order[i] for i in candidate_indices]

        # Dot-product similarity
        q = query.reshape(-1).astype(np.float32)
        sims = candidate_embs @ q

        # Top-k
        top_indices = np.argsort(sims)[::-1][:top_k]
        return [(candidate_nids[i], float(sims[i])) for i in top_indices]
