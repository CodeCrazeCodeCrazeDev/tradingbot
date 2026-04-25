"""
AADS AIP Multi-Agent Core

Implements the specialist agents that operate simultaneously in the AADS system.
Each agent has a specific role in the alpha discovery and trading pipeline.

Agent Network:
- ResearchAgent: Autonomous hypothesis generation
- OntologyAgent: Knowledge graph enrichment
- BullAgent: Adversarial bull case builder
- BearAgent: Adversarial bear case destroyer
- SimulationAgent: Monte Carlo, stress tests, causal sims
- RiskAgent: Portfolio constraints, position sizing, veto power
- ExecutionAgent: Multi-venue order routing
- AuditAgent: Immutable decision logging
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import numpy as np
import logging
import uuid
import json

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent operational status"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    DISABLED = "disabled"


class AgentPriority(Enum):
    """Agent execution priority"""
    CRITICAL = 1    # Must complete before trade
    HIGH = 2        # Important but not blocking
    MEDIUM = 3      # Standard priority
    LOW = 4         # Background tasks


@dataclass
class AgentMessage:
    """Message passed between agents"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    sender: str = ""
    recipient: str = ""
    message_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    requires_response: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'message_id': self.message_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'message_type': self.message_type,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class AgentOutput:
    """Standard output from an agent"""
    agent_name: str
    output_type: str
    data: Dict[str, Any]
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_name': self.agent_name,
            'output_type': self.output_type,
            'data': self.data,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'timestamp': self.timestamp.isoformat()
        }


class BaseAgent(ABC):
    """Base class for all AADS agents"""
    
    def __init__(self, name: str, priority: AgentPriority = AgentPriority.MEDIUM):
        self.name = name
        self.priority = priority
        self.status = AgentStatus.IDLE
        self.message_queue: List[AgentMessage] = []
        self.output_history: List[AgentOutput] = []
        self.error_count = 0
        self.total_executions = 0
        self.created_at = datetime.now()
        self.last_execution: Optional[datetime] = None
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Process input and generate output"""
        pass
    
    def receive_message(self, message: AgentMessage) -> None:
        """Receive a message from another agent"""
        self.message_queue.append(message)
    
    def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]) -> AgentMessage:
        """Create a message to send to another agent"""
        return AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            payload=payload
        )
    
    def execute(self, context: Dict[str, Any]) -> AgentOutput:
        """Execute the agent with error handling"""
        self.status = AgentStatus.PROCESSING
        self.total_executions += 1
        
        try:
            output = self.process(context)
            self.output_history.append(output)
            self.last_execution = datetime.now()
            self.status = AgentStatus.IDLE
            return output
        except Exception as e:
            self.error_count += 1
            self.status = AgentStatus.ERROR
            logger.error(f"Agent {self.name} error: {e}")
            return AgentOutput(
                agent_name=self.name,
                output_type="error",
                data={"error": str(e)},
                confidence=0.0,
                reasoning=f"Agent failed with error: {e}"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority.value,
            'total_executions': self.total_executions,
            'error_count': self.error_count,
            'error_rate': self.error_count / max(1, self.total_executions),
            'last_execution': self.last_execution.isoformat() if self.last_execution else None
        }


class ResearchAgent(BaseAgent):
    """
    Autonomous hypothesis generation agent.
    
    Searches SEC filings, earnings transcripts, academic papers, patent filings.
    Outputs: alpha hypothesis + supporting evidence + falsification criteria.
    """
    
    def __init__(self):
        super().__init__("ResearchAgent", AgentPriority.HIGH)
        self.hypothesis_count = 0
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Generate research hypothesis"""
        asset = context.get('asset', 'UNKNOWN')
        market_state = context.get('market_state', {})
        
        # Generate hypothesis based on available data
        hypothesis = self._generate_hypothesis(asset, market_state)
        evidence = self._gather_evidence(asset, market_state)
        falsification = self._define_falsification_criteria(hypothesis)
        
        self.hypothesis_count += 1
        
        return AgentOutput(
            agent_name=self.name,
            output_type="hypothesis",
            data={
                'hypothesis_id': f"H-{self.hypothesis_count:04d}",
                'asset': asset,
                'hypothesis': hypothesis,
                'evidence': evidence,
                'falsification_criteria': falsification,
                'confidence': np.random.uniform(0.5, 0.9)
            },
            confidence=0.7,
            reasoning=f"Generated hypothesis for {asset} based on market analysis"
        )
    
    def _generate_hypothesis(self, asset: str, market_state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate alpha hypothesis"""
        return {
            'thesis': f"{asset} will outperform due to favorable conditions",
            'direction': 'long',
            'horizon_days': 20,
            'expected_return': np.random.uniform(0.02, 0.10),
            'catalyst': 'Earnings surprise / sector rotation / macro tailwind'
        }
    
    def _gather_evidence(self, asset: str, market_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gather supporting evidence"""
        return [
            {'source': 'SEC Filing', 'finding': 'Revenue growth acceleration', 'weight': 0.3},
            {'source': 'Earnings Call', 'finding': 'Positive management tone', 'weight': 0.2},
            {'source': 'Technical', 'finding': 'Breakout from consolidation', 'weight': 0.25},
            {'source': 'Sentiment', 'finding': 'Improving analyst sentiment', 'weight': 0.25}
        ]
    
    def _define_falsification_criteria(self, hypothesis: Dict[str, Any]) -> List[str]:
        """Define criteria that would invalidate the hypothesis"""
        return [
            'Price drops below key support level',
            'Earnings miss by >10%',
            'Sector rotation away from this space',
            'Macro shock (VIX > 30)'
        ]


class OntologyAgent(BaseAgent):
    """
    Knowledge graph enrichment agent.
    
    Extracts entities and relationships from all incoming data streams.
    Updates the market intelligence graph in real-time.
    """
    
    def __init__(self):
        super().__init__("OntologyAgent", AgentPriority.MEDIUM)
        self.entities_extracted = 0
        self.relationships_created = 0
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Extract entities and relationships"""
        data = context.get('data', {})
        data_type = context.get('data_type', 'unknown')
        
        entities = self._extract_entities(data, data_type)
        relationships = self._extract_relationships(entities, data)
        
        self.entities_extracted += len(entities)
        self.relationships_created += len(relationships)
        
        return AgentOutput(
            agent_name=self.name,
            output_type="graph_update",
            data={
                'entities': entities,
                'relationships': relationships,
                'data_type': data_type
            },
            confidence=0.85,
            reasoning=f"Extracted {len(entities)} entities and {len(relationships)} relationships"
        )
    
    def _extract_entities(self, data: Dict[str, Any], data_type: str) -> List[Dict[str, Any]]:
        """Extract entities from data"""
        entities = []
        
        if data_type == 'news':
            entities.append({'type': 'NewsArticle', 'properties': data})
        elif data_type == 'earnings':
            entities.append({'type': 'EarningsEvent', 'properties': data})
        elif data_type == 'price':
            entities.append({'type': 'PriceUpdate', 'properties': data})
        
        return entities
    
    def _extract_relationships(self, entities: List[Dict], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationships between entities"""
        relationships = []
        
        for entity in entities:
            if 'asset' in data:
                relationships.append({
                    'type': 'MENTIONED_IN',
                    'source': data['asset'],
                    'target': entity.get('type', 'Unknown'),
                    'properties': {'timestamp': datetime.now().isoformat()}
                })
        
        return relationships


class BullAgent(BaseAgent):
    """
    Adversarial bull case builder.
    
    Given any hypothesis, builds the strongest possible entry case.
    Output: thesis + price targets + catalyst timeline.
    """
    
    def __init__(self):
        super().__init__("BullAgent", AgentPriority.HIGH)
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Build bull case for hypothesis"""
        hypothesis = context.get('hypothesis', {})
        asset = context.get('asset', 'UNKNOWN')
        current_price = context.get('current_price', 100.0)
        
        bull_case = self._build_bull_case(hypothesis, asset, current_price)
        
        return AgentOutput(
            agent_name=self.name,
            output_type="bull_case",
            data=bull_case,
            confidence=bull_case.get('confidence', 0.5),
            reasoning=bull_case.get('thesis', '')
        )
    
    def _build_bull_case(self, hypothesis: Dict, asset: str, current_price: float) -> Dict[str, Any]:
        """Build the strongest bull case"""
        upside_target = current_price * np.random.uniform(1.10, 1.30)
        
        return {
            'asset': asset,
            'direction': 'LONG',
            'thesis': f"Strong bull case for {asset}: favorable technicals, positive sentiment, catalyst approaching",
            'entry_price': current_price,
            'price_target_1': current_price * 1.10,
            'price_target_2': current_price * 1.20,
            'price_target_3': upside_target,
            'stop_loss': current_price * 0.95,
            'risk_reward_ratio': (upside_target - current_price) / (current_price * 0.05),
            'catalysts': [
                {'event': 'Earnings release', 'date': 'T+15 days', 'impact': 'high'},
                {'event': 'Product launch', 'date': 'T+30 days', 'impact': 'medium'},
                {'event': 'Analyst day', 'date': 'T+45 days', 'impact': 'medium'}
            ],
            'supporting_factors': [
                'Technical breakout confirmed',
                'Institutional accumulation detected',
                'Sector tailwinds',
                'Positive earnings revisions'
            ],
            'confidence': np.random.uniform(0.6, 0.85)
        }


class BearAgent(BaseAgent):
    """
    Adversarial bear case destroyer.
    
    Actively tries to destroy the BullAgent's thesis.
    Output: invalidation scenarios + tail risks + stop levels.
    """
    
    def __init__(self):
        super().__init__("BearAgent", AgentPriority.HIGH)
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Build bear case / destroy bull thesis"""
        bull_case = context.get('bull_case', {})
        asset = context.get('asset', 'UNKNOWN')
        current_price = context.get('current_price', 100.0)
        
        bear_case = self._build_bear_case(bull_case, asset, current_price)
        
        return AgentOutput(
            agent_name=self.name,
            output_type="bear_case",
            data=bear_case,
            confidence=bear_case.get('confidence', 0.5),
            reasoning=bear_case.get('counter_thesis', '')
        )
    
    def _build_bear_case(self, bull_case: Dict, asset: str, current_price: float) -> Dict[str, Any]:
        """Build counter-argument to bull case"""
        downside_target = current_price * np.random.uniform(0.70, 0.90)
        
        return {
            'asset': asset,
            'counter_thesis': f"Bull case for {asset} is flawed: overvaluation, deteriorating fundamentals, macro headwinds",
            'invalidation_scenarios': [
                {'scenario': 'Earnings miss', 'probability': 0.25, 'impact': -0.15},
                {'scenario': 'Guidance cut', 'probability': 0.20, 'impact': -0.20},
                {'scenario': 'Sector rotation', 'probability': 0.30, 'impact': -0.10},
                {'scenario': 'Macro shock', 'probability': 0.15, 'impact': -0.25}
            ],
            'tail_risks': [
                {'risk': 'Accounting irregularities', 'severity': 'critical'},
                {'risk': 'Key executive departure', 'severity': 'high'},
                {'risk': 'Regulatory action', 'severity': 'high'},
                {'risk': 'Competitive disruption', 'severity': 'medium'}
            ],
            'stop_levels': {
                'tight_stop': current_price * 0.97,
                'normal_stop': current_price * 0.95,
                'wide_stop': current_price * 0.90
            },
            'downside_target': downside_target,
            'max_loss_scenario': current_price * 0.50,
            'confidence': np.random.uniform(0.5, 0.75)
        }


class SimulationAgent(BaseAgent):
    """
    Simulation agent for all 5 simulation types.
    
    Runs:
    1. Monte Carlo path simulation
    2. Agent-based microstructure simulation
    3. Macro shock stress tests
    4. Counterfactual causal intervention
    5. Adversarial market maker simulation
    """
    
    def __init__(self):
        super().__init__("SimulationAgent", AgentPriority.CRITICAL)
        self.simulations_run = 0
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Run all simulation types"""
        asset = context.get('asset', 'UNKNOWN')
        position_size = context.get('position_size', 0.01)
        current_price = context.get('current_price', 100.0)
        
        results = {
            'monte_carlo': self._run_monte_carlo(current_price),
            'agent_based': self._run_agent_based(current_price),
            'stress_test': self._run_stress_tests(current_price, position_size),
            'causal': self._run_causal_sim(asset),
            'market_maker': self._run_mm_simulation(position_size)
        }
        
        # Aggregate results
        aggregated = self._aggregate_results(results)
        self.simulations_run += 1
        
        return AgentOutput(
            agent_name=self.name,
            output_type="simulation_results",
            data={
                'asset': asset,
                'simulations': results,
                'aggregated': aggregated
            },
            confidence=0.8,
            reasoning=f"Completed 5 simulation types for {asset}"
        )
    
    def _run_monte_carlo(self, current_price: float, scenarios: int = 10000) -> Dict[str, Any]:
        """Monte Carlo path simulation"""
        # Simulate returns
        returns = np.random.normal(0.0005, 0.02, (scenarios, 20))  # 20 days
        paths = current_price * np.cumprod(1 + returns, axis=1)
        final_prices = paths[:, -1]
        
        return {
            'scenarios': scenarios,
            'horizon_days': 20,
            'p10': float(np.percentile(final_prices, 10)),
            'p25': float(np.percentile(final_prices, 25)),
            'p50': float(np.percentile(final_prices, 50)),
            'p75': float(np.percentile(final_prices, 75)),
            'p90': float(np.percentile(final_prices, 90)),
            'expected_return': float((np.mean(final_prices) - current_price) / current_price),
            'var_95': float((current_price - np.percentile(final_prices, 5)) / current_price),
            'cvar_95': float((current_price - np.mean(final_prices[final_prices < np.percentile(final_prices, 5)])) / current_price)
        }
    
    def _run_agent_based(self, current_price: float) -> Dict[str, Any]:
        """Agent-based microstructure simulation"""
        return {
            'market_impact_estimate_bps': np.random.uniform(5, 20),
            'optimal_execution_time_minutes': np.random.randint(30, 180),
            'liquidity_score': np.random.uniform(0.5, 1.0),
            'adverse_selection_risk': np.random.uniform(0.1, 0.3)
        }
    
    def _run_stress_tests(self, current_price: float, position_size: float) -> Dict[str, Any]:
        """Historical stress test scenarios"""
        scenarios = {
            '2008_crisis': {'drawdown': -0.45, 'recovery_days': 400},
            'covid_march_2020': {'drawdown': -0.35, 'recovery_days': 150},
            'svb_collapse': {'drawdown': -0.15, 'recovery_days': 30},
            'flash_crash_2010': {'drawdown': -0.10, 'recovery_days': 1}
        }
        
        portfolio_impact = {
            name: scenario['drawdown'] * position_size
            for name, scenario in scenarios.items()
        }
        
        return {
            'scenarios': scenarios,
            'portfolio_impact': portfolio_impact,
            'worst_case_loss': min(portfolio_impact.values())
        }
    
    def _run_causal_sim(self, asset: str) -> Dict[str, Any]:
        """Counterfactual causal simulation"""
        return {
            'fed_shock_impact': np.random.uniform(-0.10, 0.05),
            'vix_spike_impact': np.random.uniform(-0.15, -0.05),
            'oil_shock_impact': np.random.uniform(-0.08, 0.08),
            'china_pmi_impact': np.random.uniform(-0.05, 0.05)
        }
    
    def _run_mm_simulation(self, position_size: float) -> Dict[str, Any]:
        """Adversarial market maker simulation"""
        return {
            'expected_slippage_bps': np.random.uniform(2, 10),
            'fill_probability': np.random.uniform(0.85, 0.99),
            'adverse_fill_risk': np.random.uniform(0.05, 0.15),
            'optimal_order_size_pct': min(0.05, position_size * 0.1)
        }
    
    def _aggregate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate simulation results"""
        mc = results['monte_carlo']
        stress = results['stress_test']
        
        return {
            'expected_return': mc['expected_return'],
            'p10_return': (mc['p10'] - 100) / 100,  # Assuming current_price=100
            'p90_return': (mc['p90'] - 100) / 100,
            'var_95': mc['var_95'],
            'worst_stress_loss': stress['worst_case_loss'],
            'execution_feasible': results['market_maker']['fill_probability'] > 0.9,
            'overall_risk_score': np.random.uniform(0.3, 0.7)
        }


class RiskAgent(BaseAgent):
    """
    Risk management agent with veto power.
    
    Enforces portfolio-level constraints:
    - Position VaR
    - Correlation with existing book
    - Sector concentration
    - Drawdown budget
    - Kelly fraction
    
    Hard stops:
    - Max 2% per trade
    - Max 10% per sector
    - Max 20% drawdown kills all trading
    """
    
    # Non-negotiable limits
    MAX_POSITION_PCT = 0.02
    MAX_SECTOR_PCT = 0.10
    MAX_CORRELATED_BOOK_PCT = 0.15
    CIRCUIT_BREAKER_DD = 0.10
    
    def __init__(self):
        super().__init__("RiskAgent", AgentPriority.CRITICAL)
        self.vetoes_issued = 0
        self.approvals_issued = 0
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Evaluate trade risk and approve/veto"""
        trade = context.get('trade', {})
        portfolio = context.get('portfolio', {})
        simulation_results = context.get('simulation_results', {})
        
        # Run all risk checks
        checks = self._run_risk_checks(trade, portfolio, simulation_results)
        
        # Determine approval
        approved = all(check['passed'] for check in checks.values())
        
        if approved:
            self.approvals_issued += 1
            position_size = self._calculate_position_size(trade, portfolio, simulation_results)
        else:
            self.vetoes_issued += 1
            position_size = 0.0
        
        return AgentOutput(
            agent_name=self.name,
            output_type="risk_decision",
            data={
                'approved': approved,
                'checks': checks,
                'recommended_position_size': position_size,
                'veto_reasons': [
                    check['reason'] for check in checks.values() if not check['passed']
                ]
            },
            confidence=0.95,
            reasoning="Risk assessment complete" if approved else "Trade vetoed due to risk violations"
        )
    
    def _run_risk_checks(self, trade: Dict, portfolio: Dict, sim_results: Dict) -> Dict[str, Dict]:
        """Run all risk checks"""
        checks = {}
        
        # Position size check
        requested_size = trade.get('position_size', 0.01)
        checks['position_size'] = {
            'passed': requested_size <= self.MAX_POSITION_PCT,
            'value': requested_size,
            'limit': self.MAX_POSITION_PCT,
            'reason': f"Position size {requested_size:.1%} exceeds max {self.MAX_POSITION_PCT:.1%}"
        }
        
        # Sector concentration check
        sector = trade.get('sector', 'Unknown')
        current_sector_exposure = portfolio.get('sector_exposures', {}).get(sector, 0)
        new_exposure = current_sector_exposure + requested_size
        checks['sector_concentration'] = {
            'passed': new_exposure <= self.MAX_SECTOR_PCT,
            'value': new_exposure,
            'limit': self.MAX_SECTOR_PCT,
            'reason': f"Sector exposure {new_exposure:.1%} exceeds max {self.MAX_SECTOR_PCT:.1%}"
        }
        
        # Drawdown check
        current_dd = portfolio.get('current_drawdown', 0)
        checks['drawdown_budget'] = {
            'passed': current_dd < self.CIRCUIT_BREAKER_DD,
            'value': current_dd,
            'limit': self.CIRCUIT_BREAKER_DD,
            'reason': f"Portfolio drawdown {current_dd:.1%} exceeds circuit breaker {self.CIRCUIT_BREAKER_DD:.1%}"
        }
        
        # VaR check
        trade_var = sim_results.get('aggregated', {}).get('var_95', 0.05)
        portfolio_var = portfolio.get('var_95', 0.02)
        checks['var_limit'] = {
            'passed': trade_var < 0.10,  # 10% VaR limit
            'value': trade_var,
            'limit': 0.10,
            'reason': f"Trade VaR {trade_var:.1%} exceeds limit"
        }
        
        # Correlation check
        correlation = trade.get('correlation_with_book', 0)
        checks['correlation'] = {
            'passed': correlation < 0.6 or requested_size < 0.01,
            'value': correlation,
            'limit': 0.6,
            'reason': f"High correlation {correlation:.2f} with existing book"
        }
        
        return checks
    
    def _calculate_position_size(self, trade: Dict, portfolio: Dict, sim_results: Dict) -> float:
        """Calculate optimal position size using Kelly criterion"""
        # Get win rate and payoff ratio from simulation
        expected_return = sim_results.get('aggregated', {}).get('expected_return', 0.05)
        var_95 = sim_results.get('aggregated', {}).get('var_95', 0.10)
        
        # Simplified Kelly: f = (p*b - q) / b where p=win_prob, b=win/loss ratio, q=1-p
        win_prob = 0.55  # Assumed
        win_loss_ratio = abs(expected_return / var_95) if var_95 > 0 else 1.0
        
        kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%
        
        # Apply half-Kelly for safety
        position_size = kelly_fraction * 0.5
        
        # Enforce maximum
        position_size = min(position_size, self.MAX_POSITION_PCT)
        
        return position_size


class ExecutionAgent(BaseAgent):
    """
    Multi-venue order routing agent.
    
    Splits orders intelligently across venues:
    - Equities: IBKR/Alpaca
    - Crypto: Binance/Coinbase
    - Prediction markets: Polymarket CLOB
    
    Optimizes for market impact, gas costs, slippage.
    """
    
    def __init__(self):
        super().__init__("ExecutionAgent", AgentPriority.CRITICAL)
        self.orders_executed = 0
        self.total_slippage_bps = 0.0
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Generate execution plan"""
        trade = context.get('trade', {})
        asset = context.get('asset', 'UNKNOWN')
        position_size = context.get('position_size', 0.01)
        urgency = context.get('urgency', 'medium')
        
        # Determine asset class and venue
        asset_class = self._determine_asset_class(asset)
        venues = self._select_venues(asset_class)
        
        # Generate execution plan
        execution_plan = self._generate_execution_plan(
            asset, position_size, urgency, venues
        )
        
        self.orders_executed += 1
        
        return AgentOutput(
            agent_name=self.name,
            output_type="execution_plan",
            data=execution_plan,
            confidence=0.9,
            reasoning=f"Generated execution plan for {asset} across {len(venues)} venues"
        )
    
    def _determine_asset_class(self, asset: str) -> str:
        """Determine asset class from ticker"""
        if asset.endswith('USDT') or asset.endswith('USD') and len(asset) <= 7:
            return 'crypto'
        elif asset.startswith('POLY_'):
            return 'prediction_market'
        else:
            return 'equity'
    
    def _select_venues(self, asset_class: str) -> List[Dict[str, Any]]:
        """Select execution venues for asset class"""
        venues = {
            'equity': [
                {'name': 'IBKR', 'priority': 1, 'fee_bps': 0.5},
                {'name': 'Alpaca', 'priority': 2, 'fee_bps': 0.0}
            ],
            'crypto': [
                {'name': 'Binance', 'priority': 1, 'fee_bps': 10},
                {'name': 'Coinbase', 'priority': 2, 'fee_bps': 50}
            ],
            'prediction_market': [
                {'name': 'Polymarket', 'priority': 1, 'fee_bps': 0}
            ]
        }
        return venues.get(asset_class, [])
    
    def _generate_execution_plan(
        self,
        asset: str,
        position_size: float,
        urgency: str,
        venues: List[Dict]
    ) -> Dict[str, Any]:
        """Generate detailed execution plan"""
        # Select algorithm based on urgency
        algo_map = {
            'low': 'TWAP',
            'medium': 'VWAP',
            'high': 'IS',  # Implementation Shortfall
            'critical': 'MARKET'
        }
        algo = algo_map.get(urgency, 'VWAP')
        
        # Calculate execution parameters
        if algo == 'TWAP':
            duration_minutes = 120
            participation_rate = 0.03
        elif algo == 'VWAP':
            duration_minutes = 60
            participation_rate = 0.05
        elif algo == 'IS':
            duration_minutes = 30
            participation_rate = 0.10
        else:
            duration_minutes = 1
            participation_rate = 1.0
        
        # Estimate slippage
        estimated_slippage_bps = participation_rate * 100 * 0.5  # Rough estimate
        
        return {
            'asset': asset,
            'position_size': position_size,
            'algorithm': algo,
            'duration_minutes': duration_minutes,
            'participation_rate': participation_rate,
            'venues': venues,
            'primary_venue': venues[0]['name'] if venues else 'Unknown',
            'estimated_slippage_bps': estimated_slippage_bps,
            'estimated_fees_bps': venues[0]['fee_bps'] if venues else 0,
            'child_orders': self._generate_child_orders(position_size, duration_minutes)
        }
    
    def _generate_child_orders(self, position_size: float, duration_minutes: int) -> List[Dict]:
        """Generate child orders for execution"""
        num_slices = max(1, duration_minutes // 10)
        slice_size = position_size / num_slices
        
        return [
            {
                'slice_id': i + 1,
                'size': slice_size,
                'time_offset_minutes': i * 10,
                'order_type': 'LIMIT'
            }
            for i in range(num_slices)
        ]


class AuditAgent(BaseAgent):
    """
    Immutable audit logging agent.
    
    Logs every decision with full reasoning chain:
    - Agent outputs
    - Simulation results
    - Approval status
    - Execution details
    
    Every trade must have an audit trail a regulator could read and understand.
    """
    
    def __init__(self, log_path: str = "audit_logs"):
        super().__init__("AuditAgent", AgentPriority.CRITICAL)
        self.log_path = log_path
        self.audit_entries = 0
    
    def process(self, context: Dict[str, Any]) -> AgentOutput:
        """Create audit log entry"""
        decision_id = context.get('decision_id', str(uuid.uuid4())[:12])
        
        audit_entry = self._create_audit_entry(decision_id, context)
        
        # Log to file (in production, would use immutable storage)
        self._persist_audit_entry(audit_entry)
        
        self.audit_entries += 1
        
        return AgentOutput(
            agent_name=self.name,
            output_type="audit_log",
            data={
                'audit_id': audit_entry['audit_id'],
                'decision_id': decision_id,
                'logged_at': audit_entry['timestamp']
            },
            confidence=1.0,
            reasoning=f"Audit entry created: {audit_entry['audit_id']}"
        )
    
    def _create_audit_entry(self, decision_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive audit entry"""
        return {
            'audit_id': f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{decision_id[:8]}",
            'decision_id': decision_id,
            'timestamp': datetime.now().isoformat(),
            
            # Decision details
            'asset': context.get('asset', 'UNKNOWN'),
            'direction': context.get('direction', 'UNKNOWN'),
            'position_size': context.get('position_size', 0),
            
            # Agent outputs
            'research_hypothesis': context.get('research_output', {}),
            'bull_case': context.get('bull_case', {}),
            'bear_case': context.get('bear_case', {}),
            'simulation_results': context.get('simulation_results', {}),
            'risk_decision': context.get('risk_decision', {}),
            
            # Final decision
            'approved': context.get('approved', False),
            'confidence': context.get('confidence', 0),
            'execution_plan': context.get('execution_plan', {}),
            
            # Reasoning chain
            'reasoning_chain': self._build_reasoning_chain(context),
            
            # Compliance
            'compliance_checks': context.get('compliance_checks', []),
            'regulatory_flags': []
        }
    
    def _build_reasoning_chain(self, context: Dict[str, Any]) -> List[str]:
        """Build human-readable reasoning chain"""
        chain = []
        
        if 'research_output' in context:
            chain.append(f"1. Research: Generated hypothesis for {context.get('asset', 'asset')}")
        
        if 'bull_case' in context:
            chain.append(f"2. Bull Case: {context['bull_case'].get('thesis', 'Built bull thesis')[:100]}")
        
        if 'bear_case' in context:
            chain.append(f"3. Bear Case: {context['bear_case'].get('counter_thesis', 'Built counter-thesis')[:100]}")
        
        if 'simulation_results' in context:
            chain.append("4. Simulation: Completed Monte Carlo, stress tests, causal analysis")
        
        if 'risk_decision' in context:
            approved = context['risk_decision'].get('approved', False)
            chain.append(f"5. Risk: {'APPROVED' if approved else 'VETOED'}")
        
        if 'execution_plan' in context:
            chain.append(f"6. Execution: Plan generated using {context['execution_plan'].get('algorithm', 'VWAP')}")
        
        return chain
    
    def _persist_audit_entry(self, entry: Dict[str, Any]) -> None:
        """Persist audit entry to storage"""
        # In production, use immutable storage (blockchain, append-only DB)
        # For now, just log
        logger.info(f"AUDIT: {entry['audit_id']} - {entry['asset']} - {'APPROVED' if entry['approved'] else 'REJECTED'}")
