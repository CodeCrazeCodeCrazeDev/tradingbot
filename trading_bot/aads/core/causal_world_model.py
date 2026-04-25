"""
AADS Causal World Model

Models the market as a Structural Causal Model (SCM) — a directed acyclic graph
where edges represent causal mechanisms, not just correlations.

Implements Pearl's do-calculus for counterfactual market reasoning:
"What if Fed raises rates +50bp instead of +25bp?"
is answered by surgical intervention on the causal graph — not by historical replay.

Features:
- Structural Causal Model with directed edges
- do-calculus interventions (graph surgery)
- Counterfactual scenario analysis
- Agent-based market microstructure simulation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Set
from datetime import datetime
from enum import Enum
import numpy as np
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class NodeType(Enum):
    """Types of nodes in the causal graph"""
    MACRO = "macro"                 # Macroeconomic indicators
    MARKET = "market"               # Market variables (prices, vol)
    SECTOR = "sector"               # Sector-level variables
    ASSET = "asset"                 # Individual asset variables
    SENTIMENT = "sentiment"         # Sentiment indicators
    POLICY = "policy"               # Policy variables (Fed, fiscal)
    GEOPOLITICAL = "geopolitical"   # Geopolitical events


class EdgeType(Enum):
    """Types of causal relationships"""
    DIRECT = "direct"               # Direct causal effect
    MEDIATED = "mediated"           # Effect through mediator
    CONFOUNDED = "confounded"       # Shared confounder
    INSTRUMENTAL = "instrumental"   # Instrumental variable


@dataclass
class CausalNode:
    """Node in the causal graph"""
    name: str
    node_type: NodeType
    current_value: float = 0.0
    historical_values: List[Tuple[datetime, float]] = field(default_factory=list)
    
    # Structural equation parameters
    intercept: float = 0.0
    noise_std: float = 0.1
    
    # Metadata
    unit: str = ""
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'node_type': self.node_type.value,
            'current_value': self.current_value,
            'unit': self.unit,
            'description': self.description
        }


@dataclass
class CausalEdge:
    """Edge in the causal graph representing causal mechanism"""
    source: str
    target: str
    edge_type: EdgeType
    coefficient: float              # Causal effect strength
    lag_days: int = 0               # Time lag of effect
    nonlinear_fn: Optional[str] = None  # Optional nonlinear transformation
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source,
            'target': self.target,
            'edge_type': self.edge_type.value,
            'coefficient': self.coefficient,
            'lag_days': self.lag_days
        }


@dataclass
class CausalIntervention:
    """Represents a do-calculus intervention"""
    variable: str
    value: float
    intervention_type: str = "set"  # "set", "shift", "scale"
    description: str = ""


@dataclass
class InterventionResult:
    """Result of a causal intervention"""
    intervention: CausalIntervention
    observed_variables: Dict[str, float]
    counterfactual_values: Dict[str, float]
    causal_effects: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'intervention': {
                'variable': self.intervention.variable,
                'value': self.intervention.value,
                'type': self.intervention.intervention_type
            },
            'counterfactual_values': self.counterfactual_values,
            'causal_effects': self.causal_effects,
            'timestamp': self.timestamp.isoformat()
        }


class CausalWorldModel:
    """
    Structural Causal Model of financial markets.
    
    Implements:
    - Causal graph construction and maintenance
    - do-calculus interventions (graph surgery)
    - Counterfactual reasoning
    - Causal effect estimation
    """
    
    def __init__(self):
        self.nodes: Dict[str, CausalNode] = {}
        self.edges: List[CausalEdge] = []
        self.adjacency: Dict[str, List[str]] = defaultdict(list)  # parent -> children
        self.reverse_adjacency: Dict[str, List[str]] = defaultdict(list)  # child -> parents
        
        # Initialize core market causal structure
        self._initialize_market_graph()
        
        logger.info(f"CausalWorldModel initialized with {len(self.nodes)} nodes and {len(self.edges)} edges")
    
    def _initialize_market_graph(self) -> None:
        """Initialize the core causal structure of financial markets"""
        
        # ============================================================
        # MACRO POLICY NODES
        # ============================================================
        self._add_node(CausalNode(
            name="Fed_Rate",
            node_type=NodeType.POLICY,
            description="Federal Reserve target rate",
            unit="percent"
        ))
        
        self._add_node(CausalNode(
            name="Inflation",
            node_type=NodeType.MACRO,
            description="CPI year-over-year change",
            unit="percent"
        ))
        
        self._add_node(CausalNode(
            name="GDP_Growth",
            node_type=NodeType.MACRO,
            description="Real GDP growth rate",
            unit="percent"
        ))
        
        # ============================================================
        # MARKET NODES
        # ============================================================
        self._add_node(CausalNode(
            name="Bond_Yields",
            node_type=NodeType.MARKET,
            description="10-year Treasury yield",
            unit="percent"
        ))
        
        self._add_node(CausalNode(
            name="USD_Strength",
            node_type=NodeType.MARKET,
            description="Dollar index (DXY)",
            unit="index"
        ))
        
        self._add_node(CausalNode(
            name="Credit_Spreads",
            node_type=NodeType.MARKET,
            description="High yield credit spread",
            unit="bps"
        ))
        
        self._add_node(CausalNode(
            name="Equity_Valuations",
            node_type=NodeType.MARKET,
            description="S&P 500 P/E ratio",
            unit="ratio"
        ))
        
        self._add_node(CausalNode(
            name="VIX",
            node_type=NodeType.MARKET,
            description="Volatility index",
            unit="index"
        ))
        
        self._add_node(CausalNode(
            name="Risk_Appetite",
            node_type=NodeType.SENTIMENT,
            description="Market risk appetite indicator",
            unit="index"
        ))
        
        self._add_node(CausalNode(
            name="Commodity_Prices",
            node_type=NodeType.MARKET,
            description="Broad commodity index",
            unit="index"
        ))
        
        self._add_node(CausalNode(
            name="Oil_Price",
            node_type=NodeType.MARKET,
            description="WTI crude oil price",
            unit="usd"
        ))
        
        self._add_node(CausalNode(
            name="EM_Capital_Flows",
            node_type=NodeType.MARKET,
            description="Emerging market capital flows",
            unit="billion_usd"
        ))
        
        self._add_node(CausalNode(
            name="Consumer_Spending",
            node_type=NodeType.MACRO,
            description="Consumer spending growth",
            unit="percent"
        ))
        
        self._add_node(CausalNode(
            name="Real_Wages",
            node_type=NodeType.MACRO,
            description="Real wage growth",
            unit="percent"
        ))
        
        self._add_node(CausalNode(
            name="China_PMI",
            node_type=NodeType.MACRO,
            description="China manufacturing PMI",
            unit="index"
        ))
        
        # ============================================================
        # SECTOR NODES
        # ============================================================
        self._add_node(CausalNode(
            name="REIT_Prices",
            node_type=NodeType.SECTOR,
            description="REIT sector prices",
            unit="index"
        ))
        
        self._add_node(CausalNode(
            name="Energy_Sector",
            node_type=NodeType.SECTOR,
            description="Energy sector performance",
            unit="percent"
        ))
        
        self._add_node(CausalNode(
            name="Airline_Costs",
            node_type=NodeType.SECTOR,
            description="Airline operating costs",
            unit="index"
        ))
        
        # ============================================================
        # CAUSAL EDGES (Core Market Structure)
        # ============================================================
        
        # Fed Rate effects
        self._add_edge(CausalEdge("Fed_Rate", "Bond_Yields", EdgeType.DIRECT, 0.8, lag_days=0))
        self._add_edge(CausalEdge("Fed_Rate", "USD_Strength", EdgeType.DIRECT, 0.5, lag_days=1))
        self._add_edge(CausalEdge("Fed_Rate", "Credit_Spreads", EdgeType.DIRECT, 0.3, lag_days=5))
        
        # Bond Yield effects
        self._add_edge(CausalEdge("Bond_Yields", "Equity_Valuations", EdgeType.DIRECT, -0.6, lag_days=0))
        self._add_edge(CausalEdge("Bond_Yields", "REIT_Prices", EdgeType.DIRECT, -0.7, lag_days=1))
        self._add_edge(CausalEdge("Bond_Yields", "EM_Capital_Flows", EdgeType.DIRECT, -0.4, lag_days=5))
        
        # USD effects
        self._add_edge(CausalEdge("USD_Strength", "Commodity_Prices", EdgeType.DIRECT, -0.5, lag_days=0))
        self._add_edge(CausalEdge("USD_Strength", "EM_Capital_Flows", EdgeType.DIRECT, -0.3, lag_days=2))
        
        # Inflation effects
        self._add_edge(CausalEdge("Inflation", "Fed_Rate", EdgeType.DIRECT, 0.6, lag_days=30))
        self._add_edge(CausalEdge("Inflation", "Real_Wages", EdgeType.DIRECT, -0.8, lag_days=0))
        self._add_edge(CausalEdge("Inflation", "Consumer_Spending", EdgeType.MEDIATED, -0.3, lag_days=10))
        
        # Oil effects
        self._add_edge(CausalEdge("Oil_Price", "Inflation", EdgeType.DIRECT, 0.3, lag_days=30))
        self._add_edge(CausalEdge("Oil_Price", "Airline_Costs", EdgeType.DIRECT, 0.7, lag_days=0))
        self._add_edge(CausalEdge("Oil_Price", "Energy_Sector", EdgeType.DIRECT, 0.8, lag_days=0))
        self._add_edge(CausalEdge("Oil_Price", "Consumer_Spending", EdgeType.MEDIATED, -0.2, lag_days=30))
        
        # VIX effects
        self._add_edge(CausalEdge("VIX", "Risk_Appetite", EdgeType.DIRECT, -0.9, lag_days=0))
        self._add_edge(CausalEdge("VIX", "Credit_Spreads", EdgeType.DIRECT, 0.6, lag_days=0))
        
        # Risk Appetite effects
        self._add_edge(CausalEdge("Risk_Appetite", "Equity_Valuations", EdgeType.DIRECT, 0.5, lag_days=0))
        self._add_edge(CausalEdge("Risk_Appetite", "EM_Capital_Flows", EdgeType.DIRECT, 0.4, lag_days=2))
        
        # China PMI effects
        self._add_edge(CausalEdge("China_PMI", "Commodity_Prices", EdgeType.DIRECT, 0.4, lag_days=5))
        self._add_edge(CausalEdge("China_PMI", "EM_Capital_Flows", EdgeType.DIRECT, 0.3, lag_days=5))
        
        # Consumer Spending effects
        self._add_edge(CausalEdge("Consumer_Spending", "GDP_Growth", EdgeType.DIRECT, 0.7, lag_days=30))
        self._add_edge(CausalEdge("Real_Wages", "Consumer_Spending", EdgeType.DIRECT, 0.5, lag_days=10))
    
    def _add_node(self, node: CausalNode) -> None:
        """Add a node to the graph"""
        self.nodes[node.name] = node
    
    def _add_edge(self, edge: CausalEdge) -> None:
        """Add an edge to the graph"""
        self.edges.append(edge)
        self.adjacency[edge.source].append(edge.target)
        self.reverse_adjacency[edge.target].append(edge.source)
    
    def set_node_value(self, name: str, value: float) -> None:
        """Set the current value of a node"""
        if name in self.nodes:
            self.nodes[name].current_value = value
            self.nodes[name].historical_values.append((datetime.now(), value))
    
    def get_node_value(self, name: str) -> float:
        """Get the current value of a node"""
        return self.nodes.get(name, CausalNode(name, NodeType.MACRO)).current_value
    
    def intervene(
        self,
        variable: str,
        value: float,
        observe: List[str]
    ) -> InterventionResult:
        """
        Perform do-calculus intervention: do(variable = value)
        
        Graph surgery: set variable to value, cut all incoming edges,
        propagate effects through causal mechanisms.
        
        Args:
            variable: Variable to intervene on
            value: Value to set
            observe: Variables to observe effects on
            
        Returns:
            InterventionResult with counterfactual values
        """
        if variable not in self.nodes:
            raise ValueError(f"Unknown variable: {variable}")
        
        intervention = CausalIntervention(variable=variable, value=value)
        
        # Store original values
        original_values = {name: node.current_value for name, node in self.nodes.items()}
        
        # Graph surgery: set intervention value
        intervened_values = original_values.copy()
        intervened_values[variable] = value
        
        # Propagate effects through the graph (topological order)
        propagation_order = self._get_topological_order(starting_from=variable)
        
        for node_name in propagation_order:
            if node_name == variable:
                continue  # Skip the intervened variable
            
            # Calculate new value based on parents
            new_value = self._calculate_node_value(node_name, intervened_values)
            intervened_values[node_name] = new_value
        
        # Calculate causal effects
        causal_effects = {}
        counterfactual_values = {}
        confidence_intervals = {}
        
        for obs_var in observe:
            if obs_var in intervened_values:
                counterfactual_values[obs_var] = intervened_values[obs_var]
                causal_effects[obs_var] = intervened_values[obs_var] - original_values.get(obs_var, 0)
                
                # Simple confidence interval (would be more sophisticated in production)
                effect = causal_effects[obs_var]
                ci_width = abs(effect) * 0.2  # 20% uncertainty
                confidence_intervals[obs_var] = (effect - ci_width, effect + ci_width)
        
        return InterventionResult(
            intervention=intervention,
            observed_variables={v: original_values.get(v, 0) for v in observe},
            counterfactual_values=counterfactual_values,
            causal_effects=causal_effects,
            confidence_intervals=confidence_intervals
        )
    
    def _calculate_node_value(self, node_name: str, current_values: Dict[str, float]) -> float:
        """Calculate node value based on structural equation"""
        node = self.nodes[node_name]
        
        # Start with intercept
        value = node.intercept
        
        # Add contributions from parent nodes
        for edge in self.edges:
            if edge.target == node_name:
                parent_value = current_values.get(edge.source, 0)
                contribution = parent_value * edge.coefficient
                value += contribution
        
        # Add noise
        value += np.random.normal(0, node.noise_std)
        
        return value
    
    def _get_topological_order(self, starting_from: Optional[str] = None) -> List[str]:
        """Get topological ordering of nodes for propagation"""
        visited = set()
        order = []
        
        def dfs(node: str):
            if node in visited:
                return
            visited.add(node)
            for child in self.adjacency.get(node, []):
                dfs(child)
            order.append(node)
        
        if starting_from:
            dfs(starting_from)
        else:
            for node in self.nodes:
                dfs(node)
        
        return list(reversed(order))
    
    def counterfactual_trade_analysis(
        self,
        trade_asset: str,
        trade_direction: str,
        current_exposure: float
    ) -> Dict[str, InterventionResult]:
        """
        Run causal counterfactuals for a candidate trade.
        
        Scenarios:
        - Fed hawk surprise (+75bp instead of +25bp)
        - China PMI miss (48.0)
        - VIX spike to 35
        - Oil shock +30%
        
        Args:
            trade_asset: Asset being traded
            trade_direction: "long" or "short"
            current_exposure: Current position size
            
        Returns:
            Dict of scenario name -> InterventionResult
        """
        observe_vars = ["Bond_Yields", "USD_Strength", "Equity_Valuations", 
                       "Risk_Appetite", "Credit_Spreads", "EM_Capital_Flows",
                       "Commodity_Prices", "Consumer_Spending"]
        
        scenarios = {}
        
        # Scenario 1: Fed hawk surprise
        current_fed = self.get_node_value("Fed_Rate")
        scenarios["fed_hawk_surprise"] = self.intervene(
            variable="Fed_Rate",
            value=current_fed + 0.75,  # +75bp
            observe=observe_vars
        )
        
        # Scenario 2: China PMI miss
        scenarios["china_pmi_miss"] = self.intervene(
            variable="China_PMI",
            value=48.0,  # Contraction territory
            observe=observe_vars
        )
        
        # Scenario 3: VIX spike
        scenarios["vix_spike_35"] = self.intervene(
            variable="VIX",
            value=35.0,
            observe=observe_vars
        )
        
        # Scenario 4: Oil shock
        current_oil = self.get_node_value("Oil_Price")
        scenarios["oil_shock_plus30"] = self.intervene(
            variable="Oil_Price",
            value=current_oil * 1.30,  # +30%
            observe=observe_vars
        )
        
        return scenarios
    
    def get_causal_path(self, source: str, target: str) -> List[List[str]]:
        """Find all causal paths from source to target"""
        paths = []
        
        def dfs(current: str, path: List[str]):
            if current == target:
                paths.append(path.copy())
                return
            
            for child in self.adjacency.get(current, []):
                if child not in path:  # Avoid cycles
                    path.append(child)
                    dfs(child, path)
                    path.pop()
        
        dfs(source, [source])
        return paths
    
    def get_total_causal_effect(self, source: str, target: str) -> float:
        """Calculate total causal effect from source to target"""
        paths = self.get_causal_path(source, target)
        
        if not paths:
            return 0.0
        
        total_effect = 0.0
        
        for path in paths:
            path_effect = 1.0
            for i in range(len(path) - 1):
                # Find edge coefficient
                for edge in self.edges:
                    if edge.source == path[i] and edge.target == path[i + 1]:
                        path_effect *= edge.coefficient
                        break
            total_effect += path_effect
        
        return total_effect
    
    def get_graph_summary(self) -> Dict[str, Any]:
        """Get summary of the causal graph"""
        return {
            'num_nodes': len(self.nodes),
            'num_edges': len(self.edges),
            'node_types': {
                nt.value: sum(1 for n in self.nodes.values() if n.node_type == nt)
                for nt in NodeType
            },
            'nodes': [n.name for n in self.nodes.values()],
            'key_relationships': [
                f"{e.source} -> {e.target} ({e.coefficient:+.2f})"
                for e in self.edges[:10]
            ]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the causal model"""
        return {
            'nodes': {name: node.to_dict() for name, node in self.nodes.items()},
            'edges': [edge.to_dict() for edge in self.edges],
            'summary': self.get_graph_summary()
        }


# ============================================================================
# Agent-Based Market Microstructure Simulation
# ============================================================================

@dataclass
class MarketAgent:
    """Agent in the market microstructure simulation"""
    agent_type: str
    count: int
    lag: int
    mean_reversion: bool = False
    value_anchor: bool = False
    inventory_averse: bool = False
    rebalance_triggered: bool = False
    threshold_triggered: bool = False
    
    def generate_order_flow(self, price_history: List[float], current_price: float) -> float:
        """Generate order flow based on agent type"""
        if len(price_history) < self.lag + 1:
            return 0.0
        
        if self.mean_reversion:
            # Mean reversion: buy low, sell high
            mean_price = np.mean(price_history[-self.lag:])
            deviation = (current_price - mean_price) / mean_price
            return -deviation * self.count * 0.1
        
        elif self.value_anchor:
            # Fundamental: compare to anchor value
            anchor = np.mean(price_history[-self.lag:])
            deviation = (current_price - anchor) / anchor
            return -deviation * self.count * 0.05
        
        elif self.inventory_averse:
            # Market maker: provide liquidity
            return np.random.normal(0, self.count * 0.01)
        
        elif self.threshold_triggered:
            # Panic sellers: activate on drawdown
            if len(price_history) > 20:
                recent_high = max(price_history[-20:])
                drawdown = (recent_high - current_price) / recent_high
                if drawdown > 0.05:
                    return -self.count * drawdown * 10
            return 0.0
        
        else:
            # Momentum: follow trend
            if len(price_history) >= self.lag:
                momentum = (current_price - price_history[-self.lag]) / price_history[-self.lag]
                return momentum * self.count * 0.1
        
        return 0.0


class AgentBasedSimulator:
    """
    Agent-based market microstructure simulation.
    
    Models competing market participants to capture non-linear dynamics
    that econometric models miss.
    """
    
    MARKET_AGENTS = {
        "momentum_traders": MarketAgent("momentum", 500, 5, mean_reversion=False),
        "mean_reversion": MarketAgent("mean_reversion", 300, 20, mean_reversion=True),
        "fundamental_investors": MarketAgent("fundamental", 100, 63, value_anchor=True),
        "hft_market_makers": MarketAgent("hft", 50, 0, inventory_averse=True),
        "passive_etf_flows": MarketAgent("passive", 20, 0, rebalance_triggered=True),
        "panic_sellers": MarketAgent("panic", 0, 0, threshold_triggered=True),
    }
    
    def __init__(self, initial_price: float = 100.0):
        self.initial_price = initial_price
        self.price_history: List[float] = [initial_price]
        self.order_flow_history: List[float] = []
    
    def simulate_step(self) -> float:
        """Simulate one time step"""
        current_price = self.price_history[-1]
        
        # Aggregate order flow from all agents
        total_order_flow = 0.0
        for agent in self.MARKET_AGENTS.values():
            flow = agent.generate_order_flow(self.price_history, current_price)
            total_order_flow += flow
        
        # Price impact
        price_impact = total_order_flow * 0.0001  # 1bp per unit flow
        
        # Random noise
        noise = np.random.normal(0, current_price * 0.001)
        
        # New price
        new_price = current_price * (1 + price_impact + noise)
        new_price = max(new_price, 0.01)  # Floor at near-zero
        
        self.price_history.append(new_price)
        self.order_flow_history.append(total_order_flow)
        
        return new_price
    
    def simulate(self, steps: int = 252) -> Dict[str, Any]:
        """Run simulation for multiple steps"""
        for _ in range(steps):
            self.simulate_step()
        
        returns = np.diff(self.price_history) / self.price_history[:-1]
        
        return {
            'final_price': self.price_history[-1],
            'total_return': (self.price_history[-1] - self.initial_price) / self.initial_price,
            'volatility': np.std(returns) * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown(),
            'price_history': self.price_history,
            'order_flow_history': self.order_flow_history
        }
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        peak = self.price_history[0]
        max_dd = 0.0
        
        for price in self.price_history:
            if price > peak:
                peak = price
            dd = (peak - price) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd
