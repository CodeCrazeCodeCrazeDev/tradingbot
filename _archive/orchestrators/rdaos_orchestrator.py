"""
RDAOS Orchestrator
==================
Research-Driven Alpha Operating System - Master Orchestrator

Coordinates all RDAOS components:
1. Research Ingestion
2. Hypothesis Extraction
3. Feature Synthesis
4. Sandbox Testing
5. Feature Ranking
6. Regime-Aware Meta Model
7. Live Deployment
8. Alpha Death Clock
9. Weakness Detection

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from .rdaos_core import (
    AlphaHorizon,
    AssetClass,
    FeatureFamily,
    HARD_LIMITS,
    Hypothesis,
    ProductionStatus,
    RegimeType,
    ResearchObject,
    TestingResult,
    generate_id
)

from .research_ingestion import ResearchIngestionEngine, create_ingestion_engine
from .hypothesis_extraction import HypothesisExtractionEngine, create_hypothesis_engine
from .feature_synthesis import FeatureSynthesisEngine, create_synthesis_engine
from .sandbox_testing import SandboxTestingEngine, create_testing_engine
from .feature_ranking import FeatureRankingEngine, create_ranking_engine
from .regime_meta_model import RegimeAwareMetaModel, MetaModelSignal, create_meta_model
from .live_deployment import LiveDeploymentEngine, DeploymentState, create_deployment_engine
from .alpha_death_clock import AlphaDeathClockManager, create_death_clock_manager
from .weakness_detection import WeaknessDetectionEngine, PerformanceSnapshot, create_weakness_engine

logger = logging.getLogger(__name__)


class RDAOSMode(Enum):
    """Operating modes for RDAOS"""
    RESEARCH = "research"      # Research and development only
    PAPER = "paper"            # Paper trading
    LIVE = "live"              # Live trading
    BACKTEST = "backtest"      # Backtesting mode


class PipelineStage(Enum):
    """Stages of the RDAOS pipeline"""
    INGESTION = "ingestion"
    HYPOTHESIS = "hypothesis"
    SYNTHESIS = "synthesis"
    TESTING = "testing"
    RANKING = "ranking"
    DEPLOYMENT = "deployment"
    MONITORING = "monitoring"


@dataclass
class RDAOSConfig:
    """Configuration for RDAOS"""
    mode: RDAOSMode = RDAOSMode.PAPER
    
    # Ingestion settings
    ingestion_interval_hours: int = 6
    max_papers_per_source: int = 50
    
    # Testing settings
    min_oos_ratio: float = 0.3
    min_regimes_for_promotion: int = 4
    transaction_cost_bps: float = 10.0
    slippage_bps: float = 5.0
    
    # Deployment settings
    max_deployed_families: int = 10
    initial_allocation_pct: float = 10.0
    max_total_allocation_pct: float = 100.0
    
    # Monitoring settings
    retest_interval_days: int = 30
    decay_check_interval_days: int = 7
    
    # Risk settings
    max_drawdown_pct: float = 20.0
    min_sharpe_for_deployment: float = 0.5


@dataclass
class RDAOSStatus:
    """Current status of RDAOS"""
    mode: RDAOSMode
    running: bool
    
    # Pipeline status
    current_stage: PipelineStage
    
    # Counts
    papers_ingested: int = 0
    hypotheses_extracted: int = 0
    features_synthesized: int = 0
    features_tested: int = 0
    features_promoted: int = 0
    features_deployed: int = 0
    
    # Performance
    total_allocation_pct: float = 0.0
    portfolio_sharpe: float = 0.0
    portfolio_drawdown: float = 0.0
    
    # Alerts
    active_alerts: int = 0
    features_near_decay: int = 0
    
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "running": self.running,
            "current_stage": self.current_stage.value,
            "papers_ingested": self.papers_ingested,
            "hypotheses_extracted": self.hypotheses_extracted,
            "features_synthesized": self.features_synthesized,
            "features_tested": self.features_tested,
            "features_promoted": self.features_promoted,
            "features_deployed": self.features_deployed,
            "total_allocation_pct": self.total_allocation_pct,
            "portfolio_sharpe": self.portfolio_sharpe,
            "portfolio_drawdown": self.portfolio_drawdown,
            "active_alerts": self.active_alerts,
            "features_near_decay": self.features_near_decay,
            "last_updated": self.last_updated.isoformat()
        }


class RDAOSOrchestrator:
    """
    Master orchestrator for the Research-Driven Alpha Operating System.
    
    This is the main entry point for RDAOS, coordinating:
    - Continuous research ingestion
    - Hypothesis extraction and validation
    - Feature synthesis and testing
    - Production deployment and monitoring
    - Alpha lifecycle management
    
    HARD LIMITS ENFORCED:
    - No strategies with unrealistic assumptions
    - No recommendations without cost/latency constraints
    - No overfitted or non-robust signals
    - No ignoring risk controls or capacity limits
    - No "AGI intuition" or "black box magic"
    """
    
    def __init__(self, config: Optional[RDAOSConfig] = None):
        self.config = config or RDAOSConfig()
        
        # Initialize all engines
        logger.info("Initializing RDAOS Orchestrator...")
        
        self.ingestion_engine = create_ingestion_engine({
            "db_path": "rdaos_research.db"
        })
        
        self.hypothesis_engine = create_hypothesis_engine({
            "min_confidence": 0.3
        })
        
        self.synthesis_engine = create_synthesis_engine({})
        
        self.testing_engine = create_testing_engine({
            "oos_ratio": self.config.min_oos_ratio,
            "min_regimes": self.config.min_regimes_for_promotion,
            "transaction_cost_bps": self.config.transaction_cost_bps,
            "slippage_bps": self.config.slippage_bps
        })
        
        self.ranking_engine = create_ranking_engine({
            "max_promoted": self.config.max_deployed_families
        })
        
        self.meta_model = create_meta_model({
            "max_drawdown": self.config.max_drawdown_pct
        })
        
        self.deployment_engine = create_deployment_engine({
            "initial_allocation_pct": self.config.initial_allocation_pct,
            "max_drawdown_pct": self.config.max_drawdown_pct,
            "min_sharpe_ratio": self.config.min_sharpe_for_deployment
        })
        
        self.death_clock_manager = create_death_clock_manager({
            "auto_retire_sharpe": HARD_LIMITS.AUTO_RETIRE_SHARPE_THRESHOLD
        })
        
        self.weakness_engine = create_weakness_engine({})
        
        # State
        self.running = False
        self.current_stage = PipelineStage.INGESTION
        
        # Storage
        self.research_objects: Dict[str, ResearchObject] = {}
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.feature_families: Dict[str, FeatureFamily] = {}
        self.testing_results: Dict[str, TestingResult] = {}
        
        # Candidate queue
        self.candidate_families: List[FeatureFamily] = []
        self.promoted_families: List[FeatureFamily] = []
        
        logger.info("RDAOS Orchestrator initialized")
    
    async def start(self):
        """Start the RDAOS system"""
        self.running = True
        logger.info(f"Starting RDAOS in {self.config.mode.value} mode")
        
        # Start background tasks
        if self.config.mode != RDAOSMode.BACKTEST:
            asyncio.create_task(self._research_loop())
            asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Stop the RDAOS system"""
        self.running = False
        logger.info("RDAOS stopped")
    
    async def _research_loop(self):
        """Background loop for continuous research ingestion"""
        while self.running:
            try:
                await self.run_research_pipeline()
                await asyncio.sleep(self.config.ingestion_interval_hours * 3600)
            except Exception as e:
                logger.error(f"Research loop error: {e}")
                await asyncio.sleep(300)  # Wait 5 min on error
    
    async def _monitoring_loop(self):
        """Background loop for monitoring deployed alphas"""
        while self.running:
            try:
                await self._check_deployed_alphas()
                await asyncio.sleep(3600)  # Check hourly
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(300)
    
    async def run_research_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete research pipeline.
        
        Stages:
        1. Ingest new research
        2. Extract hypotheses
        3. Synthesize features
        4. Test in sandbox
        5. Rank and promote
        """
        results = {
            "papers_ingested": 0,
            "hypotheses_extracted": 0,
            "features_synthesized": 0,
            "features_tested": 0,
            "features_promoted": 0
        }
        
        # Stage 1: Ingestion
        self.current_stage = PipelineStage.INGESTION
        logger.info("Stage 1: Research Ingestion")
        
        research_objects = await self.ingestion_engine.ingest_all_sources()
        results["papers_ingested"] = len(research_objects)
        
        for obj in research_objects:
            self.research_objects[obj.paper_id] = obj
        
        # Stage 2: Hypothesis Extraction
        self.current_stage = PipelineStage.HYPOTHESIS
        logger.info("Stage 2: Hypothesis Extraction")
        
        all_hypotheses = []
        for obj in research_objects:
            extraction_result = self.hypothesis_engine.extract_from_research(obj)
            
            if extraction_result.success:
                for hyp in extraction_result.hypotheses:
                    self.hypotheses[hyp.hypothesis_id] = hyp
                    all_hypotheses.append(hyp)
                
                # Update research object
                obj.hypotheses = extraction_result.hypotheses
            else:
                obj.production_status = ProductionStatus.REJECTED
                obj.rejection_reason = extraction_result.rejection_reason
        
        results["hypotheses_extracted"] = len(all_hypotheses)
        
        # Stage 3: Feature Synthesis
        self.current_stage = PipelineStage.SYNTHESIS
        logger.info("Stage 3: Feature Synthesis")
        
        families = self.synthesis_engine.synthesize_from_hypotheses(all_hypotheses)
        results["features_synthesized"] = len(families)
        
        for family in families:
            self.feature_families[family.family_id] = family
            self.candidate_families.append(family)
        
        logger.info(f"Research pipeline complete: {results}")
        
        return results
    
    async def run_testing_pipeline(
        self,
        data: pd.DataFrame,
        returns: pd.Series
    ) -> Dict[str, Any]:
        """
        Run testing pipeline on candidate features.
        
        Stages:
        4. Sandbox testing
        5. Ranking and promotion
        """
        results = {
            "features_tested": 0,
            "features_passed": 0,
            "features_promoted": 0
        }
        
        if not self.candidate_families:
            logger.info("No candidate families to test")
            return results
        
        # Stage 4: Sandbox Testing
        self.current_stage = PipelineStage.TESTING
        logger.info(f"Stage 4: Testing {len(self.candidate_families)} candidate families")
        
        testing_results = self.testing_engine.test_batch(
            self.candidate_families,
            data,
            returns
        )
        
        results["features_tested"] = len(testing_results)
        
        # Store results
        for family_id, result in testing_results.items():
            self.testing_results[family_id] = result
            
            if result.all_tests_passed:
                results["features_passed"] += 1
            else:
                # Update family status
                if family_id in self.feature_families:
                    self.feature_families[family_id].status = ProductionStatus.REJECTED
        
        # Stage 5: Ranking and Promotion
        self.current_stage = PipelineStage.RANKING
        logger.info("Stage 5: Ranking and Promotion")
        
        # Filter to passed families
        passed_families = [
            f for f in self.candidate_families
            if f.family_id in testing_results and testing_results[f.family_id].all_tests_passed
        ]
        
        if passed_families:
            promoted, rankings = self.ranking_engine.rank_and_promote(
                passed_families,
                testing_results
            )
            
            results["features_promoted"] = len(promoted)
            
            # Add to promoted list
            for family in promoted:
                if family not in self.promoted_families:
                    self.promoted_families.append(family)
        
        # Clear tested candidates
        self.candidate_families = [
            f for f in self.candidate_families
            if f.family_id not in testing_results
        ]
        
        logger.info(f"Testing pipeline complete: {results}")
        
        return results
    
    async def deploy_promoted_features(
        self,
        target_allocation_per_family: float = 10.0
    ) -> List[DeploymentState]:
        """Deploy promoted features to production"""
        self.current_stage = PipelineStage.DEPLOYMENT
        
        deployments = []
        
        for family in self.promoted_families:
            # Check if already deployed
            existing = self.deployment_engine.get_deployment_state(family.family_id)
            if existing:
                continue
            
            # Check total allocation
            current_total = self.deployment_engine.get_total_allocation()
            if current_total + target_allocation_per_family > self.config.max_total_allocation_pct:
                logger.warning("Max allocation reached, cannot deploy more")
                break
            
            # Get testing result
            testing_result = self.testing_results.get(family.family_id)
            if not testing_result:
                continue
            
            # Deploy
            state = self.deployment_engine.deploy(
                family,
                testing_result,
                target_allocation_per_family
            )
            
            if state:
                deployments.append(state)
                
                # Create death clock
                self.death_clock_manager.create_death_clock(
                    family,
                    testing_result.cost_adjusted_metrics.sharpe_ratio,
                    family.expected_decay_days
                )
                
                # Add to meta model
                self.meta_model.add_feature_family(family)
        
        logger.info(f"Deployed {len(deployments)} features")
        
        return deployments
    
    async def generate_signal(
        self,
        data: pd.DataFrame,
        returns: pd.Series,
        feature_values: Dict[str, float],
        current_drawdown: float = 0.0
    ) -> Optional[MetaModelSignal]:
        """Generate trading signal from meta model"""
        
        if not self.meta_model.get_active_family_count():
            logger.warning("No active features in meta model")
            return None
        
        # Get decay signals
        decay_signals = {}
        for family_id in feature_values.keys():
            metrics = self.death_clock_manager.get_decay_metrics(family_id)
            if metrics:
                decay_signals[family_id] = metrics.sharpe_decay_pct / 100
        
        # Generate signal
        signal = self.meta_model.generate_signal(
            data,
            returns,
            feature_values,
            current_drawdown,
            decay_signals
        )
        
        return signal
    
    async def update_daily_performance(
        self,
        family_id: str,
        daily_return: float,
        execution_success: bool = True,
        slippage_bps: float = 0.0
    ):
        """Update daily performance for a deployed feature"""
        
        # Update deployment
        state = self.deployment_engine.update_deployment(
            family_id,
            daily_return,
            execution_success
        )
        
        if state:
            # Update death clock
            self.death_clock_manager.update(
                family_id,
                state.live_sharpe
            )
            
            # Update meta model performance
            self.meta_model.update_performance(family_id, daily_return)
            
            # Record for weakness detection
            snapshot = PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                sharpe_ratio=state.live_sharpe,
                cumulative_return=state.cumulative_return,
                daily_return=daily_return,
                current_drawdown=state.current_drawdown,
                avg_slippage_bps=slippage_bps,
                execution_success_rate=1.0 if execution_success else 0.0
            )
            self.weakness_engine.record_performance(family_id, snapshot)
    
    async def _check_deployed_alphas(self):
        """Check health of deployed alphas"""
        self.current_stage = PipelineStage.MONITORING
        
        active_deployments = self.deployment_engine.get_active_deployments()
        
        for state in active_deployments:
            family_id = state.family_id
            family = self.feature_families.get(family_id)
            
            if not family:
                continue
            
            # Check for auto-retirement
            should_retire, reason = self.death_clock_manager.check_auto_retirement(
                family_id,
                self.meta_model.get_current_regime().primary_regime if self.meta_model.get_current_regime() else None,
                family
            )
            
            if should_retire:
                # Find replacement
                replacement = self.death_clock_manager.select_replacement(
                    family,
                    self.promoted_families,
                    self.meta_model.get_current_regime().primary_regime if self.meta_model.get_current_regime() else RegimeType.NORMAL,
                    [s.family_id for s in active_deployments]
                )
                
                # Retire
                self.death_clock_manager.retire(
                    family_id,
                    reason,
                    replacement.family_id if replacement else None
                )
                
                # Kill deployment
                self.deployment_engine.manual_kill(family_id, f"Auto-retired: {reason.value}")
                
                # Remove from meta model
                self.meta_model.remove_feature_family(family_id)
                
                # Deploy replacement if available
                if replacement:
                    testing_result = self.testing_results.get(replacement.family_id)
                    if testing_result:
                        self.deployment_engine.deploy(
                            replacement,
                            testing_result,
                            state.target_allocation_pct
                        )
                        self.meta_model.add_feature_family(replacement)
        
        # Check for features needing retest
        needs_retest = self.deployment_engine.get_families_needing_retest()
        if needs_retest:
            logger.info(f"{len(needs_retest)} features need re-testing")
    
    def get_status(self) -> RDAOSStatus:
        """Get current RDAOS status"""
        active_deployments = self.deployment_engine.get_active_deployments()
        
        return RDAOSStatus(
            mode=self.config.mode,
            running=self.running,
            current_stage=self.current_stage,
            papers_ingested=len(self.research_objects),
            hypotheses_extracted=len(self.hypotheses),
            features_synthesized=len(self.feature_families),
            features_tested=len(self.testing_results),
            features_promoted=len(self.promoted_families),
            features_deployed=len(active_deployments),
            total_allocation_pct=self.deployment_engine.get_total_allocation(),
            active_alerts=len(self.death_clock_manager.get_active_alerts()),
            features_near_decay=len(self.death_clock_manager.get_alphas_near_death(30))
        )
    
    def get_research_object(self, paper_id: str) -> Optional[ResearchObject]:
        """Get a research object by ID"""
        return self.research_objects.get(paper_id)
    
    def get_feature_family(self, family_id: str) -> Optional[FeatureFamily]:
        """Get a feature family by ID"""
        return self.feature_families.get(family_id)
    
    def get_testing_result(self, family_id: str) -> Optional[TestingResult]:
        """Get testing result for a family"""
        return self.testing_results.get(family_id)
    
    def get_deployment_state(self, family_id: str) -> Optional[DeploymentState]:
        """Get deployment state for a family"""
        return self.deployment_engine.get_deployment_state(family_id)
    
    def manual_kill_deployment(self, family_id: str, reason: str = "Manual"):
        """Manually kill a deployment"""
        self.deployment_engine.manual_kill(family_id, reason)
        self.meta_model.remove_feature_family(family_id)
    
    def export_research_object(self, paper_id: str) -> Optional[Dict]:
        """
        Export research object in the specified output format.
        
        Returns:
        {
          paper_id: "",
          alpha_source: "",
          horizon: "",
          asset_class: "",
          required_data: [],
          assumptions: [],
          failure_modes: [],
          expected_decay: "",
          capacity_limit: "",
          hypotheses: [],
          feature_families: [],
          testing_results: {},
          production_status: "rejected | candidate | promoted | deployed"
        }
        """
        obj = self.research_objects.get(paper_id)
        if not obj:
            return None
        
        return obj.to_dict()


def create_rdaos(config: Optional[RDAOSConfig] = None) -> RDAOSOrchestrator:
    """Factory function to create RDAOS orchestrator"""
    return RDAOSOrchestrator(config)


async def quick_start(config: Optional[Dict] = None) -> RDAOSOrchestrator:
    """Quick start RDAOS with default configuration"""
    rdaos_config = RDAOSConfig(
        mode=RDAOSMode(config.get("mode", "paper")) if config else RDAOSMode.PAPER
    )
    
    orchestrator = create_rdaos(rdaos_config)
    await orchestrator.start()
    
    return orchestrator
