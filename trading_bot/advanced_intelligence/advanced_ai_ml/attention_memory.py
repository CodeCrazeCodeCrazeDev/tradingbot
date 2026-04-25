"""
Idea #7: Attention-Based Market Memory
=======================================
Long-term memory networks with attention mechanisms for multi-year pattern recognition.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class MemorySlot:
    key: np.ndarray
    value: np.ndarray
    timestamp: datetime
    importance: float
    access_count: int = 0
    last_accessed: Optional[datetime] = None


class MultiHeadAttention:
    """Multi-head attention mechanism."""
    
    def __init__(self, d_model: int, num_heads: int):
        self.d_model = d_model
        self.num_heads = num_heads
        self.d_k = d_model // num_heads
        
        self.W_q = np.random.randn(d_model, d_model) * 0.01
        self.W_k = np.random.randn(d_model, d_model) * 0.01
        self.W_v = np.random.randn(d_model, d_model) * 0.01
        self.W_o = np.random.randn(d_model, d_model) * 0.01
        
    def forward(self, query: np.ndarray, key: np.ndarray, 
                value: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        batch_size = query.shape[0] if query.ndim > 1 else 1
        
        if query.ndim == 1:
            query = query.reshape(1, -1)
            key = key.reshape(1, -1) if key.ndim == 1 else key
            value = value.reshape(1, -1) if value.ndim == 1 else value
        
        Q = query @ self.W_q
        K = key @ self.W_k
        V = value @ self.W_v
        
        scores = Q @ K.T / np.sqrt(self.d_k)
        
        if mask is not None:
            scores = np.where(mask, scores, -1e9)
        
        attention_weights = self._softmax(scores)
        output = attention_weights @ V
        
        return output @ self.W_o
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / (np.sum(exp_x, axis=-1, keepdims=True) + 1e-10)


class MemoryNetwork:
    """External memory network with read/write operations."""
    
    def __init__(self, memory_size: int, memory_dim: int):
        self.memory_size = memory_size
        self.memory_dim = memory_dim
        self.memory = np.zeros((memory_size, memory_dim))
        self.usage = np.zeros(memory_size)
        self.write_weights = np.zeros(memory_size)
        self.read_weights = np.zeros(memory_size)
        
    def read(self, query: np.ndarray) -> np.ndarray:
        similarities = self.memory @ query / (
            np.linalg.norm(self.memory, axis=1, keepdims=True) * 
            np.linalg.norm(query) + 1e-10
        )
        similarities = similarities.flatten()
        
        self.read_weights = self._softmax(similarities)
        
        return self.read_weights @ self.memory
    
    def write(self, key: np.ndarray, value: np.ndarray, erase_vector: np.ndarray):
        write_idx = np.argmin(self.usage)
        
        self.memory[write_idx] = self.memory[write_idx] * (1 - erase_vector) + value
        self.usage[write_idx] = 1.0
        
        self.usage *= 0.99
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x))
        return exp_x / (np.sum(exp_x) + 1e-10)


class TemporalAttention:
    """Temporal attention for time-series patterns."""
    
    def __init__(self, d_model: int, max_seq_len: int = 1000):
        self.d_model = d_model
        self.max_seq_len = max_seq_len
        self.positional_encoding = self._create_positional_encoding()
        self.attention = MultiHeadAttention(d_model, num_heads=8)
        
    def _create_positional_encoding(self) -> np.ndarray:
        pe = np.zeros((self.max_seq_len, self.d_model))
        position = np.arange(self.max_seq_len).reshape(-1, 1)
        div_term = np.exp(np.arange(0, self.d_model, 2) * (-np.log(10000.0) / self.d_model))
        
        pe[:, 0::2] = np.sin(position * div_term)
        pe[:, 1::2] = np.cos(position * div_term)
        
        return pe
    
    def forward(self, sequence: np.ndarray) -> np.ndarray:
        seq_len = sequence.shape[0]
        
        if sequence.shape[1] != self.d_model:
            projection = np.random.randn(sequence.shape[1], self.d_model) * 0.01
            sequence = sequence @ projection
        
        sequence = sequence + self.positional_encoding[:seq_len]
        
        output = self.attention.forward(sequence, sequence, sequence)
        
        return output


class AttentionBasedMarketMemory:
    """
    Attention-Based Market Memory for multi-year pattern recognition.
    Uses transformer-style attention with external memory.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.d_model = self.config.get("d_model", 256)
        self.memory_size = self.config.get("memory_size", 10000)
        self.num_heads = self.config.get("num_heads", 8)
        
        self.attention = MultiHeadAttention(self.d_model, self.num_heads)
        self.memory_network = MemoryNetwork(self.memory_size, self.d_model)
        self.temporal_attention = TemporalAttention(self.d_model)
        
        self.long_term_memory: List[MemorySlot] = []
        self.short_term_buffer: List[np.ndarray] = []
        self.pattern_cache: Dict[str, np.ndarray] = {}
        
        self.initialized = False
        self.metrics = {
            "patterns_stored": 0,
            "patterns_retrieved": 0,
            "memory_utilization": 0.0,
            "avg_attention_score": 0.0
        }
        
    async def initialize(self):
        """Initialize the memory system."""
        logger.info("Initializing Attention-Based Market Memory")
        self.initialized = True
        
    async def store_pattern(self, pattern: np.ndarray, metadata: Dict[str, Any] = None):
        """Store a market pattern in long-term memory."""
        if not self.initialized:
            await self.initialize()
        
        if pattern.shape[-1] != self.d_model:
            projection = np.random.randn(pattern.shape[-1], self.d_model) * 0.01
            encoded = pattern @ projection if pattern.ndim == 1 else pattern.mean(axis=0) @ projection
        else:
            encoded = pattern if pattern.ndim == 1 else pattern.mean(axis=0)
        
        importance = self._compute_importance(pattern)
        
        slot = MemorySlot(
            key=encoded,
            value=pattern.flatten()[:self.d_model] if pattern.size > self.d_model else np.pad(pattern.flatten(), (0, self.d_model - pattern.size)),
            timestamp=datetime.now(),
            importance=importance
        )
        
        self.long_term_memory.append(slot)
        
        if len(self.long_term_memory) > self.memory_size:
            self.long_term_memory.sort(key=lambda x: x.importance, reverse=True)
            self.long_term_memory = self.long_term_memory[:self.memory_size]
        
        self.memory_network.write(encoded, slot.value, np.ones(self.d_model) * 0.1)
        
        self.metrics["patterns_stored"] += 1
        self.metrics["memory_utilization"] = len(self.long_term_memory) / self.memory_size
        
    async def retrieve_similar_patterns(self, query: np.ndarray, 
                                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve patterns similar to query."""
        if not self.initialized:
            await self.initialize()
        
        if query.shape[-1] != self.d_model:
            projection = np.random.randn(query.shape[-1], self.d_model) * 0.01
            query_encoded = query @ projection if query.ndim == 1 else query.mean(axis=0) @ projection
        else:
            query_encoded = query if query.ndim == 1 else query.mean(axis=0)
        
        similarities = []
        for slot in self.long_term_memory:
            sim = np.dot(query_encoded, slot.key) / (
                np.linalg.norm(query_encoded) * np.linalg.norm(slot.key) + 1e-10
            )
            similarities.append((slot, sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for slot, sim in similarities[:top_k]:
            slot.access_count += 1
            slot.last_accessed = datetime.now()
            
            results.append({
                "pattern": slot.value,
                "similarity": float(sim),
                "timestamp": slot.timestamp.isoformat(),
                "importance": slot.importance,
                "access_count": slot.access_count
            })
        
        self.metrics["patterns_retrieved"] += 1
        if similarities:
            self.metrics["avg_attention_score"] = np.mean([s[1] for s in similarities[:top_k]])
        
        return results
    
    async def attend_to_history(self, current_state: np.ndarray, 
                                 history: np.ndarray) -> Dict[str, Any]:
        """Apply attention over historical data."""
        if not self.initialized:
            await self.initialize()
        
        if history.shape[-1] != self.d_model:
            projection = np.random.randn(history.shape[-1], self.d_model) * 0.01
            history_encoded = history @ projection
        else:
            history_encoded = history
        
        if current_state.shape[-1] != self.d_model:
            projection = np.random.randn(current_state.shape[-1], self.d_model) * 0.01
            query = current_state @ projection if current_state.ndim == 1 else current_state.mean(axis=0) @ projection
        else:
            query = current_state if current_state.ndim == 1 else current_state.mean(axis=0)
        
        attended = self.attention.forward(
            query.reshape(1, -1),
            history_encoded,
            history_encoded
        )
        
        memory_context = self.memory_network.read(query)
        
        combined = attended.flatten() * 0.7 + memory_context * 0.3
        
        return {
            "attended_representation": combined,
            "attention_weights": self.memory_network.read_weights,
            "memory_contribution": float(np.linalg.norm(memory_context))
        }
    
    async def detect_recurring_patterns(self, sequence: np.ndarray,
                                         min_similarity: float = 0.8) -> List[Dict[str, Any]]:
        """Detect recurring patterns in sequence using attention."""
        if not self.initialized:
            await self.initialize()
        
        temporal_output = self.temporal_attention.forward(sequence)
        
        recurring = []
        for i in range(len(temporal_output)):
            for j in range(i + 10, len(temporal_output)):
                sim = np.dot(temporal_output[i], temporal_output[j]) / (
                    np.linalg.norm(temporal_output[i]) * np.linalg.norm(temporal_output[j]) + 1e-10
                )
                
                if sim > min_similarity:
                    recurring.append({
                        "position_1": i,
                        "position_2": j,
                        "similarity": float(sim),
                        "pattern_length": j - i
                    })
        
        return recurring
    
    async def predict_from_memory(self, current_context: np.ndarray) -> Dict[str, Any]:
        """Make predictions based on similar historical patterns."""
        similar_patterns = await self.retrieve_similar_patterns(current_context, top_k=10)
        
        if not similar_patterns:
            return {
                "prediction": np.zeros(3),
                "confidence": 0.0,
                "supporting_patterns": 0
            }
        
        weighted_prediction = np.zeros(min(3, len(similar_patterns[0]["pattern"])))
        total_weight = 0
        
        for pattern_info in similar_patterns:
            weight = pattern_info["similarity"] * pattern_info["importance"]
            pattern = pattern_info["pattern"][:3] if len(pattern_info["pattern"]) >= 3 else pattern_info["pattern"]
            weighted_prediction[:len(pattern)] += pattern * weight
            total_weight += weight
        
        if total_weight > 0:
            weighted_prediction /= total_weight
        
        confidence = np.mean([p["similarity"] for p in similar_patterns])
        
        return {
            "prediction": weighted_prediction.tolist(),
            "confidence": float(confidence),
            "supporting_patterns": len(similar_patterns)
        }
    
    def _compute_importance(self, pattern: np.ndarray) -> float:
        """Compute importance score for a pattern."""
        volatility = np.std(pattern)
        magnitude = np.abs(pattern).mean()
        uniqueness = 1.0
        
        if self.long_term_memory:
            similarities = []
            pattern_flat = pattern.flatten()[:self.d_model]
            for slot in self.long_term_memory[-100:]:
                sim = np.dot(pattern_flat, slot.value[:len(pattern_flat)]) / (
                    np.linalg.norm(pattern_flat) * np.linalg.norm(slot.value[:len(pattern_flat)]) + 1e-10
                )
                similarities.append(sim)
            uniqueness = 1.0 - np.mean(similarities) if similarities else 1.0
        
        return float(0.3 * volatility + 0.3 * magnitude + 0.4 * uniqueness)
    
    async def consolidate_memory(self):
        """Consolidate and compress long-term memory."""
        if len(self.long_term_memory) < 100:
            return
        
        self.long_term_memory.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        
        keep_count = int(self.memory_size * 0.8)
        self.long_term_memory = self.long_term_memory[:keep_count]
        
        self.metrics["memory_utilization"] = len(self.long_term_memory) / self.memory_size
        logger.info(f"Memory consolidated: {len(self.long_term_memory)} patterns retained")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get memory system metrics."""
        return {
            **self.metrics,
            "long_term_memory_size": len(self.long_term_memory),
            "d_model": self.d_model,
            "num_heads": self.num_heads
        }
    
    async def shutdown(self):
        """Shutdown the memory system."""
        self.long_term_memory.clear()
        self.short_term_buffer.clear()
        self.pattern_cache.clear()
        self.initialized = False
        logger.info("Attention-Based Market Memory shutdown complete")
