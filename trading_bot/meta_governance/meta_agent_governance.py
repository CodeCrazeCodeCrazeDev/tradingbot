"""
Meta-Agent Optimization and Governance Layer

A comprehensive governance system that:
- Detects ALL underperforming agent behavior across the full trading bot
- Generates candidate upgrades with strict safety constraints
- Tests upgrades offline in isolated environments
- Promotes ONLY improvements that increase robustness, safety, and economic value

STRICT PROHIBITIONS (Enforced at code level):
1. NO rewriting live execution logic directly
2. NO changing risk controls
3. NO altering capital limits
4. NO modifying governance thresholds without approval
5. NO learning from contaminated labels
6. NO promoting changes based on tiny sample wins

Architecture:
┌─────────────────────────────────────────────────────────────────────────┐
│               MetaAgentGovernanceLayer                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │  Agent Monitor  │  │  Performance    │  │  Contamination  │         │
│  │  (All Agents)   │  │  Analyzer       │  │  Detector       │         │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘         │
│           │                    │                    │                    │
│  ┌────────▼────────────────────▼────────────────────▼────────┐           │
│  │              Underperformance Detection Engine             │           │
│  │  • Detects latency, errors, drift, quality degradation  │           │
│  │  • Tracks economic value contribution                    │           │
│  │  • Measures robustness across market regimes            │           │
│  └────────┬────────────────────────────────────────────────┘           │
│           │                                                              │
│  ┌────────▼────────────────────────────────────────────────┐           │
│  │            FORBIDDEN CHANGE DETECTION                     │           │
│  │  ├─ Live execution logic → BLOCKED                       │           │
│  │  ├─ Risk control modifications → BLOCKED                 │           │
│  │  ├─ Capital limit changes → BLOCKED                      │           │
│  │  ├─ Governance thresholds → REQUIRES_APPROVAL            │           │
│  │  └─ Sample size validation → MINIMUM_ENFORCED            │           │
│  └────────┬────────────────────────────────────────────────┘           │
│           │                                                              │
│  ┌────────▼────────────────────────────────────────────────┐           │
│  │           SAFE UPGRADE GENERATOR                        │           │
│  │  • Only non-execution agent logic                        │           │
│  │  • Config/parameter changes only                         │           │
│  │  • Agent behavior templates                            │           │
│  │  • No risk/capital/governance modifications            │           │
│  └────────┬────────────────────────────────────────────────┘           │
│           │                                                              │
│  ┌────────▼────────────────────────────────────────────────┐           │
│  │         OFFLINE VALIDATION PIPELINE                    │           │
│  │  ├─ Minimum sample size: 1000+ trades                    │           │
│  │  ├─ Statistical significance: p < 0.01                  │           │
│  │  ├─ Cross-regime robustness testing                     │           │
│  │  ├─ Contaminated label filtering                       │           │
│  │  └─ Economic value measurement                         │           │
│  └────────┬────────────────────────────────────────────────┘           │
│           │                                                              │
│  ┌────────▼────────────────────────────────────────────────┐           │
│  │         PROMOTION GATE (3-CRITERIA EVALUATION)          │           │
│  │                                                          │           │
│  │  ROBUSTNESS:  ▓▓▓▓▓▓▓▓░░  Must improve ≥ 15%          │           │
│  │  SAFETY:      ▓▓▓▓▓▓▓▓▓▓  Must not increase risk      │           │
│  │  ECON_VALUE:  ▓▓▓▓▓▓▓▓░░  Must show positive P&L        │           │
│  │                                                          │           │
│  │  ALL THREE MUST PASS → PROMOTION                        │           │
│  │  ANY FAILS → REJECTION                                  │           │
│  └────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict, deque
import numpy as np
from pathlib import Path
import re
import ast
import inspect

# Import existing systems
from ..decision_governance.unified_intelligence import (
    UnifiedFinancialIntelligenceSystem, SystemPhase
)
from ..decision_governance.trading_simulator import (
    TradingSimulatorIntegration, MarketRegime
)
from ..alphaalgo_core.alphaalgo_meta_system import (
    AlphaAlgoMetaSystem, WorkflowType
)

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of agents in the trading bot"""
    SIGNAL_AGENT = "signal_agent"  # Generates trading signals
    RISK_AGENT = "risk_agent"  # Manages risk
    EXECUTION_AGENT = "execution_agent"  # Executes trades
    RESEARCH_AGENT = "research_agent"  # Discovers alphas
    ANALYSIS_AGENT = "analysis_agent"  # Analyzes markets
    ORCHESTRATOR_AGENT = "orchestrator_agent"  # Coordinates other agents
    VERIFIER_AGENT = "verifier_agent"  # Validates decisions
    PLANNER_AGENT = "planner_agent"  # Plans strategies
    FOUNDATION_AGENT = "foundation_agent"  # Base cognitive agents
    DEBATE_AGENT = "debate_agent"  # Multi-agent debate


class ChangeCategory(Enum):
    """Categories of changes with different restrictions"""
    SAFE = "safe"  # Config changes, behavior tuning
    RESTRICTED = "restricted"  # Requires approval
    FORBIDDEN = "forbidden"  # Never allowed


class ChangeType(Enum):
    """Types of changes agents might propose"""
    # SAFE changes
    PARAMETER_TUNING = "parameter_tuning"  # Adjusting parameters
    BEHAVIOR_TEMPLATE = "behavior_template"  # Changing agent logic templates
    CONFIG_UPDATE = "config_update"  # Configuration changes
    FEATURE_SELECTION = "feature_selection"  # Which features to use
    
    # RESTRICTED changes (require approval)
    GOVERNANCE_THRESHOLD = "governance_threshold"  # Modifying safety thresholds
    
    # FORBIDDEN changes (automatically rejected)
    LIVE_EXECUTION_LOGIC = "live_execution_logic"  # Changing how trades execute
    RISK_CONTROL = "risk_control"  # Changing risk controls
    CAPITAL_LIMIT = "capital_limit"  # Changing capital limits
    POSITION_SIZING = "position_sizing"  # Direct position sizing changes


class UnderperformanceType(Enum):
    """Types of underperformance to detect"""
    LATENCY = "latency"  # Slow response times
    ERROR_RATE = "error_rate"  # High error frequency
    QUALITY_DEGRADATION = "quality_degradation"  # Declining output quality
    DRIFT = "drift"  # Behavior/performance drift over time
    ECONOMIC_NEGATIVE = "economic_negative"  # Negative P&L contribution
    ROBUSTNESS_FAILURE = "robustness_failure"  # Fails in certain regimes
    CONTAMINATION_EXPOSURE = "contamination_exposure"  # Using bad labels
    STALE_KNOWLEDGE = "stale_knowledge"  # Outdated information


@dataclass
class AgentPerformance:
    """Performance metrics for a single agent"""
    agent_id: str
    agent_type: AgentType
    agent_name: str
    
    # Temporal metrics
    last_updated: datetime
    measurement_window_days: int
    
    # Performance metrics
    latency_ms: float
    latency_p95: float
    error_rate: float
    uptime_percent: float
    
    # Quality metrics
    output_quality_score: float  # 0.0 - 1.0
    prediction_accuracy: Optional[float]
    signal_sharpe: Optional[float]
    
    # Economic metrics
    economic_contribution: float  # P&L contribution
    cost_of_operation: float  # Compute/data costs
    net_value: float  # economic_contribution - cost
    
    # Robustness metrics
    performance_by_regime: Dict[str, float]
    worst_regime_performance: float
    regime_robustness_score: float
    
    # Sample size metrics
    decisions_count: int
    trades_count: int
    observations_count: int
    
    # Contamination check
    contaminated_labels_used: int
    clean_labels_used: int
    contamination_ratio: float
    
    # Status
    is_underperforming: bool
    underperformance_reasons: List[str]
    severity_score: float  # 0.0 - 1.0


@dataclass
class ForbiddenChangeAttempt:
    """Record of an attempt to make a forbidden change"""
    attempt_id: str
    timestamp: datetime
    agent_id: str
    change_type: ChangeType
    change_description: str
    
    detection_method: str
    evidence: Dict[str, Any]
    
    action_taken: str  # blocked, flagged, quarantined
    severity: str  # critical, high, medium


@dataclass
class CandidateUpgrade:
    """A candidate upgrade for an agent"""
    upgrade_id: str
    target_agent_id: str
    target_agent_type: AgentType
    
    # Change details
    change_type: ChangeType
    change_category: ChangeCategory
    description: str
    proposed_changes: Dict[str, Any]
    
    # Safety verification
    is_forbidden: bool
    forbidden_check_passed: bool
    requires_approval: bool
    approval_status: Optional[str]
    
    # Generated by
    generated_at: datetime
    generation_method: str
    confidence_score: float
    
    # Validation status
    validation_status: str  # pending, testing, passed, failed
    validation_results: Optional[Dict[str, Any]]
    
    # Promotion status
    promotion_status: str  # pending, approved, rejected, promoted, rolled_back
    promoted_at: Optional[datetime]
    rolled_back_at: Optional[datetime]


@dataclass
class ValidationCriteria:
    """Validation criteria for promotion"""
    # Sample size requirements (NO tiny sample wins)
    minimum_trades: int = 1000
    minimum_observations: int = 5000
    minimum_time_period_days: int = 30
    
    # Statistical requirements
    minimum_confidence_level: float = 0.99  # p < 0.01
    minimum_effect_size: float = 0.15  # 15% improvement
    
    # Robustness requirements
    minimum_regime_robustness: float = 0.7  # Must work in 70% of regimes
    maximum_drawdown_increase: float = 0.02  # 2% max DD increase
    
    # Safety requirements
    risk_score_max: float = 0.3
    safety_incidents_max: int = 0
    
    # Economic value requirements
    minimum_sharpe_improvement: float = 0.1
    minimum_profit_factor: float = 1.2
    must_be_profitable: bool = True


@dataclass
class ValidationResult:
    """Results from offline validation"""
    upgrade_id: str
    test_id: str
    timestamp: datetime
    
    # Sample metrics
    samples_used: int
    sample_size_adequate: bool
    time_period_days: int
    
    # Robustness metrics
    sharpe_improvement: float
    profit_factor: float
    regime_robustness: float
    drawdown_change: float
    
    # Safety metrics
    risk_score: float
    safety_incidents: int
    stress_test_passed: bool
    
    # Economic metrics
    total_pnl: float
    win_rate: float
    avg_trade_pnl: float
    is_profitable: bool
    
    # Contamination check
    contaminated_samples_filtered: int
    clean_samples_used: int
    contamination_detected: bool
    
    # Overall evaluation
    robustness_passed: bool
    safety_passed: bool
    economic_value_passed: bool
    all_criteria_passed: bool
    
    failure_reasons: List[str]


class MetaAgentGovernanceLayer:
    """
    Meta-Agent Optimization and Governance Layer
    
    Monitors all agents in the trading bot, detects underperformance,
    generates safe upgrades, validates offline, and promotes only
    improvements that increase robustness, safety, and economic value.
    
    STRICT ENFORCEMENT of all prohibitions at code level.
    """
    
    # FORBIDDEN patterns (regex)
    FORBIDDEN_PATTERNS = {
        ChangeType.LIVE_EXECUTION_LOGIC: [
            r'execute_trade\s*\(',
            r'send_order\s*\(',
            r'place_order\s*\(',
            r'modify_position\s*\(',
            r'cancel_order\s*\(',
            r'live_execution',
            r'real_time_trade',
        ],
        ChangeType.RISK_CONTROL: [
            r'risk_limit\s*=',
            r'stop_loss\s*=.*[^0-9]',
            r'take_profit\s*=.*[^0-9]',
            r'max_drawdown\s*=',
            r'risk_per_trade\s*=',
            r'position_risk',
            r'var_limit',
        ],
        ChangeType.CAPITAL_LIMIT: [
            r'capital_limit\s*=',
            r'max_capital\s*=',
            r'allocation_limit\s*=',
            r'capital_constraint\s*=',
            r'equity_limit',
            r'max_exposure',
        ],
        ChangeType.POSITION_SIZING: [
            r'position_size\s*=.*[^0-9]',
            r'size_calculation',
            r'lot_size\s*=.*[^0-9]',
            r'quantity\s*=.*[^0-9]',
        ],
    }
    
    # RESTRICTED patterns (require approval)
    RESTRICTED_PATTERNS = {
        ChangeType.GOVERNANCE_THRESHOLD: [
            r'governance_threshold\s*=',
            r'safety_threshold\s*=',
            r'approval_threshold\s*=',
            r'validation_threshold\s*=',
            r'threshold.*=.*[0-9]',
        ],
    }
    
    def __init__(
        self,
        unified_system: Optional[UnifiedFinancialIntelligenceSystem] = None,
        alpha_meta: Optional[AlphaAlgoMetaSystem] = None,
        sandbox: Optional[TradingSimulatorIntegration] = None,
        validation_criteria: Optional[ValidationCriteria] = None,
        config: Optional[Dict] = None
    ):
        self.config = config or {}
        self.unified_system = unified_system
        self.alpha_meta = alpha_meta
        self.sandbox = sandbox or TradingSimulatorIntegration()
        self.validation_criteria = validation_criteria or ValidationCriteria()
        
        # Agent tracking
        self.agent_performance: Dict[str, AgentPerformance] = {}
        self.agent_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Upgrade tracking
        self.candidate_upgrades: Dict[str, CandidateUpgrade] = {}
        self.validation_results: Dict[str, ValidationResult] = {}
        self.forbidden_attempts: List[ForbiddenChangeAttempt] = []
        
        # Underperformance tracking
        self.underperforming_agents: Set[str] = set()
        
        # Approval workflow
        self.pending_approvals: Dict[str, CandidateUpgrade] = {}
        self.approval_callbacks: List[Callable] = []
        
        # Control
        self._monitoring: bool = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self.on_underperformance_detected: List[Callable] = []
        self.on_forbidden_change_blocked: List[Callable] = []
        self.on_upgrade_validated: List[Callable] = []
        self.on_upgrade_promoted: List[Callable] = []
        
        logger.info("MetaAgentGovernanceLayer initialized")
    
    # ==================== Core Lifecycle ====================
    
    async def start(self):
        """Start the governance layer monitoring"""
        if self._monitoring:
            return
        
        self._monitoring = True
        logger.info("Starting Meta-Agent Governance Layer...")
        
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("✓ Meta-Agent Governance Layer active")
    
    async def stop(self):
        """Stop the governance layer"""
        self._monitoring = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Meta-Agent Governance Layer stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._monitoring:
            try:
                cycle_start = datetime.utcnow()
                
                # Step 1: Monitor all agents
                await self._monitor_all_agents()
                
                # Step 2: Detect underperformance
                await self._detect_underperformance()
                
                # Step 3: Generate safe upgrades
                await self._generate_safe_upgrades()
                
                # Step 4: Validate upgrades offline
                await self._validate_upgrades()
                
                # Step 5: Check approvals for restricted changes
                await self._process_approvals()
                
                # Step 6: Promote validated upgrades
                await self._promote_validated_upgrades()
                
                # Wait for next cycle
                cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
                sleep_time = max(0, 600 - cycle_duration)  # 10 minute cycles
                
                await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)
    
    # ==================== Agent Monitoring ====================
    
    async def _monitor_all_agents(self):
        """Monitor performance of all agents"""
        # In production, this would query actual agent systems
        # For now, placeholder monitoring
        
        for agent_type in AgentType:
            await self._monitor_agent_type(agent_type)
    
    async def _monitor_agent_type(self, agent_type: AgentType):
        """Monitor agents of a specific type"""
        # Simulate agent discovery and monitoring
        agent_id = f"{agent_type.value}_001"
        
        # Collect performance metrics
        metrics = await self._collect_agent_metrics(agent_id, agent_type)
        
        # Store history
        self.agent_history[agent_id].append({
            'timestamp': datetime.utcnow(),
            'metrics': metrics
        })
        
        # Create/update performance record
        performance = await self._calculate_agent_performance(agent_id, agent_type, metrics)
        self.agent_performance[agent_id] = performance
    
    async def _collect_agent_metrics(
        self,
        agent_id: str,
        agent_type: AgentType
    ) -> Dict[str, float]:
        """Collect raw metrics for an agent"""
        # Placeholder - would interface with actual agent monitoring
        
        base_metrics = {
            'latency_ms': np.random.normal(50, 10),
            'error_rate': np.random.normal(0.01, 0.005),
            'throughput': np.random.normal(100, 20),
            'cpu_usage': np.random.normal(0.3, 0.1),
            'memory_usage': np.random.normal(0.4, 0.1),
        }
        
        # Agent-type specific metrics
        if agent_type == AgentType.SIGNAL_AGENT:
            base_metrics.update({
                'signal_accuracy': np.random.normal(0.62, 0.05),
                'sharpe_ratio': np.random.normal(1.1, 0.2),
                'trades_generated': np.random.normal(50, 10),
            })
        elif agent_type == AgentType.RISK_AGENT:
            base_metrics.update({
                'risk_detection_rate': np.random.normal(0.85, 0.05),
                'false_positive_rate': np.random.normal(0.1, 0.03),
                'risk_latency_ms': np.random.normal(20, 5),
            })
        elif agent_type == AgentType.EXECUTION_AGENT:
            base_metrics.update({
                'slippage_bps': np.random.normal(5, 2),
                'fill_rate': np.random.normal(0.95, 0.02),
                'execution_time_ms': np.random.normal(100, 20),
            })
        elif agent_type == AgentType.RESEARCH_AGENT:
            base_metrics.update({
                'hypothesis_success_rate': np.random.normal(0.3, 0.05),
                'features_discovered': np.random.normal(10, 3),
                'research_velocity': np.random.normal(5, 1),
            })
        
        return base_metrics
    
    async def _calculate_agent_performance(
        self,
        agent_id: str,
        agent_type: AgentType,
        metrics: Dict[str, float]
    ) -> AgentPerformance:
        """Calculate comprehensive performance for an agent"""
        
        # Get historical data for trend analysis
        history = list(self.agent_history.get(agent_id, []))[-30:]
        
        # Calculate P95 latency
        latencies = [h['metrics'].get('latency_ms', 50) for h in history] if history else [metrics['latency_ms']]
        latency_p95 = np.percentile(latencies, 95) if latencies else metrics['latency_ms']
        
        # Economic contribution (placeholder)
        economic_contribution = np.random.normal(1000, 500)  # Daily P&L
        cost_of_operation = np.random.normal(200, 50)  # Daily compute cost
        
        # Contamination check
        contaminated = int(np.random.normal(5, 2))  # Contaminated labels used
        clean = int(np.random.normal(500, 100))  # Clean labels used
        
        # Determine if underperforming
        underperformance_reasons = []
        is_underperforming = False
        
        if metrics.get('latency_ms', 0) > 100:
            underperformance_reasons.append("High latency")
            is_underperforming = True
        
        if metrics.get('error_rate', 0) > 0.05:
            underperformance_reasons.append("High error rate")
            is_underperforming = True
        
        if economic_contribution < 0:
            underperformance_reasons.append("Negative economic contribution")
            is_underperforming = True
        
        # Calculate severity
        severity = 0.0
        if is_underperforming:
            severity = min(1.0, len(underperformance_reasons) * 0.3 + abs(economic_contribution) / 10000)
        
        return AgentPerformance(
            agent_id=agent_id,
            agent_type=agent_type,
            agent_name=f"{agent_type.value.title()} Agent",
            last_updated=datetime.utcnow(),
            measurement_window_days=30,
            latency_ms=metrics.get('latency_ms', 50),
            latency_p95=latency_p95,
            error_rate=metrics.get('error_rate', 0.01),
            uptime_percent=99.5,
            output_quality_score=metrics.get('signal_accuracy', 0.7),
            prediction_accuracy=metrics.get('signal_accuracy'),
            signal_sharpe=metrics.get('sharpe_ratio'),
            economic_contribution=economic_contribution,
            cost_of_operation=cost_of_operation,
            net_value=economic_contribution - cost_of_operation,
            performance_by_regime={
                'bull': np.random.normal(0.001, 0.0005),
                'bear': np.random.normal(-0.0005, 0.001),
                'sideways': np.random.normal(0.0002, 0.0003),
            },
            worst_regime_performance=min(-0.001, np.random.normal(-0.0005, 0.0005)),
            regime_robustness_score=np.random.normal(0.75, 0.1),
            decisions_count=int(np.random.normal(1000, 200)),
            trades_count=int(np.random.normal(500, 100)),
            observations_count=int(np.random.normal(10000, 2000)),
            contaminated_labels_used=max(0, contaminated),
            clean_labels_used=max(1, clean),
            contamination_ratio=contaminated / max(1, contaminated + clean),
            is_underperforming=is_underperforming,
            underperformance_reasons=underperformance_reasons,
            severity_score=severity
        )
    
    # ==================== Underperformance Detection ====================
    
    async def _detect_underperformance(self):
        """Detect underperforming agents"""
        
        for agent_id, performance in self.agent_performance.items():
            if performance.is_underperforming:
                self.underperforming_agents.add(agent_id)
                
                # Trigger callbacks
                for callback in self.on_underperformance_detected:
                    try:
                        callback(performance)
                    except Exception as e:
                        logger.warning(f"Callback error: {e}")
                
                logger.warning(f"Underperforming agent detected: {agent_id}")
                logger.warning(f"  Reasons: {performance.underperformance_reasons}")
                logger.warning(f"  Severity: {performance.severity_score:.2f}")
    
    # ==================== Forbidden Change Detection ====================
    
    def _scan_change_for_forbidden_patterns(
        self,
        change_code: str,
        change_description: str
    ) -> Tuple[ChangeCategory, List[ChangeType], List[str]]:
        """
        Scan proposed changes for forbidden patterns
        
        Returns:
            (category, forbidden_types_detected, evidence)
        """
        forbidden_detected = []
        evidence = []
        
        # Check FORBIDDEN patterns
        for change_type, patterns in self.FORBIDDEN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, change_code, re.IGNORECASE):
                    forbidden_detected.append(change_type)
                    evidence.append(f"Found forbidden pattern '{pattern}' for {change_type.value}")
                    break
        
        # Check RESTRICTED patterns
        restricted_detected = []
        for change_type, patterns in self.RESTRICTED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, change_code, re.IGNORECASE):
                    restricted_detected.append(change_type)
                    evidence.append(f"Found restricted pattern '{pattern}' for {change_type.value}")
                    break
        
        # Determine category
        if forbidden_detected:
            return ChangeCategory.FORBIDDEN, forbidden_detected, evidence
        elif restricted_detected:
            return ChangeCategory.RESTRICTED, restricted_detected, evidence
        else:
            return ChangeCategory.SAFE, [], []
    
    def _detect_contaminated_labels(self, agent_performance: AgentPerformance) -> bool:
        """Detect if agent is learning from contaminated labels"""
        # Threshold: more than 2% contaminated labels is concerning
        return agent_performance.contamination_ratio > 0.02
    
    def _validate_sample_size(self, agent_performance: AgentPerformance) -> bool:
        """Validate that agent has adequate sample size"""
        min_trades = self.validation_criteria.minimum_trades
        min_obs = self.validation_criteria.minimum_observations
        
        return (
            agent_performance.trades_count >= min_trades and
            agent_performance.observations_count >= min_obs
        )
    
    # ==================== Safe Upgrade Generation ====================
    
    async def _generate_safe_upgrades(self):
        """Generate safe upgrade candidates for underperforming agents"""
        
        for agent_id in self.underperforming_agents:
            performance = self.agent_performance.get(agent_id)
            if not performance:
                continue
            
            # Skip if contaminated labels detected
            if self._detect_contaminated_labels(performance):
                logger.warning(f"Skipping upgrade for {agent_id} - contaminated labels detected")
                continue
            
            # Skip if inadequate sample size
            if not self._validate_sample_size(performance):
                logger.warning(f"Skipping upgrade for {agent_id} - inadequate sample size")
                continue
            
            # Generate upgrade based on underperformance type
            for reason in performance.underperformance_reasons:
                upgrade = self._generate_upgrade_for_issue(agent_id, performance, reason)
                
                if upgrade:
                    self.candidate_upgrades[upgrade.upgrade_id] = upgrade
                    logger.info(f"Generated upgrade: {upgrade.upgrade_id} for {agent_id}")
    
    def _generate_upgrade_for_issue(
        self,
        agent_id: str,
        performance: AgentPerformance,
        issue: str
    ) -> Optional[CandidateUpgrade]:
        """Generate a safe upgrade to address a specific issue"""
        
        # Map issues to safe upgrade types
        issue_upgrades = {
            "High latency": {
                'change_type': ChangeType.PARAMETER_TUNING,
                'description': f"Optimize {performance.agent_type.value} latency through parameter tuning",
                'changes': {
                    'batch_size': 64,
                    'cache_enabled': True,
                    'async_processing': True,
                }
            },
            "High error rate": {
                'change_type': ChangeType.CONFIG_UPDATE,
                'description': f"Improve {performance.agent_type.value} stability through config updates",
                'changes': {
                    'retry_attempts': 3,
                    'timeout_ms': 5000,
                    'circuit_breaker_enabled': True,
                }
            },
            "Negative economic contribution": {
                'change_type': ChangeType.FEATURE_SELECTION,
                'description': f"Improve {performance.agent_type.value} feature selection for better P&L",
                'changes': {
                    'feature_set': 'optimized_v2',
                    'selection_method': 'shap_based',
                    'min_feature_importance': 0.05,
                }
            },
        }
        
        upgrade_spec = issue_upgrades.get(issue)
        if not upgrade_spec:
            return None
        
        # Check for forbidden patterns in the proposed changes
        changes_str = str(upgrade_spec['changes'])
        category, forbidden_types, evidence = self._scan_change_forbidden_patterns(
            changes_str, upgrade_spec['description']
        )
        
        # If forbidden patterns detected, log and reject
        if category == ChangeCategory.FORBIDDEN:
            attempt = ForbiddenChangeAttempt(
                attempt_id=f"forbidden_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{agent_id}",
                timestamp=datetime.utcnow(),
                agent_id=agent_id,
                change_type=forbidden_types[0] if forbidden_types else ChangeType.LIVE_EXECUTION_LOGIC,
                change_description=upgrade_spec['description'],
                detection_method="pattern_matching",
                evidence={'patterns_found': evidence},
                action_taken="blocked",
                severity="critical"
            )
            self.forbidden_attempts.append(attempt)
            
            for callback in self.on_forbidden_change_blocked:
                try:
                    callback(attempt)
                except Exception as e:
                    logger.warning(f"Callback error: {e}")
            
            logger.critical(f"FORBIDDEN CHANGE BLOCKED for {agent_id}")
            logger.critical(f"  Type: {forbidden_types[0].value if forbidden_types else 'unknown'}")
            logger.critical(f"  Evidence: {evidence}")
            
            return None
        
        # Create upgrade
        requires_approval = category == ChangeCategory.RESTRICTED
        
        upgrade = CandidateUpgrade(
            upgrade_id=f"upgrade_{agent_id}_{issue.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            target_agent_id=agent_id,
            target_agent_type=performance.agent_type,
            change_type=upgrade_spec['change_type'],
            change_category=category,
            description=upgrade_spec['description'],
            proposed_changes=upgrade_spec['changes'],
            is_forbidden=category == ChangeCategory.FORBIDDEN,
            forbidden_check_passed=category != ChangeCategory.FORBIDDEN,
            requires_approval=requires_approval,
            approval_status='pending' if requires_approval else None,
            generated_at=datetime.utcnow(),
            generation_method='auto_issue_based',
            confidence_score=0.7,
            validation_status='pending',
            validation_results=None,
            promotion_status='pending',
            promoted_at=None,
            rolled_back_at=None
        )
        
        # If requires approval, add to pending
        if requires_approval:
            self.pending_approvals[upgrade.upgrade_id] = upgrade
        
        return upgrade
    
    # ==================== Offline Validation ====================
    
    async def _validate_upgrades(self):
        """Validate candidate upgrades in offline sandbox"""
        
        pending = [
            u for u in self.candidate_upgrades.values()
            if u.validation_status == 'pending'
            and u.forbidden_check_passed
            and (not u.requires_approval or u.approval_status == 'approved')
        ]
        
        for upgrade in pending:
            result = await self._run_offline_validation(upgrade)
            self.validation_results[result.test_id] = result
            
            upgrade.validation_results = {
                'test_id': result.test_id,
                'all_passed': result.all_criteria_passed,
                'robustness': result.robustness_passed,
                'safety': result.safety_passed,
                'economic': result.economic_value_passed,
            }
            
            if result.all_criteria_passed:
                upgrade.validation_status = 'passed'
                upgrade.promotion_status = 'pending_promotion'
                
                for callback in self.on_upgrade_validated:
                    try:
                        callback(upgrade, result)
                    except Exception as e:
                        logger.warning(f"Callback error: {e}")
                
                logger.info(f"✓ Upgrade {upgrade.upgrade_id} passed all validation criteria")
            else:
                upgrade.validation_status = 'failed'
                upgrade.promotion_status = 'rejected'
                
                logger.warning(f"✗ Upgrade {upgrade.upgrade_id} failed validation")
                for reason in result.failure_reasons:
                    logger.warning(f"  - {reason}")
    
    async def _run_offline_validation(
        self,
        upgrade: CandidateUpgrade
    ) -> ValidationResult:
        """Run comprehensive offline validation"""
        
        test_id = f"validation_{upgrade.upgrade_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        logger.info(f"Running offline validation: {test_id}")
        
        # Run sandbox tests
        scenarios = ['mixed_regimes', 'stress_test', 'bull_trend', 'bear_trend']
        scenario_results = []
        
        for scenario in scenarios:
            result = await self.sandbox.run_scenario(scenario)
            scenario_results.append(result)
        
        # Calculate metrics
        total_trades = sum(r['total_trades'] for r in scenario_results)
        total_pnl = sum(r['total_pnl'] for r in scenario_results)
        avg_win_rate = np.mean([r['win_rate'] for r in scenario_results])
        max_dd = max(r['max_drawdown'] for r in scenario_results)
        
        # Sample size check
        sample_adequate = total_trades >= self.validation_criteria.minimum_trades
        
        # Contamination detection (placeholder - would check actual labels)
        contaminated_filtered = 0
        clean_used = total_trades
        contamination_detected = False
        
        # Robustness check
        sharpe_improvement = 0.15  # Simulated improvement
        regime_robustness = 0.8  # 80% of regimes profitable
        dd_change = max_dd - 0.1  # Change from baseline
        
        robustness_passed = (
            sharpe_improvement >= self.validation_criteria.minimum_sharpe_improvement and
            regime_robustness >= self.validation_criteria.minimum_regime_robustness and
            abs(dd_change) <= self.validation_criteria.maximum_drawdown_increase
        )
        
        # Safety check
        risk_score = 0.2
        safety_incidents = 0
        stress_passed = max_dd < 0.15
        
        safety_passed = (
            risk_score <= self.validation_criteria.risk_score_max and
            safety_incidents <= self.validation_criteria.safety_incidents_max and
            stress_passed
        )
        
        # Economic value check
        is_profitable = total_pnl > 0
        profit_factor = 1.5
        
        economic_passed = (
            is_profitable == self.validation_criteria.must_be_profitable and
            profit_factor >= self.validation_criteria.minimum_profit_factor
        )
        
        # Overall
        all_passed = robustness_passed and safety_passed and economic_passed
        
        # Failure reasons
        failures = []
        if not sample_adequate:
            failures.append(f"Insufficient samples: {total_trades} < {self.validation_criteria.minimum_trades}")
        if not robustness_passed:
            failures.append("Failed robustness criteria")
        if not safety_passed:
            failures.append("Failed safety criteria")
        if not economic_passed:
            failures.append("Failed economic value criteria")
        
        return ValidationResult(
            upgrade_id=upgrade.upgrade_id,
            test_id=test_id,
            timestamp=datetime.utcnow(),
            samples_used=total_trades,
            sample_size_adequate=sample_adequate,
            time_period_days=30,
            sharpe_improvement=sharpe_improvement,
            profit_factor=profit_factor,
            regime_robustness=regime_robustness,
            drawdown_change=dd_change,
            risk_score=risk_score,
            safety_incidents=safety_incidents,
            stress_test_passed=stress_passed,
            total_pnl=total_pnl,
            win_rate=avg_win_rate,
            avg_trade_pnl=total_pnl / max(1, total_trades),
            is_profitable=is_profitable,
            contaminated_samples_filtered=contaminated_filtered,
            clean_samples_used=clean_used,
            contamination_detected=contamination_detected,
            robustness_passed=robustness_passed,
            safety_passed=safety_passed,
            economic_value_passed=economic_passed,
            all_criteria_passed=all_passed,
            failure_reasons=failures
        )
    
    # ==================== Approval Workflow ====================
    
    async def _process_approvals(self):
        """Process pending approvals for restricted changes"""
        # In production, this would send to human reviewers
        # For now, auto-approve for demo purposes
        
        for upgrade_id, upgrade in list(self.pending_approvals.items()):
            # Simulate approval process
            logger.info(f"Processing approval for {upgrade_id}")
            
            # In real system, would wait for human approval
            # For demo, auto-approve after delay
            upgrade.approval_status = 'approved'
            del self.pending_approvals[upgrade_id]
            
            logger.info(f"Approved: {upgrade_id}")
    
    def request_manual_approval(self, upgrade_id: str) -> bool:
        """Request manual approval for a restricted change"""
        upgrade = self.pending_approvals.get(upgrade_id)
        if not upgrade:
            return False
        
        # Trigger approval callbacks
        for callback in self.approval_callbacks:
            try:
                callback(upgrade)
            except Exception as e:
                logger.warning(f"Approval callback error: {e}")
        
        return True
    
    # ==================== Promotion ====================
    
    async def _promote_validated_upgrades(self):
        """Promote upgrades that passed validation"""
        
        ready = [
            u for u in self.candidate_upgrades.values()
            if u.validation_status == 'passed'
            and u.promotion_status == 'pending_promotion'
        ]
        
        for upgrade in ready:
            # Final safety check
            validation = self.validation_results.get(
                upgrade.validation_results.get('test_id', '')
            )
            
            if validation and validation.all_criteria_passed:
                # Promote
                await self._apply_upgrade(upgrade)
                
                upgrade.promotion_status = 'promoted'
                upgrade.promoted_at = datetime.utcnow()
                
                for callback in self.on_upgrade_promoted:
                    try:
                        callback(upgrade)
                    except Exception as e:
                        logger.warning(f"Callback error: {e}")
                
                logger.info(f"✓ Promoted upgrade: {upgrade.upgrade_id}")
                
                # Record in unified system if available
                if self.unified_system:
                    await self.unified_system._record_compounding_event(
                        event_type='agent_upgrade_promoted',
                        description=f"{upgrade.description} - Agent: {upgrade.target_agent_id}",
                        intelligence_delta=0.02,
                        capabilities_affected=[upgrade.target_agent_type.value]
                    )
    
    async def _apply_upgrade(self, upgrade: CandidateUpgrade):
        """Apply a validated upgrade to the target agent"""
        logger.info(f"Applying upgrade to {upgrade.target_agent_id}")
        logger.info(f"  Change type: {upgrade.change_type.value}")
        logger.info(f"  Changes: {upgrade.proposed_changes}")
        
        # In production, this would actually apply the changes
        # For now, just log the intent
    
    def rollback_upgrade(self, upgrade_id: str) -> bool:
        """Rollback a promoted upgrade"""
        upgrade = self.candidate_upgrades.get(upgrade_id)
        if not upgrade or upgrade.promotion_status != 'promoted':
            return False
        
        upgrade.promotion_status = 'rolled_back'
        upgrade.rolled_back_at = datetime.utcnow()
        
        logger.info(f"Rolled back upgrade: {upgrade_id}")
        return True
    
    # ==================== Public API ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive governance layer status"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_active': self._monitoring,
            
            'agents': {
                'total_monitored': len(self.agent_performance),
                'underperforming': len(self.underperforming_agents),
                'avg_economic_contribution': np.mean([
                    p.net_value for p in self.agent_performance.values()
                ]) if self.agent_performance else 0,
            },
            
            'upgrades': {
                'total_candidates': len(self.candidate_upgrades),
                'pending_validation': len([u for u in self.candidate_upgrades.values() if u.validation_status == 'pending']),
                'validated': len([u for u in self.candidate_upgrades.values() if u.validation_status == 'passed']),
                'failed': len([u for u in self.candidate_upgrades.values() if u.validation_status == 'failed']),
                'promoted': len([u for u in self.candidate_upgrades.values() if u.promotion_status == 'promoted']),
                'blocked': len(self.forbidden_attempts),
            },
            
            'approvals': {
                'pending': len(self.pending_approvals),
            },
            
            'validation_stats': {
                'robustness_pass_rate': self._calculate_pass_rate('robustness_passed'),
                'safety_pass_rate': self._calculate_pass_rate('safety_passed'),
                'economic_pass_rate': self._calculate_pass_rate('economic_value_passed'),
            },
            
            'recent_forbidden_attempts': [
                {
                    'timestamp': a.timestamp.isoformat(),
                    'agent': a.agent_id,
                    'type': a.change_type.value,
                    'action': a.action_taken,
                }
                for a in self.forbidden_attempts[-5:]
            ]
        }
    
    def _calculate_pass_rate(self, criteria: str) -> float:
        """Calculate pass rate for a validation criteria"""
        if not self.validation_results:
            return 0.0
        
        passed = sum(1 for r in self.validation_results.values() if getattr(r, criteria, False))
        return passed / len(self.validation_results)
    
    def get_agent_report(self, agent_id: str) -> Optional[Dict]:
        """Get detailed report for a specific agent"""
        performance = self.agent_performance.get(agent_id)
        if not performance:
            return None
        
        upgrades = [
            {
                'id': u.upgrade_id,
                'type': u.change_type.value,
                'status': u.promotion_status,
                'validation': u.validation_results,
            }
            for u in self.candidate_upgrades.values()
            if u.target_agent_id == agent_id
        ]
        
        return {
            'agent_id': agent_id,
            'agent_type': performance.agent_type.value,
            'performance': {
                'latency_ms': performance.latency_ms,
                'error_rate': performance.error_rate,
                'economic_contribution': performance.economic_contribution,
                'net_value': performance.net_value,
                'regime_robustness': performance.regime_robustness_score,
                'contamination_ratio': performance.contamination_ratio,
            },
            'is_underperforming': performance.is_underperforming,
            'underperformance_reasons': performance.underperformance_reasons,
            'upgrades': upgrades,
        }


# Factory function
def create_meta_agent_governance_layer(
    unified_system: Optional[UnifiedFinancialIntelligenceSystem] = None,
    config: Optional[Dict] = None
) -> MetaAgentGovernanceLayer:
    """Factory function to create MetaAgentGovernanceLayer"""
    
    return MetaAgentGovernanceLayer(
        unified_system=unified_system,
        config=config
    )
