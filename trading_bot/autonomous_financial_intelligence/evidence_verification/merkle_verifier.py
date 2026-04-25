"""
Merkle Tree Verification System

Provides Merkle-tree based verification of data integrity for evidence chains.
Enables efficient proof of inclusion and tamper detection.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import math

logger = logging.getLogger(__name__)


@dataclass
class MerkleNode:
    """Node in a Merkle tree."""
    hash_value: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    data: Optional[Any] = None
    is_leaf: bool = False
    index: int = -1


@dataclass
class MerkleProof:
    """
    Proof of inclusion in a Merkle tree.
    Contains the path from leaf to root with sibling hashes.
    """
    leaf_hash: str
    leaf_index: int
    proof_hashes: List[Tuple[str, str]]  # (hash, position: 'left' or 'right')
    root_hash: str
    tree_size: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'leaf_hash': self.leaf_hash,
            'leaf_index': self.leaf_index,
            'proof_hashes': self.proof_hashes,
            'root_hash': self.root_hash,
            'tree_size': self.tree_size,
            'timestamp': self.timestamp.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MerkleProof':
        return cls(
            leaf_hash=data['leaf_hash'],
            leaf_index=data['leaf_index'],
            proof_hashes=data['proof_hashes'],
            root_hash=data['root_hash'],
            tree_size=data['tree_size'],
            timestamp=datetime.fromisoformat(data['timestamp']),
        )


@dataclass
class MerkleTree:
    """
    Complete Merkle tree structure.
    Stores all nodes and provides efficient verification.
    """
    tree_id: str
    root_hash: str
    leaf_count: int
    height: int
    created_at: datetime
    leaves: List[str]
    root_node: Optional[MerkleNode] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tree_id': self.tree_id,
            'root_hash': self.root_hash,
            'leaf_count': self.leaf_count,
            'height': self.height,
            'created_at': self.created_at.isoformat(),
            'leaves': self.leaves,
        }


class MerkleVerifier:
    """
    Merkle tree-based verification system for evidence integrity.
    
    Provides:
    - Tree construction from evidence hashes
    - Proof generation for inclusion verification
    - Efficient batch verification
    - Tamper detection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'merkle_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._trees: Dict[str, MerkleTree] = {}
        self._hash_algorithm = self.config.get('hash_algorithm', 'sha256')
        
        logger.info("✅ Merkle Verifier initialized")
    
    def _hash(self, data: Any) -> str:
        """Compute hash of data."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True, default=str)
        elif isinstance(data, bytes):
            data_str = data.decode('utf-8', errors='ignore')
        else:
            data_str = str(data)
        
        if self._hash_algorithm == 'sha256':
            return hashlib.sha256(data_str.encode()).hexdigest()
        elif self._hash_algorithm == 'sha3_256':
            return hashlib.sha3_256(data_str.encode()).hexdigest()
        else:
            return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _combine_hashes(self, left: str, right: str) -> str:
        """Combine two hashes to create parent hash."""
        combined = left + right
        return self._hash(combined)
    
    def build_tree(self, data_items: List[Any], tree_id: Optional[str] = None) -> MerkleTree:
        """
        Build a Merkle tree from a list of data items.
        
        Args:
            data_items: List of items to include in tree
            tree_id: Optional ID for the tree
        
        Returns:
            MerkleTree with root hash and structure
        """
        if not data_items:
            raise ValueError("Cannot build Merkle tree from empty list")
        
        import uuid
        tree_id = tree_id or f"MKT-{uuid.uuid4().hex[:16]}"
        
        leaf_hashes = [self._hash(item) for item in data_items]
        
        if len(leaf_hashes) % 2 == 1:
            leaf_hashes.append(leaf_hashes[-1])
        
        leaves = [
            MerkleNode(
                hash_value=h,
                is_leaf=True,
                index=i,
                data=data_items[i] if i < len(data_items) else None
            )
            for i, h in enumerate(leaf_hashes)
        ]
        
        current_level = leaves
        height = 1
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
                
                parent_hash = self._combine_hashes(left.hash_value, right.hash_value)
                parent = MerkleNode(
                    hash_value=parent_hash,
                    left=left,
                    right=right,
                )
                next_level.append(parent)
            
            current_level = next_level
            height += 1
        
        root_node = current_level[0]
        
        tree = MerkleTree(
            tree_id=tree_id,
            root_hash=root_node.hash_value,
            leaf_count=len(data_items),
            height=height,
            created_at=datetime.now(timezone.utc),
            leaves=[h for h in leaf_hashes[:len(data_items)]],
            root_node=root_node,
        )
        
        self._trees[tree_id] = tree
        
        logger.info(f"Built Merkle tree {tree_id}: {len(data_items)} leaves, height {height}")
        
        return tree
    
    def generate_proof(self, tree_id: str, leaf_index: int) -> Optional[MerkleProof]:
        """
        Generate a Merkle proof for a specific leaf.
        
        Args:
            tree_id: ID of the tree
            leaf_index: Index of the leaf to prove
        
        Returns:
            MerkleProof for verification
        """
        if tree_id not in self._trees:
            logger.error(f"Tree {tree_id} not found")
            return None
        
        tree = self._trees[tree_id]
        
        if leaf_index < 0 or leaf_index >= tree.leaf_count:
            logger.error(f"Invalid leaf index {leaf_index}")
            return None
        
        leaves = tree.leaves[:]
        if len(leaves) % 2 == 1:
            leaves.append(leaves[-1])
        
        proof_hashes = []
        current_index = leaf_index
        current_level = leaves
        
        while len(current_level) > 1:
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                if sibling_index < len(current_level):
                    proof_hashes.append((current_level[sibling_index], 'right'))
                else:
                    proof_hashes.append((current_level[current_index], 'right'))
            else:
                sibling_index = current_index - 1
                proof_hashes.append((current_level[sibling_index], 'left'))
            
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else current_level[i]
                parent_hash = self._combine_hashes(left, right)
                next_level.append(parent_hash)
            
            current_level = next_level
            current_index = current_index // 2
        
        proof = MerkleProof(
            leaf_hash=tree.leaves[leaf_index],
            leaf_index=leaf_index,
            proof_hashes=proof_hashes,
            root_hash=tree.root_hash,
            tree_size=tree.leaf_count,
        )
        
        return proof
    
    def verify_proof(self, proof: MerkleProof) -> Tuple[bool, str]:
        """
        Verify a Merkle proof.
        
        Args:
            proof: MerkleProof to verify
        
        Returns:
            Tuple of (is_valid, reason)
        """
        current_hash = proof.leaf_hash
        
        for sibling_hash, position in proof.proof_hashes:
            if position == 'left':
                current_hash = self._combine_hashes(sibling_hash, current_hash)
            else:
                current_hash = self._combine_hashes(current_hash, sibling_hash)
        
        if current_hash == proof.root_hash:
            return True, "Proof verified successfully"
        else:
            return False, f"Root hash mismatch: expected {proof.root_hash}, got {current_hash}"
    
    def verify_data_inclusion(
        self, 
        tree_id: str, 
        data: Any, 
        expected_index: Optional[int] = None
    ) -> Tuple[bool, Optional[MerkleProof]]:
        """
        Verify that specific data is included in a tree.
        
        Args:
            tree_id: ID of the tree
            data: Data to verify inclusion of
            expected_index: Optional expected index in tree
        
        Returns:
            Tuple of (is_included, proof)
        """
        if tree_id not in self._trees:
            return False, None
        
        tree = self._trees[tree_id]
        data_hash = self._hash(data)
        
        try:
            if expected_index is not None:
                if tree.leaves[expected_index] == data_hash:
                    proof = self.generate_proof(tree_id, expected_index)
                    return True, proof
                return False, None
            
            for i, leaf_hash in enumerate(tree.leaves):
                if leaf_hash == data_hash:
                    proof = self.generate_proof(tree_id, i)
                    return True, proof
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error verifying data inclusion: {e}")
            return False, None
    
    def batch_verify(self, proofs: List[MerkleProof]) -> Dict[str, Any]:
        """
        Verify multiple proofs efficiently.
        
        Args:
            proofs: List of proofs to verify
        
        Returns:
            Verification report
        """
        results = {
            'total': len(proofs),
            'verified': 0,
            'failed': 0,
            'details': [],
        }
        
        for proof in proofs:
            is_valid, reason = self.verify_proof(proof)
            results['details'].append({
                'leaf_hash': proof.leaf_hash,
                'leaf_index': proof.leaf_index,
                'is_valid': is_valid,
                'reason': reason,
            })
            
            if is_valid:
                results['verified'] += 1
            else:
                results['failed'] += 1
        
        results['success_rate'] = results['verified'] / results['total'] if results['total'] > 0 else 0
        
        return results
    
    def detect_tampering(self, tree_id: str, current_data: List[Any]) -> Dict[str, Any]:
        """
        Detect if data has been tampered with since tree creation.
        
        Args:
            tree_id: ID of the original tree
            current_data: Current state of the data
        
        Returns:
            Tampering detection report
        """
        if tree_id not in self._trees:
            return {'error': 'Tree not found', 'tampered': True}
        
        original_tree = self._trees[tree_id]
        
        report = {
            'tree_id': tree_id,
            'tampered': False,
            'modified_indices': [],
            'added_items': 0,
            'removed_items': 0,
            'original_count': original_tree.leaf_count,
            'current_count': len(current_data),
        }
        
        current_hashes = [self._hash(item) for item in current_data]
        
        min_len = min(len(original_tree.leaves), len(current_hashes))
        for i in range(min_len):
            if original_tree.leaves[i] != current_hashes[i]:
                report['modified_indices'].append(i)
                report['tampered'] = True
        
        if len(current_data) > original_tree.leaf_count:
            report['added_items'] = len(current_data) - original_tree.leaf_count
            report['tampered'] = True
        elif len(current_data) < original_tree.leaf_count:
            report['removed_items'] = original_tree.leaf_count - len(current_data)
            report['tampered'] = True
        
        return report
    
    def get_tree_info(self, tree_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a tree."""
        if tree_id not in self._trees:
            return None
        
        tree = self._trees[tree_id]
        return {
            'tree_id': tree.tree_id,
            'root_hash': tree.root_hash,
            'leaf_count': tree.leaf_count,
            'height': tree.height,
            'created_at': tree.created_at.isoformat(),
        }
    
    async def persist_tree(self, tree_id: str):
        """Persist a tree to storage."""
        if tree_id not in self._trees:
            return
        
        tree = self._trees[tree_id]
        tree_file = self.storage_path / f"{tree_id}.json"
        
        with open(tree_file, 'w') as f:
            json.dump(tree.to_dict(), f, indent=2)
    
    async def load_tree(self, tree_id: str) -> Optional[MerkleTree]:
        """Load a tree from storage."""
        tree_file = self.storage_path / f"{tree_id}.json"
        
        if not tree_file.exists():
            return None
        
        with open(tree_file, 'r') as f:
            data = json.load(f)
        
        tree = MerkleTree(
            tree_id=data['tree_id'],
            root_hash=data['root_hash'],
            leaf_count=data['leaf_count'],
            height=data['height'],
            created_at=datetime.fromisoformat(data['created_at']),
            leaves=data['leaves'],
        )
        
        self._trees[tree_id] = tree
        return tree
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about all trees."""
        total_leaves = sum(t.leaf_count for t in self._trees.values())
        
        return {
            'total_trees': len(self._trees),
            'total_leaves': total_leaves,
            'average_height': sum(t.height for t in self._trees.values()) / len(self._trees) if self._trees else 0,
        }
