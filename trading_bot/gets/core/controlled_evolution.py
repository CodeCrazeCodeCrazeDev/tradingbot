"""
Layer 4: Controlled Evolution Layer

Sandbox-only improvement generation. Live system never self-modifies.

Offline/Sandbox Operations:
1. Failure Analysis Pipeline - Cluster failed predictions by regime, horizon, asset
2. Mutation Proposal Engine - Generate adapter mutations, propose new heads
3. Champion-Challenger Testing - Hold-out backtesting, paper trading validation
4. Cross-Validation Regime Testing - Validation across distinct market regimes

What NEVER Happens:
- No online self-retraining on live data
- No direct production model mutation
- No optimization of RMSE/MAE alone
- No regime-unaware averaging
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import json
import numpy as np

from ..types import (
    ModelType, ForecastHorizon, MarketData, FoundationForecast,
    TradingNativeHeads, RegimeType, GETSConfig, MutationProposal,
    EvolutionChampion, FailurePattern
)

logger = logging.getLogger(__name__)


@dataclass
class FailureCluster:
    """Cluster of similar failures for pattern analysis."""
    cluster_id: str
    failure_class: str
    description: str
    affected_models: List[ModelType]
    regimes: List[RegimeType]
    horizons: List[ForecastHorizon]
    symbols: List[str]
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    
    # Characteristics
    avg_error_magnitude: float
    avg_confidence: float
    volatility_regime: str  # "high", "low", "mixed"


@dataclass
class MutationCandidate:
    """Candidate mutation before validation."""
    candidate_id: str
    mutation_type: str
    target_model: ModelType
    description: str
    
    # Technical details
    config_changes: Dict[str, Any]
    code_patch: Optional[str]  # For architectural changes
    
    # Motivation
    addresses_clusters: List[str]  # Cluster IDs
    expected_improvement: str
    rationale: str


@dataclass
class BacktestResult:
    """Results from backtesting a mutation."""
    mutation_id: str
    test_period: Tuple[datetime, datetime]
    
    # Performance metrics
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    
    # Forecast quality
    ic_mean: float  # Information coefficient
    ic_std: float
    directional_accuracy: float
    
    # Regime breakdown
    performance_by_regime: Dict[RegimeType, Dict[str, float]]
    
    # Statistical validation
    sample_count: int
    statistical_significance: float  # p-value vs baseline
    
    # Comparison to baseline
    baseline_ic: float
    improvement_vs_baseline: float


class FailureAnalysisPipeline:
    """
    Analyzes historical failures to identify patterns.
    
    Clusters failures by:
    - Regime (trending, ranging, volatile)
    - Horizon (short, medium, long)
    - Asset class
    - Model-specific blind spots
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        self.failure_history: List[Dict] = []
        self.clusters: Dict[str, FailureCluster] = {}
        
        # Clustering parameters
        self.error_threshold = 0.02  # 2% error threshold
        self.min_cluster_size = 5
    
    def add_failure(
        self,
        model_type: ModelType,
        market_data: MarketData,
        predicted_return: float,
        realized_return: float,
        detected_regime: RegimeType,
        horizon: ForecastHorizon,
        diagnosis_issues: List[str]
    ):
        """Record a failure for pattern analysis."""
        error = abs(predicted_return - realized_return)
        
        failure_record = {
            'timestamp': datetime.now(),
            'model_type': model_type,
            'symbol': market_data.symbol,
            'detected_regime': detected_regime,
            'horizon': horizon,
            'predicted_return': predicted_return,
            'realized_return': realized_return,
            'error': error,
            'diagnosis_issues': diagnosis_issues,
            'volatility_state': market_data.realized_volatility
        }
        
        self.failure_history.append(failure_record)
        
        # Keep history bounded
        if len(self.failure_history) > 10000:
            self.failure_history = self.failure_history[-10000:]
        
        # Update clusters
        self._update_clusters(failure_record)
    
    def _update_clusters(self, failure: Dict):
        """Update failure clusters with new failure."""
        # Determine cluster key based on characteristics
        regime = failure['detected_regime']
        horizon = failure['horizon']
        model = failure['model_type']
        
        cluster_key = f"{model.value}_{regime.value}_{horizon.value}"
        
        if cluster_key not in self.clusters:
            self.clusters[cluster_key] = FailureCluster(
                cluster_id=cluster_key,
                failure_class=f"{model.value}_{regime.value}_failure",
                description=f"Failures for {model.value} in {regime.value} regime at {horizon.value} horizon",
                affected_models=[model],
                regimes=[regime],
                horizons=[horizon],
                symbols=[failure['symbol']],
                count=0,
                first_occurrence=failure['timestamp'],
                last_occurrence=failure['timestamp'],
                avg_error_magnitude=0.0,
                avg_confidence=0.0,
                volatility_regime="unknown"
            )
        
        cluster = self.clusters[cluster_key]
        cluster.count += 1
        cluster.last_occurrence = failure['timestamp']
        
        if failure['symbol'] not in cluster.symbols:
            cluster.symbols.append(failure['symbol'])
        
        # Update averages
        n = cluster.count
        cluster.avg_error_magnitude = (
            (cluster.avg_error_magnitude * (n - 1) + failure['error']) / n
        )
    
    def get_significant_clusters(self, min_count: int = None) -> List[FailureCluster]:
        """Get clusters that exceed significance threshold."""
        threshold = min_count or self.min_cluster_size
        return [
            cluster for cluster in self.clusters.values()
            if cluster.count >= threshold
        ]
    
    def analyze_root_cause(self, cluster_id: str) -> Dict[str, Any]:
        """
        Perform root cause analysis on a failure cluster.
        
        Returns:
            Root cause hypothesis with confidence
        """
        if cluster_id not in self.clusters:
            return {'error': f'Cluster {cluster_id} not found'}
        
        cluster = self.clusters[cluster_id]
        
        # Analyze patterns in cluster
        related_failures = [
            f for f in self.failure_history
            if f['model_type'] in cluster.affected_models
            and f['detected_regime'] in cluster.regimes
        ]
        
        if not related_failures:
            return {'error': 'No matching failures in history'}
        
        # Analyze common issues
        issue_counts = {}
        for f in related_failures:
            for issue in f.get('diagnosis_issues', []):
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        top_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyze volatility patterns
        vols = [f.get('volatility_state', 0.5) for f in related_failures if f.get('volatility_state')]
        if vols:
            avg_vol = np.mean(vols)
            vol_regime = "high" if avg_vol > 0.3 else "low" if avg_vol < 0.15 else "medium"
        else:
            vol_regime = "unknown"
        
        return {
            'cluster_id': cluster_id,
            'failure_count': len(related_failures),
            'top_issues': top_issues,
            'volatility_regime': vol_regime,
            'affected_models': [m.value for m in cluster.affected_models],
            'regimes': [r.value for r in cluster.regimes],
            'horizons': [h.value for h in cluster.horizons],
            'root_cause_hypothesis': self._hypothesize_root_cause(top_issues, vol_regime),
            'confidence': 0.7 if top_issues else 0.3
        }
    
    def _hypothesize_root_cause(self, top_issues: List[Tuple[str, int]], vol_regime: str) -> str:
        """Generate root cause hypothesis from patterns."""
        if not top_issues:
            return "Insufficient data for root cause analysis"
        
        primary_issue = top_issues[0][0]
        
        if "stability" in primary_issue.lower():
            return f"Model instability in {vol_regime} volatility regime - consider higher regularization"
        elif "regime" in primary_issue.lower():
            return "Regime detection lag - model trained on different distribution"
        elif "evidence" in primary_issue.lower():
            return "Insufficient data quality for reliable inference"
        elif "execution" in primary_issue.lower():
            return "Edge predictions not accounting for market impact"
        elif "calibration" in primary_issue.lower():
            return "Model calibration drift - quantile predictions unreliable"
        else:
            return f"Complex failure pattern: {primary_issue}"


class MutationProposalEngine:
    """
    Generates mutation proposals to address identified failure patterns.
    
    Mutation types:
    - LoRA rank adjustment
    - Adapter alpha tuning
    - New head architecture
    - Fusion weight rebalancing
    - Data augmentation strategy
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        self.proposal_history: List[MutationCandidate] = []
        self.proposal_counter = 0
    
    def generate_mutations(
        self,
        failure_clusters: List[FailureCluster],
        current_config: GETSConfig
    ) -> List[MutationCandidate]:
        """
        Generate mutation candidates to address failure clusters.
        
        Args:
            failure_clusters: Significant failure patterns
            current_config: Current system configuration
            
        Returns:
            List of mutation candidates
        """
        candidates = []
        
        for cluster in failure_clusters:
            # Generate mutations specific to cluster characteristics
            cluster_candidates = self._generate_cluster_mutations(cluster, current_config)
            candidates.extend(cluster_candidates)
        
        # Deduplicate similar proposals
        candidates = self._deduplicate_candidates(candidates)
        
        # Store for tracking
        self.proposal_history.extend(candidates)
        
        return candidates
    
    def _generate_cluster_mutations(
        self,
        cluster: FailureCluster,
        current_config: GETSConfig
    ) -> List[MutationCandidate]:
        """Generate mutations for a specific failure cluster."""
        candidates = []
        
        # Determine mutation strategy based on cluster characteristics
        primary_model = cluster.affected_models[0] if cluster.affected_models else ModelType.KRONOS
        
        # 1. LoRA rank mutation (for instability issues)
        if cluster.avg_error_magnitude > 0.05:
            current_rank = current_config.lora_rank
            new_rank = current_rank + 4 if current_rank < 16 else max(4, current_rank - 4)
            
            self.proposal_counter += 1
            candidates.append(MutationCandidate(
                candidate_id=f"lora_rank_{self.proposal_counter:04d}",
                mutation_type="lora_rank_adjustment",
                target_model=primary_model,
                description=f"Adjust LoRA rank from {current_rank} to {new_rank} for {primary_model.value}",
                config_changes={'lora_rank': new_rank},
                code_patch=None,
                addresses_clusters=[cluster.cluster_id],
                expected_improvement=f"Reduce forecast variance in {cluster.regimes[0].value} regime",
                rationale=f"High error magnitude ({cluster.avg_error_magnitude:.3f}) suggests underfitting"
            ))
        
        # 2. Regime-specific adapter (for regime mismatch)
        if len(cluster.regimes) == 1:
            regime = cluster.regimes[0]
            self.proposal_counter += 1
            candidates.append(MutationCandidate(
                candidate_id=f"regime_adapter_{self.proposal_counter:04d}",
                mutation_type="regime_adapter_addition",
                target_model=primary_model,
                description=f"Add dedicated adapter for {regime.value} regime",
                config_changes={'add_regime_adapter': regime.value},
                code_patch=None,
                addresses_clusters=[cluster.cluster_id],
                expected_improvement=f"Improve {primary_model.value} performance in {regime.value}",
                rationale=f"Cluster shows systematic failure in {regime.value} regime"
            ))
        
        # 3. Fusion weight rebalancing (for model disagreement)
        if len(cluster.affected_models) > 1:
            self.proposal_counter += 1
            candidates.append(MutationCandidate(
                candidate_id=f"fusion_rebalance_{self.proposal_counter:04d}",
                mutation_type="fusion_weight_rebalance",
                target_model=ModelType.KRONOS,  # System-wide
                description="Rebalance foundation model fusion weights",
                config_changes={'fusion_rebalance': True},
                code_patch=None,
                addresses_clusters=[cluster.cluster_id],
                expected_improvement="Better agreement between models",
                rationale="Multiple models failing suggests fusion weight issue"
            ))
        
        # 4. Head architecture mutation (for complex patterns)
        if cluster.count > 20 and cluster.avg_error_magnitude > 0.03:
            self.proposal_counter += 1
            candidates.append(MutationCandidate(
                candidate_id=f"head_arch_{self.proposal_counter:04d}",
                mutation_type="head_architecture_change",
                target_model=primary_model,
                description="Expand edge-after-cost head architecture",
                config_changes={'edge_head_hidden_dims': [512, 256, 128, 64]},
                code_patch=None,
                addresses_clusters=[cluster.cluster_id],
                expected_improvement="Better capture of complex edge patterns",
                rationale="Persistent high-error failures require more capacity"
            ))
        
        return candidates
    
    def _deduplicate_candidates(self, candidates: List[MutationCandidate]) -> List[MutationCandidate]:
        """Remove duplicate or very similar candidates."""
        seen = set()
        unique = []
        
        for c in candidates:
            key = (c.mutation_type, c.target_model, str(sorted(c.config_changes.items())))
            if key not in seen:
                seen.add(key)
                unique.append(c)
        
        return unique


class ChampionChallengerSystem:
    """
    Validates mutations through champion-challenger testing.
    
    Never replaces live model without explicit competition.
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        self.backtest_results: Dict[str, BacktestResult] = {}
        self.champions: Dict[str, EvolutionChampion] = {}
        self.baseline_version = "v1.0.0"
    
    def run_backtest(
        self,
        mutation: MutationCandidate,
        test_data: List[Dict[str, Any]],  # Historical market data
        baseline_results: Optional[BacktestResult] = None
    ) -> BacktestResult:
        """
        Run backtest for a mutation candidate.
        
        Args:
            mutation: Mutation to test
            test_data: Historical data for testing
            baseline_results: Optional baseline for comparison
            
        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Running backtest for mutation {mutation.candidate_id}")
        
        # Placeholder backtest implementation
        # In production, this would run actual model with mutation
        
        # Simulate performance metrics
        np.random.seed(hash(mutation.candidate_id) % 2**32)
        
        # Slightly better than baseline (for demonstration)
        baseline_ic = baseline_results.ic_mean if baseline_results else 0.05
        improvement = np.random.normal(0.02, 0.01)  # Mean 2% improvement
        
        ic_mean = baseline_ic + improvement
        ic_std = 0.15
        
        # Statistical significance test
        n_samples = len(test_data) if test_data else 1000
        t_stat = improvement / (ic_std / np.sqrt(n_samples))
        from math import erf
        p_value = 1 - 0.5 * (1 + erf(t_stat / np.sqrt(2)))
        
        result = BacktestResult(
            mutation_id=mutation.candidate_id,
            test_period=(datetime.now(), datetime.now()),  # Would be actual period
            total_return=0.15 + improvement,
            sharpe_ratio=1.2 + improvement * 10,
            max_drawdown=0.12 - improvement,
            win_rate=0.55 + improvement,
            ic_mean=ic_mean,
            ic_std=ic_std,
            directional_accuracy=0.58 + improvement,
            performance_by_regime={},  # Would populate with regime-specific results
            sample_count=n_samples,
            statistical_significance=p_value,
            baseline_ic=baseline_ic,
            improvement_vs_baseline=improvement
        )
        
        self.backtest_results[mutation.candidate_id] = result
        return result
    
    def evaluate_for_promotion(
        self,
        mutation: MutationCandidate,
        backtest_result: BacktestResult
    ) -> Tuple[bool, str]:
        """
        Evaluate if mutation should be promoted to champion status.
        
        Args:
            mutation: Mutation to evaluate
            backtest_result: Backtest results
            
        Returns:
            (should_promote, reason)
        """
        checks = []
        
        # 1. Statistical significance
        sig_threshold = self.config.significance_threshold if self.config else 0.05
        if backtest_result.statistical_significance > sig_threshold:
            checks.append(f"FAIL: Not statistically significant (p={backtest_result.statistical_significance:.3f})")
        else:
            checks.append(f"PASS: Statistically significant (p={backtest_result.statistical_significance:.3f})")
        
        # 2. Minimum samples
        min_samples = self.config.min_backtest_samples if self.config else 1000
        if backtest_result.sample_count < min_samples:
            checks.append(f"FAIL: Insufficient samples ({backtest_result.sample_count} < {min_samples})")
        else:
            checks.append(f"PASS: Sufficient samples ({backtest_result.sample_count})")
        
        # 3. IC improvement
        if backtest_result.improvement_vs_baseline <= 0:
            checks.append(f"FAIL: No IC improvement ({backtest_result.improvement_vs_baseline:.4f})")
        else:
            checks.append(f"PASS: IC improved by {backtest_result.improvement_vs_baseline:.4f}")
        
        # 4. Max drawdown
        max_dd = self.config.max_drawdown_tolerance if self.config else 0.15
        if backtest_result.max_drawdown > max_dd:
            checks.append(f"FAIL: Max drawdown too high ({backtest_result.max_drawdown:.2%} > {max_dd:.0%})")
        else:
            checks.append(f"PASS: Max drawdown acceptable ({backtest_result.max_drawdown:.2%})")
        
        # 5. Sharpe ratio
        if backtest_result.sharpe_ratio < 1.0:
            checks.append(f"WARNING: Low Sharpe ratio ({backtest_result.sharpe_ratio:.2f})")
        else:
            checks.append(f"PASS: Sharpe ratio good ({backtest_result.sharpe_ratio:.2f})")
        
        # Determine outcome
        failures = [c for c in checks if c.startswith("FAIL")]
        should_promote = len(failures) == 0
        
        reason = "\n".join(checks)
        if should_promote:
            reason = f"PROMOTION APPROVED:\n{reason}"
        else:
            reason = f"PROMOTION REJECTED:\n{reason}"
        
        return should_promote, reason
    
    def create_champion(
        self,
        mutations: List[MutationCandidate],
        backtest_results: List[BacktestResult]
    ) -> EvolutionChampion:
        """
        Create a champion from validated mutations.
        
        Args:
            mutations: Validated mutations to include
            backtest_results: Corresponding backtest results
            
        Returns:
            EvolutionChampion ready for promotion
        """
        champion_id = f"champion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Aggregate metrics
        avg_ic_improvement = np.mean([r.improvement_vs_baseline for r in backtest_results])
        avg_sharpe = np.mean([r.sharpe_ratio for r in backtest_results])
        max_dd = np.max([r.max_drawdown for r in backtest_results])
        
        # Determine regime coverage
        regimes_tested: Set[RegimeType] = set()
        for mutation in mutations:
            for cluster_id in mutation.addresses_clusters:
                # Extract regime from cluster ID
                for regime in RegimeType:
                    if regime.value in cluster_id:
                        regimes_tested.add(regime)
        
        coverage_score = len(regimes_tested) / len(RegimeType)
        
        champion = EvolutionChampion(
            champion_id=champion_id,
            baseline_version=self.baseline_version,
            mutation_proposals=[m.candidate_id for m in mutations],
            ic_improvement=avg_ic_improvement,
            sharpe_improvement=avg_sharpe - 1.2,  # Assuming baseline Sharpe of 1.2
            max_drawdown_improvement=-max_dd,  # Negative is improvement
            regimes_tested=list(regimes_tested),
            regime_coverage_score=coverage_score,
            rollback_available=True
        )
        
        self.champions[champion_id] = champion
        return champion


class ControlledEvolutionLayer:
    """
    Layer 4: Controlled Evolution Layer
    
    Orchestrates sandbox-only improvement generation.
    Manages the complete evolution pipeline: failure analysis → mutation generation →
    champion-challenger testing → champion creation.
    """
    
    def __init__(self, config: GETSConfig = None):
        self.config = config or GETSConfig()
        
        # Sub-components
        self.failure_analyzer = FailureAnalysisPipeline(config)
        self.mutation_engine = MutationProposalEngine(config)
        self.champion_system = ChampionChallengerSystem(config)
        
        # Sandboxed state (completely separate from live system)
        self.sandbox_path = Path(config.sandbox_path if config else "./gets_sandbox")
        self.sandbox_path.mkdir(parents=True, exist_ok=True)
        
        # Tracking
        self.active_mutations: Dict[str, MutationProposal] = {}
        self.pending_champions: List[EvolutionChampion] = []
        
        self._initialized = True
    
    def record_failure(
        self,
        model_type: ModelType,
        market_data: MarketData,
        predicted_return: float,
        realized_return: float,
        detected_regime: RegimeType,
        horizon: ForecastHorizon,
        diagnosis_issues: List[str]
    ):
        """Record a failure for pattern analysis (offline only)."""
        self.failure_analyzer.add_failure(
            model_type, market_data, predicted_return, realized_return,
            detected_regime, horizon, diagnosis_issues
        )
    
    def analyze_failures(self) -> List[FailureCluster]:
        """Analyze recorded failures and identify significant clusters."""
        significant_clusters = self.failure_analyzer.get_significant_clusters()
        
        logger.info(f"Found {len(significant_clusters)} significant failure clusters")
        for cluster in significant_clusters:
            logger.info(f"  - {cluster.cluster_id}: {cluster.count} failures")
        
        return significant_clusters
    
    def propose_mutations(self, current_config: GETSConfig) -> List[MutationCandidate]:
        """Generate mutation candidates to address failure patterns."""
        clusters = self.analyze_failures()
        
        if not clusters:
            logger.info("No significant failure patterns - no mutations needed")
            return []
        
        candidates = self.mutation_engine.generate_mutations(clusters, current_config)
        
        logger.info(f"Generated {len(candidates)} mutation candidates")
        for c in candidates:
            logger.info(f"  - {c.candidate_id}: {c.mutation_type} for {c.target_model.value}")
        
        return candidates
    
    def test_mutation(
        self,
        candidate: MutationCandidate,
        historical_data: List[Dict[str, Any]]
    ) -> MutationProposal:
        """
        Run champion-challenger testing for a mutation candidate.
        
        Args:
            candidate: Mutation to test
            historical_data: Historical data for backtesting
            
        Returns:
            MutationProposal with test results
        """
        logger.info(f"Testing mutation {candidate.candidate_id}")
        
        # Run backtest
        backtest_result = self.champion_system.run_backtest(
            candidate, historical_data
        )
        
        # Evaluate for promotion
        should_promote, evaluation_reason = self.champion_system.evaluate_for_promotion(
            candidate, backtest_result
        )
        
        # Create proposal
        proposal = MutationProposal(
            mutation_id=candidate.candidate_id,
            timestamp=datetime.now(),
            mutation_type=candidate.mutation_type,
            target_model=candidate.target_model,
            description=candidate.description,
            failure_pattern_addressed=cluster.cluster_id if candidate.addresses_clusters else "general",
            expected_improvement=candidate.expected_improvement,
            backtest_results={
                'ic_mean': backtest_result.ic_mean,
                'sharpe_ratio': backtest_result.sharpe_ratio,
                'max_drawdown': backtest_result.max_drawdown,
                'win_rate': backtest_result.win_rate,
                'sample_count': backtest_result.sample_count
            },
            paper_trading_results=None,  # Would populate after paper trading
            statistical_significance=backtest_result.statistical_significance,
            status="validated" if should_promote else "rejected"
        )
        
        logger.info(f"Mutation {candidate.candidate_id}: {proposal.status}")
        if not should_promote:
            logger.info(f"  Reason: {evaluation_reason}")
        
        self.active_mutations[proposal.mutation_id] = proposal
        return proposal
    
    def create_promotion_candidate(
        self,
        validated_mutations: List[MutationProposal]
    ) -> Optional[EvolutionChampion]:
        """
        Create a champion from validated mutations.
        
        This champion can be submitted to Layer 5 for final promotion approval.
        """
        if not validated_mutations:
            return None
        
        # Get original mutation candidates
        mutation_candidates = [
            MutationCandidate(
                candidate_id=m.mutation_id,
                mutation_type=m.mutation_type,
                target_model=m.target_model,
                description=m.description,
                config_changes={},  # Would retrieve from storage
                code_patch=None,
                addresses_clusters=[m.failure_pattern_addressed],
                expected_improvement=m.expected_improvement,
                rationale=""
            )
            for m in validated_mutations
        ]
        
        # Get backtest results
        backtest_results = [
            self.champion_system.backtest_results.get(m.mutation_id)
            for m in validated_mutations
        ]
        backtest_results = [r for r in backtest_results if r is not None]
        
        if not backtest_results:
            return None
        
        champion = self.champion_system.create_champion(
            mutation_candidates, backtest_results
        )
        
        self.pending_champions.append(champion)
        
        logger.info(f"Created champion {champion.champion_id}")
        logger.info(f"  IC improvement: {champion.ic_improvement:.4f}")
        logger.info(f"  Regime coverage: {champion.regime_coverage_score:.1%}")
        
        return champion
    
    def get_pending_champions(self) -> List[EvolutionChampion]:
        """Get champions awaiting Layer 5 promotion approval."""
        return list(self.pending_champions)
    
    def get_mutation_status(self, mutation_id: str) -> Optional[MutationProposal]:
        """Get status of a specific mutation."""
        return self.active_mutations.get(mutation_id)
    
    def save_sandbox_state(self):
        """Persist sandbox state to disk."""
        state = {
            'failure_clusters': [
                {
                    'cluster_id': c.cluster_id,
                    'failure_class': c.failure_class,
                    'count': c.count,
                    'affected_models': [m.value for m in c.affected_models],
                    'regimes': [r.value for r in c.regimes],
                    'horizons': [h.value for h in c.horizons]
                }
                for c in self.failure_analyzer.clusters.values()
            ],
            'active_mutations': {
                k: {
                    'mutation_id': v.mutation_id,
                    'status': v.status,
                    'backtest_results': v.backtest_results
                }
                for k, v in self.active_mutations.items()
            },
            'pending_champions': [
                {
                    'champion_id': c.champion_id,
                    'ic_improvement': c.ic_improvement,
                    'regime_coverage': c.regime_coverage_score,
                    'mutations': c.mutation_proposals
                }
                for c in self.pending_champions
            ]
        }
        
        state_file = self.sandbox_path / "evolution_state.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Saved sandbox state to {state_file}")
