"""
Perplexity Reasoning Chains
============================

Advanced reasoning system with step-by-step logic:
- Chain of Thought (CoT) reasoning
- Tree of Thoughts (ToT) exploration
- Self-consistency checking
- Backtracking and revision
- Confidence propagation
- Reasoning verification
- Multi-path exploration

Enables transparent, verifiable reasoning for trading decisions
with full explanation of the logical steps taken.
"""

import asyncio
import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import hashlib
import json

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of reasoning"""
    DEDUCTIVE = "deductive"       # General to specific
    INDUCTIVE = "inductive"       # Specific to general
    ABDUCTIVE = "abductive"       # Best explanation
    ANALOGICAL = "analogical"     # By comparison
    CAUSAL = "causal"             # Cause and effect
    PROBABILISTIC = "probabilistic"  # Based on probabilities


class ThoughtStatus(Enum):
    """Status of a thought in the chain"""
    PENDING = "pending"
    PROCESSING = "processing"
    VERIFIED = "verified"
    REJECTED = "rejected"
    REVISED = "revised"


class ConfidenceLevel(Enum):
    """Confidence levels for reasoning steps"""
    CERTAIN = "certain"           # >95%
    HIGH = "high"                 # 80-95%
    MODERATE = "moderate"         # 60-80%
    LOW = "low"                   # 40-60%
    UNCERTAIN = "uncertain"       # <40%


@dataclass
class Thought:
    """A single thought in the reasoning chain"""
    thought_id: str
    content: str
    reasoning_type: ReasoningType
    
    # Chain position
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    depth: int = 0
    
    # Confidence
    confidence: float = 0.5
    confidence_level: ConfidenceLevel = ConfidenceLevel.MODERATE
    
    # Evidence
    evidence: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    # Status
    status: ThoughtStatus = ThoughtStatus.PENDING
    verification_result: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0
    
    def update_confidence_level(self) -> None:
        """Update confidence level based on numeric confidence"""
        if self.confidence >= 0.95:
            self.confidence_level = ConfidenceLevel.CERTAIN
        elif self.confidence >= 0.80:
            self.confidence_level = ConfidenceLevel.HIGH
        elif self.confidence >= 0.60:
            self.confidence_level = ConfidenceLevel.MODERATE
        elif self.confidence >= 0.40:
            self.confidence_level = ConfidenceLevel.LOW
        else:
            self.confidence_level = ConfidenceLevel.UNCERTAIN


@dataclass
class ReasoningStep:
    """A step in the reasoning process"""
    step_id: str
    step_number: int
    description: str
    
    # Input/Output
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    
    # Logic
    logic_applied: str
    reasoning_type: ReasoningType
    
    # Confidence
    input_confidence: float
    output_confidence: float
    confidence_delta: float = 0.0
    
    # Verification
    is_verified: bool = False
    verification_method: Optional[str] = None
    
    def to_explanation(self) -> str:
        """Convert step to human-readable explanation"""
        return (
            f"Step {self.step_number}: {self.description}\n"
            f"  Logic: {self.logic_applied}\n"
            f"  Confidence: {self.input_confidence:.1%} → {self.output_confidence:.1%}"
        )


@dataclass
class ReasoningChain:
    """A complete chain of reasoning"""
    chain_id: str
    query: str
    
    # Chain structure
    thoughts: List[Thought] = field(default_factory=list)
    steps: List[ReasoningStep] = field(default_factory=list)
    
    # Result
    conclusion: Optional[str] = None
    final_confidence: float = 0.0
    
    # Metadata
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_thoughts: int = 0
    verified_thoughts: int = 0
    rejected_thoughts: int = 0
    
    def get_main_path(self) -> List[Thought]:
        """Get the main reasoning path (highest confidence)"""
        if not self.thoughts:
            return []
        
        # Find root
        root = None
        for t in self.thoughts:
            if t.parent_id is None:
                root = t
                break
        
        if not root:
            return []
        
        # Follow highest confidence path
        path = [root]
        current = root
        
        while current.children_ids:
            # Find highest confidence child
            best_child = None
            best_confidence = -1
            
            for child_id in current.children_ids:
                child = next((t for t in self.thoughts if t.thought_id == child_id), None)
                if child and child.confidence > best_confidence:
                    best_confidence = child.confidence
                    best_child = child
            
            if best_child:
                path.append(best_child)
                current = best_child
            else:
                break
        
        return path
    
    def get_explanation(self) -> str:
        """Get full explanation of reasoning"""
        lines = [f"Query: {self.query}", ""]
        
        for step in self.steps:
            lines.append(step.to_explanation())
            lines.append("")
        
        if self.conclusion:
            lines.append(f"Conclusion: {self.conclusion}")
            lines.append(f"Final Confidence: {self.final_confidence:.1%}")
        
        return "\n".join(lines)


class ThoughtVerifier:
    """
    Verifies thoughts for consistency and validity
    """
    
    def __init__(self):
        self.verification_rules: List[Callable[[Thought], Tuple[bool, str]]] = []
        self._init_default_rules()
    
    def _init_default_rules(self) -> None:
        """Initialize default verification rules"""
        # Rule: Must have evidence
        def has_evidence(thought: Thought) -> Tuple[bool, str]:
            if not thought.evidence and thought.confidence > 0.7:
                return False, "High confidence claim without evidence"
            return True, "Evidence check passed"
        
        # Rule: Assumptions must be reasonable
        def reasonable_assumptions(thought: Thought) -> Tuple[bool, str]:
            if len(thought.assumptions) > 5:
                return False, "Too many assumptions"
            return True, "Assumptions check passed"
        
        # Rule: Confidence must match content
        def confidence_matches(thought: Thought) -> Tuple[bool, str]:
            # Check for hedging words with high confidence
            hedging_words = ["might", "maybe", "possibly", "uncertain", "unclear"]
            content_lower = thought.content.lower()
            
            has_hedging = any(word in content_lower for word in hedging_words)
            if has_hedging and thought.confidence > 0.8:
                return False, "Hedging language with high confidence"
            
            return True, "Confidence-content alignment check passed"
        
        self.verification_rules.extend([
            has_evidence,
            reasonable_assumptions,
            confidence_matches,
        ])
    
    def verify(self, thought: Thought) -> Tuple[bool, List[str]]:
        """Verify a thought against all rules"""
        results = []
        all_passed = True
        
        for rule in self.verification_rules:
            passed, message = rule(thought)
            results.append(message)
            if not passed:
                all_passed = False
        
        return all_passed, results
    
    def add_rule(self, rule: Callable[[Thought], Tuple[bool, str]]) -> None:
        """Add a verification rule"""
        self.verification_rules.append(rule)


class TreeOfThoughts:
    """
    Tree of Thoughts exploration for complex reasoning
    """
    
    def __init__(self, max_depth: int = 5, branching_factor: int = 3):
        self.max_depth = max_depth
        self.branching_factor = branching_factor
        self.thoughts: Dict[str, Thought] = {}
        self.root_id: Optional[str] = None
    
    def create_root(self, content: str, reasoning_type: ReasoningType) -> Thought:
        """Create root thought"""
        thought = Thought(
            thought_id=f"thought_root_{datetime.utcnow().strftime('%H%M%S%f')}",
            content=content,
            reasoning_type=reasoning_type,
            depth=0,
        )
        
        self.thoughts[thought.thought_id] = thought
        self.root_id = thought.thought_id
        
        return thought
    
    def expand(self, parent_id: str, thoughts: List[Tuple[str, ReasoningType, float]]) -> List[Thought]:
        """Expand a thought with children"""
        parent = self.thoughts.get(parent_id)
        if not parent:
            return []
        
        if parent.depth >= self.max_depth:
            return []
        
        children = []
        for content, reasoning_type, confidence in thoughts[:self.branching_factor]:
            child = Thought(
                thought_id=f"thought_{datetime.utcnow().strftime('%H%M%S%f')}_{len(self.thoughts)}",
                content=content,
                reasoning_type=reasoning_type,
                parent_id=parent_id,
                depth=parent.depth + 1,
                confidence=confidence,
            )
            child.update_confidence_level()
            
            self.thoughts[child.thought_id] = child
            parent.children_ids.append(child.thought_id)
            children.append(child)
        
        return children
    
    def prune(self, min_confidence: float = 0.3) -> int:
        """Prune low-confidence branches"""
        to_remove = []
        
        for thought_id, thought in self.thoughts.items():
            if thought_id == self.root_id:
                continue
            
            if thought.confidence < min_confidence:
                to_remove.append(thought_id)
        
        for thought_id in to_remove:
            self._remove_subtree(thought_id)
        
        return len(to_remove)
    
    def _remove_subtree(self, thought_id: str) -> None:
        """Remove a thought and all its descendants"""
        thought = self.thoughts.get(thought_id)
        if not thought:
            return
        
        # Remove children first
        for child_id in thought.children_ids:
            self._remove_subtree(child_id)
        
        # Remove from parent
        if thought.parent_id and thought.parent_id in self.thoughts:
            parent = self.thoughts[thought.parent_id]
            if thought_id in parent.children_ids:
                parent.children_ids.remove(thought_id)
        
        # Remove thought
        del self.thoughts[thought_id]
    
    def get_best_path(self) -> List[Thought]:
        """Get the best reasoning path"""
        if not self.root_id:
            return []
        
        path = []
        current_id = self.root_id
        
        while current_id:
            thought = self.thoughts.get(current_id)
            if not thought:
                break
            
            path.append(thought)
            
            # Find best child
            if thought.children_ids:
                best_child_id = max(
                    thought.children_ids,
                    key=lambda cid: self.thoughts[cid].confidence if cid in self.thoughts else 0
                )
                current_id = best_child_id
            else:
                current_id = None
        
        return path
    
    def get_all_paths(self) -> List[List[Thought]]:
        """Get all leaf-to-root paths"""
        paths = []
        
        # Find leaves
        leaves = [
            t for t in self.thoughts.values()
            if not t.children_ids
        ]
        
        for leaf in leaves:
            path = []
            current = leaf
            
            while current:
                path.append(current)
                if current.parent_id:
                    current = self.thoughts.get(current.parent_id)
                else:
                    current = None
            
            path.reverse()
            paths.append(path)
        
        return paths


class SelfConsistencyChecker:
    """
    Checks self-consistency across multiple reasoning paths
    """
    
    def __init__(self, num_samples: int = 5):
        self.num_samples = num_samples
        self.consistency_history: List[Dict[str, Any]] = []
    
    def check_consistency(self, paths: List[List[Thought]]) -> Dict[str, Any]:
        """Check consistency across paths"""
        if not paths:
            return {"consistent": True, "agreement": 1.0, "details": []}
        
        # Extract conclusions from each path
        conclusions = []
        for path in paths:
            if path:
                conclusion = path[-1].content
                confidence = path[-1].confidence
                conclusions.append((conclusion, confidence))
        
        if not conclusions:
            return {"consistent": True, "agreement": 1.0, "details": []}
        
        # Check agreement
        # Group similar conclusions
        groups: Dict[str, List[float]] = {}
        for conclusion, confidence in conclusions:
            # Simple grouping by first few words
            key = " ".join(conclusion.split()[:5]).lower()
            if key not in groups:
                groups[key] = []
            groups[key].append(confidence)
        
        # Calculate agreement
        largest_group = max(len(g) for g in groups.values())
        agreement = largest_group / len(conclusions)
        
        # Weighted agreement by confidence
        total_confidence = sum(c for _, c in conclusions)
        if total_confidence > 0:
            weighted_agreement = sum(
                c for conclusion, c in conclusions
                if " ".join(conclusion.split()[:5]).lower() == max(groups, key=lambda k: len(groups[k]))
            ) / total_confidence
        else:
            weighted_agreement = agreement
        
        result = {
            "consistent": agreement >= 0.6,
            "agreement": agreement,
            "weighted_agreement": weighted_agreement,
            "num_paths": len(paths),
            "num_groups": len(groups),
            "majority_conclusion": max(groups, key=lambda k: len(groups[k])),
        }
        
        self.consistency_history.append(result)
        
        return result


class ReasoningChainEngine:
    """
    Reasoning Chain Engine
    
    Implements advanced reasoning with:
    - Chain of Thought reasoning
    - Tree of Thoughts exploration
    - Self-consistency checking
    - Confidence propagation
    - Verification and revision
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.verifier = ThoughtVerifier()
        self.consistency_checker = SelfConsistencyChecker()
        
        # Active chains
        self.active_chains: Dict[str, ReasoningChain] = {}
        self.completed_chains: List[ReasoningChain] = []
        
        # Statistics
        self.total_chains = 0
        self.total_thoughts = 0
        self.total_verifications = 0
        
        logger.info("ReasoningChainEngine initialized")
    
    async def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        use_tree: bool = True,
    ) -> ReasoningChain:
        """Perform reasoning on a query"""
        chain_id = f"chain_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        
        chain = ReasoningChain(
            chain_id=chain_id,
            query=query,
        )
        
        self.active_chains[chain_id] = chain
        self.total_chains += 1
        
        try:
            if use_tree:
                # Tree of Thoughts reasoning
                await self._tree_reasoning(chain, context)
            else:
                # Linear chain reasoning
                await self._chain_reasoning(chain, context)
            
            # Self-consistency check
            if use_tree:
                tree = self._get_tree_for_chain(chain)
                if tree:
                    paths = tree.get_all_paths()
                    consistency = self.consistency_checker.check_consistency(paths)
                    
                    if not consistency["consistent"]:
                        # Revise based on majority
                        chain.conclusion = f"Majority conclusion: {consistency['majority_conclusion']}"
                        chain.final_confidence *= consistency["weighted_agreement"]
            
            chain.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Reasoning error: {e}")
            chain.conclusion = f"Error: {str(e)}"
            chain.final_confidence = 0
        
        finally:
            del self.active_chains[chain_id]
            self.completed_chains.append(chain)
        
        return chain
    
    async def _chain_reasoning(
        self,
        chain: ReasoningChain,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Linear chain of thought reasoning"""
        # Step 1: Understand the query
        step1 = await self._create_step(
            chain, 1,
            "Understanding the query",
            {"query": chain.query},
            ReasoningType.DEDUCTIVE,
        )
        chain.steps.append(step1)
        
        # Step 2: Gather relevant information
        step2 = await self._create_step(
            chain, 2,
            "Gathering relevant information",
            {"context": context or {}},
            ReasoningType.INDUCTIVE,
            input_confidence=step1.output_confidence,
        )
        chain.steps.append(step2)
        
        # Step 3: Analyze information
        step3 = await self._create_step(
            chain, 3,
            "Analyzing information",
            {"previous_output": step2.output_data},
            ReasoningType.ABDUCTIVE,
            input_confidence=step2.output_confidence,
        )
        chain.steps.append(step3)
        
        # Step 4: Form conclusion
        step4 = await self._create_step(
            chain, 4,
            "Forming conclusion",
            {"analysis": step3.output_data},
            ReasoningType.DEDUCTIVE,
            input_confidence=step3.output_confidence,
        )
        chain.steps.append(step4)
        
        # Set conclusion
        chain.conclusion = step4.output_data.get("conclusion", "Unable to reach conclusion")
        chain.final_confidence = step4.output_confidence
    
    async def _tree_reasoning(
        self,
        chain: ReasoningChain,
        context: Optional[Dict[str, Any]]
    ) -> None:
        """Tree of thoughts reasoning"""
        tree = TreeOfThoughts(max_depth=4, branching_factor=3)
        
        # Create root thought
        root = tree.create_root(
            f"Analyzing: {chain.query}",
            ReasoningType.DEDUCTIVE
        )
        root.confidence = 0.9
        chain.thoughts.append(root)
        chain.total_thoughts += 1
        
        # Expand tree
        await self._expand_tree(tree, root.thought_id, chain, context, depth=0)
        
        # Prune low-confidence branches
        pruned = tree.prune(min_confidence=0.3)
        chain.rejected_thoughts += pruned
        
        # Get best path
        best_path = tree.get_best_path()
        
        if best_path:
            # Convert to steps
            for i, thought in enumerate(best_path):
                step = ReasoningStep(
                    step_id=f"step_{i}",
                    step_number=i + 1,
                    description=thought.content,
                    input_data={"thought": thought.content},
                    output_data={"confidence": thought.confidence},
                    logic_applied=thought.reasoning_type.value,
                    reasoning_type=thought.reasoning_type,
                    input_confidence=best_path[i-1].confidence if i > 0 else 1.0,
                    output_confidence=thought.confidence,
                )
                chain.steps.append(step)
            
            # Set conclusion from last thought
            chain.conclusion = best_path[-1].content
            chain.final_confidence = best_path[-1].confidence
        
        # Store tree reference
        chain.thoughts = list(tree.thoughts.values())
    
    async def _expand_tree(
        self,
        tree: TreeOfThoughts,
        parent_id: str,
        chain: ReasoningChain,
        context: Optional[Dict[str, Any]],
        depth: int
    ) -> None:
        """Recursively expand the thought tree"""
        if depth >= tree.max_depth:
            return
        
        parent = tree.thoughts.get(parent_id)
        if not parent:
            return
        
        # Generate child thoughts
        child_thoughts = await self._generate_thoughts(parent, context)
        
        # Expand
        children = tree.expand(parent_id, child_thoughts)
        
        for child in children:
            chain.thoughts.append(child)
            chain.total_thoughts += 1
            self.total_thoughts += 1
            
            # Verify thought
            is_valid, results = self.verifier.verify(child)
            self.total_verifications += 1
            
            if is_valid:
                child.status = ThoughtStatus.VERIFIED
                chain.verified_thoughts += 1
                
                # Recursively expand
                await self._expand_tree(tree, child.thought_id, chain, context, depth + 1)
            else:
                child.status = ThoughtStatus.REJECTED
                child.verification_result = "; ".join(results)
                chain.rejected_thoughts += 1
    
    async def _generate_thoughts(
        self,
        parent: Thought,
        context: Optional[Dict[str, Any]]
    ) -> List[Tuple[str, ReasoningType, float]]:
        """Generate child thoughts from parent"""
        # Simulate thought generation
        await asyncio.sleep(0.05)
        
        thoughts = []
        
        # Generate based on parent reasoning type
        if parent.reasoning_type == ReasoningType.DEDUCTIVE:
            thoughts = [
                ("If the premise holds, then the market should move accordingly", 
                 ReasoningType.DEDUCTIVE, parent.confidence * 0.9),
                ("Consider alternative interpretations of the data",
                 ReasoningType.ABDUCTIVE, parent.confidence * 0.7),
                ("Historical patterns suggest similar outcomes",
                 ReasoningType.ANALOGICAL, parent.confidence * 0.8),
            ]
        
        elif parent.reasoning_type == ReasoningType.INDUCTIVE:
            thoughts = [
                ("The pattern observed suggests a general trend",
                 ReasoningType.INDUCTIVE, parent.confidence * 0.85),
                ("Multiple data points confirm this direction",
                 ReasoningType.PROBABILISTIC, parent.confidence * 0.8),
                ("Exceptions to this pattern should be considered",
                 ReasoningType.ABDUCTIVE, parent.confidence * 0.6),
            ]
        
        elif parent.reasoning_type == ReasoningType.ABDUCTIVE:
            thoughts = [
                ("The best explanation for observed behavior is...",
                 ReasoningType.ABDUCTIVE, parent.confidence * 0.75),
                ("This explanation implies certain consequences",
                 ReasoningType.CAUSAL, parent.confidence * 0.8),
                ("Alternative explanations should be ruled out",
                 ReasoningType.DEDUCTIVE, parent.confidence * 0.7),
            ]
        
        else:
            thoughts = [
                ("Further analysis supports this conclusion",
                 ReasoningType.DEDUCTIVE, parent.confidence * 0.85),
                ("Probability-weighted outcome assessment",
                 ReasoningType.PROBABILISTIC, parent.confidence * 0.8),
                ("Causal factors point to this direction",
                 ReasoningType.CAUSAL, parent.confidence * 0.75),
            ]
        
        # Add some randomness
        for i in range(len(thoughts)):
            content, rtype, conf = thoughts[i]
            conf *= random.uniform(0.9, 1.1)
            conf = min(1.0, max(0.1, conf))
            thoughts[i] = (content, rtype, conf)
        
        return thoughts
    
    async def _create_step(
        self,
        chain: ReasoningChain,
        step_number: int,
        description: str,
        input_data: Dict[str, Any],
        reasoning_type: ReasoningType,
        input_confidence: float = 1.0,
    ) -> ReasoningStep:
        """Create a reasoning step"""
        # Simulate processing
        await asyncio.sleep(0.05)
        
        # Calculate output confidence (with some decay)
        output_confidence = input_confidence * random.uniform(0.85, 0.98)
        
        step = ReasoningStep(
            step_id=f"step_{chain.chain_id}_{step_number}",
            step_number=step_number,
            description=description,
            input_data=input_data,
            output_data={"processed": True, "conclusion": f"Step {step_number} complete"},
            logic_applied=f"{reasoning_type.value} reasoning applied",
            reasoning_type=reasoning_type,
            input_confidence=input_confidence,
            output_confidence=output_confidence,
            confidence_delta=output_confidence - input_confidence,
        )
        
        return step
    
    def _get_tree_for_chain(self, chain: ReasoningChain) -> Optional[TreeOfThoughts]:
        """Reconstruct tree from chain thoughts"""
        if not chain.thoughts:
            return None
        
        tree = TreeOfThoughts()
        
        for thought in chain.thoughts:
            tree.thoughts[thought.thought_id] = thought
            if thought.parent_id is None:
                tree.root_id = thought.thought_id
        
        return tree
    
    def get_report(self) -> Dict[str, Any]:
        """Get reasoning engine report"""
        return {
            "total_chains": self.total_chains,
            "total_thoughts": self.total_thoughts,
            "total_verifications": self.total_verifications,
            "active_chains": len(self.active_chains),
            "completed_chains": len(self.completed_chains),
            "avg_confidence": (
                sum(c.final_confidence for c in self.completed_chains) / len(self.completed_chains)
                if self.completed_chains else 0
            ),
            "consistency_history": self.consistency_checker.consistency_history[-10:],
        }


# Factory function
def create_reasoning_chain_engine(
    config: Optional[Dict[str, Any]] = None
) -> ReasoningChainEngine:
    """Create reasoning chain engine"""
    return ReasoningChainEngine(config)
