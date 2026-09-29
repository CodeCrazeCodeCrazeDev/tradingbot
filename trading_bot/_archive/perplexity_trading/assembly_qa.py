"""
Assembly and QA Layer for Perplexity Trading Architecture
============================================================

Assembles subtask results into final output and performs
quality assurance verification.

Like Perplexity Computer's QA check:
- Cross-references data against original sources
- Checks for consistency and conflicts
- Generates confidence scores
- Tracks citations
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import hashlib

from .core_types import (
    SubTaskResult,
    TradingDecision,
    Citation,
    QACheckResult,
    ApprovalStatus,
    RetrievalSource,
)

logger = logging.getLogger(__name__)


class CitationTracker:
    """
    Tracks and manages citations for data provenance.
    
    Ensures all data points in the final decision can be
    traced back to their original sources.
    """
    
    def __init__(self):
        self.citations: List[Citation] = []
        self.citation_index: Dict[str, Citation] = {}  # hash -> citation
    
    def add_citation(self, citation: Citation) -> str:
        """Add a citation and return its hash"""
        citation_hash = self._hash_citation(citation)
        
        if citation_hash not in self.citation_index:
            self.citations.append(citation)
            self.citation_index[citation_hash] = citation
        
        return citation_hash
    
    def add_from_result(self, result: SubTaskResult) -> List[str]:
        """Add all citations from a subtask result"""
        hashes = []
        for citation in result.citations:
            hashes.append(self.add_citation(citation))
        return hashes
    
    def _hash_citation(self, citation: Citation) -> str:
        """Generate hash for citation deduplication"""
        content = f"{citation.source_type.value}:{citation.source_name}:{citation.data_point}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def get_citations_by_source(self, source: RetrievalSource) -> List[Citation]:
        """Get all citations from a specific source"""
        return [c for c in self.citations if c.source_type == source]
    
    def get_all(self) -> List[Citation]:
        """Get all citations"""
        return self.citations.copy()
    
    def get_summary(self) -> Dict[str, int]:
        """Get citation summary by source type"""
        summary = {}
        for citation in self.citations:
            source = citation.source_type.value
            summary[source] = summary.get(source, 0) + 1
        return summary


class ConfidenceScorer:
    """
    Calculates overall confidence scores for trading decisions.
    
    Factors:
    - Individual subtask confidence
    - Data freshness
    - Source agreement
    - QA check results
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Weights for different factors
        self.weights = {
            'subtask_confidence': 0.4,
            'data_freshness': 0.2,
            'source_agreement': 0.25,
            'qa_checks': 0.15,
        }
    
    def calculate(
        self,
        subtask_results: Dict[str, SubTaskResult],
        qa_results: List[QACheckResult],
        data_freshness_seconds: float,
    ) -> float:
        """Calculate overall confidence score"""
        scores = {}
        
        # Subtask confidence (weighted average)
        subtask_confidences = [r.confidence for r in subtask_results.values() if r.success]
        if subtask_confidences:
            scores['subtask_confidence'] = sum(subtask_confidences) / len(subtask_confidences)
        else:
            scores['subtask_confidence'] = 0.0
        
        # Data freshness (decay over time)
        max_freshness = 300.0  # 5 minutes
        freshness_score = max(0, 1 - (data_freshness_seconds / max_freshness))
        scores['data_freshness'] = freshness_score
        
        # Source agreement (check if signals align)
        scores['source_agreement'] = self._calculate_agreement(subtask_results)
        
        # QA check results
        if qa_results:
            passed_checks = sum(1 for q in qa_results if q.passed)
            scores['qa_checks'] = passed_checks / len(qa_results)
        else:
            scores['qa_checks'] = 0.5  # Neutral if no checks
        
        # Weighted sum
        total = sum(
            scores[factor] * weight
            for factor, weight in self.weights.items()
        )
        
        return min(max(total, 0.0), 1.0)
    
    def _calculate_agreement(self, results: Dict[str, SubTaskResult]) -> float:
        """Calculate agreement between different analysis sources"""
        signals = []
        
        for result in results.values():
            if not result.success:
                continue
            
            # Extract signal direction from output
            output = result.output_data
            
            if 'trading_signal' in output:
                signal = output['trading_signal']
                if signal in ['BUY', 'LONG']:
                    signals.append(1)
                elif signal in ['SELL', 'SHORT']:
                    signals.append(-1)
                else:
                    signals.append(0)
            
            if 'overall_signal' in output:
                signal = output['overall_signal']
                if signal == 'bullish':
                    signals.append(1)
                elif signal == 'bearish':
                    signals.append(-1)
                else:
                    signals.append(0)
        
        if not signals:
            return 0.5
        
        # Agreement = how much signals point in same direction
        avg_signal = sum(signals) / len(signals)
        agreement = abs(avg_signal)  # 0 = mixed, 1 = full agreement
        
        return agreement


class QAVerifier:
    """
    Performs quality assurance checks on trading decisions.
    
    Checks:
    - Cross-reference: Data matches original sources
    - Consistency: No conflicting signals
    - Completeness: All required data present
    - Reasonableness: Values within expected ranges
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def verify(
        self,
        subtask_results: Dict[str, SubTaskResult],
        citations: List[Citation],
    ) -> List[QACheckResult]:
        """Run all QA checks"""
        results = []
        
        # Cross-reference check
        results.append(self._check_cross_reference(subtask_results, citations))
        
        # Consistency check
        results.append(self._check_consistency(subtask_results))
        
        # Completeness check
        results.append(self._check_completeness(subtask_results))
        
        # Reasonableness check
        results.append(self._check_reasonableness(subtask_results))
        
        return results
    
    def _check_cross_reference(
        self,
        results: Dict[str, SubTaskResult],
        citations: List[Citation],
    ) -> QACheckResult:
        """Check that data can be traced to sources"""
        issues = []
        
        # Check that we have citations
        if not citations:
            issues.append("No citations provided for data")
        
        # Check citation confidence
        low_confidence = [c for c in citations if c.confidence < 0.5]
        if low_confidence:
            issues.append(f"{len(low_confidence)} citations have low confidence")
        
        passed = len(issues) == 0
        
        return QACheckResult(
            passed=passed,
            method="cross_reference",
            issues=issues,
            confidence_adjustment=-0.1 if not passed else 0.0,
        )
    
    def _check_consistency(self, results: Dict[str, SubTaskResult]) -> QACheckResult:
        """Check for conflicting signals"""
        issues = []
        
        # Collect all signals
        bullish_signals = 0
        bearish_signals = 0
        
        for result in results.values():
            if not result.success:
                continue
            
            output = result.output_data
            
            # Check various signal fields
            for key in ['trading_signal', 'overall_signal', 'signal']:
                if key in output:
                    signal = str(output[key]).lower()
                    if signal in ['buy', 'long', 'bullish']:
                        bullish_signals += 1
                    elif signal in ['sell', 'short', 'bearish']:
                        bearish_signals += 1
        
        # Check for strong conflict
        if bullish_signals > 0 and bearish_signals > 0:
            conflict_ratio = min(bullish_signals, bearish_signals) / max(bullish_signals, bearish_signals)
            if conflict_ratio > 0.5:
                issues.append(f"Conflicting signals: {bullish_signals} bullish vs {bearish_signals} bearish")
        
        passed = len(issues) == 0
        
        return QACheckResult(
            passed=passed,
            method="consistency_check",
            issues=issues,
            confidence_adjustment=-0.15 if not passed else 0.05,
        )
    
    def _check_completeness(self, results: Dict[str, SubTaskResult]) -> QACheckResult:
        """Check that all required data is present"""
        issues = []
        
        # Check for failed subtasks
        failed = [r for r in results.values() if not r.success]
        if failed:
            issues.append(f"{len(failed)} subtasks failed")
        
        # Check for required outputs
        required_outputs = ['technical_signals', 'risk_reward']
        found_outputs: Set[str] = set()
        
        for result in results.values():
            if result.success:
                found_outputs.update(result.output_data.keys())
        
        missing = set(required_outputs) - found_outputs
        if missing:
            issues.append(f"Missing required outputs: {missing}")
        
        passed = len(issues) == 0
        
        return QACheckResult(
            passed=passed,
            method="completeness_check",
            issues=issues,
            confidence_adjustment=-0.2 if not passed else 0.0,
        )
    
    def _check_reasonableness(self, results: Dict[str, SubTaskResult]) -> QACheckResult:
        """Check that values are within reasonable ranges"""
        issues = []
        corrections = {}
        
        for result in results.values():
            if not result.success:
                continue
            
            output = result.output_data
            
            # Check risk/reward ratio
            if 'risk_reward' in output:
                rr = output['risk_reward']
                if rr < 0.5:
                    issues.append(f"Risk/reward ratio too low: {rr}")
                elif rr > 10:
                    issues.append(f"Risk/reward ratio unusually high: {rr}")
                    corrections['risk_reward'] = min(rr, 5.0)
            
            # Check position size
            if 'position_size' in output:
                size = output['position_size']
                if size < 0:
                    issues.append(f"Negative position size: {size}")
                    corrections['position_size'] = 0
            
            # Check confidence
            if 'confidence' in output:
                conf = output['confidence']
                if conf < 0 or conf > 1:
                    issues.append(f"Invalid confidence value: {conf}")
                    corrections['confidence'] = max(0, min(1, conf))
        
        passed = len(issues) == 0
        
        return QACheckResult(
            passed=passed,
            method="reasonableness_check",
            issues=issues,
            corrections=corrections,
            confidence_adjustment=-0.1 if not passed else 0.0,
        )


class AssemblyEngine:
    """
    Assembles subtask results into final trading decision.
    
    Responsibilities:
    - Merge outputs from all subtasks
    - Generate reasoning chain
    - Calculate final confidence
    - Apply QA adjustments
    - Determine approval requirements
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.citation_tracker = CitationTracker()
        self.confidence_scorer = ConfidenceScorer(config)
        self.qa_verifier = QAVerifier(config)
    
    def assemble(
        self,
        query_id: str,
        subtask_results: Dict[str, SubTaskResult],
        symbol: Optional[str] = None,
    ) -> TradingDecision:
        """
        Assemble subtask results into final trading decision.
        """
        logger.info(f"Assembling {len(subtask_results)} subtask results")
        
        start_time = datetime.utcnow()
        
        # Track all citations
        for result in subtask_results.values():
            self.citation_tracker.add_from_result(result)
        
        # Run QA verification
        qa_results = self.qa_verifier.verify(
            subtask_results,
            self.citation_tracker.get_all(),
        )
        
        # Extract key outputs
        merged_output = self._merge_outputs(subtask_results)
        
        # Generate reasoning chain
        reasoning_chain = self._generate_reasoning_chain(subtask_results)
        
        # Calculate data freshness
        data_freshness = self._calculate_freshness(subtask_results)
        
        # Calculate confidence
        base_confidence = self.confidence_scorer.calculate(
            subtask_results,
            qa_results,
            data_freshness,
        )
        
        # Apply QA adjustments
        confidence_adjustment = sum(q.confidence_adjustment for q in qa_results)
        final_confidence = max(0.0, min(1.0, base_confidence + confidence_adjustment))
        
        # Determine action
        action = merged_output.get('trading_signal', 'HOLD')
        
        # Determine if approval required
        requires_approval = self._requires_approval(action, final_confidence, merged_output)
        
        # Build decision
        decision = TradingDecision(
            query_id=query_id,
            action=action,
            symbol=symbol,
            confidence=final_confidence,
            entry_price=merged_output.get('entry_price'),
            stop_loss=merged_output.get('stop_loss'),
            take_profit=merged_output.get('take_profit'),
            position_size=merged_output.get('position_size'),
            order_type=merged_output.get('order_type', 'LIMIT'),
            reasoning_chain=reasoning_chain,
            citations=self.citation_tracker.get_all(),
            subtask_results=subtask_results,
            qa_results=qa_results,
            data_freshness_seconds=data_freshness,
            requires_approval=requires_approval,
            approval_status=ApprovalStatus.PENDING if requires_approval else ApprovalStatus.AUTO_APPROVED,
            processing_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000,
        )
        
        logger.info(f"Assembled decision: {action} with {final_confidence:.0%} confidence")
        
        return decision
    
    def _merge_outputs(self, results: Dict[str, SubTaskResult]) -> Dict[str, Any]:
        """Merge outputs from all subtasks"""
        merged = {}
        
        # Priority order for conflicting keys
        priority_order = ['synthesis', 'summary', 'reasoning', 'technical', 'risk']
        
        # First pass: collect all outputs
        all_outputs: Dict[str, List[tuple]] = {}
        for task_id, result in results.items():
            if not result.success:
                continue
            
            for key, value in result.output_data.items():
                if key not in all_outputs:
                    all_outputs[key] = []
                all_outputs[key].append((task_id, value))
        
        # Second pass: resolve conflicts
        for key, values in all_outputs.items():
            if len(values) == 1:
                merged[key] = values[0][1]
            else:
                # Use priority order
                for priority in priority_order:
                    for task_id, value in values:
                        if priority in task_id.lower():
                            merged[key] = value
                            break
                    if key in merged:
                        break
                
                # If still not resolved, use first value
                if key not in merged:
                    merged[key] = values[0][1]
        
        return merged
    
    def _generate_reasoning_chain(self, results: Dict[str, SubTaskResult]) -> List[str]:
        """Generate human-readable reasoning chain"""
        chain = []
        
        # Sort by task ID to maintain order
        sorted_results = sorted(results.items(), key=lambda x: x[0])
        
        for task_id, result in sorted_results:
            if result.success and result.reasoning:
                # Clean up and add to chain
                reasoning = result.reasoning.strip()
                if reasoning:
                    chain.append(f"[{task_id}] {reasoning}")
        
        return chain
    
    def _calculate_freshness(self, results: Dict[str, SubTaskResult]) -> float:
        """Calculate overall data freshness (oldest data age in seconds)"""
        max_age = 0.0
        
        for result in results.values():
            if result.success:
                for citation in result.citations:
                    age = (datetime.utcnow() - citation.timestamp).total_seconds()
                    max_age = max(max_age, age)
        
        return max_age
    
    def _requires_approval(
        self,
        action: str,
        confidence: float,
        output: Dict[str, Any],
    ) -> bool:
        """Determine if human approval is required"""
        # Always require approval for execution actions
        if action in ['BUY', 'SELL']:
            return True
        
        # Require approval for low confidence
        if confidence < 0.6:
            return True
        
        # Require approval for large positions
        position_size = output.get('position_size', 0)
        max_auto_size = self.config.get('max_auto_position_size', 0)
        if position_size > max_auto_size:
            return True
        
        return False
    
    def reset(self) -> None:
        """Reset for new assembly"""
        self.citation_tracker = CitationTracker()
