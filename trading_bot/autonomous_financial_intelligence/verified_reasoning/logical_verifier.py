"""
Logical Verifier

Formal logic verification of reasoning chains.
Ensures logical consistency and validity of arguments.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class LogicalOperator(Enum):
    """Logical operators."""
    AND = "and"
    OR = "or"
    NOT = "not"
    IMPLIES = "implies"
    IFF = "iff"
    XOR = "xor"


class ArgumentForm(Enum):
    """Common argument forms."""
    MODUS_PONENS = "modus_ponens"
    MODUS_TOLLENS = "modus_tollens"
    HYPOTHETICAL_SYLLOGISM = "hypothetical_syllogism"
    DISJUNCTIVE_SYLLOGISM = "disjunctive_syllogism"
    CONSTRUCTIVE_DILEMMA = "constructive_dilemma"
    REDUCTIO_AD_ABSURDUM = "reductio_ad_absurdum"
    INDUCTIVE_GENERALIZATION = "inductive_generalization"
    ANALOGICAL_REASONING = "analogical_reasoning"


class FallacyType(Enum):
    """Types of logical fallacies."""
    AFFIRMING_CONSEQUENT = "affirming_consequent"
    DENYING_ANTECEDENT = "denying_antecedent"
    FALSE_DILEMMA = "false_dilemma"
    CIRCULAR_REASONING = "circular_reasoning"
    HASTY_GENERALIZATION = "hasty_generalization"
    POST_HOC = "post_hoc"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    STRAW_MAN = "straw_man"
    AD_HOMINEM = "ad_hominem"
    SLIPPERY_SLOPE = "slippery_slope"
    NON_SEQUITUR = "non_sequitur"


class VerificationStatus(Enum):
    """Status of logical verification."""
    VALID = "valid"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"
    FALLACIOUS = "fallacious"
    INCOMPLETE = "incomplete"


@dataclass
class LogicalProposition:
    """A logical proposition."""
    proposition_id: str
    content: str
    is_premise: bool
    is_conclusion: bool
    truth_value: Optional[bool] = None
    confidence: float = 1.0
    dependencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'proposition_id': self.proposition_id,
            'content': self.content,
            'is_premise': self.is_premise,
            'is_conclusion': self.is_conclusion,
            'truth_value': self.truth_value,
            'confidence': self.confidence,
            'dependencies': self.dependencies,
        }


@dataclass
class LogicalStructure:
    """Structure of a logical argument."""
    structure_id: str
    premises: List[LogicalProposition]
    conclusion: LogicalProposition
    argument_form: ArgumentForm
    operators_used: List[LogicalOperator]
    is_valid: bool = False
    fallacies_detected: List[FallacyType] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'structure_id': self.structure_id,
            'premises': [p.to_dict() for p in self.premises],
            'conclusion': self.conclusion.to_dict(),
            'argument_form': self.argument_form.value,
            'operators_used': [o.value for o in self.operators_used],
            'is_valid': self.is_valid,
            'fallacies_detected': [f.value for f in self.fallacies_detected],
        }


@dataclass
class VerificationResult:
    """Result of logical verification."""
    result_id: str
    structure: LogicalStructure
    status: VerificationStatus
    validity_score: float
    soundness_score: float
    fallacies: List[Dict[str, Any]]
    consistency_issues: List[str]
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'result_id': self.result_id,
            'structure': self.structure.to_dict(),
            'status': self.status.value,
            'validity_score': self.validity_score,
            'soundness_score': self.soundness_score,
            'fallacies': self.fallacies,
            'consistency_issues': self.consistency_issues,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
        }


class LogicalVerifier:
    """
    Formal logic verification system.
    
    Provides:
    - Argument structure analysis
    - Validity checking
    - Fallacy detection
    - Consistency verification
    - Soundness assessment
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'logical_verifier_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._structures: Dict[str, LogicalStructure] = {}
        self._results: Dict[str, VerificationResult] = {}
        
        self._validity_rules = self._initialize_validity_rules()
        self._fallacy_patterns = self._initialize_fallacy_patterns()
        
        logger.info("✅ Logical Verifier initialized")
    
    def _initialize_validity_rules(self) -> Dict[ArgumentForm, callable]:
        """Initialize validity checking rules for argument forms."""
        return {
            ArgumentForm.MODUS_PONENS: self._check_modus_ponens,
            ArgumentForm.MODUS_TOLLENS: self._check_modus_tollens,
            ArgumentForm.HYPOTHETICAL_SYLLOGISM: self._check_hypothetical_syllogism,
            ArgumentForm.DISJUNCTIVE_SYLLOGISM: self._check_disjunctive_syllogism,
        }
    
    def _initialize_fallacy_patterns(self) -> Dict[FallacyType, Dict[str, Any]]:
        """Initialize patterns for detecting fallacies."""
        return {
            FallacyType.AFFIRMING_CONSEQUENT: {
                'pattern': 'If P then Q. Q. Therefore P.',
                'description': 'Incorrectly inferring the antecedent from the consequent',
            },
            FallacyType.DENYING_ANTECEDENT: {
                'pattern': 'If P then Q. Not P. Therefore not Q.',
                'description': 'Incorrectly inferring negation of consequent from negation of antecedent',
            },
            FallacyType.CIRCULAR_REASONING: {
                'pattern': 'Conclusion appears in premises',
                'description': 'Using the conclusion as a premise',
            },
            FallacyType.HASTY_GENERALIZATION: {
                'pattern': 'Small sample to universal claim',
                'description': 'Drawing broad conclusions from insufficient evidence',
            },
            FallacyType.POST_HOC: {
                'pattern': 'A before B, therefore A caused B',
                'description': 'Assuming causation from temporal sequence',
            },
            FallacyType.NON_SEQUITUR: {
                'pattern': 'Conclusion does not follow from premises',
                'description': 'Conclusion is not logically connected to premises',
            },
        }
    
    async def analyze_argument(
        self,
        premises: List[str],
        conclusion: str,
        argument_form: Optional[ArgumentForm] = None,
    ) -> LogicalStructure:
        """
        Analyze the logical structure of an argument.
        
        Args:
            premises: List of premise statements
            conclusion: The conclusion statement
            argument_form: Optional specified argument form
        
        Returns:
            LogicalStructure
        """
        structure_id = f"LS-{uuid.uuid4().hex[:12]}"
        
        premise_props = []
        for i, premise in enumerate(premises):
            prop = LogicalProposition(
                proposition_id=f"P{i+1}",
                content=premise,
                is_premise=True,
                is_conclusion=False,
            )
            premise_props.append(prop)
        
        conclusion_prop = LogicalProposition(
            proposition_id="C",
            content=conclusion,
            is_premise=False,
            is_conclusion=True,
            dependencies=[p.proposition_id for p in premise_props],
        )
        
        if not argument_form:
            argument_form = self._detect_argument_form(premise_props, conclusion_prop)
        
        operators = self._detect_operators(premises + [conclusion])
        
        structure = LogicalStructure(
            structure_id=structure_id,
            premises=premise_props,
            conclusion=conclusion_prop,
            argument_form=argument_form,
            operators_used=operators,
        )
        
        self._structures[structure_id] = structure
        
        return structure
    
    def _detect_argument_form(
        self,
        premises: List[LogicalProposition],
        conclusion: LogicalProposition,
    ) -> ArgumentForm:
        """Detect the argument form from premises and conclusion."""
        premise_contents = [p.content.lower() for p in premises]
        conclusion_content = conclusion.content.lower()
        
        if len(premises) >= 2:
            if any('if' in p and 'then' in p for p in premise_contents):
                if any('not' in p for p in premise_contents):
                    return ArgumentForm.MODUS_TOLLENS
                return ArgumentForm.MODUS_PONENS
            
            if any('or' in p for p in premise_contents):
                return ArgumentForm.DISJUNCTIVE_SYLLOGISM
        
        if any('similar' in p or 'like' in p for p in premise_contents):
            return ArgumentForm.ANALOGICAL_REASONING
        
        if any('all' in p or 'every' in p or 'most' in p for p in premise_contents):
            return ArgumentForm.INDUCTIVE_GENERALIZATION
        
        return ArgumentForm.MODUS_PONENS
    
    def _detect_operators(self, statements: List[str]) -> List[LogicalOperator]:
        """Detect logical operators used in statements."""
        operators = []
        
        combined = ' '.join(statements).lower()
        
        if ' and ' in combined or ',' in combined:
            operators.append(LogicalOperator.AND)
        if ' or ' in combined:
            operators.append(LogicalOperator.OR)
        if 'not ' in combined or "n't" in combined:
            operators.append(LogicalOperator.NOT)
        if 'if ' in combined and 'then' in combined:
            operators.append(LogicalOperator.IMPLIES)
        if 'if and only if' in combined or 'iff' in combined:
            operators.append(LogicalOperator.IFF)
        
        return operators
    
    async def verify_logic(
        self,
        structure: LogicalStructure,
    ) -> VerificationResult:
        """
        Verify the logical validity of an argument structure.
        
        Args:
            structure: LogicalStructure to verify
        
        Returns:
            VerificationResult
        """
        result_id = f"VR-{uuid.uuid4().hex[:12]}"
        
        validity_score = await self._check_validity(structure)
        
        fallacies = await self._detect_fallacies(structure)
        structure.fallacies_detected = [f['type'] for f in fallacies]
        
        consistency_issues = await self._check_consistency(structure)
        
        soundness_score = await self._assess_soundness(structure)
        
        if validity_score >= 0.8 and not fallacies and not consistency_issues:
            status = VerificationStatus.VALID
            structure.is_valid = True
        elif fallacies:
            status = VerificationStatus.FALLACIOUS
        elif consistency_issues:
            status = VerificationStatus.INVALID
        elif validity_score < 0.5:
            status = VerificationStatus.INVALID
        else:
            status = VerificationStatus.UNCERTAIN
        
        recommendations = self._generate_recommendations(
            validity_score, fallacies, consistency_issues
        )
        
        result = VerificationResult(
            result_id=result_id,
            structure=structure,
            status=status,
            validity_score=validity_score,
            soundness_score=soundness_score,
            fallacies=fallacies,
            consistency_issues=consistency_issues,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._results[result_id] = result
        await self._persist_result(result)
        
        logger.info(f"Logical verification complete: {status.value} "
                   f"(validity: {validity_score:.2f})")
        
        return result
    
    async def _check_validity(self, structure: LogicalStructure) -> float:
        """Check the validity of an argument."""
        validity_score = 0.5
        
        if structure.argument_form in self._validity_rules:
            rule_check = self._validity_rules[structure.argument_form]
            form_valid = rule_check(structure)
            if form_valid:
                validity_score += 0.3
        
        if len(structure.premises) >= 2:
            validity_score += 0.1
        
        conclusion_terms = set(structure.conclusion.content.lower().split())
        premise_terms = set()
        for p in structure.premises:
            premise_terms.update(p.content.lower().split())
        
        term_overlap = len(conclusion_terms & premise_terms) / len(conclusion_terms) if conclusion_terms else 0
        validity_score += term_overlap * 0.1
        
        return min(1.0, validity_score)
    
    def _check_modus_ponens(self, structure: LogicalStructure) -> bool:
        """Check if argument follows modus ponens form."""
        if len(structure.premises) < 2:
            return False
        
        has_conditional = any(
            'if' in p.content.lower() and 'then' in p.content.lower()
            for p in structure.premises
        )
        
        return has_conditional
    
    def _check_modus_tollens(self, structure: LogicalStructure) -> bool:
        """Check if argument follows modus tollens form."""
        if len(structure.premises) < 2:
            return False
        
        has_conditional = any(
            'if' in p.content.lower() and 'then' in p.content.lower()
            for p in structure.premises
        )
        
        has_negation = any(
            'not' in p.content.lower() or "n't" in p.content.lower()
            for p in structure.premises
        )
        
        return has_conditional and has_negation
    
    def _check_hypothetical_syllogism(self, structure: LogicalStructure) -> bool:
        """Check if argument follows hypothetical syllogism form."""
        conditionals = [
            p for p in structure.premises
            if 'if' in p.content.lower() and 'then' in p.content.lower()
        ]
        return len(conditionals) >= 2
    
    def _check_disjunctive_syllogism(self, structure: LogicalStructure) -> bool:
        """Check if argument follows disjunctive syllogism form."""
        has_disjunction = any(
            ' or ' in p.content.lower()
            for p in structure.premises
        )
        
        has_negation = any(
            'not' in p.content.lower() or "n't" in p.content.lower()
            for p in structure.premises
        )
        
        return has_disjunction and has_negation
    
    async def _detect_fallacies(
        self,
        structure: LogicalStructure,
    ) -> List[Dict[str, Any]]:
        """Detect logical fallacies in the argument."""
        fallacies = []
        
        conclusion_content = structure.conclusion.content.lower()
        for premise in structure.premises:
            if premise.content.lower() == conclusion_content:
                fallacies.append({
                    'type': FallacyType.CIRCULAR_REASONING,
                    'description': 'Conclusion appears verbatim in premises',
                    'severity': 'high',
                })
                break
        
        premise_terms = set()
        for p in structure.premises:
            premise_terms.update(p.content.lower().split())
        
        conclusion_terms = set(conclusion_content.split())
        new_terms = conclusion_terms - premise_terms - {'the', 'a', 'an', 'is', 'are', 'was', 'were'}
        
        if len(new_terms) > len(conclusion_terms) * 0.5:
            fallacies.append({
                'type': FallacyType.NON_SEQUITUR,
                'description': 'Conclusion introduces many terms not in premises',
                'severity': 'medium',
                'new_terms': list(new_terms),
            })
        
        for premise in structure.premises:
            content = premise.content.lower()
            if 'all' in content or 'every' in content or 'always' in content:
                if 'one' in content or 'single' in content or 'example' in content:
                    fallacies.append({
                        'type': FallacyType.HASTY_GENERALIZATION,
                        'description': 'Universal claim from limited evidence',
                        'severity': 'medium',
                        'premise': premise.content,
                    })
        
        for premise in structure.premises:
            content = premise.content.lower()
            if ('after' in content or 'then' in content) and ('caused' in content or 'because' in content):
                fallacies.append({
                    'type': FallacyType.POST_HOC,
                    'description': 'Assuming causation from temporal sequence',
                    'severity': 'medium',
                    'premise': premise.content,
                })
        
        return fallacies
    
    async def _check_consistency(
        self,
        structure: LogicalStructure,
    ) -> List[str]:
        """Check for consistency issues in the argument."""
        issues = []
        
        for i, p1 in enumerate(structure.premises):
            for p2 in structure.premises[i+1:]:
                if self._are_contradictory(p1.content, p2.content):
                    issues.append(f"Premises '{p1.content}' and '{p2.content}' may be contradictory")
        
        for premise in structure.premises:
            if self._are_contradictory(premise.content, structure.conclusion.content):
                issues.append(f"Premise '{premise.content}' contradicts conclusion")
        
        return issues
    
    def _are_contradictory(self, stmt1: str, stmt2: str) -> bool:
        """Check if two statements are contradictory."""
        s1 = stmt1.lower()
        s2 = stmt2.lower()
        
        if ('not ' in s1 or "n't" in s1) and ('not ' not in s2 and "n't" not in s2):
            s1_clean = s1.replace('not ', '').replace("n't", '')
            if s1_clean.strip() == s2.strip():
                return True
        
        if ('not ' in s2 or "n't" in s2) and ('not ' not in s1 and "n't" not in s1):
            s2_clean = s2.replace('not ', '').replace("n't", '')
            if s2_clean.strip() == s1.strip():
                return True
        
        return False
    
    async def _assess_soundness(self, structure: LogicalStructure) -> float:
        """Assess the soundness of an argument (validity + true premises)."""
        premise_confidences = [p.confidence for p in structure.premises]
        avg_premise_confidence = sum(premise_confidences) / len(premise_confidences) if premise_confidences else 0
        
        validity_factor = 1.0 if structure.is_valid else 0.5
        
        soundness = avg_premise_confidence * validity_factor
        
        return soundness
    
    def _generate_recommendations(
        self,
        validity_score: float,
        fallacies: List[Dict[str, Any]],
        consistency_issues: List[str],
    ) -> List[str]:
        """Generate recommendations for improving the argument."""
        recommendations = []
        
        if validity_score < 0.7:
            recommendations.append("Strengthen the logical connection between premises and conclusion")
        
        for fallacy in fallacies:
            if fallacy['type'] == FallacyType.CIRCULAR_REASONING:
                recommendations.append("Remove circular reasoning - conclusion should not appear in premises")
            elif fallacy['type'] == FallacyType.HASTY_GENERALIZATION:
                recommendations.append("Provide more evidence before making universal claims")
            elif fallacy['type'] == FallacyType.NON_SEQUITUR:
                recommendations.append("Ensure conclusion follows logically from premises")
            elif fallacy['type'] == FallacyType.POST_HOC:
                recommendations.append("Establish causal mechanism, not just temporal sequence")
        
        if consistency_issues:
            recommendations.append("Resolve contradictions between premises")
        
        return recommendations
    
    async def verify_reasoning_chain(
        self,
        steps: List[Dict[str, Any]],
    ) -> List[VerificationResult]:
        """
        Verify logic of each step in a reasoning chain.
        
        Args:
            steps: List of reasoning steps with premises and conclusions
        
        Returns:
            List of VerificationResults
        """
        results = []
        
        for step in steps:
            premises = step.get('premises', [step.get('premise', '')])
            if isinstance(premises, str):
                premises = [premises]
            
            conclusion = step.get('conclusion', '')
            
            structure = await self.analyze_argument(premises, conclusion)
            result = await self.verify_logic(structure)
            results.append(result)
        
        return results
    
    def get_structure(self, structure_id: str) -> Optional[LogicalStructure]:
        """Get a logical structure by ID."""
        return self._structures.get(structure_id)
    
    def get_result(self, result_id: str) -> Optional[VerificationResult]:
        """Get a verification result by ID."""
        return self._results.get(result_id)
    
    async def _persist_result(self, result: VerificationResult):
        """Persist verification result to storage."""
        result_file = self.storage_path / 'results' / f"{result.result_id}.json"
        result_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get verifier statistics."""
        valid_results = [r for r in self._results.values() if r.status == VerificationStatus.VALID]
        
        fallacy_counts = {}
        for result in self._results.values():
            for fallacy in result.fallacies:
                ft = fallacy['type'].value if isinstance(fallacy['type'], FallacyType) else fallacy['type']
                fallacy_counts[ft] = fallacy_counts.get(ft, 0) + 1
        
        return {
            'total_structures': len(self._structures),
            'total_verifications': len(self._results),
            'valid_arguments': len(valid_results),
            'validity_rate': len(valid_results) / len(self._results) if self._results else 0,
            'fallacies_detected': fallacy_counts,
        }
