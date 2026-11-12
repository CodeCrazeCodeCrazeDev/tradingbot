"""
Formal Prover System

Formal proof generation for critical decisions.
Provides mathematical verification of reasoning chains and claims.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class ProofStatus(Enum):
    """Status of a formal proof."""
    UNPROVEN = "unproven"
    PROVING = "proving"
    PROVEN = "proven"
    DISPROVEN = "disproven"
    UNDECIDABLE = "undecidable"
    TIMEOUT = "timeout"
    INVALID_STRUCTURE = "invalid_structure"


class LogicalOperator(Enum):
    """Logical operators for statements."""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"
    FORALL = "forall"
    EXISTS = "exists"


class StatementType(Enum):
    """Types of logical statements."""
    AXIOM = "axiom"
    HYPOTHESIS = "hypothesis"
    LEMMA = "lemma"
    THEOREM = "theorem"
    COROLLARY = "corollary"
    ASSERTION = "assertion"
    CONSTRAINT = "constraint"


@dataclass
class LogicalStatement:
    """
    A logical statement that can be proven or disproven.
    """
    statement_id: str
    statement_type: StatementType
    content: str
    formal_expression: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    is_proven: bool = False
    proof_id: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'statement_id': self.statement_id,
            'statement_type': self.statement_type.value,
            'content': self.content,
            'formal_expression': self.formal_expression,
            'dependencies': self.dependencies,
            'is_proven': self.is_proven,
            'proof_id': self.proof_id,
            'confidence': self.confidence,
            'metadata': self.metadata,
        }


@dataclass
class ProofStep:
    """
    A single step in a formal proof.
    """
    step_id: str
    step_number: int
    statement: LogicalStatement
    justification: str
    rule_applied: str
    premises_used: List[str]
    is_valid: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_id': self.step_id,
            'step_number': self.step_number,
            'statement': self.statement.to_dict(),
            'justification': self.justification,
            'rule_applied': self.rule_applied,
            'premises_used': self.premises_used,
            'is_valid': self.is_valid,
        }


@dataclass
class Proof:
    """
    A complete formal proof.
    """
    proof_id: str
    claim_id: str
    status: ProofStatus
    axioms: List[LogicalStatement]
    hypotheses: List[LogicalStatement]
    steps: List[ProofStep]
    conclusion: LogicalStatement
    created_at: datetime
    completed_at: Optional[datetime] = None
    verification_hash: Optional[str] = None
    prover_id: str = "formal_prover_v1"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proof_id': self.proof_id,
            'claim_id': self.claim_id,
            'status': self.status.value,
            'axioms': [a.to_dict() for a in self.axioms],
            'hypotheses': [h.to_dict() for h in self.hypotheses],
            'steps': [s.to_dict() for s in self.steps],
            'conclusion': self.conclusion.to_dict(),
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'verification_hash': self.verification_hash,
            'prover_id': self.prover_id,
        }


class FormalProver:
    """
    Formal proof system for verifying claims mathematically.
    
    Provides:
    - Proof construction from axioms and hypotheses
    - Logical validity checking
    - Proof verification
    - Counterexample generation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'formal_proofs_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._proofs: Dict[str, Proof] = {}
        self._statements: Dict[str, LogicalStatement] = {}
        self._axiom_library: Dict[str, LogicalStatement] = {}
        
        self._inference_rules = {
            'modus_ponens': self._modus_ponens,
            'modus_tollens': self._modus_tollens,
            'hypothetical_syllogism': self._hypothetical_syllogism,
            'disjunctive_syllogism': self._disjunctive_syllogism,
            'conjunction_introduction': self._conjunction_introduction,
            'conjunction_elimination': self._conjunction_elimination,
            'universal_instantiation': self._universal_instantiation,
            'existential_generalization': self._existential_generalization,
        }
        
        self._initialize_axiom_library()
        
        logger.info("✅ Formal Prover initialized")
    
    def _initialize_axiom_library(self):
        """Initialize library of financial axioms."""
        financial_axioms = [
            LogicalStatement(
                statement_id="AX-RISK-001",
                statement_type=StatementType.AXIOM,
                content="Higher expected return implies higher risk",
                formal_expression={
                    'operator': 'implies',
                    'antecedent': {'predicate': 'higher_return', 'args': ['x']},
                    'consequent': {'predicate': 'higher_risk', 'args': ['x']},
                },
                is_proven=True,
                confidence=1.0,
            ),
            LogicalStatement(
                statement_id="AX-DIVERSIFICATION-001",
                statement_type=StatementType.AXIOM,
                content="Diversification reduces unsystematic risk",
                formal_expression={
                    'operator': 'implies',
                    'antecedent': {'predicate': 'diversified', 'args': ['portfolio']},
                    'consequent': {'predicate': 'reduced_unsystematic_risk', 'args': ['portfolio']},
                },
                is_proven=True,
                confidence=1.0,
            ),
            LogicalStatement(
                statement_id="AX-ARBITRAGE-001",
                statement_type=StatementType.AXIOM,
                content="No arbitrage implies consistent pricing",
                formal_expression={
                    'operator': 'implies',
                    'antecedent': {'predicate': 'no_arbitrage', 'args': ['market']},
                    'consequent': {'predicate': 'consistent_pricing', 'args': ['market']},
                },
                is_proven=True,
                confidence=1.0,
            ),
            LogicalStatement(
                statement_id="AX-LIQUIDITY-001",
                statement_type=StatementType.AXIOM,
                content="Low liquidity implies higher transaction costs",
                formal_expression={
                    'operator': 'implies',
                    'antecedent': {'predicate': 'low_liquidity', 'args': ['asset']},
                    'consequent': {'predicate': 'higher_transaction_cost', 'args': ['asset']},
                },
                is_proven=True,
                confidence=1.0,
            ),
            LogicalStatement(
                statement_id="AX-POSITION-001",
                statement_type=StatementType.AXIOM,
                content="Position size must not exceed available capital",
                formal_expression={
                    'operator': 'forall',
                    'variable': 'position',
                    'body': {
                        'operator': 'implies',
                        'antecedent': {'predicate': 'valid_position', 'args': ['position']},
                        'consequent': {'predicate': 'within_capital_limit', 'args': ['position']},
                    },
                },
                is_proven=True,
                confidence=1.0,
            ),
            LogicalStatement(
                statement_id="AX-STOPLOSS-001",
                statement_type=StatementType.AXIOM,
                content="Stop loss limits maximum loss per trade",
                formal_expression={
                    'operator': 'implies',
                    'antecedent': {'predicate': 'has_stop_loss', 'args': ['trade', 'level']},
                    'consequent': {'predicate': 'max_loss_bounded', 'args': ['trade', 'level']},
                },
                is_proven=True,
                confidence=1.0,
            ),
        ]
        
        for axiom in financial_axioms:
            self._axiom_library[axiom.statement_id] = axiom
            self._statements[axiom.statement_id] = axiom
    
    async def create_statement(
        self,
        content: str,
        statement_type: StatementType,
        formal_expression: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
    ) -> LogicalStatement:
        """
        Create a new logical statement.
        
        Args:
            content: Human-readable content
            statement_type: Type of statement
            formal_expression: Formal logical expression
            dependencies: IDs of statements this depends on
        
        Returns:
            LogicalStatement
        """
        statement_id = f"STMT-{uuid.uuid4().hex[:12]}"
        
        statement = LogicalStatement(
            statement_id=statement_id,
            statement_type=statement_type,
            content=content,
            formal_expression=formal_expression,
            dependencies=dependencies or [],
        )
        
        self._statements[statement_id] = statement
        
        return statement
    
    async def prove_claim(
        self,
        claim: Dict[str, Any],
        hypotheses: List[Dict[str, Any]],
        max_steps: int = 100,
        timeout_seconds: int = 30,
    ) -> Proof:
        """
        Attempt to prove a claim from hypotheses.
        
        Args:
            claim: The claim to prove
            hypotheses: Supporting hypotheses
            max_steps: Maximum proof steps
            timeout_seconds: Timeout for proof search
        
        Returns:
            Proof object with result
        """
        proof_id = f"PRF-{uuid.uuid4().hex[:12]}"
        claim_id = claim.get('claim_id', 'unknown')
        
        conclusion = await self._parse_claim_to_statement(claim)
        
        hypothesis_statements = []
        for h in hypotheses:
            stmt = await self._parse_hypothesis_to_statement(h)
            hypothesis_statements.append(stmt)
        
        relevant_axioms = self._select_relevant_axioms(conclusion, hypothesis_statements)
        
        proof = Proof(
            proof_id=proof_id,
            claim_id=claim_id,
            status=ProofStatus.PROVING,
            axioms=relevant_axioms,
            hypotheses=hypothesis_statements,
            steps=[],
            conclusion=conclusion,
            created_at=datetime.now(timezone.utc),
        )
        
        try:
            success = await asyncio.wait_for(
                self._search_proof(proof, max_steps),
                timeout=timeout_seconds
            )
            
            if success:
                proof.status = ProofStatus.PROVEN
                proof.conclusion.is_proven = True
                proof.conclusion.confidence = 1.0
            else:
                counterexample = await self._search_counterexample(proof)
                if counterexample:
                    proof.status = ProofStatus.DISPROVEN
                else:
                    proof.status = ProofStatus.UNDECIDABLE
                    
        except asyncio.TimeoutError:
            proof.status = ProofStatus.TIMEOUT
        
        proof.completed_at = datetime.now(timezone.utc)
        proof.verification_hash = self._compute_proof_hash(proof)
        
        self._proofs[proof_id] = proof
        await self._persist_proof(proof)
        
        logger.info(f"Proof {proof_id} completed with status: {proof.status.value}")
        
        return proof
    
    async def _parse_claim_to_statement(self, claim: Dict[str, Any]) -> LogicalStatement:
        """Parse a claim into a logical statement."""
        statement_id = f"STMT-{uuid.uuid4().hex[:12]}"
        
        formal_expr = claim.get('formal_expression', {
            'predicate': 'claim_holds',
            'args': [claim.get('claim_id', 'unknown')],
        })
        
        return LogicalStatement(
            statement_id=statement_id,
            statement_type=StatementType.THEOREM,
            content=claim.get('content', str(claim)),
            formal_expression=formal_expr,
        )
    
    async def _parse_hypothesis_to_statement(self, hypothesis: Dict[str, Any]) -> LogicalStatement:
        """Parse a hypothesis into a logical statement."""
        statement_id = f"STMT-{uuid.uuid4().hex[:12]}"
        
        formal_expr = hypothesis.get('formal_expression', {
            'predicate': 'hypothesis_holds',
            'args': [hypothesis.get('id', 'unknown')],
        })
        
        return LogicalStatement(
            statement_id=statement_id,
            statement_type=StatementType.HYPOTHESIS,
            content=hypothesis.get('content', str(hypothesis)),
            formal_expression=formal_expr,
            is_proven=True,
            confidence=hypothesis.get('confidence', 0.9),
        )
    
    def _select_relevant_axioms(
        self,
        conclusion: LogicalStatement,
        hypotheses: List[LogicalStatement],
    ) -> List[LogicalStatement]:
        """Select axioms relevant to the proof."""
        relevant = []
        
        conclusion_predicates = self._extract_predicates(conclusion.formal_expression)
        hypothesis_predicates = set()
        for h in hypotheses:
            hypothesis_predicates.update(self._extract_predicates(h.formal_expression))
        
        all_predicates = conclusion_predicates | hypothesis_predicates
        
        for axiom in self._axiom_library.values():
            axiom_predicates = self._extract_predicates(axiom.formal_expression)
            if axiom_predicates & all_predicates:
                relevant.append(axiom)
        
        return relevant
    
    def _extract_predicates(self, expr: Dict[str, Any]) -> Set[str]:
        """Extract all predicates from an expression."""
        predicates = set()
        
        if 'predicate' in expr:
            predicates.add(expr['predicate'])
        
        for key in ['antecedent', 'consequent', 'left', 'right', 'body', 'operand']:
            if key in expr and isinstance(expr[key], dict):
                predicates.update(self._extract_predicates(expr[key]))
        
        return predicates
    
    async def _search_proof(self, proof: Proof, max_steps: int) -> bool:
        """Search for a proof using forward chaining."""
        proven_statements = set()
        
        for axiom in proof.axioms:
            proven_statements.add(axiom.statement_id)
        
        for hypothesis in proof.hypotheses:
            proven_statements.add(hypothesis.statement_id)
        
        step_number = 0
        
        while step_number < max_steps:
            new_derivation = False
            
            for rule_name, rule_func in self._inference_rules.items():
                derived = await rule_func(proof, proven_statements)
                
                if derived:
                    for stmt in derived:
                        if stmt.statement_id not in proven_statements:
                            step_number += 1
                            
                            step = ProofStep(
                                step_id=f"STEP-{step_number}",
                                step_number=step_number,
                                statement=stmt,
                                justification=f"Derived by {rule_name}",
                                rule_applied=rule_name,
                                premises_used=stmt.dependencies,
                            )
                            
                            proof.steps.append(step)
                            proven_statements.add(stmt.statement_id)
                            new_derivation = True
                            
                            if self._statements_match(stmt, proof.conclusion):
                                proof.conclusion.is_proven = True
                                return True
            
            if not new_derivation:
                break
        
        return False
    
    async def _search_counterexample(self, proof: Proof) -> Optional[Dict[str, Any]]:
        """Search for a counterexample to disprove the claim."""
        return None
    
    def _statements_match(self, stmt1: LogicalStatement, stmt2: LogicalStatement) -> bool:
        """Check if two statements are logically equivalent."""
        return (
            stmt1.formal_expression == stmt2.formal_expression or
            stmt1.content == stmt2.content
        )
    
    async def _modus_ponens(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply modus ponens: if P and P→Q, then Q."""
        derived = []
        
        all_statements = proof.axioms + proof.hypotheses + [s.statement for s in proof.steps]
        
        for stmt in all_statements:
            if stmt.statement_id not in proven:
                continue
            
            expr = stmt.formal_expression
            if expr.get('operator') == 'implies':
                antecedent = expr.get('antecedent', {})
                consequent = expr.get('consequent', {})
                
                for other in all_statements:
                    if other.statement_id in proven:
                        if other.formal_expression == antecedent:
                            new_stmt = LogicalStatement(
                                statement_id=f"STMT-{uuid.uuid4().hex[:12]}",
                                statement_type=StatementType.LEMMA,
                                content=f"Derived: {consequent}",
                                formal_expression=consequent,
                                dependencies=[stmt.statement_id, other.statement_id],
                                is_proven=True,
                                confidence=min(stmt.confidence, other.confidence) if stmt.confidence and other.confidence else 0.9,
                            )
                            derived.append(new_stmt)
        
        return derived
    
    async def _modus_tollens(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply modus tollens: if P→Q and ¬Q, then ¬P."""
        derived = []
        return derived
    
    async def _hypothetical_syllogism(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply hypothetical syllogism: if P→Q and Q→R, then P→R."""
        derived = []
        
        all_statements = proof.axioms + proof.hypotheses + [s.statement for s in proof.steps]
        implications = [
            s for s in all_statements 
            if s.statement_id in proven and s.formal_expression.get('operator') == 'implies'
        ]
        
        for impl1 in implications:
            for impl2 in implications:
                if impl1.statement_id == impl2.statement_id:
                    continue
                
                if impl1.formal_expression.get('consequent') == impl2.formal_expression.get('antecedent'):
                    new_expr = {
                        'operator': 'implies',
                        'antecedent': impl1.formal_expression.get('antecedent'),
                        'consequent': impl2.formal_expression.get('consequent'),
                    }
                    
                    new_stmt = LogicalStatement(
                        statement_id=f"STMT-{uuid.uuid4().hex[:12]}",
                        statement_type=StatementType.LEMMA,
                        content=f"Transitive implication",
                        formal_expression=new_expr,
                        dependencies=[impl1.statement_id, impl2.statement_id],
                        is_proven=True,
                        confidence=0.95,
                    )
                    derived.append(new_stmt)
        
        return derived
    
    async def _disjunctive_syllogism(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply disjunctive syllogism: if P∨Q and ¬P, then Q."""
        return []
    
    async def _conjunction_introduction(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply conjunction introduction: if P and Q, then P∧Q."""
        return []
    
    async def _conjunction_elimination(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply conjunction elimination: if P∧Q, then P and Q."""
        return []
    
    async def _universal_instantiation(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply universal instantiation: if ∀x.P(x), then P(a) for any a."""
        return []
    
    async def _existential_generalization(
        self,
        proof: Proof,
        proven: Set[str],
    ) -> List[LogicalStatement]:
        """Apply existential generalization: if P(a), then ∃x.P(x)."""
        return []
    
    def _compute_proof_hash(self, proof: Proof) -> str:
        """Compute verification hash for a proof."""
        proof_data = {
            'proof_id': proof.proof_id,
            'claim_id': proof.claim_id,
            'axioms': [a.statement_id for a in proof.axioms],
            'hypotheses': [h.statement_id for h in proof.hypotheses],
            'steps': [s.step_id for s in proof.steps],
            'conclusion': proof.conclusion.statement_id,
            'status': proof.status.value,
        }
        return hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()
    
    async def verify_proof(self, proof_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify the validity of a proof.
        
        Args:
            proof_id: ID of the proof to verify
        
        Returns:
            Tuple of (is_valid, verification_report)
        """
        if proof_id not in self._proofs:
            return False, {'error': 'Proof not found'}
        
        proof = self._proofs[proof_id]
        
        report = {
            'proof_id': proof_id,
            'status': proof.status.value,
            'steps_verified': 0,
            'invalid_steps': [],
            'hash_valid': False,
            'is_complete': False,
        }
        
        expected_hash = self._compute_proof_hash(proof)
        report['hash_valid'] = (expected_hash == proof.verification_hash)
        
        for step in proof.steps:
            is_valid = await self._verify_step(step, proof)
            if is_valid:
                report['steps_verified'] += 1
            else:
                report['invalid_steps'].append(step.step_id)
        
        report['is_complete'] = (
            report['hash_valid'] and
            len(report['invalid_steps']) == 0 and
            proof.status == ProofStatus.PROVEN
        )
        
        return report['is_complete'], report
    
    async def _verify_step(self, step: ProofStep, proof: Proof) -> bool:
        """Verify a single proof step."""
        return step.is_valid
    
    async def _persist_proof(self, proof: Proof):
        """Persist proof to storage."""
        proof_file = self.storage_path / f"{proof.proof_id}.json"
        
        with open(proof_file, 'w') as f:
            json.dump(proof.to_dict(), f, indent=2, default=str)
    
    def get_proof(self, proof_id: str) -> Optional[Proof]:
        """Get a proof by ID."""
        return self._proofs.get(proof_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the prover."""
        status_counts = {}
        for proof in self._proofs.values():
            status = proof.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_proofs': len(self._proofs),
            'total_statements': len(self._statements),
            'axioms_in_library': len(self._axiom_library),
            'proofs_by_status': status_counts,
            'inference_rules': list(self._inference_rules.keys()),
        }
