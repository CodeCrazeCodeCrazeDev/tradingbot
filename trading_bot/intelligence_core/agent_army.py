"""
Agent Army - 60 Specialized Research Agents
=============================================

An army of 60 specialized AI agents working together as a swarm
for the Intelligence Core quant research lab.

ORGANIZATION:
- 6 Brigades (10 agents each)
- Each brigade has a specific research domain
- Agents can communicate, vote, and reach consensus
- Reputation system tracks agent performance

BRIGADE STRUCTURE:
1. HYPOTHESIS BRIGADE (Agents 1-10) - Generate and test hypotheses
2. MARKET BRIGADE (Agents 11-20) - Market analysis and regime detection
3. RISK BRIGADE (Agents 21-30) - Risk assessment and management
4. STRATEGY BRIGADE (Agents 31-40) - Strategy development and optimization
5. DATA BRIGADE (Agents 41-50) - Data validation and quality
6. AUDIT BRIGADE (Agents 51-60) - Verification and compliance
"""

import logging
import hashlib
import threading
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent"""
    IDLE = "idle"
    WORKING = "working"
    VOTING = "voting"
    CONSENSUS = "consensus"
    DISABLED = "disabled"


class AgentType(Enum):
    """Types of agents"""
    # HYPOTHESIS BRIGADE (1-10)
    PATTERN_HUNTER = "pattern_hunter"           # Agent 1
    ANOMALY_DETECTOR = "anomaly_detector"       # Agent 2
    CAUSE_ANALYZER = "cause_analyzer"          # Agent 3
    EFFECT_PREDICTOR = "effect_predictor"      # Agent 4
    MECHANISM_EXPLORER = "mechanism_explorer"  # Agent 5
    BOUNDARY_MAPPER = "boundary_mapper"        # Agent 6
    KILL_CONDITION_DESIGNER = "kill_designer"  # Agent 7
    PREDICTION_FORMULATOR = "prediction_formulator"  # Agent 8
    HYPOTHESIS_INTEGRATOR = "hypothesis_integrator"  # Agent 9
    HYPOTHESIS_VALIDATOR = "hypothesis_validator"    # Agent 10
    
    # MARKET BRIGADE (11-20)
    REGIME_SPOTTER = "regime_spotter"          # Agent 11
    TREND_TRACKER = "trend_tracker"            # Agent 12
    VOLATILITY_ASSESSOR = "volatility_assessor"    # Agent 13
    LIQUIDITY_MAPPER = "liquidity_mapper"       # Agent 14
    ORDERFLOW_ANALYZER = "orderflow_analyzer"   # Agent 15
    SENTIMENT_GAUGER = "sentiment_gauger"       # Agent 16
    CORRELATION_TRACKER = "correlation_tracker"    # Agent 17
    MICROSTRUCTURE_EXPERT = "microstructure_expert"  # Agent 18
    SESSION_ANALYZER = "session_analyzer"       # Agent 19
    MARKET_MEMORY_KEEPER = "market_memory_keeper"    # Agent 20
    
    # RISK BRIGADE (21-30)
    DRAWDOWN_GUARDIAN = "drawdown_guardian"     # Agent 21
    TAIL_RISK_HUNTER = "tail_risk_hunter"       # Agent 22
    POSITION_SIZER = "position_sizer"           # Agent 23
    LEVERAGE_CONTROLLER = "leverage_controller"  # Agent 24
    CORRELATION_MONITOR = "correlation_monitor"   # Agent 25
    STRESS_TESTER = "stress_tester"             # Agent 26
    SCENARIO_PLANNER = "scenario_planner"        # Agent 27
    BLACK_SWAN_WATCHER = "black_swan_watcher"    # Agent 28
    RISK_BUDGET_ALLOCATOR = "risk_budget_allocator"  # Agent 29
    CIRCUIT_BREAKER = "circuit_breaker"          # Agent 30
    
    # STRATEGY BRIGADE (31-40)
    ENTRY_OPTIMIZER = "entry_optimizer"          # Agent 31
    EXIT_OPTIMIZER = "exit_optimizer"          # Agent 32
    STOP_LOSS_DESIGNER = "stop_loss_designer"    # Agent 33
    TAKE_PROFIT_PLANNER = "take_profit_planner"  # Agent 34
    TIMING_SPECIALIST = "timing_specialist"     # Agent 35
    EXECUTION_PLANNER = "execution_planner"      # Agent 36
    PYRAMIDING_CONTROLLER = "pyramiding_controller"  # Agent 37
    SCALE_IN_SPECIALIST = "scale_in_specialist"   # Agent 38
    SCALE_OUT_PLANNER = "scale_out_planner"       # Agent 39
    STRATEGY_COMPOSER = "strategy_composer"       # Agent 40
    
    # DATA BRIGADE (41-50)
    DATA_VALIDATOR = "data_validator"            # Agent 41
    GAP_DETECTOR = "gap_detector"               # Agent 42
    OUTLIER_HUNTER = "outlier_hunter"           # Agent 43
    LOOKAHEAD_CHECKER = "lookahead_checker"     # Agent 44
    SURVIVORSHIP_AUDITOR = "survivorship_auditor"  # Agent 45
    STATIONARITY_TESTER = "stationarity_tester"   # Agent 46
    SAMPLE_SIZE_ANALYZER = "sample_size_analyzer"  # Agent 47
    MULTIPLE_TESTING_GUARD = "multiple_testing_guard"  # Agent 48
    DATA_QUALITY_INSPECTOR = "data_quality_inspector"  # Agent 49
    SYNTHETIC_DATA_GENERATOR = "synthetic_data_generator"  # Agent 50
    
    # AUDIT BRIGADE (51-60)
    OVERFITTING_DETECTIVE = "overfitting_detective"  # Agent 51
    P_HACKING_POLICE = "p_hacking_police"            # Agent 52
    CURVE_FITTING_HUNTER = "curve_fitting_hunter"    # Agent 53
    GOVERNANCE_ENFORCER = "governance_enforcer"      # Agent 54
    LOGGING_INSPECTOR = "logging_inspector"        # Agent 55
    REPRODUCIBILITY_CHECKER = "reproducibility_checker"  # Agent 56
    BIAS_DETECTOR = "bias_detector"                # Agent 57
    ASSUMPTION_VALIDATOR = "assumption_validator"  # Agent 58
    RESULT_VERIFIER = "result_verifier"            # Agent 59
    CHIEF_AUDIT_OFFICER = "chief_audit_officer"    # Agent 60 (Commander)


class Brigade(Enum):
    """Brigade assignments"""
    HYPOTHESIS = "hypothesis"
    MARKET = "market"
    RISK = "risk"
    STRATEGY = "strategy"
    DATA = "data"
    AUDIT = "audit"


# AGENT BRIGADE MAPPING
AGENT_BRIGADES = {
    # HYPOTHESIS BRIGADE
    AgentType.PATTERN_HUNTER: Brigade.HYPOTHESIS,
    AgentType.ANOMALY_DETECTOR: Brigade.HYPOTHESIS,
    AgentType.CAUSE_ANALYZER: Brigade.HYPOTHESIS,
    AgentType.EFFECT_PREDICTOR: Brigade.HYPOTHESIS,
    AgentType.MECHANISM_EXPLORER: Brigade.HYPOTHESIS,
    AgentType.BOUNDARY_MAPPER: Brigade.HYPOTHESIS,
    AgentType.KILL_CONDITION_DESIGNER: Brigade.HYPOTHESIS,
    AgentType.PREDICTION_FORMULATOR: Brigade.HYPOTHESIS,
    AgentType.HYPOTHESIS_INTEGRATOR: Brigade.HYPOTHESIS,
    AgentType.HYPOTHESIS_VALIDATOR: Brigade.HYPOTHESIS,
    
    # MARKET BRIGADE
    AgentType.REGIME_SPOTTER: Brigade.MARKET,
    AgentType.TREND_TRACKER: Brigade.MARKET,
    AgentType.VOLATILITY_ASSESSOR: Brigade.MARKET,
    AgentType.LIQUIDITY_MAPPER: Brigade.MARKET,
    AgentType.ORDERFLOW_ANALYZER: Brigade.MARKET,
    AgentType.SENTIMENT_GAUGER: Brigade.MARKET,
    AgentType.CORRELATION_TRACKER: Brigade.MARKET,
    AgentType.MICROSTRUCTURE_EXPERT: Brigade.MARKET,
    AgentType.SESSION_ANALYZER: Brigade.MARKET,
    AgentType.MARKET_MEMORY_KEEPER: Brigade.MARKET,
    
    # RISK BRIGADE
    AgentType.DRAWDOWN_GUARDIAN: Brigade.RISK,
    AgentType.TAIL_RISK_HUNTER: Brigade.RISK,
    AgentType.POSITION_SIZER: Brigade.RISK,
    AgentType.LEVERAGE_CONTROLLER: Brigade.RISK,
    AgentType.CORRELATION_MONITOR: Brigade.RISK,
    AgentType.STRESS_TESTER: Brigade.RISK,
    AgentType.SCENARIO_PLANNER: Brigade.RISK,
    AgentType.BLACK_SWAN_WATCHER: Brigade.RISK,
    AgentType.RISK_BUDGET_ALLOCATOR: Brigade.RISK,
    AgentType.CIRCUIT_BREAKER: Brigade.RISK,
    
    # STRATEGY BRIGADE
    AgentType.ENTRY_OPTIMIZER: Brigade.STRATEGY,
    AgentType.EXIT_OPTIMIZER: Brigade.STRATEGY,
    AgentType.STOP_LOSS_DESIGNER: Brigade.STRATEGY,
    AgentType.TAKE_PROFIT_PLANNER: Brigade.STRATEGY,
    AgentType.TIMING_SPECIALIST: Brigade.STRATEGY,
    AgentType.EXECUTION_PLANNER: Brigade.STRATEGY,
    AgentType.PYRAMIDING_CONTROLLER: Brigade.STRATEGY,
    AgentType.SCALE_IN_SPECIALIST: Brigade.STRATEGY,
    AgentType.SCALE_OUT_PLANNER: Brigade.STRATEGY,
    AgentType.STRATEGY_COMPOSER: Brigade.STRATEGY,
    
    # DATA BRIGADE
    AgentType.DATA_VALIDATOR: Brigade.DATA,
    AgentType.GAP_DETECTOR: Brigade.DATA,
    AgentType.OUTLIER_HUNTER: Brigade.DATA,
    AgentType.LOOKAHEAD_CHECKER: Brigade.DATA,
    AgentType.SURVIVORSHIP_AUDITOR: Brigade.DATA,
    AgentType.STATIONARITY_TESTER: Brigade.DATA,
    AgentType.SAMPLE_SIZE_ANALYZER: Brigade.DATA,
    AgentType.MULTIPLE_TESTING_GUARD: Brigade.DATA,
    AgentType.DATA_QUALITY_INSPECTOR: Brigade.DATA,
    AgentType.SYNTHETIC_DATA_GENERATOR: Brigade.DATA,
    
    # AUDIT BRIGADE
    AgentType.OVERFITTING_DETECTIVE: Brigade.AUDIT,
    AgentType.P_HACKING_POLICE: Brigade.AUDIT,
    AgentType.CURVE_FITTING_HUNTER: Brigade.AUDIT,
    AgentType.GOVERNANCE_ENFORCER: Brigade.AUDIT,
    AgentType.LOGGING_INSPECTOR: Brigade.AUDIT,
    AgentType.REPRODUCIBILITY_CHECKER: Brigade.AUDIT,
    AgentType.BIAS_DETECTOR: Brigade.AUDIT,
    AgentType.ASSUMPTION_VALIDATOR: Brigade.AUDIT,
    AgentType.RESULT_VERIFIER: Brigade.AUDIT,
    AgentType.CHIEF_AUDIT_OFFICER: Brigade.AUDIT,
}


# AGENT DESCRIPTIONS
AGENT_DESCRIPTIONS = {
    # HYPOTHESIS BRIGADE
    AgentType.PATTERN_HUNTER: "Discovers price patterns and market anomalies",
    AgentType.ANOMALY_DETECTOR: "Identifies unusual market behavior and outliers",
    AgentType.CAUSE_ANALYZER: "Determines root causes of market movements",
    AgentType.EFFECT_PREDICTOR: "Forecasts consequences of market events",
    AgentType.MECHANISM_EXPLORER: "Uncovers underlying market mechanisms",
    AgentType.BOUNDARY_MAPPER: "Defines when hypotheses apply and when they don't",
    AgentType.KILL_CONDITION_DESIGNER: "Creates falsifiability conditions",
    AgentType.PREDICTION_FORMULATOR: "Translates hypotheses into testable predictions",
    AgentType.HYPOTHESIS_INTEGRATOR: "Combines multiple hypotheses into coherent theories",
    AgentType.HYPOTHESIS_VALIDATOR: "Verifies hypothesis quality and testability",
    
    # MARKET BRIGADE
    AgentType.REGIME_SPOTTER: "Detects market regime changes",
    AgentType.TREND_TRACKER: "Monitors trend direction and strength",
    AgentType.VOLATILITY_ASSESSOR: "Evaluates market volatility conditions",
    AgentType.LIQUIDITY_MAPPER: "Analyzes market depth and liquidity",
    AgentType.ORDERFLOW_ANALYZER: "Decodes order flow and volume patterns",
    AgentType.SENTIMENT_GAUGER: "Measures market sentiment and positioning",
    AgentType.CORRELATION_TRACKER: "Monitors inter-market correlations",
    AgentType.MICROSTRUCTURE_EXPERT: "Analyzes tick-level market structure",
    AgentType.SESSION_ANALYZER: "Studies session-based patterns",
    AgentType.MARKET_MEMORY_KEEPER: "Maintains historical market context",
    
    # RISK BRIGADE
    AgentType.DRAWDOWN_GUARDIAN: "Monitors and limits drawdowns",
    AgentType.TAIL_RISK_HUNTER: "Identifies extreme risk scenarios",
    AgentType.POSITION_SIZER: "Calculates optimal position sizes",
    AgentType.LEVERAGE_CONTROLLER: "Manages leverage exposure",
    AgentType.CORRELATION_MONITOR: "Tracks portfolio correlation risk",
    AgentType.STRESS_TESTER: "Simulates stress scenarios",
    AgentType.SCENARIO_PLANNER: "Plans for adverse conditions",
    AgentType.BLACK_SWAN_WATCHER: "Watches for unprecedented events",
    AgentType.RISK_BUDGET_ALLOCATOR: "Allocates risk capital efficiently",
    AgentType.CIRCUIT_BREAKER: "Triggers emergency stops when needed",
    
    # STRATEGY BRIGADE
    AgentType.ENTRY_OPTIMIZER: "Finds optimal entry points",
    AgentType.EXIT_OPTIMIZER: "Determines best exit timing",
    AgentType.STOP_LOSS_DESIGNER: "Designs effective stop loss levels",
    AgentType.TAKE_PROFIT_PLANNER: "Plans profit-taking levels",
    AgentType.TIMING_SPECIALIST: "Optimizes trade timing",
    AgentType.EXECUTION_PLANNER: "Plans order execution strategy",
    AgentType.PYRAMIDING_CONTROLLER: "Manages position scaling up",
    AgentType.SCALE_IN_SPECIALIST: "Handles gradual position entry",
    AgentType.SCALE_OUT_PLANNER: "Manages gradual position exit",
    AgentType.STRATEGY_COMPOSER: "Combines strategies into portfolios",
    
    # DATA BRIGADE
    AgentType.DATA_VALIDATOR: "Verifies data integrity and accuracy",
    AgentType.GAP_DETECTOR: "Identifies missing data points",
    AgentType.OUTLIER_HUNTER: "Finds data anomalies",
    AgentType.LOOKAHEAD_CHECKER: "Prevents future data leakage",
    AgentType.SURVIVORSHIP_AUDITOR: "Detects survivorship bias",
    AgentType.STATIONARITY_TESTER: "Tests data stationarity",
    AgentType.SAMPLE_SIZE_ANALYZER: "Validates statistical power",
    AgentType.MULTIPLE_TESTING_GUARD: "Adjusts for multiple comparisons",
    AgentType.DATA_QUALITY_INSPECTOR: "Assesses overall data quality",
    AgentType.SYNTHETIC_DATA_GENERATOR: "Creates synthetic datasets for testing",
    
    # AUDIT BRIGADE
    AgentType.OVERFITTING_DETECTIVE: "Detects model overfitting",
    AgentType.P_HACKING_POLICE: "Prevents p-hacking and data snooping",
    AgentType.CURVE_FITTING_HUNTER: "Identifies curve fitting",
    AgentType.GOVERNANCE_ENFORCER: "Ensures compliance with governance rules",
    AgentType.LOGGING_INSPECTOR: "Verifies comprehensive logging",
    AgentType.REPRODUCIBILITY_CHECKER: "Tests result reproducibility",
    AgentType.BIAS_DETECTOR: "Identifies various forms of bias",
    AgentType.ASSUMPTION_VALIDATOR: "Validates model assumptions",
    AgentType.RESULT_VERIFIER: "Verifies statistical results",
    AgentType.CHIEF_AUDIT_OFFICER: "Commands the audit brigade",
}


@dataclass
class Agent:
    """A single agent in the army"""
    agent_id: str
    agent_number: int  # 1-60
    agent_type: AgentType
    brigade: Brigade
    name: str
    description: str
    
    # Status
    status: AgentStatus = AgentStatus.IDLE
    
    # Performance tracking
    tasks_completed: int = 0
    tasks_failed: int = 0
    accuracy: float = 0.0
    reputation_score: float = 1.0  # 0-1 scale
    
    # Specialization
    expertise_domains: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.6
    
    # Voting
    votes_cast: int = 0
    votes_agreed: int = 0
    
    # Last activity
    last_active: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'agent_number': self.agent_number,
            'agent_type': self.agent_type.value,
            'brigade': self.brigade.value,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'accuracy': self.accuracy,
            'reputation_score': self.reputation_score,
            'expertise_domains': self.expertise_domains,
            'votes_cast': self.votes_cast,
            'votes_agreed': self.votes_agreed
        }


@dataclass
class Vote:
    """A vote from an agent"""
    vote_id: str
    agent_id: str
    agent_type: AgentType
    decision: str  # e.g., "approve", "reject", "neutral"
    confidence: float  # 0-1
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusResult:
    """Result of a consensus vote"""
    consensus_id: str
    topic: str
    
    # Voting results
    total_votes: int
    votes_for: int
    votes_against: int
    votes_neutral: int
    
    # Decision
    decision: str  # "approved", "rejected", "no_consensus"
    confidence: float
    
    # Breakdown
    by_brigade: Dict[str, Dict[str, int]]
    
    # Details
    winning_reasoning: List[str]
    dissenting_reasoning: List[str]
    
    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'consensus_id': self.consensus_id,
            'topic': self.topic,
            'total_votes': self.total_votes,
            'votes_for': self.votes_for,
            'votes_against': self.votes_against,
            'votes_neutral': self.votes_neutral,
            'decision': self.decision,
            'confidence': self.confidence,
            'by_brigade': self.by_brigade,
            'winning_reasoning': self.winning_reasoning,
            'timestamp': self.timestamp.isoformat()
        }


class AgentArmy:
    """
    The 60-Agent Army for the Intelligence Core.
    
    6 Brigades, 10 Agents each:
    - HYPOTHESIS: Generate and test hypotheses
    - MARKET: Analyze market conditions
    - RISK: Assess and manage risk
    - STRATEGY: Develop trading strategies
    - DATA: Validate data quality
    - AUDIT: Verify compliance and correctness
    """
    
    def __init__(self):
        self.lock = threading.RLock()
        self.agents: Dict[str, Agent] = {}
        self.agents_by_brigade: Dict[Brigade, List[Agent]] = defaultdict(list)
        self.agents_by_type: Dict[AgentType, Agent] = {}
        
        # Consensus tracking
        self.consensus_history: List[ConsensusResult] = []
        self.voting_history: List[Vote] = []
        
        # Performance metrics
        self.total_tasks_completed = 0
        self.total_consensus_votes = 0
        
        # Initialize the army
        self._initialize_army()
        
        logger.info("Agent Army initialized with 60 specialized agents")
    
    def _initialize_army(self):
        """Initialize all 60 agents"""
        agent_number = 1
        
        for agent_type in AgentType:
            brigade = AGENT_BRIGADES[agent_type]
            description = AGENT_DESCRIPTIONS[agent_type]
            
            agent_id = f"agent_{agent_number:03d}_{agent_type.value}"
            
            agent = Agent(
                agent_id=agent_id,
                agent_number=agent_number,
                agent_type=agent_type,
                brigade=brigade,
                name=agent_type.value.replace('_', ' ').title(),
                description=description,
                expertise_domains=[brigade.value, agent_type.value]
            )
            
            self.agents[agent_id] = agent
            self.agents_by_brigade[brigade].append(agent)
            self.agents_by_type[agent_type] = agent
            
            agent_number += 1
    
    def get_agent(self, agent_type: AgentType) -> Optional[Agent]:
        """Get an agent by type"""
        return self.agents_by_type.get(agent_type)
    
    def get_brigade(self, brigade: Brigade) -> List[Agent]:
        """Get all agents in a brigade"""
        return self.agents_by_brigade.get(brigade, [])
    
    def get_all_agents(self) -> List[Agent]:
        """Get all 60 agents"""
        return list(self.agents.values())
    
    def assign_task(
        self,
        agent_type: AgentType,
        task: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assign a task to a specific agent.
        
        Returns simulated agent output.
        """
        with self.lock:
            agent = self.agents_by_type.get(agent_type)
            if not agent:
                return {'error': f'Agent {agent_type.value} not found'}
            
            # Mark as working
            agent.status = AgentStatus.WORKING
            agent.last_active = datetime.now()
            
            # Simulate task execution
            result = self._simulate_agent_work(agent, task, data)
            
            # Update performance
            agent.tasks_completed += 1
            agent.accuracy = 0.5 + (np.random.random() * 0.4)  # Simulated
            agent.status = AgentStatus.IDLE
            
            self.total_tasks_completed += 1
            
            return {
                'agent_id': agent.agent_id,
                'agent_type': agent.agent_type.value,
                'task': task,
                'result': result,
                'confidence': agent.accuracy
            }
    
    def _simulate_agent_work(
        self,
        agent: Agent,
        task: str,
        data: Dict[str, Any]
    ) -> Any:
        """Simulate agent work based on type"""
        # HYPOTHESIS BRIGADE
        if agent.agent_type == AgentType.PATTERN_HUNTER:
            return {'patterns_found': np.random.randint(1, 5), 'reliability': 0.6 + np.random.random() * 0.3}
        
        elif agent.agent_type == AgentType.HYPOTHESIS_VALIDATOR:
            return {'valid': np.random.random() > 0.3, 'issues': ['small_sample'] if np.random.random() > 0.7 else []}
        
        # MARKET BRIGADE
        elif agent.agent_type == AgentType.REGIME_SPOTTER:
            regimes = ['trending', 'ranging', 'volatile', 'calm']
            return {'current_regime': np.random.choice(regimes), 'confidence': 0.7 + np.random.random() * 0.2}
        
        elif agent.agent_type == AgentType.VOLATILITY_ASSESSOR:
            return {'volatility': 0.02 + np.random.random() * 0.03, 'trend': 'increasing' if np.random.random() > 0.5 else 'decreasing'}
        
        # RISK BRIGADE
        elif agent.agent_type == AgentType.DRAWDOWN_GUARDIAN:
            return {'current_drawdown': np.random.random() * 0.1, 'max_drawdown': 0.15, 'safe': True}
        
        elif agent.agent_type == AgentType.POSITION_SIZER:
            return {'optimal_size': 0.05 + np.random.random() * 0.1, 'risk_per_trade': 0.01}
        
        # STRATEGY BRIGADE
        elif agent.agent_type == AgentType.ENTRY_OPTIMIZER:
            return {'entry_price': data.get('price', 1.0) * (1 - np.random.random() * 0.02), 'confidence': 0.75}
        
        elif agent.agent_type == AgentType.STOP_LOSS_DESIGNER:
            return {'stop_loss': data.get('price', 1.0) * (1 - np.random.random() * 0.05), 'type': 'volatility_based'}
        
        # DATA BRIGADE
        elif agent.agent_type == AgentType.DATA_VALIDATOR:
            return {'valid': np.random.random() > 0.1, 'issues': ['missing_data'] if np.random.random() > 0.8 else []}
        
        elif agent.agent_type == AgentType.LOOKAHEAD_CHECKER:
            return {'lookahead_bias': False, 'warnings': []}
        
        # AUDIT BRIGADE
        elif agent.agent_type == AgentType.OVERFITTING_DETECTIVE:
            return {'overfitting_detected': np.random.random() > 0.7, 'severity': 'moderate'}
        
        elif agent.agent_type == AgentType.CHIEF_AUDIT_OFFICER:
            return {'audit_passed': np.random.random() > 0.3, 'violations': []}
        
        # Default
        else:
            return {'status': 'completed', 'confidence': 0.7}
    
    def brigade_consensus(
        self,
        brigade: Brigade,
        topic: str,
        context: Dict[str, Any]
    ) -> ConsensusResult:
        """
        Get consensus from a specific brigade.
        
        Returns the collective decision of the 10 agents.
        """
        with self.lock:
            agents = self.agents_by_brigade.get(brigade, [])
            if not agents:
                return None
            
            votes = []
            for agent in agents:
                # Simulate agent voting
                decision = self._simulate_vote(agent, topic, context)
                vote = Vote(
                    vote_id=hashlib.md5(f"{agent.agent_id}_{topic}_{datetime.now()}".encode()).hexdigest()[:16],
                    agent_id=agent.agent_id,
                    agent_type=agent.agent_type,
                    decision=decision,
                    confidence=0.6 + np.random.random() * 0.3,
                    reasoning=f"Based on {agent.agent_type.value} expertise"
                )
                votes.append(vote)
                
                # Update agent stats
                agent.votes_cast += 1
                agent.status = AgentStatus.VOTING
            
            # Count votes
            votes_for = sum(1 for v in votes if v.decision == 'approve')
            votes_against = sum(1 for v in votes if v.decision == 'reject')
            votes_neutral = sum(1 for v in votes if v.decision == 'neutral')
            
            # Determine decision
            if votes_for > votes_against and votes_for > votes_neutral:
                decision = 'approved'
                confidence = votes_for / len(votes)
            elif votes_against > votes_for and votes_against > votes_neutral:
                decision = 'rejected'
                confidence = votes_against / len(votes)
            else:
                decision = 'no_consensus'
                confidence = 0.5
            
            # Collect reasoning
            winning_votes = [v for v in votes if v.decision == ('approve' if decision == 'approved' else 'reject' if decision == 'rejected' else 'neutral')]
            winning_reasoning = [v.reasoning for v in winning_votes[:3]]
            dissenting_reasoning = [v.reasoning for v in votes if v not in winning_votes][:3]
            
            # Create consensus result
            consensus = ConsensusResult(
                consensus_id=hashlib.md5(f"{brigade.value}_{topic}_{datetime.now()}".encode()).hexdigest()[:16],
                topic=topic,
                total_votes=len(votes),
                votes_for=votes_for,
                votes_against=votes_against,
                votes_neutral=votes_neutral,
                decision=decision,
                confidence=confidence,
                by_brigade={brigade.value: {'for': votes_for, 'against': votes_against, 'neutral': votes_neutral}},
                winning_reasoning=winning_reasoning,
                dissenting_reasoning=dissenting_reasoning
            )
            
            # Store
            self.consensus_history.append(consensus)
            self.voting_history.extend(votes)
            self.total_consensus_votes += len(votes)
            
            # Update agents
            for agent in agents:
                agent.status = AgentStatus.IDLE
                if decision == 'approved':
                    agent.votes_agreed += votes_for
                elif decision == 'rejected':
                    agent.votes_agreed += votes_against
            
            return consensus
    
    def _simulate_vote(
        self,
        agent: Agent,
        topic: str,
        context: Dict[str, Any]
    ) -> str:
        """Simulate an agent's vote"""
        # Different brigades have different tendencies
        weights = {
            Brigade.HYPOTHESIS: {'approve': 0.5, 'reject': 0.3, 'neutral': 0.2},
            Brigade.MARKET: {'approve': 0.4, 'reject': 0.4, 'neutral': 0.2},
            Brigade.RISK: {'approve': 0.2, 'reject': 0.6, 'neutral': 0.2},  # Risk-averse
            Brigade.STRATEGY: {'approve': 0.5, 'reject': 0.3, 'neutral': 0.2},
            Brigade.DATA: {'approve': 0.3, 'reject': 0.5, 'neutral': 0.2},  # Strict
            Brigade.AUDIT: {'approve': 0.2, 'reject': 0.6, 'neutral': 0.2},  # Very strict
        }
        
        w = weights.get(agent.brigade, {'approve': 0.4, 'reject': 0.4, 'neutral': 0.2})
        return np.random.choice(['approve', 'reject', 'neutral'], p=[w['approve'], w['reject'], w['neutral']])
    
    def full_army_consensus(
        self,
        topic: str,
        context: Dict[str, Any]
    ) -> ConsensusResult:
        """
        Get consensus from ALL 60 agents.
        
        This is the ultimate decision-making mechanism.
        """
        with self.lock:
            votes = []
            by_brigade = {}
            
            for brigade in Brigade:
                brigade_agents = self.agents_by_brigade[brigade]
                brigade_votes = {'for': 0, 'against': 0, 'neutral': 0}
                
                for agent in brigade_agents:
                    decision = self._simulate_vote(agent, topic, context)
                    vote = Vote(
                        vote_id=hashlib.md5(f"{agent.agent_id}_{topic}_{datetime.now()}".encode()).hexdigest()[:16],
                        agent_id=agent.agent_id,
                        agent_type=agent.agent_type,
                        decision=decision,
                        confidence=0.6 + np.random.random() * 0.3,
                        reasoning=f"{agent.agent_type.value} analysis: {decision}"
                    )
                    votes.append(vote)
                    agent.votes_cast += 1
                    
                    if decision == 'approve':
                        brigade_votes['for'] += 1
                    elif decision == 'reject':
                        brigade_votes['against'] += 1
                    else:
                        brigade_votes['neutral'] += 1
                
                by_brigade[brigade.value] = brigade_votes
            
            # Count total votes
            votes_for = sum(b['for'] for b in by_brigade.values())
            votes_against = sum(b['against'] for b in by_brigade.values())
            votes_neutral = sum(b['neutral'] for b in by_brigade.values())
            
            # Determine decision
            if votes_for > votes_against and votes_for > 30:  # Majority of 60
                decision = 'approved'
                confidence = votes_for / 60
            elif votes_against > votes_for and votes_against > 30:
                decision = 'rejected'
                confidence = votes_against / 60
            else:
                decision = 'no_consensus'
                confidence = max(votes_for, votes_against) / 60
            
            # Create consensus
            consensus = ConsensusResult(
                consensus_id=hashlib.md5(f"full_army_{topic}_{datetime.now()}".encode()).hexdigest()[:16],
                topic=topic,
                total_votes=60,
                votes_for=votes_for,
                votes_against=votes_against,
                votes_neutral=votes_neutral,
                decision=decision,
                confidence=confidence,
                by_brigade=by_brigade,
                winning_reasoning=["Brigade consensus achieved"],
                dissenting_reasoning=[]
            )
            
            self.consensus_history.append(consensus)
            self.voting_history.extend(votes)
            self.total_consensus_votes += 60
            
            return consensus
    
    def get_brigade_summary(self, brigade: Brigade) -> Dict[str, Any]:
        """Get summary of a brigade's status"""
        agents = self.agents_by_brigade.get(brigade, [])
        
        return {
            'brigade': brigade.value,
            'agent_count': len(agents),
            'agents': [a.to_dict() for a in agents],
            'total_tasks': sum(a.tasks_completed for a in agents),
            'average_reputation': np.mean([a.reputation_score for a in agents]),
            'active_agents': sum(1 for a in agents if a.status != AgentStatus.DISABLED)
        }
    
    def get_army_statistics(self) -> Dict[str, Any]:
        """Get statistics for the entire army"""
        all_agents = list(self.agents.values())
        
        return {
            'total_agents': len(all_agents),
            'total_tasks_completed': self.total_tasks_completed,
            'total_consensus_votes': self.total_consensus_votes,
            'brigades': {
                brigade.value: {
                    'agent_count': len(self.agents_by_brigade[brigade]),
                    'tasks_completed': sum(a.tasks_completed for a in self.agents_by_brigade[brigade])
                }
                for brigade in Brigade
            },
            'top_performers': sorted(
                [a.to_dict() for a in all_agents],
                key=lambda x: x['reputation_score'],
                reverse=True
            )[:10],
            'recent_consensus': [
                c.to_dict() for c in self.consensus_history[-5:]
            ]
        }


def quick_start_army() -> AgentArmy:
    """
    Quick start the 60-Agent Army.
    
    Returns:
        AgentArmy instance with all 60 agents ready
    """
    army = AgentArmy()
    logger.info("60-Agent Army deployed and ready for duty")
    return army
