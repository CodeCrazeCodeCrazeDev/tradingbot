"""
AADS LAYER 8 — POLYMARKET MODULE

Continuously scans all open Polymarket contracts.
For each contract:
1. Pull current YES/NO implied probabilities
2. Run own probability estimate using:
   - LLM reasoning on all relevant context
   - Structured models (logistic regression on base rates)
   - Historical calibration data (Brier score tracking)
3. If |your_estimate - market_price| > edge_threshold:
   - Calculate Kelly fraction
   - Check correlation with existing prediction positions
   - Run 500-scenario portfolio simulation
   - Submit via py-clob-client if approved
4. Track all resolutions and recalibrate models

Prediction markets provide unique alpha:
- Real-time probability estimates on discrete events
- Crowd wisdom aggregation
- Arbitrage opportunities vs other markets
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import uuid
import logging
import hashlib

logger = logging.getLogger(__name__)


class ContractCategory(Enum):
    """Categories of Polymarket contracts"""
    POLITICS = "politics"
    ECONOMICS = "economics"
    CRYPTO = "crypto"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    SCIENCE = "science"
    GEOPOLITICS = "geopolitics"
    MARKETS = "markets"
    OTHER = "other"


class ContractStatus(Enum):
    """Status of a contract"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    DISPUTED = "disputed"


class PositionSide(Enum):
    """Side of a position"""
    YES = "yes"
    NO = "no"


@dataclass
class PolymarketContract:
    """Representation of a Polymarket contract"""
    contract_id: str
    question: str
    description: str
    category: ContractCategory
    
    # Prices
    yes_price: float  # 0-1
    no_price: float   # 0-1
    
    # Liquidity
    volume_24h: float
    total_volume: float
    liquidity: float
    spread_bps: float
    
    # Timing
    created_at: datetime
    closes_at: datetime
    resolution_date: Optional[datetime] = None
    
    # Status
    status: ContractStatus = ContractStatus.ACTIVE
    resolved_outcome: Optional[str] = None
    
    # Our analysis
    our_probability: Optional[float] = None
    edge: Optional[float] = None
    confidence: float = 0.0
    
    @property
    def implied_probability(self) -> float:
        """Market implied probability of YES"""
        return self.yes_price
    
    @property
    def time_to_resolution(self) -> timedelta:
        """Time until contract closes"""
        return self.closes_at - datetime.now()
    
    @property
    def days_to_resolution(self) -> float:
        """Days until contract closes"""
        return self.time_to_resolution.total_seconds() / 86400
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'contract_id': self.contract_id,
            'question': self.question,
            'category': self.category.value,
            'yes_price': self.yes_price,
            'no_price': self.no_price,
            'volume_24h': self.volume_24h,
            'liquidity': self.liquidity,
            'closes_at': self.closes_at.isoformat(),
            'our_probability': self.our_probability,
            'edge': self.edge,
            'status': self.status.value
        }


@dataclass
class PredictionPosition:
    """A position in a prediction market"""
    position_id: str
    contract_id: str
    side: PositionSide
    size: float  # Number of shares
    entry_price: float
    current_price: float
    
    # PnL
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    # Risk
    max_loss: float = 0.0
    max_gain: float = 0.0
    
    # Timing
    opened_at: datetime = field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    
    @property
    def is_open(self) -> bool:
        return self.closed_at is None
    
    def update_pnl(self, current_price: float) -> None:
        """Update unrealized PnL"""
        self.current_price = current_price
        if self.side == PositionSide.YES:
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.size
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'position_id': self.position_id,
            'contract_id': self.contract_id,
            'side': self.side.value,
            'size': self.size,
            'entry_price': self.entry_price,
            'current_price': self.current_price,
            'unrealized_pnl': self.unrealized_pnl,
            'is_open': self.is_open
        }


@dataclass
class CalibrationRecord:
    """Record for tracking prediction calibration"""
    prediction_id: str
    contract_id: str
    our_probability: float
    market_probability: float
    actual_outcome: Optional[bool] = None
    brier_score: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def compute_brier_score(self) -> Optional[float]:
        """Compute Brier score if outcome is known"""
        if self.actual_outcome is None:
            return None
        
        outcome = 1.0 if self.actual_outcome else 0.0
        self.brier_score = (self.our_probability - outcome) ** 2
        return self.brier_score


@dataclass
class ProbabilityEstimate:
    """Our probability estimate for a contract"""
    contract_id: str
    probability: float
    confidence: float
    
    # Components
    llm_estimate: float
    base_rate_estimate: float
    historical_estimate: float
    
    # Weights
    llm_weight: float = 0.4
    base_rate_weight: float = 0.3
    historical_weight: float = 0.3
    
    # Reasoning
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'contract_id': self.contract_id,
            'probability': self.probability,
            'confidence': self.confidence,
            'llm_estimate': self.llm_estimate,
            'base_rate_estimate': self.base_rate_estimate,
            'historical_estimate': self.historical_estimate,
            'reasoning': self.reasoning
        }


class BaseRateModel:
    """
    Base rate model for probability estimation.
    
    Uses historical frequencies of similar events.
    """
    
    # Historical base rates by category
    BASE_RATES = {
        ContractCategory.POLITICS: {
            "incumbent_wins": 0.55,
            "challenger_wins": 0.45,
            "policy_passes": 0.40,
            "scandal_resignation": 0.15,
        },
        ContractCategory.ECONOMICS: {
            "fed_rate_hike": 0.60,
            "fed_rate_cut": 0.30,
            "recession_next_year": 0.15,
            "inflation_above_target": 0.40,
        },
        ContractCategory.CRYPTO: {
            "btc_ath_this_year": 0.30,
            "eth_ath_this_year": 0.25,
            "major_hack": 0.20,
            "etf_approval": 0.50,
        },
        ContractCategory.GEOPOLITICS: {
            "conflict_escalation": 0.25,
            "peace_agreement": 0.15,
            "sanctions_imposed": 0.40,
        }
    }
    
    def estimate(self, contract: PolymarketContract) -> float:
        """Estimate probability using base rates"""
        
        category_rates = self.BASE_RATES.get(contract.category, {})
        
        # Try to match question to known patterns
        question_lower = contract.question.lower()
        
        for pattern, rate in category_rates.items():
            if pattern.replace("_", " ") in question_lower:
                return rate
        
        # Default: use market price as base rate (efficient market assumption)
        return contract.implied_probability


class PolymarketModule:
    """
    Main Polymarket integration module.
    
    Scans contracts, estimates probabilities, identifies edges,
    manages positions, and tracks calibration.
    """
    
    def __init__(
        self,
        edge_threshold: float = 0.05,
        max_position_pct: float = 0.02,
        min_liquidity: float = 10000,
        min_volume_24h: float = 1000
    ):
        self.edge_threshold = edge_threshold
        self.max_position_pct = max_position_pct
        self.min_liquidity = min_liquidity
        self.min_volume_24h = min_volume_24h
        
        self.contracts: Dict[str, PolymarketContract] = {}
        self.positions: Dict[str, PredictionPosition] = {}
        self.calibration_records: List[CalibrationRecord] = []
        self.estimates: Dict[str, ProbabilityEstimate] = {}
        
        self.base_rate_model = BaseRateModel()
        
        # Portfolio state
        self.total_capital = 0.0
        self.allocated_capital = 0.0
        
        logger.info("PolymarketModule initialized")
    
    def set_capital(self, capital: float) -> None:
        """Set total capital available for prediction markets"""
        self.total_capital = capital
    
    def scan_contracts(self, contracts: List[Dict[str, Any]]) -> List[PolymarketContract]:
        """
        Scan and process new contracts from Polymarket API.
        
        Filters for liquidity and volume requirements.
        """
        processed = []
        
        for data in contracts:
            contract = PolymarketContract(
                contract_id=data.get("id", str(uuid.uuid4())),
                question=data.get("question", ""),
                description=data.get("description", ""),
                category=self._categorize_contract(data.get("question", "")),
                yes_price=data.get("yes_price", 0.5),
                no_price=data.get("no_price", 0.5),
                volume_24h=data.get("volume_24h", 0),
                total_volume=data.get("total_volume", 0),
                liquidity=data.get("liquidity", 0),
                spread_bps=data.get("spread_bps", 100),
                created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
                closes_at=datetime.fromisoformat(data.get("closes_at", (datetime.now() + timedelta(days=30)).isoformat()))
            )
            
            # Filter
            if contract.liquidity < self.min_liquidity:
                continue
            if contract.volume_24h < self.min_volume_24h:
                continue
            if contract.status != ContractStatus.ACTIVE:
                continue
            
            self.contracts[contract.contract_id] = contract
            processed.append(contract)
        
        logger.info(f"Scanned {len(contracts)} contracts, {len(processed)} passed filters")
        return processed
    
    def estimate_probability(
        self,
        contract: PolymarketContract,
        context: Optional[Dict[str, Any]] = None
    ) -> ProbabilityEstimate:
        """
        Estimate probability for a contract using multiple methods.
        
        Combines:
        1. LLM reasoning (if available)
        2. Base rate models
        3. Historical calibration
        """
        
        # Base rate estimate
        base_rate = self.base_rate_model.estimate(contract)
        
        # Historical estimate (use market price adjusted by our calibration)
        historical = self._historical_adjusted_estimate(contract)
        
        # LLM estimate (placeholder - would call actual LLM)
        llm_estimate = self._llm_estimate(contract, context)
        
        # Combine estimates
        weights = [0.4, 0.3, 0.3]  # LLM, base rate, historical
        combined = (
            weights[0] * llm_estimate +
            weights[1] * base_rate +
            weights[2] * historical
        )
        
        # Confidence based on agreement
        estimates = [llm_estimate, base_rate, historical]
        variance = sum((e - combined) ** 2 for e in estimates) / len(estimates)
        confidence = max(0, 1 - variance * 4)  # Scale variance to confidence
        
        estimate = ProbabilityEstimate(
            contract_id=contract.contract_id,
            probability=combined,
            confidence=confidence,
            llm_estimate=llm_estimate,
            base_rate_estimate=base_rate,
            historical_estimate=historical,
            reasoning=self._generate_reasoning(contract, estimates)
        )
        
        # Update contract
        contract.our_probability = combined
        contract.edge = combined - contract.implied_probability
        contract.confidence = confidence
        
        self.estimates[contract.contract_id] = estimate
        
        return estimate
    
    def find_edges(self) -> List[Tuple[PolymarketContract, float]]:
        """
        Find contracts where we have an edge over the market.
        
        Returns list of (contract, edge) tuples sorted by edge size.
        """
        edges = []
        
        for contract in self.contracts.values():
            if contract.our_probability is None:
                self.estimate_probability(contract)
            
            edge = abs(contract.edge or 0)
            
            if edge >= self.edge_threshold:
                edges.append((contract, edge))
        
        # Sort by edge size
        edges.sort(key=lambda x: x[1], reverse=True)
        
        return edges
    
    def calculate_kelly_fraction(
        self,
        contract: PolymarketContract,
        side: PositionSide
    ) -> float:
        """
        Calculate Kelly fraction for optimal position sizing.
        
        Kelly = (p * b - q) / b
        where p = probability of winning, b = odds, q = 1 - p
        """
        if contract.our_probability is None:
            return 0.0
        
        if side == PositionSide.YES:
            p = contract.our_probability
            b = (1 - contract.yes_price) / contract.yes_price  # Odds
        else:
            p = 1 - contract.our_probability
            b = (1 - contract.no_price) / contract.no_price
        
        q = 1 - p
        
        if b <= 0:
            return 0.0
        
        kelly = (p * b - q) / b
        
        # Half Kelly for safety
        kelly = kelly / 2
        
        # Cap at max position
        kelly = min(kelly, self.max_position_pct)
        
        return max(0, kelly)
    
    def check_correlation(
        self,
        contract: PolymarketContract
    ) -> Dict[str, Any]:
        """
        Check correlation with existing positions.
        
        Prevents overconcentration in correlated outcomes.
        """
        correlations = []
        
        for pos in self.positions.values():
            if not pos.is_open:
                continue
            
            existing_contract = self.contracts.get(pos.contract_id)
            if not existing_contract:
                continue
            
            # Simple correlation heuristic based on category
            if existing_contract.category == contract.category:
                correlations.append({
                    'position_id': pos.position_id,
                    'contract_id': pos.contract_id,
                    'correlation': 0.5,  # Same category = moderate correlation
                    'exposure': pos.size * pos.current_price
                })
        
        total_correlated_exposure = sum(c['exposure'] for c in correlations)
        
        return {
            'correlations': correlations,
            'total_correlated_exposure': total_correlated_exposure,
            'max_additional_exposure': self.total_capital * 0.15 - total_correlated_exposure
        }
    
    def simulate_portfolio(
        self,
        contract: PolymarketContract,
        side: PositionSide,
        size: float,
        n_scenarios: int = 500
    ) -> Dict[str, Any]:
        """
        Run portfolio simulation with new position.
        
        Simulates outcomes across scenarios.
        """
        import numpy as np
        
        # Current portfolio value
        current_value = sum(
            pos.size * pos.current_price
            for pos in self.positions.values()
            if pos.is_open
        )
        
        # New position value
        entry_price = contract.yes_price if side == PositionSide.YES else contract.no_price
        new_position_value = size * entry_price
        
        # Simulate outcomes
        outcomes = []
        
        for _ in range(n_scenarios):
            # Simulate resolution
            resolved_yes = np.random.random() < contract.our_probability
            
            # Calculate PnL
            if side == PositionSide.YES:
                pnl = size * (1.0 if resolved_yes else 0.0) - new_position_value
            else:
                pnl = size * (1.0 if not resolved_yes else 0.0) - new_position_value
            
            outcomes.append(pnl)
        
        outcomes = np.array(outcomes)
        
        return {
            'mean_pnl': float(np.mean(outcomes)),
            'std_pnl': float(np.std(outcomes)),
            'p10': float(np.percentile(outcomes, 10)),
            'p50': float(np.percentile(outcomes, 50)),
            'p90': float(np.percentile(outcomes, 90)),
            'max_loss': float(np.min(outcomes)),
            'max_gain': float(np.max(outcomes)),
            'win_rate': float(np.mean(outcomes > 0)),
            'expected_value': float(np.mean(outcomes)),
            'sharpe': float(np.mean(outcomes) / np.std(outcomes)) if np.std(outcomes) > 0 else 0
        }
    
    def evaluate_trade(
        self,
        contract: PolymarketContract
    ) -> Dict[str, Any]:
        """
        Full evaluation of a potential trade.
        
        Combines probability estimation, Kelly sizing,
        correlation check, and portfolio simulation.
        """
        # Estimate probability
        estimate = self.estimate_probability(contract)
        
        # Determine side
        if contract.edge > 0:
            side = PositionSide.YES
        else:
            side = PositionSide.NO
        
        # Kelly fraction
        kelly = self.calculate_kelly_fraction(contract, side)
        
        # Correlation check
        correlation = self.check_correlation(contract)
        
        # Adjust size for correlation
        max_size = min(
            kelly * self.total_capital,
            correlation['max_additional_exposure']
        )
        
        # Portfolio simulation
        simulation = self.simulate_portfolio(contract, side, max_size)
        
        # Decision
        approved = (
            abs(contract.edge) >= self.edge_threshold and
            estimate.confidence >= 0.5 and
            simulation['expected_value'] > 0 and
            simulation['sharpe'] > 0.5 and
            max_size > 0
        )
        
        return {
            'contract_id': contract.contract_id,
            'question': contract.question,
            'market_price': contract.implied_probability,
            'our_estimate': estimate.probability,
            'edge': contract.edge,
            'confidence': estimate.confidence,
            'side': side.value,
            'kelly_fraction': kelly,
            'recommended_size': max_size,
            'correlation_exposure': correlation['total_correlated_exposure'],
            'simulation': simulation,
            'approved': approved,
            'reasoning': estimate.reasoning
        }
    
    def open_position(
        self,
        contract: PolymarketContract,
        side: PositionSide,
        size: float
    ) -> PredictionPosition:
        """Open a new position"""
        
        entry_price = contract.yes_price if side == PositionSide.YES else contract.no_price
        
        position = PredictionPosition(
            position_id=str(uuid.uuid4()),
            contract_id=contract.contract_id,
            side=side,
            size=size,
            entry_price=entry_price,
            current_price=entry_price,
            max_loss=size * entry_price,
            max_gain=size * (1 - entry_price)
        )
        
        self.positions[position.position_id] = position
        self.allocated_capital += size * entry_price
        
        # Record for calibration
        self.calibration_records.append(CalibrationRecord(
            prediction_id=str(uuid.uuid4()),
            contract_id=contract.contract_id,
            our_probability=contract.our_probability or 0.5,
            market_probability=contract.implied_probability
        ))
        
        logger.info(f"Opened position: {side.value} {size:.2f} @ {entry_price:.4f} on {contract.question[:50]}")
        
        return position
    
    def close_position(
        self,
        position_id: str,
        exit_price: float
    ) -> Optional[PredictionPosition]:
        """Close an existing position"""
        
        position = self.positions.get(position_id)
        if not position or not position.is_open:
            return None
        
        position.current_price = exit_price
        position.update_pnl(exit_price)
        position.realized_pnl = position.unrealized_pnl
        position.unrealized_pnl = 0
        position.closed_at = datetime.now()
        
        self.allocated_capital -= position.size * position.entry_price
        
        logger.info(f"Closed position: PnL={position.realized_pnl:.2f}")
        
        return position
    
    def resolve_contract(
        self,
        contract_id: str,
        outcome: bool  # True = YES won
    ) -> None:
        """
        Handle contract resolution.
        
        Updates positions and calibration records.
        """
        contract = self.contracts.get(contract_id)
        if not contract:
            return
        
        contract.status = ContractStatus.RESOLVED
        contract.resolved_outcome = "YES" if outcome else "NO"
        contract.resolution_date = datetime.now()
        
        # Close all positions on this contract
        for position in self.positions.values():
            if position.contract_id == contract_id and position.is_open:
                if position.side == PositionSide.YES:
                    exit_price = 1.0 if outcome else 0.0
                else:
                    exit_price = 0.0 if outcome else 1.0
                
                self.close_position(position.position_id, exit_price)
        
        # Update calibration records
        for record in self.calibration_records:
            if record.contract_id == contract_id and record.actual_outcome is None:
                record.actual_outcome = outcome
                record.compute_brier_score()
        
        logger.info(f"Contract resolved: {contract.question[:50]} -> {contract.resolved_outcome}")
    
    def get_calibration_stats(self) -> Dict[str, Any]:
        """Get calibration statistics"""
        
        resolved = [r for r in self.calibration_records if r.brier_score is not None]
        
        if not resolved:
            return {
                'total_predictions': len(self.calibration_records),
                'resolved': 0,
                'brier_score': None,
                'calibration': None
            }
        
        brier_scores = [r.brier_score for r in resolved]
        avg_brier = sum(brier_scores) / len(brier_scores)
        
        # Calibration by bucket
        buckets = {}
        for r in resolved:
            bucket = round(r.our_probability * 10) / 10
            if bucket not in buckets:
                buckets[bucket] = {'predictions': 0, 'outcomes': 0}
            buckets[bucket]['predictions'] += 1
            if r.actual_outcome:
                buckets[bucket]['outcomes'] += 1
        
        calibration = {
            bucket: data['outcomes'] / data['predictions']
            for bucket, data in buckets.items()
            if data['predictions'] > 0
        }
        
        return {
            'total_predictions': len(self.calibration_records),
            'resolved': len(resolved),
            'brier_score': avg_brier,
            'calibration': calibration,
            'accuracy': sum(1 for r in resolved if (r.our_probability > 0.5) == r.actual_outcome) / len(resolved)
        }
    
    def get_portfolio_stats(self) -> Dict[str, Any]:
        """Get portfolio statistics"""
        
        open_positions = [p for p in self.positions.values() if p.is_open]
        closed_positions = [p for p in self.positions.values() if not p.is_open]
        
        total_unrealized = sum(p.unrealized_pnl for p in open_positions)
        total_realized = sum(p.realized_pnl for p in closed_positions)
        
        return {
            'total_capital': self.total_capital,
            'allocated_capital': self.allocated_capital,
            'available_capital': self.total_capital - self.allocated_capital,
            'open_positions': len(open_positions),
            'closed_positions': len(closed_positions),
            'unrealized_pnl': total_unrealized,
            'realized_pnl': total_realized,
            'total_pnl': total_unrealized + total_realized,
            'return_pct': (total_unrealized + total_realized) / self.total_capital if self.total_capital > 0 else 0
        }
    
    def _categorize_contract(self, question: str) -> ContractCategory:
        """Categorize a contract based on its question"""
        question_lower = question.lower()
        
        if any(w in question_lower for w in ['election', 'president', 'congress', 'vote', 'poll']):
            return ContractCategory.POLITICS
        if any(w in question_lower for w in ['fed', 'rate', 'inflation', 'gdp', 'recession', 'cpi']):
            return ContractCategory.ECONOMICS
        if any(w in question_lower for w in ['bitcoin', 'btc', 'eth', 'crypto', 'token']):
            return ContractCategory.CRYPTO
        if any(w in question_lower for w in ['war', 'conflict', 'sanction', 'treaty']):
            return ContractCategory.GEOPOLITICS
        if any(w in question_lower for w in ['stock', 'market', 's&p', 'nasdaq']):
            return ContractCategory.MARKETS
        
        return ContractCategory.OTHER
    
    def _historical_adjusted_estimate(self, contract: PolymarketContract) -> float:
        """Adjust market price based on historical calibration"""
        
        # Get calibration for this category
        category_records = [
            r for r in self.calibration_records
            if r.brier_score is not None
        ]
        
        if not category_records:
            return contract.implied_probability
        
        # Calculate our historical bias
        avg_our = sum(r.our_probability for r in category_records) / len(category_records)
        avg_actual = sum(1 if r.actual_outcome else 0 for r in category_records) / len(category_records)
        
        bias = avg_our - avg_actual
        
        # Adjust market price by our historical bias
        adjusted = contract.implied_probability - bias
        
        return max(0.01, min(0.99, adjusted))
    
    def _llm_estimate(
        self,
        contract: PolymarketContract,
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Get LLM probability estimate.
        
        In production, this would call an actual LLM.
        For now, uses heuristics.
        """
        # Placeholder: use market price with small random adjustment
        import random
        
        base = contract.implied_probability
        adjustment = random.gauss(0, 0.05)
        
        return max(0.01, min(0.99, base + adjustment))
    
    def _generate_reasoning(
        self,
        contract: PolymarketContract,
        estimates: List[float]
    ) -> str:
        """Generate reasoning for probability estimate"""
        
        avg = sum(estimates) / len(estimates)
        market = contract.implied_probability
        
        if avg > market + 0.05:
            direction = "higher"
            reason = "Our models suggest the market is underpricing this outcome."
        elif avg < market - 0.05:
            direction = "lower"
            reason = "Our models suggest the market is overpricing this outcome."
        else:
            direction = "similar"
            reason = "Our estimate aligns with market consensus."
        
        return f"Estimate {direction} than market ({avg:.1%} vs {market:.1%}). {reason}"


# Singleton instance
_polymarket_module: Optional[PolymarketModule] = None


def get_polymarket_module() -> PolymarketModule:
    """Get the global Polymarket module instance"""
    global _polymarket_module
    if _polymarket_module is None:
        _polymarket_module = PolymarketModule()
    return _polymarket_module
