"""
Behavior Synthesis Engine
=========================

Combines multiple extracted behaviors into composite capabilities.
Supports ensembles, chaining, and hybrid approaches.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable, Tuple
from enum import Enum
import numpy as np
from collections import defaultdict

from .capability_registry import CapabilityRegistry, CapabilityRecord

logger = logging.getLogger(__name__)


class SynthesisMode(Enum):
    """Modes of behavior synthesis"""
    ENSEMBLE = "ensemble"  # Multiple behaviors vote/aggregate
    CHAIN = "chain"  # Output of one feeds into next
    HYBRID = "hybrid"  # Combination of ensemble and chain
    SELECTIVE = "selective"  # Pick best behavior based on input


@dataclass
class BehaviorComponent:
    """A component behavior in a synthesis"""
    capability_id: str
    name: str
    weight: float = 1.0
    position: int = 0  # For chaining: execution order
    condition: Optional[str] = None  # Condition for selective activation
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SynthesizedCapability:
    """A capability created by synthesizing multiple behaviors"""
    synthesis_id: str
    name: str
    task_category: str
    mode: SynthesisMode
    components: List[BehaviorComponent]
    aggregation_fn: str  # 'weighted_avg', 'majority_vote', 'best_of_n', 'cascade'
    performance_score: float = 0.0
    latency_ms: float = 0.0
    reliability_score: float = 0.0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    usage_count: int = 0
    success_count: int = 0
    status: str = "experimental"  # experimental, validated, deprecated


@dataclass
class SynthesisResult:
    """Result of behavior synthesis execution"""
    synthesis_id: str
    success: bool
    output: Any
    component_results: List[Dict[str, Any]]
    latency_ms: float
    confidence: float
    aggregation_method: str


class EnsembleAggregator:
    """Aggregates outputs from multiple behaviors"""
    
    @staticmethod
    def weighted_average(outputs: List[Any], weights: List[float]) -> Any:
        """Weighted average for numerical outputs"""
        if not outputs or not weights:
            return None
        
        # Handle different output types
        if all(isinstance(o, (int, float)) for o in outputs):
            total_weight = sum(weights)
            if total_weight == 0:
                return np.mean(outputs)
            return sum(o * w for o, w in zip(outputs, weights)) / total_weight
        
        # For structured outputs, take weighted vote on key fields
        if all(isinstance(o, dict) for o in outputs):
            result = {}
            for key in outputs[0].keys():
                values = [o.get(key) for o in outputs]
                if all(isinstance(v, (int, float)) for v in values if v is not None):
                    valid_pairs = [(v, w) for v, w in zip(values, weights) if v is not None]
                    if valid_pairs:
                        result[key] = sum(v * w for v, w in valid_pairs) / sum(w for _, w in valid_pairs)
                else:
                    # Take most common non-None value
                    non_none = [v for v in values if v is not None]
                    if non_none:
                        result[key] = max(set(non_none), key=non_none.count)
            return result
        
        # Default: return highest weighted output
        max_idx = np.argmax(weights)
        return outputs[max_idx]
    
    @staticmethod
    def majority_vote(outputs: List[Any], weights: Optional[List[float]] = None) -> Any:
        """Majority vote for categorical outputs"""
        if not outputs:
            return None
        
        # Count occurrences
        counts = defaultdict(float)
        for i, output in enumerate(outputs):
            weight = weights[i] if weights else 1.0
            
            # Handle different types
            if isinstance(output, dict):
                # Hashable representation for voting
                key = tuple(sorted(output.items()))
            else:
                key = output
            
            counts[key] += weight
        
        # Get winner
        winner = max(counts, key=counts.get)
        
        # Convert back from hashable if needed
        if isinstance(winner, tuple):
            return dict(winner)
        return winner
    
    @staticmethod
    def best_of_n(outputs: List[Any], scores: List[float]) -> Any:
        """Select best output based on confidence scores"""
        if not outputs or not scores:
            return outputs[0] if outputs else None
        
        best_idx = np.argmax(scores)
        return outputs[best_idx]
    
    @staticmethod
    def confidence_weighted(outputs: List[Any], confidences: List[float]) -> Any:
        """Weight outputs by their confidence scores"""
        return EnsembleAggregator.weighted_average(outputs, confidences)


class ChainExecutor:
    """Executes behaviors in a chain"""
    
    async def execute_chain(self, 
                          components: List[BehaviorComponent],
                          implementations: Dict[str, Callable],
                          initial_input: Dict[str, Any],
                          timeout_per_step: float = 5.0) -> Tuple[Any, List[Dict[str, Any]]]:
        """
        Execute components in chain order.
        
        Returns: (final_output, step_results)
        """
        current_input = initial_input
        step_results = []
        
        # Sort by position
        sorted_components = sorted(components, key=lambda c: c.position)
        
        for component in sorted_components:
            impl = implementations.get(component.capability_id)
            if not impl:
                step_results.append({
                    'component': component.capability_id,
                    'success': False,
                    'error': 'Implementation not found'
                })
                continue
            
            try:
                start_time = datetime.utcnow()
                
                if asyncio.iscoroutinefunction(impl):
                    output = await asyncio.wait_for(
                        impl(current_input),
                        timeout=timeout_per_step
                    )
                else:
                    output = impl(current_input)
                
                latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                step_results.append({
                    'component': component.capability_id,
                    'success': True,
                    'output': output,
                    'latency_ms': latency_ms
                })
                
                # Output becomes next input
                current_input = {
                    **initial_input,
                    'previous_output': output,
                    'step': component.position
                }
                
            except Exception as e:
                step_results.append({
                    'component': component.capability_id,
                    'success': False,
                    'error': str(e)
                })
                # Continue with original input if step fails
        
        # Extract final output from last successful step
        final_output = step_results[-1]['output'] if step_results and step_results[-1].get('success') else None
        
        return final_output, step_results


class BehaviorSynthesizer:
    """
    Synthesizes multiple behaviors into composite capabilities.
    
    Supports:
    - Ensembling: Multiple behaviors vote on output
    - Chaining: Behaviors feed into each other sequentially
    - Hybrid: Combination approaches
    """
    
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry
        self.ensemble_aggregator = EnsembleAggregator()
        self.chain_executor = ChainExecutor()
        
        # Active syntheses
        self.syntheses: Dict[str, SynthesizedCapability] = {}
        
        # Implementation cache
        self.implementations: Dict[str, Callable] = {}
        
        logger.info("BehaviorSynthesizer initialized")
    
    def register_implementation(self, capability_id: str, impl: Callable):
        """Register an implementation for a capability"""
        self.implementations[capability_id] = impl
    
    async def create_ensemble(self, 
                             name: str,
                             task_category: str,
                             capability_ids: List[str],
                             aggregation_fn: str = "weighted_avg") -> SynthesizedCapability:
        """
        Create an ensemble synthesis from multiple capabilities.
        
        Args:
            name: Name for the synthesized capability
            task_category: Task category
            capability_ids: List of capability IDs to ensemble
            aggregation_fn: How to aggregate outputs ('weighted_avg', 'majority_vote', 'best_of_n')
        """
        # Load capabilities
        components = []
        total_latency = 0
        min_reliability = 1.0
        
        for cap_id in capability_ids:
            record = self.registry.get_capability(cap_id)
            if not record:
                logger.warning(f"Capability {cap_id} not found in registry")
                continue
            
            # Calculate weight based on performance and reliability
            weight = record.performance_score * record.reliability_score
            
            components.append(BehaviorComponent(
                capability_id=cap_id,
                name=record.name,
                weight=weight,
                position=0
            ))
            
            total_latency += record.latency_ms
            min_reliability = min(min_reliability, record.reliability_score)
        
        if not components:
            raise ValueError("No valid capabilities found for ensemble")
        
        # Normalize weights
        total_weight = sum(c.weight for c in components)
        for c in components:
            c.weight = c.weight / total_weight if total_weight > 0 else 1.0 / len(components)
        
        synthesis = SynthesizedCapability(
            synthesis_id=self._generate_id(f"ensemble_{name}"),
            name=name,
            task_category=task_category,
            mode=SynthesisMode.ENSEMBLE,
            components=components,
            aggregation_fn=aggregation_fn,
            latency_ms=total_latency,  # Parallel execution
            reliability_score=min_reliability
        )
        
        self.syntheses[synthesis.synthesis_id] = synthesis
        
        logger.info(f"Created ensemble synthesis {synthesis.synthesis_id} with {len(components)} components")
        return synthesis
    
    async def create_chain(self,
                          name: str,
                          task_category: str,
                          capability_ids: List[str],
                          stage_names: Optional[List[str]] = None) -> SynthesizedCapability:
        """
        Create a chain synthesis where outputs feed into next stage.
        
        Example: [preprocess, analyze, postprocess]
        """
        components = []
        total_latency = 0
        cumulative_reliability = 1.0
        
        for i, cap_id in enumerate(capability_ids):
            record = self.registry.get_capability(cap_id)
            if not record:
                logger.warning(f"Capability {cap_id} not found")
                continue
            
            name_suffix = stage_names[i] if stage_names and i < len(stage_names) else f"stage_{i}"
            
            components.append(BehaviorComponent(
                capability_id=cap_id,
                name=f"{record.name}_{name_suffix}",
                weight=1.0,
                position=i
            ))
            
            total_latency += record.latency_ms
            cumulative_reliability *= record.reliability_score
        
        if not components:
            raise ValueError("No valid capabilities found for chain")
        
        synthesis = SynthesizedCapability(
            synthesis_id=self._generate_id(f"chain_{name}"),
            name=name,
            task_category=task_category,
            mode=SynthesisMode.CHAIN,
            components=components,
            aggregation_fn="cascade",
            latency_ms=total_latency,  # Sequential execution
            reliability_score=cumulative_reliability
        )
        
        self.syntheses[synthesis.synthesis_id] = synthesis
        
        logger.info(f"Created chain synthesis {synthesis.synthesis_id} with {len(components)} stages")
        return synthesis
    
    async def execute_synthesis(self, 
                               synthesis_id: str,
                               input_data: Dict[str, Any],
                               timeout_ms: int = 10000) -> SynthesisResult:
        """Execute a synthesized capability"""
        
        synthesis = self.syntheses.get(synthesis_id)
        if not synthesis:
            return SynthesisResult(
                synthesis_id=synthesis_id,
                success=False,
                output=None,
                component_results=[],
                latency_ms=0,
                confidence=0.0,
                aggregation_method="unknown"
            )
        
        start_time = datetime.utcnow()
        
        try:
            if synthesis.mode == SynthesisMode.ENSEMBLE:
                result = await self._execute_ensemble(synthesis, input_data, timeout_ms)
            elif synthesis.mode == SynthesisMode.CHAIN:
                result = await self._execute_chain(synthesis, input_data, timeout_ms)
            else:
                result = await self._execute_hybrid(synthesis, input_data, timeout_ms)
            
            # Update synthesis stats
            synthesis.usage_count += 1
            if result.success:
                synthesis.success_count += 1
            
            return result
            
        except Exception as e:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            logger.error(f"Error executing synthesis {synthesis_id}: {e}")
            
            return SynthesisResult(
                synthesis_id=synthesis_id,
                success=False,
                output=None,
                component_results=[],
                latency_ms=latency_ms,
                confidence=0.0,
                aggregation_method=synthesis.aggregation_fn
            )
    
    async def _execute_ensemble(self, 
                               synthesis: SynthesizedCapability,
                               input_data: Dict[str, Any],
                               timeout_ms: int) -> SynthesisResult:
        """Execute ensemble synthesis"""
        start_time = datetime.utcnow()
        
        # Execute all components in parallel
        component_results = []
        outputs = []
        weights = []
        confidences = []
        
        async def execute_component(component: BehaviorComponent) -> Dict[str, Any]:
            impl = self.implementations.get(component.capability_id)
            if not impl:
                return {
                    'component': component.capability_id,
                    'success': False,
                    'error': 'Implementation not found'
                }
            
            try:
                comp_start = datetime.utcnow()
                
                if asyncio.iscoroutinefunction(impl):
                    output = await asyncio.wait_for(
                        impl(input_data),
                        timeout=timeout_ms / 1000 / len(synthesis.components)
                    )
                else:
                    output = impl(input_data)
                
                comp_latency = (datetime.utcnow() - comp_start).total_seconds() * 1000
                
                return {
                    'component': component.capability_id,
                    'success': True,
                    'output': output,
                    'latency_ms': comp_latency,
                    'weight': component.weight
                }
            except Exception as e:
                return {
                    'component': component.capability_id,
                    'success': False,
                    'error': str(e)
                }
        
        # Execute all components
        tasks = [execute_component(c) for c in synthesis.components]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                component_results.append({
                    'component': 'unknown',
                    'success': False,
                    'error': str(result)
                })
            else:
                component_results.append(result)
                if result.get('success'):
                    outputs.append(result['output'])
                    weights.append(result.get('weight', 1.0))
        
        # Aggregate outputs
        if not outputs:
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            return SynthesisResult(
                synthesis_id=synthesis.synthesis_id,
                success=False,
                output=None,
                component_results=component_results,
                latency_ms=latency_ms,
                confidence=0.0,
                aggregation_method=synthesis.aggregation_fn
            )
        
        # Apply aggregation
        if synthesis.aggregation_fn == "weighted_avg":
            final_output = self.ensemble_aggregator.weighted_average(outputs, weights)
        elif synthesis.aggregation_fn == "majority_vote":
            final_output = self.ensemble_aggregator.majority_vote(outputs, weights)
        elif synthesis.aggregation_fn == "best_of_n":
            # Use weights as proxy for confidence
            final_output = self.ensemble_aggregator.best_of_n(outputs, weights)
        else:
            final_output = outputs[0] if outputs else None
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Calculate confidence based on agreement
        success_rate = sum(1 for r in component_results if r.get('success')) / len(component_results)
        confidence = success_rate * (1.0 - np.std(weights) if len(weights) > 1 else 1.0)
        
        return SynthesisResult(
            synthesis_id=synthesis.synthesis_id,
            success=True,
            output=final_output,
            component_results=component_results,
            latency_ms=latency_ms,
            confidence=confidence,
            aggregation_method=synthesis.aggregation_fn
        )
    
    async def _execute_chain(self,
                            synthesis: SynthesizedCapability,
                            input_data: Dict[str, Any],
                            timeout_ms: int) -> SynthesisResult:
        """Execute chain synthesis"""
        start_time = datetime.utcnow()
        
        # Get implementations
        implementations = {
            c.capability_id: self.implementations.get(c.capability_id)
            for c in synthesis.components
        }
        
        # Execute chain
        final_output, step_results = await self.chain_executor.execute_chain(
            components=synthesis.components,
            implementations=implementations,
            initial_input=input_data,
            timeout_per_step=timeout_ms / 1000 / max(1, len(synthesis.components))
        )
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Calculate success
        success_count = sum(1 for r in step_results if r.get('success'))
        success = success_count == len(synthesis.components)
        
        # Confidence based on chain reliability
        confidence = synthesis.reliability_score if success else 0.0
        
        return SynthesisResult(
            synthesis_id=synthesis.synthesis_id,
            success=success,
            output=final_output,
            component_results=step_results,
            latency_ms=latency_ms,
            confidence=confidence,
            aggregation_method="cascade"
        )
    
    async def _execute_hybrid(self,
                             synthesis: SynthesizedCapability,
                             input_data: Dict[str, Any],
                             timeout_ms: int) -> SynthesisResult:
        """Execute hybrid synthesis (ensemble within chain stages)"""
        # TODO: Implement hybrid mode
        return await self._execute_chain(synthesis, input_data, timeout_ms)
    
    async def validate_synthesis(self, 
                                synthesis_id: str,
                                test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate a synthesized capability with test cases"""
        synthesis = self.syntheses.get(synthesis_id)
        if not synthesis:
            return {'error': 'Synthesis not found'}
        
        results = []
        successes = 0
        total_latency = 0
        
        for test in test_cases:
            result = await self.execute_synthesis(
                synthesis_id=synthesis_id,
                input_data=test['input'],
                timeout_ms=test.get('timeout_ms', 5000)
            )
            
            # Check if output matches expected (if provided)
            expected = test.get('expected_output')
            if expected and result.success:
                # Simple equality check - can be enhanced
                matches = result.output == expected
                if not matches:
                    result.success = False
            
            results.append({
                'test_input': test['input'],
                'success': result.success,
                'output': result.output,
                'latency_ms': result.latency_ms
            })
            
            if result.success:
                successes += 1
            total_latency += result.latency_ms
        
        # Update synthesis performance
        accuracy = successes / len(test_cases) if test_cases else 0
        avg_latency = total_latency / len(test_cases) if test_cases else 0
        
        synthesis.performance_score = accuracy
        synthesis.latency_ms = avg_latency
        synthesis.validation_results = results
        
        if accuracy > 0.8:
            synthesis.status = "validated"
        
        return {
            'synthesis_id': synthesis_id,
            'accuracy': accuracy,
            'avg_latency_ms': avg_latency,
            'test_count': len(test_cases),
            'passed': successes,
            'status': synthesis.status,
            'results': results
        }
    
    def register_to_registry(self, synthesis_id: str) -> Optional[str]:
        """Register a validated synthesis to the capability registry"""
        synthesis = self.syntheses.get(synthesis_id)
        if not synthesis:
            return None
        
        if synthesis.status != "validated":
            logger.warning(f"Synthesis {synthesis_id} not validated, skipping registration")
            return None
        
        # Create capability record
        from .capability_registry import CapabilityRecord
        
        record = CapabilityRecord(
            capability_id=synthesis.synthesis_id,
            name=synthesis.name,
            task_category=synthesis.task_category,
            task_tags=[synthesis.mode.value, "synthesized"],
            source_model="synthesis",
            behaviors=[{
                'mode': synthesis.mode.value,
                'components': [{'id': c.capability_id, 'name': c.name} for c in synthesis.components],
                'aggregation': synthesis.aggregation_fn
            }],
            controls=[],  # Inherit from component capabilities
            performance_score=synthesis.performance_score,
            latency_ms=synthesis.latency_ms,
            reliability_score=synthesis.reliability_score,
            metadata={
                'synthesis_mode': synthesis.mode.value,
                'component_count': len(synthesis.components),
                'created_at': synthesis.created_at
            }
        )
        
        self.registry.register_capability(record)
        
        logger.info(f"Registered synthesis {synthesis_id} to capability registry")
        return synthesis.synthesis_id
    
    def get_synthesis_stats(self, synthesis_id: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for syntheses"""
        if synthesis_id:
            synthesis = self.syntheses.get(synthesis_id)
            if not synthesis:
                return {}
            
            return {
                'synthesis_id': synthesis_id,
                'name': synthesis.name,
                'mode': synthesis.mode.value,
                'component_count': len(synthesis.components),
                'performance_score': synthesis.performance_score,
                'reliability_score': synthesis.reliability_score,
                'latency_ms': synthesis.latency_ms,
                'usage_count': synthesis.usage_count,
                'success_rate': synthesis.success_count / max(1, synthesis.usage_count),
                'status': synthesis.status
            }
        
        # Return stats for all syntheses
        return {
            'total_syntheses': len(self.syntheses),
            'by_mode': {
                mode.value: len([s for s in self.syntheses.values() if s.mode == mode])
                for mode in SynthesisMode
            },
            'validated': len([s for s in self.syntheses.values() if s.status == 'validated']),
            'experimental': len([s for s in self.syntheses.values() if s.status == 'experimental'])
        }
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID"""
        hash_input = f"{prefix}_{datetime.utcnow().timestamp()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def create_synthesizer(registry: CapabilityRegistry) -> BehaviorSynthesizer:
    """Factory function to create a behavior synthesizer"""
    return BehaviorSynthesizer(registry)
