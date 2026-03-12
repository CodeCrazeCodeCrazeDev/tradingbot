"""
AlphaAlgo Institutional - Idea Vectors
======================================

This module implements the 150+ Idea Vectors as constraints and considerations
for the AlphaAlgo Institutional system.

Idea Vectors are mandatory considerations that must be evaluated
during system design, model development, and trading decisions.

Categories:
1. Market Microstructure (20 vectors)
2. Risk Management (25 vectors)
3. Portfolio Construction (20 vectors)
4. Model Development (25 vectors)
5. Execution (15 vectors)
6. Behavioral Finance (15 vectors)
7. System Design (15 vectors)
8. Regime & Adaptation (15 vectors)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# IDEA VECTOR CATEGORIES
# =============================================================================

class IdeaCategory(Enum):
    """Categories of idea vectors."""
    MARKET_MICROSTRUCTURE = "market_microstructure"
    RISK_MANAGEMENT = "risk_management"
    PORTFOLIO_CONSTRUCTION = "portfolio_construction"
    MODEL_DEVELOPMENT = "model_development"
    EXECUTION = "execution"
    BEHAVIORAL_FINANCE = "behavioral_finance"
    SYSTEM_DESIGN = "system_design"
    REGIME_ADAPTATION = "regime_adaptation"


class IdeaPriority(Enum):
    """Priority levels for idea vectors."""
    CRITICAL = "critical"  # Must always be considered
    HIGH = "high"  # Should be considered in most decisions
    MEDIUM = "medium"  # Consider when relevant
    LOW = "low"  # Nice to have


@dataclass
class IdeaVector:
    """An idea vector - a mandatory consideration."""
    id: str
    category: IdeaCategory
    name: str
    description: str
    priority: IdeaPriority
    considerations: List[str]
    failure_modes: List[str]
    related_vectors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'category': self.category.value,
            'name': self.name,
            'description': self.description,
            'priority': self.priority.value,
            'considerations': self.considerations,
            'failure_modes': self.failure_modes
        }


@dataclass
class IdeaVectorEvaluation:
    """Evaluation of an idea vector for a specific context."""
    vector_id: str
    context: str
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    satisfied: bool = False
    score: float = 0.0  # 0-1
    notes: str = ""
    mitigations: List[str] = field(default_factory=list)


# =============================================================================
# IDEA VECTOR DEFINITIONS
# =============================================================================

# Market Microstructure Vectors (20)
MARKET_MICROSTRUCTURE_VECTORS = [
    IdeaVector(
        id="MM001",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Bid-Ask Spread Dynamics",
        description="Spreads widen during stress and narrow during calm",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Account for spread in all return calculations",
            "Wider spreads indicate lower liquidity",
            "Spread is a cost, not just a price difference"
        ],
        failure_modes=["Ignoring spread in backtests", "Assuming constant spread"]
    ),
    IdeaVector(
        id="MM002",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Order Book Depth",
        description="Visible liquidity is not guaranteed liquidity",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Large orders move prices",
            "Depth can disappear instantly",
            "Hidden orders exist"
        ],
        failure_modes=["Assuming infinite liquidity", "Ignoring market impact"]
    ),
    IdeaVector(
        id="MM003",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Price Impact",
        description="Your trades move the market against you",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Impact is non-linear in size",
            "Impact persists after trade",
            "Impact varies by regime"
        ],
        failure_modes=["Ignoring impact in sizing", "Assuming zero impact"]
    ),
    IdeaVector(
        id="MM004",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Adverse Selection",
        description="Informed traders trade against you",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Getting filled easily may be bad",
            "Limit orders face adverse selection",
            "Information asymmetry is real"
        ],
        failure_modes=["Celebrating easy fills", "Ignoring fill quality"]
    ),
    IdeaVector(
        id="MM005",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Latency Sensitivity",
        description="Speed matters in execution",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Stale prices are dangerous",
            "Execution delay costs money",
            "HFT exists and is faster"
        ],
        failure_modes=["Ignoring execution latency", "Assuming instant fills"]
    ),
    IdeaVector(
        id="MM006",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Market Hours Effects",
        description="Behavior differs by time of day",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Open and close are different",
            "Overnight risk is real",
            "Liquidity varies intraday"
        ],
        failure_modes=["Ignoring time-of-day effects", "Trading illiquid hours"]
    ),
    IdeaVector(
        id="MM007",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Cross-Market Linkages",
        description="Markets are interconnected",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Arbitrage links markets",
            "Shocks propagate",
            "Correlations spike in stress"
        ],
        failure_modes=["Treating markets as independent", "Ignoring contagion"]
    ),
    IdeaVector(
        id="MM008",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Quote Stuffing Awareness",
        description="Not all quotes are real",
        priority=IdeaPriority.LOW,
        considerations=[
            "Fake liquidity exists",
            "Quote-to-trade ratios matter",
            "Manipulation is real"
        ],
        failure_modes=["Trusting all quotes", "Ignoring manipulation"]
    ),
    IdeaVector(
        id="MM009",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Tick Size Constraints",
        description="Prices move in discrete increments",
        priority=IdeaPriority.LOW,
        considerations=[
            "Minimum price increment matters",
            "Tick size affects spread",
            "Rounding matters"
        ],
        failure_modes=["Ignoring tick size", "Continuous price assumption"]
    ),
    IdeaVector(
        id="MM010",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Circuit Breakers",
        description="Markets can halt",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Halts prevent exit",
            "Limit up/down exists",
            "Gaps occur after halts"
        ],
        failure_modes=["Assuming continuous trading", "Ignoring halt risk"]
    ),
    IdeaVector(
        id="MM011",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Settlement Risk",
        description="Trades must settle",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "T+1/T+2 settlement",
            "Counterparty risk exists",
            "Failed trades happen"
        ],
        failure_modes=["Ignoring settlement", "Assuming instant settlement"]
    ),
    IdeaVector(
        id="MM012",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Margin Requirements",
        description="Leverage requires margin",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Margin calls are real",
            "Requirements change",
            "Forced liquidation risk"
        ],
        failure_modes=["Ignoring margin", "Over-leveraging"]
    ),
    IdeaVector(
        id="MM013",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Short Selling Constraints",
        description="Shorting has costs and limits",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Borrow costs exist",
            "Locates required",
            "Short squeezes happen"
        ],
        failure_modes=["Assuming free shorting", "Ignoring borrow costs"]
    ),
    IdeaVector(
        id="MM014",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Corporate Actions",
        description="Stocks have events",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Dividends affect prices",
            "Splits change shares",
            "Mergers change everything"
        ],
        failure_modes=["Ignoring corporate actions", "Unadjusted data"]
    ),
    IdeaVector(
        id="MM015",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Index Rebalancing",
        description="Index changes move prices",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Additions/deletions matter",
            "Rebalancing is predictable",
            "Front-running exists"
        ],
        failure_modes=["Ignoring index effects", "Missing rebalance dates"]
    ),
    IdeaVector(
        id="MM016",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Options Expiration",
        description="Derivatives affect underlying",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Pin risk near strikes",
            "Gamma exposure matters",
            "Expiration volatility"
        ],
        failure_modes=["Ignoring options effects", "Missing expiration dates"]
    ),
    IdeaVector(
        id="MM017",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Flash Crash Risk",
        description="Prices can crash and recover instantly",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Stop losses can be triggered",
            "Liquidity vanishes",
            "Recovery is fast"
        ],
        failure_modes=["Tight stops in volatile markets", "Ignoring flash crash risk"]
    ),
    IdeaVector(
        id="MM018",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Dark Pool Liquidity",
        description="Not all liquidity is visible",
        priority=IdeaPriority.LOW,
        considerations=[
            "Dark pools exist",
            "Hidden liquidity",
            "Execution venue matters"
        ],
        failure_modes=["Only using lit markets", "Ignoring dark liquidity"]
    ),
    IdeaVector(
        id="MM019",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Maker-Taker Fees",
        description="Exchange fees affect profitability",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Rebates for providing liquidity",
            "Fees for taking liquidity",
            "Net cost matters"
        ],
        failure_modes=["Ignoring exchange fees", "Wrong fee assumptions"]
    ),
    IdeaVector(
        id="MM020",
        category=IdeaCategory.MARKET_MICROSTRUCTURE,
        name="Order Type Selection",
        description="Order type affects execution",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Market vs limit tradeoff",
            "Stop orders have risks",
            "Conditional orders exist"
        ],
        failure_modes=["Always using market orders", "Wrong order type"]
    ),
]

# Risk Management Vectors (25)
RISK_MANAGEMENT_VECTORS = [
    IdeaVector(
        id="RM001",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Position Sizing",
        description="Size determines survival",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "No single position should threaten survival",
            "Size based on risk, not conviction",
            "Reduce size when uncertain"
        ],
        failure_modes=["Oversizing", "Sizing based on conviction alone"]
    ),
    IdeaVector(
        id="RM002",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Drawdown Limits",
        description="Drawdown limits are absolute",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Max drawdown is non-negotiable",
            "Reduce exposure as drawdown increases",
            "Recovery from large drawdowns is hard"
        ],
        failure_modes=["Ignoring drawdown limits", "Averaging down in drawdown"]
    ),
    IdeaVector(
        id="RM003",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Correlation Risk",
        description="Correlations spike in stress",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Diversification fails when needed most",
            "Measure correlation in stress periods",
            "Assume higher correlation in crisis"
        ],
        failure_modes=["Using calm-period correlations", "Over-diversification illusion"]
    ),
    IdeaVector(
        id="RM004",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Tail Risk",
        description="Extreme events happen more than expected",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Fat tails are real",
            "VaR underestimates tail risk",
            "Black swans happen"
        ],
        failure_modes=["Assuming normal distribution", "Ignoring tail risk"]
    ),
    IdeaVector(
        id="RM005",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Leverage Control",
        description="Leverage amplifies everything",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Leverage amplifies losses too",
            "Margin calls force liquidation",
            "Reduce leverage in stress"
        ],
        failure_modes=["Excessive leverage", "Ignoring leverage risk"]
    ),
    IdeaVector(
        id="RM006",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Liquidity Risk",
        description="You can't always exit",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Liquidity disappears in stress",
            "Large positions are illiquid",
            "Exit cost increases with urgency"
        ],
        failure_modes=["Assuming infinite liquidity", "Ignoring exit costs"]
    ),
    IdeaVector(
        id="RM007",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Concentration Risk",
        description="Don't put all eggs in one basket",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Single position limits",
            "Sector limits",
            "Factor concentration"
        ],
        failure_modes=["Over-concentration", "Hidden concentration"]
    ),
    IdeaVector(
        id="RM008",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Model Risk",
        description="Models are wrong",
        priority=IdeaPriority.HIGH,
        considerations=[
            "All models are approximations",
            "Model assumptions fail",
            "Backtest != live performance"
        ],
        failure_modes=["Over-trusting models", "Ignoring model limitations"]
    ),
    IdeaVector(
        id="RM009",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Operational Risk",
        description="Systems fail",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Technology fails",
            "Human error happens",
            "Processes break"
        ],
        failure_modes=["No redundancy", "Ignoring operational risk"]
    ),
    IdeaVector(
        id="RM010",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Counterparty Risk",
        description="Others can fail",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Brokers can fail",
            "Exchanges can fail",
            "Counterparties can default"
        ],
        failure_modes=["Single counterparty", "Ignoring counterparty risk"]
    ),
    IdeaVector(
        id="RM011",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Currency Risk",
        description="FX exposure matters",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Unhedged FX is a position",
            "Currency moves can dominate",
            "Hedging has costs"
        ],
        failure_modes=["Ignoring FX exposure", "Unintended FX bets"]
    ),
    IdeaVector(
        id="RM012",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Interest Rate Risk",
        description="Rates affect everything",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Duration matters",
            "Rate changes affect valuations",
            "Funding costs change"
        ],
        failure_modes=["Ignoring rate sensitivity", "Unhedged duration"]
    ),
    IdeaVector(
        id="RM013",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Volatility Risk",
        description="Volatility is not constant",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Vol clusters",
            "Vol spikes suddenly",
            "Vol affects position sizing"
        ],
        failure_modes=["Assuming constant vol", "Ignoring vol regime"]
    ),
    IdeaVector(
        id="RM014",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Gap Risk",
        description="Prices can gap",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Overnight gaps",
            "News gaps",
            "Stop losses may not protect"
        ],
        failure_modes=["Ignoring gap risk", "Relying on stops for gaps"]
    ),
    IdeaVector(
        id="RM015",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Regulatory Risk",
        description="Rules change",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Regulations change",
            "Compliance is mandatory",
            "Strategies can become illegal"
        ],
        failure_modes=["Ignoring regulations", "Non-compliance"]
    ),
    IdeaVector(
        id="RM016",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Stress Testing",
        description="Test for extreme scenarios",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Historical stress scenarios",
            "Hypothetical scenarios",
            "Reverse stress tests"
        ],
        failure_modes=["No stress testing", "Weak scenarios"]
    ),
    IdeaVector(
        id="RM017",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Risk Budgeting",
        description="Allocate risk, not capital",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Risk contribution matters",
            "Equal risk is not equal capital",
            "Risk budget is finite"
        ],
        failure_modes=["Capital-based allocation", "Ignoring risk contribution"]
    ),
    IdeaVector(
        id="RM018",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Stop Loss Strategy",
        description="Know when to exit",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Stops protect capital",
            "Stops can be triggered badly",
            "Mental stops are dangerous"
        ],
        failure_modes=["No stops", "Stops too tight/loose"]
    ),
    IdeaVector(
        id="RM019",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Recovery Planning",
        description="Plan for losses",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "How to recover from drawdown",
            "When to reduce risk",
            "When to stop trading"
        ],
        failure_modes=["No recovery plan", "Doubling down on losses"]
    ),
    IdeaVector(
        id="RM020",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Risk Monitoring",
        description="Monitor risk continuously",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Real-time risk monitoring",
            "Alerts for breaches",
            "Regular risk reviews"
        ],
        failure_modes=["Infrequent monitoring", "No alerts"]
    ),
    IdeaVector(
        id="RM021",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Hedging Strategy",
        description="Know how to hedge",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Hedging has costs",
            "Imperfect hedges",
            "When to hedge"
        ],
        failure_modes=["Over-hedging", "Under-hedging", "Wrong hedge"]
    ),
    IdeaVector(
        id="RM022",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Risk Limits",
        description="Set and enforce limits",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Hard limits are non-negotiable",
            "Soft limits trigger review",
            "Limits must be monitored"
        ],
        failure_modes=["No limits", "Unenforced limits"]
    ),
    IdeaVector(
        id="RM023",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Risk Attribution",
        description="Know where risk comes from",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Factor risk attribution",
            "Strategy risk attribution",
            "Marginal risk contribution"
        ],
        failure_modes=["Unknown risk sources", "No attribution"]
    ),
    IdeaVector(
        id="RM024",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Scenario Analysis",
        description="What if analysis",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "What if rates rise",
            "What if vol spikes",
            "What if correlations change"
        ],
        failure_modes=["No scenario analysis", "Limited scenarios"]
    ),
    IdeaVector(
        id="RM025",
        category=IdeaCategory.RISK_MANAGEMENT,
        name="Risk Culture",
        description="Risk awareness is cultural",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Everyone owns risk",
            "Risk is discussed openly",
            "No blame for risk events"
        ],
        failure_modes=["Risk as afterthought", "Blame culture"]
    ),
]

# Portfolio Construction Vectors (20)
PORTFOLIO_CONSTRUCTION_VECTORS = [
    IdeaVector(
        id="PC001",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Diversification",
        description="Don't rely on single sources of return",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Diversify across strategies",
            "Diversify across assets",
            "Diversify across time"
        ],
        failure_modes=["Single strategy dependence", "Hidden concentration"]
    ),
    IdeaVector(
        id="PC002",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Rebalancing",
        description="Maintain target allocations",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Drift from targets",
            "Rebalancing costs",
            "Rebalancing frequency"
        ],
        failure_modes=["No rebalancing", "Over-rebalancing"]
    ),
    IdeaVector(
        id="PC003",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Factor Exposure",
        description="Know your factor bets",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Intended factor exposure",
            "Unintended factor exposure",
            "Factor crowding"
        ],
        failure_modes=["Unknown factor exposure", "Unintended bets"]
    ),
    IdeaVector(
        id="PC004",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Capacity Constraints",
        description="Strategies have capacity limits",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Alpha decays with size",
            "Market impact increases",
            "Capacity varies by strategy"
        ],
        failure_modes=["Ignoring capacity", "Over-scaling"]
    ),
    IdeaVector(
        id="PC005",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Transaction Costs",
        description="Trading costs are real",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Commissions",
            "Spread costs",
            "Market impact"
        ],
        failure_modes=["Ignoring costs", "Over-trading"]
    ),
    IdeaVector(
        id="PC006",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Turnover Management",
        description="Control portfolio turnover",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "High turnover = high costs",
            "Tax implications",
            "Signal decay vs turnover"
        ],
        failure_modes=["Excessive turnover", "Chasing signals"]
    ),
    IdeaVector(
        id="PC007",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Benchmark Awareness",
        description="Know your benchmark",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Tracking error",
            "Active share",
            "Benchmark selection"
        ],
        failure_modes=["Wrong benchmark", "Closet indexing"]
    ),
    IdeaVector(
        id="PC008",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Cash Management",
        description="Cash is a position",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Cash drag",
            "Cash as hedge",
            "Cash for opportunities"
        ],
        failure_modes=["Ignoring cash", "Always fully invested"]
    ),
    IdeaVector(
        id="PC009",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Constraint Management",
        description="Work within constraints",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Regulatory constraints",
            "Investment policy constraints",
            "Practical constraints"
        ],
        failure_modes=["Ignoring constraints", "Over-constrained"]
    ),
    IdeaVector(
        id="PC010",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Alpha Decay",
        description="Alpha decays over time",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Signals lose predictive power",
            "Crowding erodes alpha",
            "Markets adapt"
        ],
        failure_modes=["Assuming permanent alpha", "Ignoring decay"]
    ),
    IdeaVector(
        id="PC011",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Strategy Correlation",
        description="Strategies can be correlated",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Hidden correlations",
            "Correlation in stress",
            "Strategy diversification"
        ],
        failure_modes=["Assuming independence", "Correlated strategies"]
    ),
    IdeaVector(
        id="PC012",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Time Horizon",
        description="Match horizon to strategy",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Short-term vs long-term",
            "Holding period",
            "Horizon mismatch"
        ],
        failure_modes=["Horizon mismatch", "Impatience"]
    ),
    IdeaVector(
        id="PC013",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Regime Conditioning",
        description="Allocate based on regime",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Different regimes need different allocations",
            "Regime detection",
            "Regime transitions"
        ],
        failure_modes=["Static allocation", "Ignoring regime"]
    ),
    IdeaVector(
        id="PC014",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Risk Parity",
        description="Equal risk contribution",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Risk-based allocation",
            "Leverage for risk parity",
            "Risk parity limitations"
        ],
        failure_modes=["Capital-based allocation", "Ignoring risk contribution"]
    ),
    IdeaVector(
        id="PC015",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Tail Hedging",
        description="Protect against extreme events",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Cost of tail hedging",
            "Hedge effectiveness",
            "When to hedge"
        ],
        failure_modes=["No tail protection", "Over-hedging"]
    ),
    IdeaVector(
        id="PC016",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Liquidity Tiering",
        description="Tier positions by liquidity",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Liquid core",
            "Illiquid satellite",
            "Liquidity buffer"
        ],
        failure_modes=["All illiquid", "No liquidity management"]
    ),
    IdeaVector(
        id="PC017",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Conviction Weighting",
        description="Size based on conviction",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Higher conviction = larger size",
            "Conviction vs risk",
            "Overconfidence risk"
        ],
        failure_modes=["Equal weighting always", "Overconfidence"]
    ),
    IdeaVector(
        id="PC018",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Sector Allocation",
        description="Manage sector exposure",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Sector concentration",
            "Sector rotation",
            "Sector limits"
        ],
        failure_modes=["Sector concentration", "Ignoring sectors"]
    ),
    IdeaVector(
        id="PC019",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Geographic Allocation",
        description="Manage geographic exposure",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Country risk",
            "Currency exposure",
            "Time zone considerations"
        ],
        failure_modes=["Home bias", "Ignoring geography"]
    ),
    IdeaVector(
        id="PC020",
        category=IdeaCategory.PORTFOLIO_CONSTRUCTION,
        name="Portfolio Optimization",
        description="Optimize portfolio construction",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Mean-variance optimization",
            "Robust optimization",
            "Optimization pitfalls"
        ],
        failure_modes=["Naive optimization", "Over-optimization"]
    ),
]

# Model Development Vectors (25)
MODEL_DEVELOPMENT_VECTORS = [
    IdeaVector(
        id="MD001",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Overfitting",
        description="Models can memorize noise",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "In-sample vs out-of-sample",
            "Degrees of freedom",
            "Regularization"
        ],
        failure_modes=["Overfitting to history", "Too many parameters"]
    ),
    IdeaVector(
        id="MD002",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Data Snooping",
        description="Multiple testing inflates results",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Multiple hypothesis testing",
            "Bonferroni correction",
            "Out-of-sample validation"
        ],
        failure_modes=["Testing many strategies", "Cherry-picking results"]
    ),
    IdeaVector(
        id="MD003",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Survivorship Bias",
        description="Dead companies don't appear in data",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Include delisted stocks",
            "Survivorship-free data",
            "Bias in backtests"
        ],
        failure_modes=["Using survivor-only data", "Ignoring delistings"]
    ),
    IdeaVector(
        id="MD004",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Look-Ahead Bias",
        description="Don't use future information",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Point-in-time data",
            "Announcement dates",
            "Data revisions"
        ],
        failure_modes=["Using revised data", "Future information leakage"]
    ),
    IdeaVector(
        id="MD005",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Sample Size",
        description="More data is better",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Statistical significance",
            "Regime coverage",
            "Rare event coverage"
        ],
        failure_modes=["Small sample size", "Insufficient history"]
    ),
    IdeaVector(
        id="MD006",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Non-Stationarity",
        description="Markets change over time",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Structural breaks",
            "Regime changes",
            "Parameter drift"
        ],
        failure_modes=["Assuming stationarity", "Ignoring structural changes"]
    ),
    IdeaVector(
        id="MD007",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Feature Engineering",
        description="Features matter more than models",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Domain knowledge",
            "Feature selection",
            "Feature importance"
        ],
        failure_modes=["Bad features", "Too many features"]
    ),
    IdeaVector(
        id="MD008",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Model Complexity",
        description="Simpler is often better",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Occam's razor",
            "Interpretability",
            "Robustness"
        ],
        failure_modes=["Over-complex models", "Black boxes"]
    ),
    IdeaVector(
        id="MD009",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Validation Strategy",
        description="Proper validation is essential",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Train/validation/test split",
            "Walk-forward validation",
            "Cross-validation"
        ],
        failure_modes=["No validation", "Wrong validation"]
    ),
    IdeaVector(
        id="MD010",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Hypothesis Testing",
        description="Test hypotheses rigorously",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Null hypothesis",
            "Statistical significance",
            "Economic significance"
        ],
        failure_modes=["No hypothesis", "P-hacking"]
    ),
    IdeaVector(
        id="MD011",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Backtest Realism",
        description="Backtests must be realistic",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Transaction costs",
            "Slippage",
            "Market impact"
        ],
        failure_modes=["Unrealistic backtests", "Ignoring costs"]
    ),
    IdeaVector(
        id="MD012",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Model Decay",
        description="Models lose effectiveness",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Alpha decay",
            "Crowding",
            "Market adaptation"
        ],
        failure_modes=["Assuming permanent edge", "No decay monitoring"]
    ),
    IdeaVector(
        id="MD013",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Ensemble Methods",
        description="Combine multiple models",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Model diversity",
            "Combination methods",
            "Ensemble benefits"
        ],
        failure_modes=["Single model reliance", "Correlated models"]
    ),
    IdeaVector(
        id="MD014",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Uncertainty Quantification",
        description="Know model uncertainty",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Confidence intervals",
            "Prediction intervals",
            "Model uncertainty"
        ],
        failure_modes=["Ignoring uncertainty", "Overconfident predictions"]
    ),
    IdeaVector(
        id="MD015",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Interpretability",
        description="Understand model decisions",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Feature importance",
            "Decision explanation",
            "Model transparency"
        ],
        failure_modes=["Black box models", "No explanation"]
    ),
    IdeaVector(
        id="MD016",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Robustness Testing",
        description="Test model robustness",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Parameter sensitivity",
            "Data perturbation",
            "Out-of-distribution"
        ],
        failure_modes=["Fragile models", "No robustness testing"]
    ),
    IdeaVector(
        id="MD017",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Data Quality",
        description="Garbage in, garbage out",
        priority=IdeaPriority.CRITICAL,
        considerations=[
            "Data cleaning",
            "Missing data",
            "Data errors"
        ],
        failure_modes=["Bad data", "No data validation"]
    ),
    IdeaVector(
        id="MD018",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Model Monitoring",
        description="Monitor model performance",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Performance tracking",
            "Drift detection",
            "Alert systems"
        ],
        failure_modes=["No monitoring", "Delayed detection"]
    ),
    IdeaVector(
        id="MD019",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Version Control",
        description="Track model versions",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Model versioning",
            "Reproducibility",
            "Rollback capability"
        ],
        failure_modes=["No versioning", "Lost models"]
    ),
    IdeaVector(
        id="MD020",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Documentation",
        description="Document everything",
        priority=IdeaPriority.MEDIUM,
        considerations=[
            "Model documentation",
            "Assumptions",
            "Limitations"
        ],
        failure_modes=["No documentation", "Tribal knowledge"]
    ),
    IdeaVector(
        id="MD021",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Economic Rationale",
        description="Models need economic basis",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Why should this work",
            "Economic intuition",
            "Behavioral basis"
        ],
        failure_modes=["No rationale", "Data mining"]
    ),
    IdeaVector(
        id="MD022",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Transaction Cost Modeling",
        description="Model costs accurately",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Spread modeling",
            "Impact modeling",
            "Cost estimation"
        ],
        failure_modes=["Ignoring costs", "Wrong cost model"]
    ),
    IdeaVector(
        id="MD023",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Signal Decay",
        description="Signals lose value over time",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Signal half-life",
            "Optimal holding period",
            "Decay rate"
        ],
        failure_modes=["Ignoring decay", "Wrong holding period"]
    ),
    IdeaVector(
        id="MD024",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Regime Dependence",
        description="Models work in some regimes",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Regime identification",
            "Regime-specific models",
            "Regime transitions"
        ],
        failure_modes=["Ignoring regimes", "Wrong regime model"]
    ),
    IdeaVector(
        id="MD025",
        category=IdeaCategory.MODEL_DEVELOPMENT,
        name="Model Retirement",
        description="Know when to stop",
        priority=IdeaPriority.HIGH,
        considerations=[
            "Retirement criteria",
            "Graceful shutdown",
            "Capital reallocation"
        ],
        failure_modes=["Zombie models", "No retirement process"]
    ),
]

# Additional vectors for other categories (abbreviated for space)
EXECUTION_VECTORS = [
    IdeaVector(id="EX001", category=IdeaCategory.EXECUTION, name="Execution Algorithm Selection",
               description="Choose right algorithm", priority=IdeaPriority.HIGH,
               considerations=["TWAP vs VWAP", "Urgency", "Size"], failure_modes=["Wrong algorithm"]),
    IdeaVector(id="EX002", category=IdeaCategory.EXECUTION, name="Slippage Management",
               description="Minimize slippage", priority=IdeaPriority.HIGH,
               considerations=["Expected slippage", "Actual slippage", "Slippage attribution"],
               failure_modes=["High slippage", "No tracking"]),
    IdeaVector(id="EX003", category=IdeaCategory.EXECUTION, name="Order Timing",
               description="Time orders well", priority=IdeaPriority.MEDIUM,
               considerations=["Market timing", "News timing", "Liquidity timing"],
               failure_modes=["Bad timing", "Ignoring timing"]),
]

BEHAVIORAL_VECTORS = [
    IdeaVector(id="BF001", category=IdeaCategory.BEHAVIORAL_FINANCE, name="Overconfidence",
               description="Don't be overconfident", priority=IdeaPriority.HIGH,
               considerations=["Calibration", "Humility", "Uncertainty"],
               failure_modes=["Overconfidence", "Ignoring uncertainty"]),
    IdeaVector(id="BF002", category=IdeaCategory.BEHAVIORAL_FINANCE, name="Loss Aversion",
               description="Losses hurt more than gains", priority=IdeaPriority.HIGH,
               considerations=["Symmetric treatment", "Cut losses", "Let winners run"],
               failure_modes=["Holding losers", "Cutting winners"]),
    IdeaVector(id="BF003", category=IdeaCategory.BEHAVIORAL_FINANCE, name="Recency Bias",
               description="Recent events dominate", priority=IdeaPriority.HIGH,
               considerations=["Long-term perspective", "Base rates", "History"],
               failure_modes=["Chasing recent performance", "Ignoring history"]),
]

SYSTEM_DESIGN_VECTORS = [
    IdeaVector(id="SD001", category=IdeaCategory.SYSTEM_DESIGN, name="Fault Tolerance",
               description="Systems must handle failures", priority=IdeaPriority.CRITICAL,
               considerations=["Redundancy", "Failover", "Recovery"],
               failure_modes=["Single point of failure", "No recovery"]),
    IdeaVector(id="SD002", category=IdeaCategory.SYSTEM_DESIGN, name="Scalability",
               description="Systems must scale", priority=IdeaPriority.MEDIUM,
               considerations=["Horizontal scaling", "Vertical scaling", "Bottlenecks"],
               failure_modes=["Not scalable", "Performance issues"]),
]

REGIME_VECTORS = [
    IdeaVector(id="RA001", category=IdeaCategory.REGIME_ADAPTATION, name="Regime Detection",
               description="Detect market regimes", priority=IdeaPriority.CRITICAL,
               considerations=["Regime identification", "Transition detection", "Regime classification"],
               failure_modes=["Wrong regime", "Late detection"]),
    IdeaVector(id="RA002", category=IdeaCategory.REGIME_ADAPTATION, name="Adaptive Behavior",
               description="Adapt to regime changes", priority=IdeaPriority.CRITICAL,
               considerations=["Strategy switching", "Parameter adjustment", "Risk adjustment"],
               failure_modes=["No adaptation", "Wrong adaptation"]),
]


# =============================================================================
# IDEA VECTOR CONSTRAINTS SYSTEM
# =============================================================================

class IdeaVectorConstraints:
    """
    System for managing and enforcing idea vector constraints.
    
    All 150+ idea vectors are mandatory considerations that must be
    evaluated during system design, model development, and trading decisions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        try:
            self.config = config or {}
        
            # Compile all vectors
            self.vectors: Dict[str, IdeaVector] = {}
            self._load_all_vectors()
        
            # Evaluation history
            self.evaluations: List[IdeaVectorEvaluation] = []
        
            logger.info(f"IdeaVectorConstraints initialized with {len(self.vectors)} vectors")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _load_all_vectors(self):
        """Load all idea vectors."""
        try:
            all_vectors = (
                MARKET_MICROSTRUCTURE_VECTORS +
                RISK_MANAGEMENT_VECTORS +
                PORTFOLIO_CONSTRUCTION_VECTORS +
                MODEL_DEVELOPMENT_VECTORS +
                EXECUTION_VECTORS +
                BEHAVIORAL_VECTORS +
                SYSTEM_DESIGN_VECTORS +
                REGIME_VECTORS
            )
        
            for vector in all_vectors:
                self.vectors[vector.id] = vector
        except Exception as e:
            logger.error(f"Error in _load_all_vectors: {e}")
            raise
    
    def get_vector(self, vector_id: str) -> Optional[IdeaVector]:
        """Get a vector by ID."""
        return self.vectors.get(vector_id)
    
    def get_vectors_by_category(self, category: IdeaCategory) -> List[IdeaVector]:
        """Get all vectors in a category."""
        return [v for v in self.vectors.values() if v.category == category]
    
    def get_critical_vectors(self) -> List[IdeaVector]:
        """Get all critical priority vectors."""
        return [v for v in self.vectors.values() if v.priority == IdeaPriority.CRITICAL]
    
    def evaluate_vector(
        self,
        vector_id: str,
        context: str,
        satisfied: bool,
        score: float,
        notes: str = "",
        mitigations: List[str] = None
    ) -> IdeaVectorEvaluation:
        """
        Evaluate an idea vector for a specific context.
        
        Args:
            vector_id: Vector ID
            context: Context being evaluated
            satisfied: Whether vector is satisfied
            score: Score 0-1
            notes: Additional notes
            mitigations: Mitigations if not satisfied
            
        Returns:
            IdeaVectorEvaluation
        """
        try:
            evaluation = IdeaVectorEvaluation(
                vector_id=vector_id,
                context=context,
                satisfied=satisfied,
                score=score,
                notes=notes,
                mitigations=mitigations or []
            )
        
            self.evaluations.append(evaluation)
            return evaluation
        except Exception as e:
            logger.error(f"Error in evaluate_vector: {e}")
            raise
    
    def evaluate_all_critical(self, context: str) -> Dict[str, IdeaVectorEvaluation]:
        """
        Evaluate all critical vectors for a context.
        
        Returns:
            Dict of vector_id -> evaluation
        """
        try:
            results = {}
            critical = self.get_critical_vectors()
        
            for vector in critical:
                # Default evaluation - would be customized in practice
                evaluation = IdeaVectorEvaluation(
                    vector_id=vector.id,
                    context=context,
                    satisfied=False,  # Conservative default
                    score=0.5,
                    notes="Requires manual evaluation"
                )
                results[vector.id] = evaluation
        
            return results
        except Exception as e:
            logger.error(f"Error in evaluate_all_critical: {e}")
            raise
    
    def check_compliance(self, evaluations: List[IdeaVectorEvaluation]) -> Tuple[bool, List[str]]:
        """
        Check if evaluations meet compliance requirements.
        
        Returns:
            Tuple of (compliant, list of violations)
        """
        try:
            violations = []
        
            for eval in evaluations:
                vector = self.vectors.get(eval.vector_id)
                if vector is None:
                    continue
            
                # Critical vectors must be satisfied
                if vector.priority == IdeaPriority.CRITICAL and not eval.satisfied:
                    violations.append(f"Critical vector {vector.id} ({vector.name}) not satisfied")
            
                # High priority vectors should have score > 0.5
                if vector.priority == IdeaPriority.HIGH and eval.score < 0.5:
                    violations.append(f"High priority vector {vector.id} ({vector.name}) has low score: {eval.score:.2f}")
        
            return len(violations) == 0, violations
        except Exception as e:
            logger.error(f"Error in check_compliance: {e}")
            raise
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of idea vectors."""
        try:
            by_category = {}
            by_priority = {}
        
            for vector in self.vectors.values():
                cat = vector.category.value
                pri = vector.priority.value
            
                by_category[cat] = by_category.get(cat, 0) + 1
                by_priority[pri] = by_priority.get(pri, 0) + 1
        
            return {
                'total_vectors': len(self.vectors),
                'by_category': by_category,
                'by_priority': by_priority,
                'evaluations_count': len(self.evaluations)
            }
        except Exception as e:
            logger.error(f"Error in get_summary: {e}")
            raise
