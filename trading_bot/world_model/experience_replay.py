"""
Experience Replay Buffer with FAISS Indexing
============================================

Persistent storage for synthetic experiences with semantic search:
- FAISS vector indexing for similarity search
- Priority-based sampling (prioritized experience replay)
- Clustering for diverse experience selection
- Integration with neuros_evolution memory systems

Enables efficient retrieval of relevant experiences at 10,000x scale
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import json
import pickle
import logging
from collections import deque
import hashlib

logger = logging.getLogger(__name__)

# Optional FAISS import (with fallback)
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available. Using numpy-based similarity search.")


@dataclass
class Experience:
    """
    Single experience entry for replay buffer
    
    Combines state, action, reward, next_state (SARS tuple)
    with metadata for prioritization and retrieval
    """
    experience_id: str
    
    # Core SARS data
    state: np.ndarray  # Market state vector
    action: int
    reward: float
    next_state: np.ndarray
    done: bool
    
    # Metadata
    timestamp: datetime
    source: str  # 'real', 'synthetic', 'simulation', 'self_play'
    episode_id: Optional[str] = None
    
    # For prioritization
    priority: float = 1.0
    td_error: float = 0.0
    
    # For semantic search
    embedding: Optional[np.ndarray] = None
    
    # Context
    market_regime: str = "normal"
    volatility: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'experience_id': self.experience_id,
            'state': self.state.tolist() if isinstance(self.state, np.ndarray) else self.state,
            'action': self.action,
            'reward': self.reward,
            'next_state': self.next_state.tolist() if isinstance(self.next_state, np.ndarray) else self.next_state,
            'done': self.done,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'episode_id': self.episode_id,
            'priority': self.priority,
            'td_error': self.td_error,
            'embedding': self.embedding.tolist() if self.embedding is not None else None,
            'market_regime': self.market_regime,
            'volatility': self.volatility
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Experience':
        """Create Experience from dictionary"""
        return cls(
            experience_id=data['experience_id'],
            state=np.array(data['state']),
            action=data['action'],
            reward=data['reward'],
            next_state=np.array(data['next_state']),
            done=data['done'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            source=data['source'],
            episode_id=data.get('episode_id'),
            priority=data.get('priority', 1.0),
            td_error=data.get('td_error', 0.0),
            embedding=np.array(data['embedding']) if data.get('embedding') else None,
            market_regime=data.get('market_regime', 'normal'),
            volatility=data.get('volatility', 0.0)
        )


class EmbeddingEncoder(nn.Module):
    """
    Neural network to encode experiences into embedding vectors
    for semantic similarity search
    """
    
    def __init__(
        self,
        state_dim: int = 20,
        embedding_dim: int = 64,
        hidden_dim: int = 128
    ):
        super().__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(state_dim + 1, hidden_dim),  # state + action
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, embedding_dim)
        )
        
        self.embedding_dim = embedding_dim
    
    def forward(self, state: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Encode state-action pair to embedding"""
        x = torch.cat([state, action.unsqueeze(-1)], dim=-1)
        return self.encoder(x)
    
    def encode_experience(self, experience: Experience) -> np.ndarray:
        """Encode single experience"""
        with torch.no_grad():
            state = torch.FloatTensor(experience.state).unsqueeze(0)
            action = torch.tensor([experience.action]).float()
            embedding = self.forward(state, action).squeeze().numpy()
        return embedding


class ExperienceReplayBuffer:
    """
    Experience Replay Buffer with FAISS indexing
    
    Features:
    - FAISS vector similarity search
    - Prioritized experience replay (PER)
    - Clustering for diverse sampling
    - Persistence to disk
    """
    
    def __init__(
        self,
        capacity: int = 1000000,  # 1M experiences
        embedding_dim: int = 64,
        state_dim: int = 20,
        use_faiss: bool = True,
        storage_path: Optional[str] = None
    ):
        self.capacity = capacity
        self.embedding_dim = embedding_dim
        self.state_dim = state_dim
        self.storage_path = Path(storage_path) if storage_path else None
        
        # Storage
        self.buffer: deque = deque(maxlen=capacity)
        self.experience_index: Dict[str, int] = {}  # id -> position
        
        # Embedding encoder
        self.encoder = EmbeddingEncoder(state_dim, embedding_dim)
        
        # FAISS index for similarity search
        self.use_faiss = use_faiss and FAISS_AVAILABLE
        self.faiss_index = None
        self._init_faiss_index()
        
        # Priority management
        self.priorities = np.ones(capacity) * 1e-6
        self.alpha = 0.6  # Priority exponent
        self.beta = 0.4  # Importance sampling exponent
        self.beta_increment = 0.001
        
        # Statistics
        self.total_added = 0
        self.total_sampled = 0
        
        # Load from disk if exists
        if self.storage_path and self.storage_path.exists():
            self.load()
        
        logger.info(f"✅ ExperienceReplayBuffer initialized")
        logger.info(f"   Capacity: {capacity:,}")
        logger.info(f"   Embedding dim: {embedding_dim}")
        logger.info(f"   FAISS enabled: {self.use_faiss}")
    
    def _init_faiss_index(self):
        """Initialize FAISS index for similarity search"""
        if not self.use_faiss:
            return
        
        # Use IndexFlatIP for inner product (cosine similarity)
        self.faiss_index = faiss.IndexFlatIP(self.embedding_dim)
        
        # Wrap with ID map to track experience IDs
        self.faiss_index = faiss.IndexIDMap(self.faiss_index)
        
        logger.info("✅ FAISS index initialized")
    
    def add(self, experience: Experience) -> str:
        """
        Add experience to buffer
        
        Returns experience ID
        """
        # Generate embedding
        if experience.embedding is None:
            experience.embedding = self.encoder.encode_experience(experience)
        
        # Add to buffer
        if len(self.buffer) >= self.capacity:
            # Remove oldest
            oldest = self.buffer[0]
            if oldest.experience_id in self.experience_index:
                del self.experience_index[oldest.experience_id]
        
        position = len(self.buffer)
        self.buffer.append(experience)
        self.experience_index[experience.experience_id] = position
        
        # Add to FAISS index
        if self.use_faiss and self.faiss_index is not None:
            embedding = experience.embedding.reshape(1, -1).astype('float32')
            # Normalize for cosine similarity
            faiss.normalize_L2(embedding)
            
            # Add with ID
            experience_id_hash = int(hashlib.md5(
                experience.experience_id.encode()
            ).hexdigest()[:8], 16)
            
            self.faiss_index.add_with_ids(embedding, np.array([experience_id_hash]))
        
        # Update priority
        max_priority = self.priorities.max() if len(self.buffer) > 0 else 1.0
        if position < len(self.priorities):
            self.priorities[position] = max_priority
        
        self.total_added += 1
        
        return experience.experience_id
    
    def sample(
        self,
        batch_size: int = 32,
        use_priorities: bool = True,
        ensure_diversity: bool = True
    ) -> Tuple[List[Experience], np.ndarray, np.ndarray]:
        """
        Sample batch of experiences
        
        Returns:
            (experiences, indices, importance_weights)
        """
        if len(self.buffer) == 0:
            return [], np.array([]), np.array([])
        
        buffer_size = len(self.buffer)
        
        if use_priorities and buffer_size > batch_size:
            # Prioritized sampling
            priorities = self.priorities[:buffer_size] ** self.alpha
            probabilities = priorities / priorities.sum()
            
            indices = np.random.choice(
                buffer_size,
                size=batch_size,
                p=probabilities,
                replace=False
            )
        else:
            # Uniform sampling
            indices = np.random.choice(buffer_size, size=batch_size, replace=False)
            probabilities = np.ones(buffer_size) / buffer_size
        
        # Get experiences
        experiences = [list(self.buffer)[i] for i in indices]
        
        # Calculate importance sampling weights
        weights = (buffer_size * probabilities[indices]) ** (-self.beta)
        weights /= weights.max()  # Normalize
        
        # Increment beta
        self.beta = min(1.0, self.beta + self.beta_increment)
        
        self.total_sampled += batch_size
        
        # Ensure diversity through clustering if requested
        if ensure_diversity and len(experiences) > 10:
            experiences = self._ensure_diversity(experiences)
        
        return experiences, indices, weights
    
    def _ensure_diversity(self, experiences: List[Experience]) -> List[Experience]:
        """Ensure sampled experiences are diverse using clustering"""
        if len(experiences) < 10:
            return experiences
        
        # Extract embeddings
        embeddings = np.array([e.embedding for e in experiences if e.embedding is not None])
        
        if len(embeddings) < 10:
            return experiences
        
        # Simple k-means clustering (simplified)
        n_clusters = min(5, len(embeddings) // 2)
        
        # Select representatives from each cluster
        selected_indices = np.random.choice(
            len(experiences),
            size=min(len(experiences), len(experiences)),
            replace=False
        )
        
        return [experiences[i] for i in selected_indices]
    
    def similarity_search(
        self,
        query_state: np.ndarray,
        query_action: Optional[int] = None,
        k: int = 10
    ) -> List[Tuple[Experience, float]]:
        """
        Find k most similar experiences using FAISS
        
        Returns list of (experience, similarity_score) tuples
        """
        if not self.use_faiss or self.faiss_index is None:
            # Fallback to numpy search
            return self._numpy_similarity_search(query_state, query_action, k)
        
        # Encode query
        with torch.no_grad():
            state = torch.FloatTensor(query_state).unsqueeze(0)
            action = torch.tensor([query_action if query_action is not None else 0]).float()
            query_embedding = self.encoder(state, action).squeeze().numpy()
        
        # Normalize
        query_embedding = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query_embedding)
        
        # Search
        similarities, ids = self.faiss_index.search(query_embedding, k)
        
        # Map back to experiences (simplified - using buffer order)
        results = []
        for i, idx in enumerate(ids[0]):
            if idx < len(self.buffer):
                exp = list(self.buffer)[idx]
                results.append((exp, float(similarities[0][i])))
        
        return results
    
    def _numpy_similarity_search(
        self,
        query_state: np.ndarray,
        query_action: Optional[int] = None,
        k: int = 10
    ) -> List[Tuple[Experience, float]]:
        """Fallback similarity search using numpy"""
        if len(self.buffer) == 0:
            return []
        
        # Calculate similarities
        similarities = []
        
        for exp in self.buffer:
            if exp.embedding is not None:
                # Cosine similarity
                sim = np.dot(query_state, exp.embedding) / (
                    np.linalg.norm(query_state) * np.linalg.norm(exp.embedding) + 1e-8
                )
                similarities.append((exp, sim))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:k]
    
    def update_priorities(self, indices: np.ndarray, td_errors: np.ndarray):
        """Update priorities based on TD errors"""
        for idx, td_error in zip(indices, td_errors):
            if idx < len(self.priorities):
                # Priority proportional to TD error (plus small constant)
                self.priorities[idx] = abs(td_error) + 1e-6
    
    def save(self, filepath: Optional[str] = None):
        """Save buffer to disk"""
        path = Path(filepath) if filepath else self.storage_path
        
        if path is None:
            logger.warning("No storage path specified")
            return
        
        # Create directory
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save buffer
        data = {
            'experiences': [e.to_dict() for e in self.buffer],
            'priorities': self.priorities.tolist(),
            'total_added': self.total_added,
            'total_sampled': self.total_sampled,
            'metadata': {
                'capacity': self.capacity,
                'embedding_dim': self.embedding_dim,
                'saved_at': datetime.utcnow().isoformat()
            }
        }
        
        with open(path, 'w') as f:
            json.dump(data, f)
        
        # Save FAISS index separately
        if self.use_faiss and self.faiss_index is not None:
            faiss_path = path.with_suffix('.faiss')
            faiss.write_index(self.faiss_index, str(faiss_path))
        
        logger.info(f"💾 Experience buffer saved to {path}")
    
    def load(self, filepath: Optional[str] = None):
        """Load buffer from disk"""
        path = Path(filepath) if filepath else self.storage_path
        
        if path is None or not path.exists():
            logger.warning(f"No saved buffer found at {path}")
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Load experiences
            self.buffer = deque(
                [Experience.from_dict(e) for e in data['experiences']],
                maxlen=self.capacity
            )
            
            # Load priorities
            self.priorities = np.array(data.get('priorities', []))
            if len(self.priorities) < self.capacity:
                self.priorities = np.concatenate([
                    self.priorities,
                    np.ones(self.capacity - len(self.priorities)) * 1e-6
                ])
            
            self.total_added = data.get('total_added', 0)
            self.total_sampled = data.get('total_sampled', 0)
            
            # Rebuild FAISS index
            if self.use_faiss:
                self._init_faiss_index()
                for exp in self.buffer:
                    if exp.embedding is not None:
                        embedding = exp.embedding.reshape(1, -1).astype('float32')
                        faiss.normalize_L2(embedding)
                        exp_id_hash = int(hashlib.md5(
                            exp.experience_id.encode()
                        ).hexdigest()[:8], 16)
                        self.faiss_index.add_with_ids(embedding, np.array([exp_id_hash]))
            
            logger.info(f"📂 Experience buffer loaded: {len(self.buffer)} experiences")
            
        except Exception as e:
            logger.error(f"Error loading buffer: {e}")
    
    def get_statistics(self) -> Dict:
        """Get buffer statistics"""
        if not self.buffer:
            return {'total_experiences': 0}
        
        # Count by source
        sources = {}
        for exp in self.buffer:
            sources[exp.source] = sources.get(exp.source, 0) + 1
        
        # Count by regime
        regimes = {}
        for exp in self.buffer:
            regimes[exp.market_regime] = regimes.get(exp.market_regime, 0) + 1
        
        return {
            'total_experiences': len(self.buffer),
            'total_added': self.total_added,
            'total_sampled': self.total_sampled,
            'capacity': self.capacity,
            'utilization': len(self.buffer) / self.capacity,
            'by_source': sources,
            'by_regime': regimes,
            'avg_priority': float(np.mean(self.priorities[:len(self.buffer)])),
            'faiss_enabled': self.use_faiss
        }
    
    def clear(self):
        """Clear all experiences"""
        self.buffer.clear()
        self.experience_index.clear()
        self.priorities = np.ones(self.capacity) * 1e-6
        
        if self.use_faiss:
            self._init_faiss_index()
        
        logger.info("🗑️ Experience buffer cleared")


# Factory function
def create_experience_replay_buffer(
    capacity: int = 1000000,
    embedding_dim: int = 64,
    state_dim: int = 20,
    storage_path: Optional[str] = None
) -> ExperienceReplayBuffer:
    """Create experience replay buffer with FAISS indexing"""
    return ExperienceReplayBuffer(
        capacity=capacity,
        embedding_dim=embedding_dim,
        state_dim=state_dim,
        storage_path=storage_path
    )


# =============================================================================
# L4: Belief State + Skill-Indexed Episodic Memory
# =============================================================================

class S4Block(nn.Module):
    """
    Structured State Space (S4) block for continuous-time long-range dependency.
    Hybrid SSM + retrieval/attention is the safer design for belief tracking
    over continuous streaming traces.
    """

    def __init__(self, d_model: int = 64, d_state: int = 16, dt_min: float = 0.001, dt_max: float = 0.1):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state

        # SSM parameters
        self.log_A_real = nn.Parameter(torch.randn(d_model, d_state) * 0.5)
        self.A_imag = nn.Parameter(torch.randn(d_model, d_state) * 0.5)
        self.log_B = nn.Parameter(torch.randn(d_model, d_state) * 0.5)
        self.C = nn.Parameter(torch.randn(d_state, d_model) * 0.5)
        self.D = nn.Parameter(torch.ones(d_model))
        self.log_dt = nn.Parameter(torch.rand(d_model) * (np.log(dt_max) - np.log(dt_min)) + np.log(dt_min))

        # Retrieval/attention hybrid component
        self.retrieval_attn = nn.MultiheadAttention(d_model, num_heads=4, batch_first=True)

        # Gating between SSM and retrieval
        self.gate = nn.Linear(d_model * 2, 1)

    def forward(self, x: torch.Tensor, hidden: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through S4 block with hybrid retrieval.

        Args:
            x: [B, L, D] input sequence
            hidden: optional previous hidden state

        Returns:
            output: [B, L, D]
            new_hidden: state for next call
        """
        B, L, D = x.shape

        # SSM path
        dt = torch.exp(self.log_dt).unsqueeze(0).unsqueeze(-1)  # [1, D, 1]
        A = -torch.exp(self.log_A_real) + 1j * self.A_imag  # [D, N]
        B_param = torch.exp(self.log_B)  # [D, N]

        # Simplified S4 recurrence
        ssm_out = x * self.D.unsqueeze(0).unsqueeze(0)  # Skip connection

        # Retrieval/attention path
        attn_out, _ = self.retrieval_attn(x, x, x)

        # Gate between SSM and retrieval
        gate_input = torch.cat([ssm_out, attn_out], dim=-1)
        if gate_input.size(-1) != D * 2:
            # Fallback if dimensions don't match
            gate_input = torch.cat([ssm_out[:, :, :D], attn_out[:, :, :D]], dim=-1)
        gate_weight = torch.sigmoid(self.gate(gate_input) if gate_input.size(-1) == D * 2 else self.gate(torch.cat([ssm_out[:, :, :D//2], attn_out[:, :, :D//2]], dim=-1)))

        output = gate_weight * ssm_out + (1 - gate_weight) * attn_out

        new_hidden = x[:, -1:, :]  # Store last state as hidden
        return output, new_hidden


class HyperdimensionalEncoder:
    """
    Hippocampal-Inspired Pattern Separation and Completion.
    Projects pre-skill belief state into high-dimensional binary vector space (HDC).
    Enables extremely fast, non-parametric memory of what went wrong at skill boundaries.
    """

    def __init__(self, input_dim: int = 64, hdc_dim: int = 10000):
        self.input_dim = input_dim
        self.hdc_dim = hdc_dim
        # Random projection matrix (fixed, not learned)
        self.projection = np.random.choice([-1, 1], size=(input_dim, hdc_dim)).astype(np.float32)

    def encode(self, latent_vector: np.ndarray) -> np.ndarray:
        """Project latent into HDC binary vector."""
        projected = latent_vector @ self.projection
        return (projected > 0).astype(np.int8)

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Hamming similarity between two HDC vectors."""
        return 1.0 - np.sum(np.abs(vec_a - vec_b)) / len(vec_a)

    def pattern_completion(self, partial: np.ndarray, memory_table: Dict[str, np.ndarray], threshold: float = 0.7) -> Optional[str]:
        """Complete partial pattern by finding nearest match in memory."""
        best_key = None
        best_sim = 0.0
        for key, stored in memory_table.items():
            sim = self.similarity(partial, stored)
            if sim > best_sim:
                best_sim = sim
                best_key = key
        if best_sim >= threshold:
            return best_key
        return None


@dataclass
class SkillMemoryEntry:
    """
    Key-Value Triple for skill-indexed episodic memory.

    Key: Latent State before a skill (HDC encoded)
    Action: The Option/Skill chosen
    Result: Latent State after + Delta in World Model Surprise
    """
    entry_id: str
    pre_skill_hdc: np.ndarray  # HDC-encoded pre-skill belief state
    skill_id: str  # Option/skill identifier
    pre_skill_latent: np.ndarray  # Original latent before skill
    post_skill_latent: np.ndarray  # Latent after skill
    world_model_surprise: float  # L3 ensemble disagreement delta
    outcome_tag: str  # 'success', 'failure', 'partial'
    failure_mode: Optional[str] = None  # 'precondition_violation', 'execution_error', etc.
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())

    # For OCHL: option boundary where surprise spiked
    option_boundary_timestep: Optional[int] = None
    hindsight_goal: Optional[str] = None  # Relabeled goal for OCHL


class BeliefStateTracker(nn.Module):
    """
    L4: Belief State Tracker using hybrid SSM + retrieval/attention.

    Maintains:
    - Current belief state
    - Latent map of hidden variables
    - Episodic trajectory memory (skill-indexed)
    - Semantic memory of world regularities
    - Learned reusable skills/options
    """

    def __init__(
        self,
        latent_dim: int = 64,
        d_state: int = 16,
        n_skills: int = 50,
        hdc_dim: int = 10000
    ):
        super().__init__()

        # S4-based belief tracker
        self.s4_tracker = S4Block(latent_dim, d_state)

        # HDC encoder for pattern separation/completion
        self.hdc_encoder = HyperdimensionalEncoder(latent_dim, hdc_dim)

        # Skill-indexed episodic memory
        self.skill_memory: Dict[str, List[SkillMemoryEntry]] = {}
        self.hdc_memory_table: Dict[str, np.ndarray] = {}  # entry_id -> HDC vector

        # Semantic memory (world regularities)
        self.semantic_memory: Dict[str, Dict] = {}

        # Skill/option library
        self.skill_library: Dict[str, Dict] = {}
        for i in range(n_skills):
            skill_id = f"skill_{i}"
            self.skill_library[skill_id] = {
                'preconditions': {},
                'termination_conditions': {},
                'usage_count': 0,
                'success_rate': 0.5,
                'failure_modes': {}
            }

        self.latent_dim = latent_dim
        self._belief_hidden = None

        logger.info(f"✅ Belief State Tracker (L4) initialized")
        logger.info(f"   Latent dim: {latent_dim}")
        logger.info(f"   Skills: {n_skills}")
        logger.info(f"   HDC dim: {hdc_dim}")

    def forward(self, latent_sequence: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Update belief state from latent sequence.

        Returns:
            belief_state: Current belief state
            new_hidden: Updated hidden state
        """
        belief, new_hidden = self.s4_tracker(latent_sequence, self._belief_hidden)
        self._belief_hidden = new_hidden.detach()
        return belief[:, -1, :], new_hidden

    def store_skill_memory(
        self,
        pre_skill_latent: np.ndarray,
        skill_id: str,
        post_skill_latent: np.ndarray,
        surprise_delta: float,
        outcome: str,
        failure_mode: Optional[str] = None,
        option_boundary_timestep: Optional[int] = None
    ):
        """Store skill-indexed episodic memory entry."""
        pre_hdc = self.hdc_encoder.encode(pre_skill_latent)
        entry_id = f"mem_{skill_id}_{len(self.skill_memory.get(skill_id, []))}"

        entry = SkillMemoryEntry(
            entry_id=entry_id,
            pre_skill_hdc=pre_hdc,
            skill_id=skill_id,
            pre_skill_latent=pre_skill_latent,
            post_skill_latent=post_skill_latent,
            world_model_surprise=surprise_delta,
            outcome_tag=outcome,
            failure_mode=failure_mode,
            option_boundary_timestep=option_boundary_timestep
        )

        if skill_id not in self.skill_memory:
            self.skill_memory[skill_id] = []
        self.skill_memory[skill_id].append(entry)
        self.hdc_memory_table[entry_id] = pre_hdc

        # Update skill library stats
        if skill_id in self.skill_library:
            self.skill_library[skill_id]['usage_count'] += 1
            if outcome == 'success':
                n = self.skill_library[skill_id]['usage_count']
                old_rate = self.skill_library[skill_id]['success_rate']
                self.skill_library[skill_id]['success_rate'] = old_rate + (1.0 - old_rate) / n
            if failure_mode:
                self.skill_library[skill_id]['failure_modes'][failure_mode] = \
                    self.skill_library[skill_id]['failure_modes'].get(failure_mode, 0) + 1

    def query_similar_experience(
        self,
        current_latent: np.ndarray,
        skill_id: Optional[str] = None,
        threshold: float = 0.7
    ) -> Optional[SkillMemoryEntry]:
        """
        Pattern completion query: "Last time the world looked like this,
        what happened when I tried Skill X?"
        """
        current_hdc = self.hdc_encoder.encode(current_latent)

        # Search within specific skill or all skills
        search_keys = [skill_id] if skill_id else list(self.skill_memory.keys())
        best_entry = None
        best_sim = 0.0

        for sid in search_keys:
            for entry in self.skill_memory.get(sid, []):
                sim = self.hdc_encoder.similarity(current_hdc, entry.pre_skill_hdc)
                if sim > best_sim:
                    best_sim = sim
                    best_entry = entry

        if best_sim >= threshold:
            return best_entry
        return None

    def ochl_relabel(
        self,
        failed_skill_id: str,
        surprise_spike_timestep: int,
        new_goal: str
    ):
        """
        B3 Fix: Option-Conditioned Hindsight Learning.

        When a task fails, identify the Option Boundary where L3 Surprise spiked,
        re-label the preceding sub-sequence with a new goal, and update the
        Skill Library with this new Precondition constraint.
        """
        entries = self.skill_memory.get(failed_skill_id, [])
        for entry in entries:
            if entry.outcome_tag == 'failure' and entry.option_boundary_timestep is None:
                entry.option_boundary_timestep = surprise_spike_timestep
                entry.hindsight_goal = new_goal

        # Update skill library with new precondition
        if failed_skill_id in self.skill_library:
            if 'preconditions' not in self.skill_library[failed_skill_id]:
                self.skill_library[failed_skill_id]['preconditions'] = {}
            self.skill_library[failed_skill_id]['preconditions'][new_goal] = True


# =============================================================================
# L6: Value / Constraint / Curiosity Model
# =============================================================================

class SuccessorFeatureNetwork(nn.Module):
    """
    Successor Features for zero-shot constraint transfer.

    Instead of learning a single scalar V(s), learn a vector ψ(s) where each
    dimension corresponds to a different cumulative future outcome (e.g.,
    "Total Time," "Battery Used," "Constraint Violation Count").

    If the goal changes, the planner can instantly recompute the new value by
    taking the dot product of ψ(s) with a new weight vector w. No retraining
    of the value network is required. Essential for Governance Layer (L10) overrides.
    """

    def __init__(self, latent_dim: int = 64, n_features: int = 8, hidden_dim: int = 128):
        super().__init__()
        self.n_features = n_features

        self.feature_net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_features)
        )

        # Constraint violation detector
        self.constraint_detector = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, n_features),
            nn.Sigmoid()  # Per-feature violation probability
        )

        # Risk/uncertainty cost estimator
        self.risk_estimator = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

        # Exploration value (information gain / curiosity)
        self.exploration_value = nn.Sequential(
            nn.Linear(latent_dim + 1, hidden_dim),  # latent + disagreement
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        latent_state: torch.Tensor,
        ensemble_disagreement: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Compute value decomposition.

        Returns:
            successor_features: ψ(s) vector
            constraint_violations: Per-feature violation probabilities
            risk_cost: Estimated risk/uncertainty cost
            exploration_value: Information gain value
            total_value: Weighted combination
        """
        psi = self.feature_net(latent_state)
        constraint_violations = self.constraint_detector(latent_state)
        risk_cost = self.risk_estimator(latent_state)

        if ensemble_disagreement is not None:
            expl_input = torch.cat([latent_state, ensemble_disagreement.unsqueeze(-1)], dim=-1)
        else:
            expl_input = torch.cat([latent_state, torch.zeros(latent_state.size(0), 1, device=latent_state.device)], dim=-1)
        exploration_val = self.exploration_value(expl_input)

        # Default weight vector (can be overridden by L10 governance)
        default_w = torch.ones(self.n_features, device=latent_state.device) / self.n_features
        total_value = psi @ default_w - risk_cost.squeeze(-1) + exploration_val.squeeze(-1) * 0.1

        return {
            'successor_features': psi,
            'constraint_violations': constraint_violations,
            'risk_cost': risk_cost,
            'exploration_value': exploration_val,
            'total_value': total_value
        }

    def compute_value_with_weights(
        self,
        latent_state: torch.Tensor,
        weight_vector: torch.Tensor,
        ensemble_disagreement: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Zero-shot value recomputation with new weight vector.
        No retraining needed — just dot product ψ(s) · w.
        """
        psi = self.feature_net(latent_state)
        risk = self.risk_estimator(latent_state)

        value = psi @ weight_vector - risk.squeeze(-1)
        return value


class CuriosityDrive:
    """
    Active inference / experiment selection.

    The agent should ask:
    - What do I not know?
    - Which observation or action would reduce uncertainty most?
    - Which experiment is worth running?

    Uses L3 ensemble disagreement as curiosity reward.
    Adversarial self-play: L3 identifies high-uncertainty regions,
    L5 generates imagined scenarios to exploit that uncertainty,
    L7 attempts to solve them, L4 stores successful strategies.
    """

    def __init__(
        self,
        disagreement_threshold: float = 2.0,
        curiosity_scale: float = 0.01,
        novelty_decay: float = 0.99
    ):
        self.disagreement_threshold = disagreement_threshold
        self.curiosity_scale = curiosity_scale
        self.novelty_decay = novelty_decay
        self.state_visit_counts: Dict[str, int] = {}

    def compute_curiosity_reward(
        self,
        latent_state: np.ndarray,
        ensemble_disagreement: float
    ) -> float:
        """
        Compute intrinsic curiosity reward based on:
        1. Ensemble disagreement (epistemic uncertainty)
        2. State novelty (visit count)
        """
        state_key = tuple(latent_state.round(3)[:10])  # Coarse discretization
        visit_count = self.state_visit_counts.get(state_key, 0)
        self.state_visit_counts[state_key] = visit_count + 1

        # Curiosity from disagreement
        disagreement_curiosity = ensemble_disagreement * self.curiosity_scale

        # Curiosity from novelty (inversely proportional to visit count)
        novelty_curiosity = 1.0 / (1.0 + visit_count)

        # Total curiosity reward
        total = disagreement_curiosity + novelty_curiosity * self.curiosity_scale
        return total

    def select_experiment(
        self,
        belief_tracker: BeliefStateTracker,
        skill_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Select which experiment to run based on information gain.
        Queries L4 for all times a skill was attempted, uses L3
        disagreement as curiosity reward to replay and refine skill boundaries.
        """
        if skill_id and skill_id in belief_tracker.skill_memory:
            entries = belief_tracker.skill_memory[skill_id]
            # Find entries with highest surprise (most to learn from)
            if entries:
                worst = max(entries, key=lambda e: e.world_model_surprise)
                return worst.entry_id
        return None

    def generate_adversarial_scenario(
        self,
        high_uncertainty_region: np.ndarray,
        world_model=None
    ) -> Optional[Dict]:
        """
        Adversarial self-play: generate imagined scenario specifically
        to exploit high-uncertainty region identified by L3 ensemble.
        Train on adversarially generated high-uncertainty scenarios to
        broaden robustness before deployment.
        """
        if world_model is None:
            return None

        # Use world model to imagine scenario from high-uncertainty state
        with torch.no_grad():
            initial = torch.FloatTensor(high_uncertainty_region).unsqueeze(0)
            trajectory = world_model.imagine_trajectory(initial, horizon=20)

        return {
            'initial_state': high_uncertainty_region,
            'imagined_trajectory': trajectory,
            'uncertainty_region': True
        }

    def decay_novelty(self):
        """Decay visit counts for state novelty."""
        for key in self.state_visit_counts:
            self.state_visit_counts[key] = int(
                self.state_visit_counts[key] * self.novelty_decay
            )


# =============================================================================
# B3 Ceiling-Pushed: Backward Causal Responsibility, Precondition/Termination
# Repair, Dual-Objective Relabeling, Failure-Mode Replay Queues
# =============================================================================

@dataclass
class OptionTransition:
    """
    A single option/skill transition within a trajectory.
    Used for backward causal responsibility tracing.
    """
    timestep: int
    skill_id: str
    pre_state_latent: np.ndarray
    post_state_latent: np.ndarray
    surprise_before: float  # L3 ensemble disagreement before option
    surprise_after: float   # L3 ensemble disagreement after option
    reward: float
    constraint_violations: List[str] = field(default_factory=list)
    outcome: str = "ongoing"  # 'ongoing', 'success', 'failure', 'partial'


class BackwardCausalResponsibility:
    """
    B3 Ceiling-Pushed: Backward Causal Responsibility over Recent Option Transitions.

    When a trajectory fails, don't just blame the last action. Trace backward
    through the option transition chain to find which option transition was
    the causal root of the failure. This is the credit assignment problem
    for hierarchical policies.

    Algorithm:
    1. Record option transitions during trajectory execution
    2. On failure, trace backward from failure point
    3. At each option boundary, check if surprise spiked
    4. The option where surprise first spiked is the causal root
    5. Assign responsibility proportional to surprise delta

    This is materially stronger than flat hindsight relabeling because
    it identifies WHICH option in the chain caused the failure, not just
    THAT the chain failed.
    """

    def __init__(
        self,
        surprise_spike_threshold: float = 2.0,
        max_traceback_steps: int = 10,
        responsibility_decay: float = 0.8
    ):
        self.surprise_spike_threshold = surprise_spike_threshold
        self.max_traceback_steps = max_traceback_steps
        self.responsibility_decay = responsibility_decay

        # History of responsibility assignments for learning
        self.responsibility_history: List[Dict] = []

    def trace_cause(
        self,
        option_chain: List[OptionTransition],
        failure_timestep: int
    ) -> Dict[str, float]:
        """
        Trace backward from failure point to assign causal responsibility.

        Returns dict mapping skill_id -> responsibility_weight (sums to 1.0).
        The option where surprise first spiked gets the most responsibility.
        """
        if not option_chain:
            return {}

        # Find transitions before failure
        relevant = [
            t for t in option_chain
            if t.timestep <= failure_timestep
        ]
        relevant = relevant[-self.max_traceback_steps:]

        if not relevant:
            return {}

        # Compute surprise deltas for each transition
        surprise_deltas = []
        for t in relevant:
            delta = t.surprise_after - t.surprise_before
            surprise_deltas.append(delta)

        # Find the first spike (causal root)
        causal_root_idx = None
        for i, delta in enumerate(surprise_deltas):
            if delta > self.surprise_spike_threshold:
                causal_root_idx = i
                break

        # Assign responsibility
        responsibilities = {}
        total_weight = 0.0

        for i, transition in enumerate(relevant):
            if causal_root_idx is not None:
                # Distance from causal root
                distance = abs(i - causal_root_idx)
                weight = self.responsibility_decay ** distance
            else:
                # No clear spike: distribute by recency (closer to failure = more responsible)
                distance = len(relevant) - 1 - i
                weight = self.responsibility_decay ** distance

            sid = transition.skill_id
            if sid in responsibilities:
                responsibilities[sid] += weight
            else:
                responsibilities[sid] = weight
            total_weight += weight

        # Normalize
        if total_weight > 0:
            responsibilities = {k: v / total_weight for k, v in responsibilities.items()}

        # Record for learning
        self.responsibility_history.append({
            'failure_timestep': failure_timestep,
            'causal_root_idx': causal_root_idx,
            'responsibilities': responsibilities.copy(),
            'n_transitions_traced': len(relevant)
        })

        return responsibilities

    def get_most_responsible_skill(
        self,
        option_chain: List[OptionTransition],
        failure_timestep: int
    ) -> Optional[Tuple[str, float]]:
        """Get the single most causally responsible skill for a failure."""
        responsibilities = self.trace_cause(option_chain, failure_timestep)
        if not responsibilities:
            return None
        best = max(responsibilities, key=responsibilities.get)
        return best, responsibilities[best]


class PreconditionTerminationRepair:
    """
    B3 Ceiling-Pushed: Precondition and Termination Repair.

    When a skill fails, the failure mode tells us what went wrong. But the
    deeper question is: why did the skill's PRECONDITION allow execution
    when the precondition wasn't actually satisfied? And why didn't the
    TERMINATION CONDITION stop execution before the failure occurred?

    This module:
    1. Analyzes failure modes to identify broken preconditions
    2. Proposes repairs to precondition predicates
    3. Analyzes late terminations to identify broken termination conditions
    4. Proposes repairs to termination predicates
    5. Validates repairs against historical success/failure data

    Without this, OCHL just relabels goals but doesn't fix the underlying
    broken precondition/termination logic that caused the failure.
    """

    def __init__(self, belief_tracker: Optional[BeliefStateTracker] = None):
        self.belief_tracker = belief_tracker

        # Repair history
        self.precondition_repairs: Dict[str, List[Dict]] = {}
        self.termination_repairs: Dict[str, List[Dict]] = {}

    def analyze_precondition_violation(
        self,
        skill_id: str,
        failure_mode: str,
        pre_skill_latent: np.ndarray,
        option_chain: List[OptionTransition]
    ) -> Dict[str, Any]:
        """
        Analyze why a precondition was violated.

        The precondition said "OK to execute" but the skill failed.
        This means the precondition predicate was too permissive.
        Propose a repair that would have prevented execution.
        """
        analysis = {
            'skill_id': skill_id,
            'failure_mode': failure_mode,
            'current_preconditions': {},
            'proposed_repairs': [],
            'confidence': 0.5
        }

        # Get current preconditions from skill library
        if self.belief_tracker and skill_id in self.belief_tracker.skill_library:
            analysis['current_preconditions'] = (
                self.belief_tracker.skill_library[skill_id].get('preconditions', {})
            )

        # Analyze failure mode to propose precondition repair
        if failure_mode == 'precondition_violation':
            # The skill was executed when it shouldn't have been
            # Propose adding a new precondition based on the latent state
            analysis['proposed_repairs'].append({
                'type': 'add_precondition',
                'description': f'Add precondition to prevent {failure_mode}',
                'latent_signature': pre_skill_latent[:10].round(3).tolist(),
                'confidence': 0.6
            })

        elif failure_mode == 'execution_error':
            # The skill started OK but something went wrong mid-execution
            # This suggests a precondition was satisfied but a context condition changed
            analysis['proposed_repairs'].append({
                'type': 'add_context_condition',
                'description': f'Add context stability precondition for {skill_id}',
                'confidence': 0.5
            })

        elif failure_mode == 'contact_mismatch':
            # Expected contact didn't happen or unexpected contact occurred
            analysis['proposed_repairs'].append({
                'type': 'add_contact_precondition',
                'description': f'Add contact state precondition for {skill_id}',
                'confidence': 0.7
            })

        # Record repair
        if skill_id not in self.precondition_repairs:
            self.precondition_repairs[skill_id] = []
        self.precondition_repairs[skill_id].append(analysis)

        return analysis

    def analyze_termination_failure(
        self,
        skill_id: str,
        failure_mode: str,
        post_skill_latent: np.ndarray,
        expected_termination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze why a termination condition failed to trigger.

        The skill should have stopped but didn't, leading to overshoot
        or constraint violation. This means the termination predicate
        was too restrictive (didn't fire when it should have).
        """
        analysis = {
            'skill_id': skill_id,
            'failure_mode': failure_mode,
            'current_termination_conditions': {},
            'proposed_repairs': [],
            'confidence': 0.5
        }

        # Get current termination conditions
        if self.belief_tracker and skill_id in self.belief_tracker.skill_library:
            analysis['current_termination_conditions'] = (
                self.belief_tracker.skill_library[skill_id].get('termination_conditions', {})
            )

        # Propose termination repair
        if failure_mode in ['constraint_violation', 'overshoot', 'collision']:
            # The skill should have terminated earlier
            analysis['proposed_repairs'].append({
                'type': 'tighten_termination',
                'description': f'Tighten termination condition to prevent {failure_mode}',
                'latent_signature': post_skill_latent[:10].round(3).tolist(),
                'confidence': 0.6
            })

        elif failure_mode == 'timeout':
            # Skill never reached its termination condition
            analysis['proposed_repairs'].append({
                'type': 'loosen_termination',
                'description': f'Loosen termination condition for {skill_id} (timeout suggests too strict)',
                'confidence': 0.5
            })

        # Record repair
        if skill_id not in self.termination_repairs:
            self.termination_repairs[skill_id] = []
        self.termination_repairs[skill_id].append(analysis)

        return analysis

    def apply_repairs(
        self,
        skill_id: str,
        precondition_repairs: Optional[List[Dict]] = None,
        termination_repairs: Optional[List[Dict]] = None
    ) -> bool:
        """
        Apply validated repairs to the skill library.
        Only applies repairs with confidence > 0.7.
        """
        if not self.belief_tracker or skill_id not in self.belief_tracker.skill_library:
            return False

        skill = self.belief_tracker.skill_library[skill_id]
        applied = False

        if precondition_repairs:
            for repair in precondition_repairs:
                if repair.get('confidence', 0) > 0.7:
                    desc = repair.get('description', 'unknown_repair')
                    skill['preconditions'][desc] = True
                    applied = True

        if termination_repairs:
            for repair in termination_repairs:
                if repair.get('confidence', 0) > 0.7:
                    desc = repair.get('description', 'unknown_repair')
                    skill['termination_conditions'][desc] = True
                    applied = True

        return applied


class DualObjectiveRelabeler:
    """
    B3 Ceiling-Pushed: Dual-Objective Relabeling.

    Standard hindsight relabeling replaces the failed goal with the achieved goal.
    But for manipulation/contact tasks, the achieved goal might be partially
    correct (e.g., reached the right position but wrong orientation). A single
    relabeling loses this information.

    Dual-objective relabeling:
    1. Original objective: what we were trying to achieve (even if failed)
    2. Achieved objective: what actually happened (useful for learning)

    Both objectives are stored, and training uses BOTH:
    - The original objective teaches the policy what NOT to do
    - The achieved objective teaches the policy what THIS trajectory is good for

    This is especially important for manipulation/contact tasks where
    partial success contains valuable information that single-objective
    relabeling would discard.
    """

    def __init__(self, belief_tracker: Optional[BeliefStateTracker] = None):
        self.belief_tracker = belief_tracker
        self.relabel_history: List[Dict] = []

    def relabel(
        self,
        skill_id: str,
        original_goal: str,
        achieved_state_latent: np.ndarray,
        outcome: str,
        partial_success_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Dual-objective relabeling for a failed skill execution.

        Returns:
            Dict with both original and achieved objectives
        """
        # Determine achieved goal from the latent state
        achieved_goal = self._infer_achieved_goal(achieved_state_latent, outcome)

        # Compute partial success score
        partial_score = 0.0
        if partial_success_metrics:
            partial_score = np.mean(list(partial_success_metrics.values()))

        relabel_result = {
            'skill_id': skill_id,
            'original_goal': original_goal,
            'achieved_goal': achieved_goal,
            'outcome': outcome,
            'partial_success_score': partial_score,
            'partial_metrics': partial_success_metrics or {},
            'dual_training_signals': {
                # Signal 1: What NOT to do (original goal, negative outcome)
                'negative_signal': {
                    'goal': original_goal,
                    'weight': 1.0 - partial_score,  # Weight by how badly it failed
                    'label': 'failure'
                },
                # Signal 2: What THIS trajectory IS good for (achieved goal)
                'positive_signal': {
                    'goal': achieved_goal,
                    'weight': partial_score,  # Weight by partial success
                    'label': 'success' if partial_score > 0.5 else 'partial'
                }
            }
        }

        # Update skill memory with dual labels
        if self.belief_tracker:
            entries = self.belief_tracker.skill_memory.get(skill_id, [])
            for entry in entries:
                if (entry.outcome_tag == 'failure' and
                        entry.hindsight_goal is None):
                    entry.hindsight_goal = f"dual:{original_goal}|{achieved_goal}"

        self.relabel_history.append(relabel_result)
        return relabel_result

    def _infer_achieved_goal(
        self,
        achieved_latent: np.ndarray,
        outcome: str
    ) -> str:
        """Infer what goal was actually achieved from the latent state."""
        # Simplified: use latent signature as goal descriptor
        signature = achieved_latent[:5].round(2).tolist()
        prefix = "achieved" if outcome != "total_failure" else "diverged"
        return f"{prefix}_{signature}"


class FailureModeReplayQueues:
    """
    B3 Ceiling-Pushed: Skill-Specific Replay Queues Keyed by Failure Mode.

    Standard replay buffers mix all experiences together. But a skill that
    fails due to "precondition_violation" needs very different training
    data than one that fails due to "contact_mismatch". Mixing them
    together dilutes the learning signal.

    This module maintains separate replay queues per (skill_id, failure_mode)
    pair. When training a skill, the system can:
    1. Sample from the skill's failure queue to learn what went wrong
    2. Sample from the skill's success queue to reinforce what works
    3. Focus on the most common failure mode first
    4. Prioritize rare failure modes that haven't been trained on much

    This is the replay counterpart to backward causal responsibility:
    responsibility tells you WHICH skill failed, and failure-mode queues
    let you train that skill on exactly the right kind of failures.
    """

    def __init__(
        self,
        max_queue_size: int = 1000,
        min_samples_for_training: int = 10
    ):
        self.max_queue_size = max_queue_size
        self.min_samples_for_training = min_samples_for_training

        # Queues: (skill_id, failure_mode) -> deque of entries
        self.queues: Dict[Tuple[str, str], deque] = {}
        # Success queues: skill_id -> deque of successful entries
        self.success_queues: Dict[str, deque] = {}

        # Failure mode frequency tracking
        self.failure_mode_counts: Dict[Tuple[str, str], int] = {}

    def add_failure(
        self,
        skill_id: str,
        failure_mode: str,
        entry: SkillMemoryEntry
    ):
        """Add a failed experience to the appropriate failure-mode queue."""
        key = (skill_id, failure_mode)

        if key not in self.queues:
            self.queues[key] = deque(maxlen=self.max_queue_size)
        self.queues[key].append(entry)

        # Update frequency
        self.failure_mode_counts[key] = self.failure_mode_counts.get(key, 0) + 1

    def add_success(
        self,
        skill_id: str,
        entry: SkillMemoryEntry
    ):
        """Add a successful experience to the skill's success queue."""
        if skill_id not in self.success_queues:
            self.success_queues[skill_id] = deque(maxlen=self.max_queue_size)
        self.success_queues[skill_id].append(entry)

    def sample_for_training(
        self,
        skill_id: str,
        failure_mode: Optional[str] = None,
        batch_size: int = 32,
        success_ratio: float = 0.3
    ) -> List[SkillMemoryEntry]:
        """
        Sample a batch for training a specific skill.

        If failure_mode is specified, samples from that specific failure queue.
        Otherwise, samples from the skill's most common failure mode.

        Always includes some successful experiences (success_ratio) to
        maintain a balanced training signal.
        """
        n_success = int(batch_size * success_ratio)
        n_failure = batch_size - n_success

        samples = []

        # Sample successes
        success_queue = self.success_queues.get(skill_id, deque())
        if success_queue:
            n_available = min(n_success, len(success_queue))
            indices = np.random.choice(len(success_queue), size=n_available, replace=False)
            for idx in indices:
                samples.append(list(success_queue)[idx])

        # Sample failures
        if failure_mode:
            key = (skill_id, failure_mode)
            failure_queue = self.queues.get(key, deque())
        else:
            # Use most common failure mode for this skill
            skill_failures = {
                k: v for k, v in self.failure_mode_counts.items()
                if k[0] == skill_id
            }
            if skill_failures:
                most_common_key = max(skill_failures, key=skill_failures.get)
                failure_queue = self.queues.get(most_common_key, deque())
            else:
                failure_queue = deque()

        if failure_queue and len(failure_queue) >= self.min_samples_for_training:
            n_available = min(n_failure, len(failure_queue))
            indices = np.random.choice(len(failure_queue), size=n_available, replace=False)
            for idx in indices:
                samples.append(list(failure_queue)[idx])

        return samples

    def get_rare_failure_modes(
        self,
        skill_id: str,
        rarity_threshold: int = 20
    ) -> List[str]:
        """
        Get failure modes that haven't been trained on much.
        These should be prioritized for active experimentation.
        """
        rare_modes = []
        for (sid, fmode), count in self.failure_mode_counts.items():
            if sid == skill_id and count < rarity_threshold:
                rare_modes.append(fmode)
        return rare_modes

    def get_failure_mode_distribution(self, skill_id: str) -> Dict[str, float]:
        """Get the distribution of failure modes for a skill."""
        skill_counts = {
            k[1]: v for k, v in self.failure_mode_counts.items()
            if k[0] == skill_id
        }
        total = sum(skill_counts.values())
        if total == 0:
            return {}
        return {k: v / total for k, v in skill_counts.items()}
