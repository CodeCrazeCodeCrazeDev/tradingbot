"""
Existing Systems Bridge - Integration with Current Trading Bot Systems
=========================================================================

Bridges the Foundation Agents with existing systems:
1. Improvement Orchestrator integration
2. Self-Assembly AI integration
3. Alpha Discovery Engine integration

This module provides adapters and connectors to integrate the new
autonomous research capabilities with the existing trading infrastructure.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class IntegrationConfig:
    """Configuration for system integration"""
    enable_improvement_integration: bool = True
    enable_self_assembly_integration: bool = True
    enable_alpha_discovery_integration: bool = True
    
    # Sync intervals
    improvement_sync_interval_minutes: int = 15
    self_assembly_sync_interval_minutes: int = 30
    alpha_discovery_sync_interval_minutes: int = 10
    
    # Feature flags
    auto_deploy_improvements: bool = False
    auto_evolve_strategies: bool = False
    auto_deploy_alphas: bool = False


class ImprovementOrchestratorAdapter:
    """
    Adapter for integrating with the existing Improvement Orchestrator.
    
    Connects foundation agent research capabilities with the
    continuous improvement system.
    """
    
    def __init__(self, improvement_orchestrator=None):
        self.orchestrator = improvement_orchestrator
        self.pending_improvements: List[Dict] = []
        self.deployed_improvements: List[Dict] = []
        
        logger.info("Improvement Orchestrator Adapter initialized")
    
    def connect(self, orchestrator):
        """Connect to the improvement orchestrator"""
        self.orchestrator = orchestrator
        logger.info("Connected to Improvement Orchestrator")
    
    def submit_research_finding(
        self,
        finding_type: str,
        description: str,
        evidence: Dict[str, Any],
        suggested_improvement: Optional[str] = None,
        priority: str = "medium"
    ) -> Dict:
        """Submit a research finding as a potential improvement"""
        improvement = {
            'id': f"imp_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'type': finding_type,
            'description': description,
            'evidence': evidence,
            'suggested_improvement': suggested_improvement,
            'priority': priority,
            'status': 'pending',
            'submitted_at': datetime.utcnow().isoformat(),
            'source': 'foundation_agents'
        }
        
        self.pending_improvements.append(improvement)
        
        # If connected, submit to orchestrator
        if self.orchestrator:
            try:
                self.orchestrator.add_improvement_opportunity(improvement)
            except Exception as e:
                logger.error(f"Failed to submit improvement: {e}")
        
        return improvement
    
    def submit_hypothesis_result(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        result: str,  # supported, rejected, inconclusive
        evidence: Dict[str, Any],
        trading_implications: Optional[str] = None
    ) -> Dict:
        """Submit hypothesis test result as potential improvement"""
        if result == 'supported':
            return self.submit_research_finding(
                finding_type='validated_hypothesis',
                description=f"Validated: {hypothesis_statement}",
                evidence=evidence,
                suggested_improvement=trading_implications,
                priority='high' if trading_implications else 'medium'
            )
        return {'status': 'not_submitted', 'reason': f'hypothesis_{result}'}
    
    def submit_theory(
        self,
        theory_id: str,
        theory_name: str,
        theory_description: str,
        mechanisms: List[Dict],
        predictions: List[str]
    ) -> Dict:
        """Submit a validated theory as improvement opportunity"""
        return self.submit_research_finding(
            finding_type='economic_theory',
            description=f"Theory: {theory_name} - {theory_description}",
            evidence={
                'mechanisms': mechanisms,
                'predictions': predictions
            },
            suggested_improvement=f"Implement trading rules based on {theory_name}",
            priority='high'
        )
    
    def get_improvement_feedback(self) -> List[Dict]:
        """Get feedback on submitted improvements"""
        feedback = []
        
        if self.orchestrator:
            try:
                # Get status of our submitted improvements
                for imp in self.pending_improvements:
                    status = self.orchestrator.get_improvement_status(imp['id'])
                    if status:
                        feedback.append({
                            'improvement_id': imp['id'],
                            'status': status
                        })
            except Exception as e:
                logger.error(f"Failed to get feedback: {e}")
        
        return feedback
    
    def get_statistics(self) -> Dict:
        return {
            'pending_improvements': len(self.pending_improvements),
            'deployed_improvements': len(self.deployed_improvements),
            'connected': self.orchestrator is not None
        }


class SelfAssemblyAdapter:
    """
    Adapter for integrating with the Self-Assembly AI system.
    
    Connects foundation agent curiosity and research with
    the self-evolving strategy system.
    """
    
    def __init__(self, self_assembly_orchestrator=None):
        self.orchestrator = self_assembly_orchestrator
        self.suggested_mutations: List[Dict] = []
        self.curiosity_signals: List[Dict] = []
        
        logger.info("Self-Assembly Adapter initialized")
    
    def connect(self, orchestrator):
        """Connect to the self-assembly orchestrator"""
        self.orchestrator = orchestrator
        logger.info("Connected to Self-Assembly Orchestrator")
    
    def suggest_mutation(
        self,
        strategy_id: str,
        mutation_type: str,
        mutation_description: str,
        rationale: str,
        expected_improvement: float = 0.0
    ) -> Dict:
        """Suggest a mutation based on research findings"""
        mutation = {
            'id': f"mut_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'strategy_id': strategy_id,
            'mutation_type': mutation_type,
            'description': mutation_description,
            'rationale': rationale,
            'expected_improvement': expected_improvement,
            'status': 'suggested',
            'source': 'foundation_agents'
        }
        
        self.suggested_mutations.append(mutation)
        
        if self.orchestrator:
            try:
                self.orchestrator.add_guided_mutation(mutation)
            except Exception as e:
                logger.error(f"Failed to suggest mutation: {e}")
        
        return mutation
    
    def send_curiosity_signal(
        self,
        signal_type: str,
        target: str,
        intensity: float,
        context: Dict[str, Any]
    ) -> Dict:
        """Send curiosity signal to guide evolution"""
        signal = {
            'id': f"cur_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'signal_type': signal_type,
            'target': target,
            'intensity': intensity,
            'context': context,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.curiosity_signals.append(signal)
        
        if self.orchestrator:
            try:
                self.orchestrator.receive_curiosity_signal(signal)
            except Exception as e:
                logger.error(f"Failed to send curiosity signal: {e}")
        
        return signal
    
    def suggest_exploration_direction(
        self,
        direction_type: str,
        description: str,
        priority: float,
        based_on: List[str]
    ) -> Dict:
        """Suggest exploration direction based on anomalies/hypotheses"""
        return self.send_curiosity_signal(
            signal_type='exploration_direction',
            target=direction_type,
            intensity=priority,
            context={
                'description': description,
                'based_on': based_on
            }
        )
    
    def report_cross_domain_insight(
        self,
        source_domain: str,
        insight: str,
        applicability: float,
        suggested_application: str
    ) -> Dict:
        """Report cross-domain insight for strategy evolution"""
        return self.send_curiosity_signal(
            signal_type='cross_domain_insight',
            target='strategy_evolution',
            intensity=applicability,
            context={
                'source_domain': source_domain,
                'insight': insight,
                'suggested_application': suggested_application
            }
        )
    
    def get_evolution_feedback(self) -> List[Dict]:
        """Get feedback on suggested mutations"""
        feedback = []
        
        if self.orchestrator:
            try:
                for mut in self.suggested_mutations:
                    status = self.orchestrator.get_mutation_status(mut['id'])
                    if status:
                        feedback.append({
                            'mutation_id': mut['id'],
                            'status': status
                        })
            except Exception as e:
                logger.error(f"Failed to get evolution feedback: {e}")
        
        return feedback
    
    def get_statistics(self) -> Dict:
        return {
            'suggested_mutations': len(self.suggested_mutations),
            'curiosity_signals_sent': len(self.curiosity_signals),
            'connected': self.orchestrator is not None
        }


class AlphaDiscoveryAdapter:
    """
    Adapter for integrating with the Alpha Discovery Engine.
    
    Connects foundation agent hypothesis generation with
    alpha signal discovery.
    """
    
    def __init__(self, alpha_discovery_engine=None):
        self.engine = alpha_discovery_engine
        self.submitted_hypotheses: List[Dict] = []
        self.discovered_alphas: List[Dict] = []
        
        logger.info("Alpha Discovery Adapter initialized")
    
    def connect(self, engine):
        """Connect to the alpha discovery engine"""
        self.engine = engine
        logger.info("Connected to Alpha Discovery Engine")
    
    def submit_alpha_hypothesis(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        hypothesis_type: str,
        variables: List[str],
        expected_relationship: str,
        confidence: float
    ) -> Dict:
        """Submit a hypothesis as potential alpha signal"""
        alpha_hypothesis = {
            'id': f"alpha_{hypothesis_id}",
            'hypothesis_id': hypothesis_id,
            'statement': hypothesis_statement,
            'type': hypothesis_type,
            'variables': variables,
            'expected_relationship': expected_relationship,
            'confidence': confidence,
            'status': 'submitted',
            'source': 'foundation_agents',
            'submitted_at': datetime.utcnow().isoformat()
        }
        
        self.submitted_hypotheses.append(alpha_hypothesis)
        
        if self.engine:
            try:
                self.engine.add_hypothesis_based_alpha(alpha_hypothesis)
            except Exception as e:
                logger.error(f"Failed to submit alpha hypothesis: {e}")
        
        return alpha_hypothesis
    
    def submit_causal_alpha(
        self,
        cause_variable: str,
        effect_variable: str,
        lag: int,
        strength: float,
        mechanism: str
    ) -> Dict:
        """Submit a causal relationship as potential alpha"""
        return self.submit_alpha_hypothesis(
            hypothesis_id=f"causal_{cause_variable}_{effect_variable}",
            hypothesis_statement=f"{cause_variable} causes {effect_variable} with lag {lag}",
            hypothesis_type='causal',
            variables=[cause_variable, effect_variable],
            expected_relationship=f"positive_lag_{lag}" if strength > 0 else f"negative_lag_{lag}",
            confidence=abs(strength)
        )
    
    def submit_anomaly_alpha(
        self,
        anomaly_type: str,
        asset: str,
        pattern: str,
        historical_performance: float
    ) -> Dict:
        """Submit an anomaly pattern as potential alpha"""
        return self.submit_alpha_hypothesis(
            hypothesis_id=f"anomaly_{anomaly_type}_{asset}",
            hypothesis_statement=f"{anomaly_type} anomaly in {asset}: {pattern}",
            hypothesis_type='anomaly',
            variables=[asset, anomaly_type],
            expected_relationship=pattern,
            confidence=min(0.9, abs(historical_performance))
        )
    
    def submit_cross_domain_alpha(
        self,
        source_domain: str,
        analogy: str,
        trading_application: str,
        novelty_score: float
    ) -> Dict:
        """Submit cross-domain insight as potential alpha"""
        return self.submit_alpha_hypothesis(
            hypothesis_id=f"xdomain_{source_domain}",
            hypothesis_statement=f"Apply {analogy} from {source_domain} to trading",
            hypothesis_type='cross_domain',
            variables=[source_domain, 'trading'],
            expected_relationship=trading_application,
            confidence=novelty_score * 0.5  # Discount for novelty
        )
    
    def get_alpha_validation_results(self) -> List[Dict]:
        """Get validation results for submitted alphas"""
        results = []
        
        if self.engine:
            try:
                for hyp in self.submitted_hypotheses:
                    validation = self.engine.get_alpha_validation(hyp['id'])
                    if validation:
                        results.append({
                            'alpha_id': hyp['id'],
                            'validation': validation
                        })
                        
                        if validation.get('status') == 'validated':
                            self.discovered_alphas.append({
                                **hyp,
                                'validation': validation
                            })
            except Exception as e:
                logger.error(f"Failed to get validation results: {e}")
        
        return results
    
    def get_statistics(self) -> Dict:
        return {
            'submitted_hypotheses': len(self.submitted_hypotheses),
            'discovered_alphas': len(self.discovered_alphas),
            'connected': self.engine is not None
        }


class ExistingSystemsBridge:
    """
    Main bridge class that coordinates integration with all existing systems.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        self.config = config or IntegrationConfig()
        
        # Adapters
        self.improvement_adapter = ImprovementOrchestratorAdapter()
        self.self_assembly_adapter = SelfAssemblyAdapter()
        self.alpha_discovery_adapter = AlphaDiscoveryAdapter()
        
        # State
        self.is_connected = False
        self.last_sync: Dict[str, datetime] = {}
        
        # Statistics
        self.stats = {
            'improvements_submitted': 0,
            'mutations_suggested': 0,
            'alphas_submitted': 0,
            'syncs_performed': 0
        }
        
        logger.info("Existing Systems Bridge initialized")
    
    def connect_all(
        self,
        improvement_orchestrator=None,
        self_assembly_orchestrator=None,
        alpha_discovery_engine=None
    ):
        """Connect to all existing systems"""
        if improvement_orchestrator and self.config.enable_improvement_integration:
            self.improvement_adapter.connect(improvement_orchestrator)
        
        if self_assembly_orchestrator and self.config.enable_self_assembly_integration:
            self.self_assembly_adapter.connect(self_assembly_orchestrator)
        
        if alpha_discovery_engine and self.config.enable_alpha_discovery_integration:
            self.alpha_discovery_adapter.connect(alpha_discovery_engine)
        
        self.is_connected = True
        logger.info("Connected to existing systems")
    
    def process_research_output(
        self,
        output_type: str,
        output_data: Dict[str, Any]
    ):
        """Process research output and route to appropriate systems"""
        
        if output_type == 'hypothesis_result':
            # Route to improvement orchestrator
            self.improvement_adapter.submit_hypothesis_result(
                hypothesis_id=output_data.get('hypothesis_id', ''),
                hypothesis_statement=output_data.get('statement', ''),
                result=output_data.get('result', 'inconclusive'),
                evidence=output_data.get('evidence', {}),
                trading_implications=output_data.get('trading_implications')
            )
            
            # Also submit to alpha discovery if supported
            if output_data.get('result') == 'supported':
                self.alpha_discovery_adapter.submit_alpha_hypothesis(
                    hypothesis_id=output_data.get('hypothesis_id', ''),
                    hypothesis_statement=output_data.get('statement', ''),
                    hypothesis_type=output_data.get('type', 'general'),
                    variables=output_data.get('variables', []),
                    expected_relationship=output_data.get('relationship', ''),
                    confidence=output_data.get('confidence', 0.5)
                )
                self.stats['alphas_submitted'] += 1
            
            self.stats['improvements_submitted'] += 1
        
        elif output_type == 'anomaly':
            # Route to self-assembly for exploration
            self.self_assembly_adapter.suggest_exploration_direction(
                direction_type='anomaly_investigation',
                description=output_data.get('description', ''),
                priority=output_data.get('severity', 0.5),
                based_on=[output_data.get('anomaly_id', '')]
            )
            
            # Also submit to alpha discovery
            self.alpha_discovery_adapter.submit_anomaly_alpha(
                anomaly_type=output_data.get('anomaly_type', ''),
                asset=output_data.get('asset', ''),
                pattern=output_data.get('pattern', ''),
                historical_performance=output_data.get('performance', 0.0)
            )
            self.stats['alphas_submitted'] += 1
        
        elif output_type == 'causal_discovery':
            # Route to alpha discovery
            self.alpha_discovery_adapter.submit_causal_alpha(
                cause_variable=output_data.get('cause', ''),
                effect_variable=output_data.get('effect', ''),
                lag=output_data.get('lag', 0),
                strength=output_data.get('strength', 0.0),
                mechanism=output_data.get('mechanism', '')
            )
            self.stats['alphas_submitted'] += 1
        
        elif output_type == 'cross_domain_insight':
            # Route to self-assembly
            self.self_assembly_adapter.report_cross_domain_insight(
                source_domain=output_data.get('source_domain', ''),
                insight=output_data.get('insight', ''),
                applicability=output_data.get('applicability', 0.5),
                suggested_application=output_data.get('application', '')
            )
            
            # Also submit to alpha discovery
            self.alpha_discovery_adapter.submit_cross_domain_alpha(
                source_domain=output_data.get('source_domain', ''),
                analogy=output_data.get('analogy', ''),
                trading_application=output_data.get('application', ''),
                novelty_score=output_data.get('novelty', 0.5)
            )
            self.stats['alphas_submitted'] += 1
        
        elif output_type == 'theory':
            # Route to improvement orchestrator
            self.improvement_adapter.submit_theory(
                theory_id=output_data.get('theory_id', ''),
                theory_name=output_data.get('name', ''),
                theory_description=output_data.get('description', ''),
                mechanisms=output_data.get('mechanisms', []),
                predictions=output_data.get('predictions', [])
            )
            self.stats['improvements_submitted'] += 1
        
        elif output_type == 'strategy_suggestion':
            # Route to self-assembly
            self.self_assembly_adapter.suggest_mutation(
                strategy_id=output_data.get('strategy_id', 'default'),
                mutation_type=output_data.get('mutation_type', 'parameter'),
                mutation_description=output_data.get('description', ''),
                rationale=output_data.get('rationale', ''),
                expected_improvement=output_data.get('expected_improvement', 0.0)
            )
            self.stats['mutations_suggested'] += 1
    
    async def sync_all(self):
        """Synchronize with all connected systems"""
        now = datetime.utcnow()
        
        # Sync improvement feedback
        if self.config.enable_improvement_integration:
            feedback = self.improvement_adapter.get_improvement_feedback()
            self.last_sync['improvement'] = now
        
        # Sync evolution feedback
        if self.config.enable_self_assembly_integration:
            feedback = self.self_assembly_adapter.get_evolution_feedback()
            self.last_sync['self_assembly'] = now
        
        # Sync alpha validation
        if self.config.enable_alpha_discovery_integration:
            results = self.alpha_discovery_adapter.get_alpha_validation_results()
            self.last_sync['alpha_discovery'] = now
        
        self.stats['syncs_performed'] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get bridge statistics"""
        return {
            **self.stats,
            'is_connected': self.is_connected,
            'last_sync': {k: v.isoformat() for k, v in self.last_sync.items()},
            'adapters': {
                'improvement': self.improvement_adapter.get_statistics(),
                'self_assembly': self.self_assembly_adapter.get_statistics(),
                'alpha_discovery': self.alpha_discovery_adapter.get_statistics()
            }
        }
