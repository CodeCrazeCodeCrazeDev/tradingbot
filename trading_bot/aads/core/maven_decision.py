"""
AADS Maven Decision Intelligence Layer

Implements the full Maven Smart System loop for every trade decision:
1. SITUATIONAL AWARENESS - Build real-time market picture
2. WARGAME - BullAgent vs BearAgent adversarial analysis
3. SIMULATION - All 5 simulation types
4. DECISION BRIEF - Structured decision document
5. APPROVAL GATE - Auto-execute, human review, or reject

Every decision produces a human-readable brief that a compliance officer could audit.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import numpy as np
import logging
import uuid

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """Decision approval status"""
    AUTO_EXECUTE = "auto_execute"       # Confidence >= 75, all checks pass
    HUMAN_REVIEW = "human_review"       # Confidence 50-74
    REJECTED = "rejected"               # Confidence < 50 or risk veto


class MarketRegime(Enum):
    """Current market regime"""
    RISK_ON = "risk_on"
    RISK_OFF = "risk_off"
    TRANSITIONING = "transitioning"
    CRISIS = "crisis"


class VolatilityRegime(Enum):
    """Volatility regime based on VIX"""
    LOW = "low"           # VIX < 15
    NORMAL = "normal"     # VIX 15-25
    ELEVATED = "elevated" # VIX 25-35
    CRISIS = "crisis"     # VIX > 35


class SentimentRegime(Enum):
    """Market sentiment regime"""
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


@dataclass
class SituationalAwareness:
    """Real-time market picture"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Portfolio state
    current_positions: Dict[str, float] = field(default_factory=dict)
    live_pnl: float = 0.0
    active_signals: List[str] = field(default_factory=list)
    
    # Market regimes
    market_regime: MarketRegime = MarketRegime.RISK_ON
    volatility_regime: VolatilityRegime = VolatilityRegime.NORMAL
    sentiment_regime: SentimentRegime = SentimentRegime.NEUTRAL
    
    # Key metrics
    vix_level: float = 20.0
    vix_term_structure: str = "contango"  # contango or backwardation
    credit_spreads_bps: float = 350.0
    
    # Liquidity conditions
    liquidity_score: float = 0.8  # 0-1
    bid_ask_spread_bps: float = 5.0
    
    # Upcoming catalysts
    upcoming_catalysts: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'current_positions': self.current_positions,
            'live_pnl': self.live_pnl,
            'market_regime': self.market_regime.value,
            'volatility_regime': self.volatility_regime.value,
            'sentiment_regime': self.sentiment_regime.value,
            'vix_level': self.vix_level,
            'liquidity_score': self.liquidity_score,
            'upcoming_catalysts': self.upcoming_catalysts
        }


@dataclass
class WargameResult:
    """Result of Bull vs Bear adversarial analysis"""
    bull_thesis: str
    bull_confidence: float
    bull_price_targets: List[float]
    bull_catalysts: List[Dict[str, Any]]
    
    bear_counter_thesis: str
    bear_confidence: float
    bear_invalidation_scenarios: List[Dict[str, Any]]
    bear_tail_risks: List[Dict[str, Any]]
    
    # Adjudication
    adjudicated_direction: str  # "long", "short", "neutral"
    adjudicated_confidence: float
    risk_adjusted_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bull': {
                'thesis': self.bull_thesis,
                'confidence': self.bull_confidence,
                'price_targets': self.bull_price_targets,
                'catalysts': self.bull_catalysts
            },
            'bear': {
                'counter_thesis': self.bear_counter_thesis,
                'confidence': self.bear_confidence,
                'invalidation_scenarios': self.bear_invalidation_scenarios,
                'tail_risks': self.bear_tail_risks
            },
            'adjudication': {
                'direction': self.adjudicated_direction,
                'confidence': self.adjudicated_confidence,
                'risk_adjusted_score': self.risk_adjusted_score
            }
        }


@dataclass
class SimulationSummary:
    """Summary of all simulation results"""
    # Monte Carlo
    p10_return: float
    p50_return: float
    p90_return: float
    var_95: float
    cvar_95: float
    
    # Stress tests
    worst_stress_scenario: str
    worst_stress_loss: float
    
    # Causal scenarios
    fed_shock_impact: float
    vix_spike_impact: float
    oil_shock_impact: float
    
    # Execution
    estimated_slippage_bps: float
    market_impact_bps: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'monte_carlo': {
                'p10': self.p10_return,
                'p50': self.p50_return,
                'p90': self.p90_return,
                'var_95': self.var_95,
                'cvar_95': self.cvar_95
            },
            'stress_test': {
                'worst_scenario': self.worst_stress_scenario,
                'worst_loss': self.worst_stress_loss
            },
            'causal': {
                'fed_shock': self.fed_shock_impact,
                'vix_spike': self.vix_spike_impact,
                'oil_shock': self.oil_shock_impact
            },
            'execution': {
                'slippage_bps': self.estimated_slippage_bps,
                'market_impact_bps': self.market_impact_bps
            }
        }


@dataclass
class DecisionBrief:
    """
    Structured decision brief for every trade.
    
    Human-readable format that a compliance officer can audit.
    """
    # Identification
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Trade details
    asset: str = ""
    direction: str = ""  # "LONG" or "SHORT"
    venue: str = ""
    size_pct: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    stop_pct: float = 0.0
    take_profit: float = 0.0
    target_pct: float = 0.0
    horizon_days: int = 20
    
    # Thesis
    one_sentence_thesis: str = ""
    key_evidence: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    
    # Swarm consensus
    swarm_direction: str = ""
    swarm_strength: float = 0.0
    swarm_dissent: float = 0.0
    dominant_fish: str = ""
    
    # Visual signals
    visual_signal_summary: str = ""
    
    # Causal scenarios
    causal_scenarios: Dict[str, float] = field(default_factory=dict)
    
    # Backtest results
    backtest_sharpe: float = 0.0
    backtest_max_dd: float = 0.0
    backtest_win_rate: float = 0.0
    
    # Simulation results
    simulation_p10: float = 0.0
    simulation_p50: float = 0.0
    simulation_p90: float = 0.0
    
    # Decision
    confidence: int = 0  # 0-100
    approval_status: ApprovalStatus = ApprovalStatus.REJECTED
    
    # Evolution tracking
    genome_id: str = ""
    genome_generation: int = 0
    genome_fitness: float = 0.0
    
    # Audit
    audit_reference_id: str = ""
    
    def to_formatted_string(self) -> str:
        """Generate human-readable decision brief"""
        return f"""
══════════════════════════════════════════════════════════════
AADS DECISION BRIEF — {self.decision_id}
══════════════════════════════════════════════════════════════
Asset:      {self.asset}
Direction:  {self.direction}
Venue:      {self.venue}
Size:       {self.size_pct:.1%} of portfolio
Entry:      ${self.entry_price:.2f}
Stop:       ${self.stop_loss:.2f} ({self.stop_pct:.1%})
Target:     ${self.take_profit:.2f} ({self.target_pct:.1%})
Horizon:    {self.horizon_days} days

THESIS
{self.one_sentence_thesis}

EVIDENCE
{chr(10).join(f'- {e}' for e in self.key_evidence[:3])}

RISKS
{chr(10).join(f'- {r}' for r in self.key_risks[:3])}

SWARM CONSENSUS
{self.swarm_direction} | Strength: {self.swarm_strength:.0%} | Dissent: {self.swarm_dissent:.0%}
Dominant signal: {self.dominant_fish}

VISUAL SIGNALS (OpenCLIP)
{self.visual_signal_summary}

CAUSAL SCENARIOS
- Base case:    {self.causal_scenarios.get('base', 0):+.1%}
- Fed shock:    {self.causal_scenarios.get('fed_shock', 0):+.1%}
- VIX spike:    {self.causal_scenarios.get('vix_spike', 0):+.1%}
- Oil shock:    {self.causal_scenarios.get('oil_shock', 0):+.1%}

BACKTEST (OOS)
Sharpe: {self.backtest_sharpe:.2f} | Max DD: {self.backtest_max_dd:.1%} | Win rate: {self.backtest_win_rate:.0%}

SIMULATION
P10: {self.simulation_p10:+.1%} | P50: {self.simulation_p50:+.1%} | P90: {self.simulation_p90:+.1%}

CONFIDENCE: {self.confidence}/100
APPROVAL:   {self.approval_status.value.upper().replace('_', ' ')}
EVOLUTION:  Strategy genome {self.genome_id[:8]} (gen {self.genome_generation}, fitness {self.genome_fitness:.3f})
══════════════════════════════════════════════════════════════
"""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'decision_id': self.decision_id,
            'timestamp': self.timestamp.isoformat(),
            'asset': self.asset,
            'direction': self.direction,
            'venue': self.venue,
            'size_pct': self.size_pct,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'horizon_days': self.horizon_days,
            'thesis': self.one_sentence_thesis,
            'evidence': self.key_evidence,
            'risks': self.key_risks,
            'swarm': {
                'direction': self.swarm_direction,
                'strength': self.swarm_strength,
                'dissent': self.swarm_dissent,
                'dominant_fish': self.dominant_fish
            },
            'backtest': {
                'sharpe': self.backtest_sharpe,
                'max_dd': self.backtest_max_dd,
                'win_rate': self.backtest_win_rate
            },
            'simulation': {
                'p10': self.simulation_p10,
                'p50': self.simulation_p50,
                'p90': self.simulation_p90
            },
            'confidence': self.confidence,
            'approval_status': self.approval_status.value,
            'genome_id': self.genome_id,
            'audit_reference_id': self.audit_reference_id
        }


class MavenDecisionEngine:
    """
    Maven Smart System Decision Intelligence Engine.
    
    Implements the full decision loop:
    1. Situational Awareness
    2. Wargame (Bull vs Bear)
    3. Simulation
    4. Decision Brief
    5. Approval Gate
    """
    
    # Approval thresholds
    AUTO_EXECUTE_THRESHOLD = 75
    HUMAN_REVIEW_THRESHOLD = 50
    
    def __init__(self):
        self.decisions: List[DecisionBrief] = []
        self.situational_awareness: Optional[SituationalAwareness] = None
        
        logger.info("MavenDecisionEngine initialized")
    
    def update_situational_awareness(
        self,
        positions: Dict[str, float],
        pnl: float,
        vix: float,
        catalysts: List[Dict[str, Any]]
    ) -> SituationalAwareness:
        """
        Step 1: Build real-time market picture.
        """
        # Determine regimes
        market_regime = self._determine_market_regime(vix, pnl)
        vol_regime = self._determine_vol_regime(vix)
        sentiment_regime = self._determine_sentiment_regime(vix)
        
        self.situational_awareness = SituationalAwareness(
            current_positions=positions,
            live_pnl=pnl,
            market_regime=market_regime,
            volatility_regime=vol_regime,
            sentiment_regime=sentiment_regime,
            vix_level=vix,
            upcoming_catalysts=catalysts
        )
        
        return self.situational_awareness
    
    def _determine_market_regime(self, vix: float, pnl: float) -> MarketRegime:
        """Determine current market regime"""
        if vix > 35:
            return MarketRegime.CRISIS
        elif vix > 25:
            return MarketRegime.RISK_OFF
        elif vix < 15:
            return MarketRegime.RISK_ON
        else:
            return MarketRegime.TRANSITIONING
    
    def _determine_vol_regime(self, vix: float) -> VolatilityRegime:
        """Determine volatility regime"""
        if vix < 15:
            return VolatilityRegime.LOW
        elif vix < 25:
            return VolatilityRegime.NORMAL
        elif vix < 35:
            return VolatilityRegime.ELEVATED
        else:
            return VolatilityRegime.CRISIS
    
    def _determine_sentiment_regime(self, vix: float) -> SentimentRegime:
        """Determine sentiment regime (simplified)"""
        if vix > 35:
            return SentimentRegime.EXTREME_FEAR
        elif vix > 25:
            return SentimentRegime.FEAR
        elif vix < 12:
            return SentimentRegime.EXTREME_GREED
        elif vix < 18:
            return SentimentRegime.GREED
        else:
            return SentimentRegime.NEUTRAL
    
    def run_wargame(
        self,
        bull_output: Dict[str, Any],
        bear_output: Dict[str, Any]
    ) -> WargameResult:
        """
        Step 2: Adversarial wargame between Bull and Bear agents.
        
        Neither agent can see the other's output until both complete.
        RiskAgent adjudicates and assigns confidence score.
        """
        # Extract bull case
        bull_thesis = bull_output.get('thesis', '')
        bull_confidence = bull_output.get('confidence', 0.5)
        bull_targets = [
            bull_output.get('price_target_1', 0),
            bull_output.get('price_target_2', 0),
            bull_output.get('price_target_3', 0)
        ]
        bull_catalysts = bull_output.get('catalysts', [])
        
        # Extract bear case
        bear_thesis = bear_output.get('counter_thesis', '')
        bear_confidence = bear_output.get('confidence', 0.5)
        bear_invalidations = bear_output.get('invalidation_scenarios', [])
        bear_tail_risks = bear_output.get('tail_risks', [])
        
        # Adjudicate
        confidence_delta = bull_confidence - bear_confidence
        
        if confidence_delta > 0.2:
            direction = "long"
            adj_confidence = bull_confidence * 0.8 + 0.2 * (1 - bear_confidence)
        elif confidence_delta < -0.2:
            direction = "short"
            adj_confidence = bear_confidence * 0.8 + 0.2 * (1 - bull_confidence)
        else:
            direction = "neutral"
            adj_confidence = 0.5
        
        # Risk-adjusted score
        risk_score = adj_confidence * (1 - len(bear_tail_risks) * 0.1)
        
        return WargameResult(
            bull_thesis=bull_thesis,
            bull_confidence=bull_confidence,
            bull_price_targets=bull_targets,
            bull_catalysts=bull_catalysts,
            bear_counter_thesis=bear_thesis,
            bear_confidence=bear_confidence,
            bear_invalidation_scenarios=bear_invalidations,
            bear_tail_risks=bear_tail_risks,
            adjudicated_direction=direction,
            adjudicated_confidence=adj_confidence,
            risk_adjusted_score=risk_score
        )
    
    def synthesize_simulation_results(
        self,
        simulation_output: Dict[str, Any]
    ) -> SimulationSummary:
        """
        Step 3: Synthesize all simulation results.
        """
        mc = simulation_output.get('monte_carlo', {})
        stress = simulation_output.get('stress_test', {})
        causal = simulation_output.get('causal', {})
        mm = simulation_output.get('market_maker', {})
        
        # Find worst stress scenario
        stress_scenarios = stress.get('scenarios', {})
        worst_scenario = min(
            stress_scenarios.items(),
            key=lambda x: x[1].get('drawdown', 0),
            default=('none', {'drawdown': 0})
        )
        
        return SimulationSummary(
            p10_return=mc.get('p10', 0) / 100 - 1 if mc.get('p10') else -0.10,
            p50_return=mc.get('p50', 0) / 100 - 1 if mc.get('p50') else 0.0,
            p90_return=mc.get('p90', 0) / 100 - 1 if mc.get('p90') else 0.10,
            var_95=mc.get('var_95', 0.05),
            cvar_95=mc.get('cvar_95', 0.08),
            worst_stress_scenario=worst_scenario[0],
            worst_stress_loss=worst_scenario[1].get('drawdown', 0),
            fed_shock_impact=causal.get('fed_shock_impact', 0),
            vix_spike_impact=causal.get('vix_spike_impact', 0),
            oil_shock_impact=causal.get('oil_shock_impact', 0),
            estimated_slippage_bps=mm.get('expected_slippage_bps', 5),
            market_impact_bps=mm.get('expected_slippage_bps', 5) * 1.5
        )
    
    def generate_decision_brief(
        self,
        asset: str,
        current_price: float,
        wargame: WargameResult,
        simulation: SimulationSummary,
        swarm_signal: Dict[str, Any],
        visual_signals: List[Dict[str, Any]],
        backtest_results: Dict[str, Any],
        genome_info: Dict[str, Any],
        risk_decision: Dict[str, Any]
    ) -> DecisionBrief:
        """
        Step 4: Generate structured decision brief.
        """
        # Determine direction and size
        direction = "LONG" if wargame.adjudicated_direction == "long" else "SHORT"
        size_pct = risk_decision.get('recommended_position_size', 0.01)
        
        # Calculate levels
        if direction == "LONG":
            stop_loss = current_price * 0.95
            take_profit = wargame.bull_price_targets[1] if wargame.bull_price_targets else current_price * 1.10
        else:
            stop_loss = current_price * 1.05
            take_profit = current_price * 0.90
        
        stop_pct = abs(stop_loss - current_price) / current_price
        target_pct = abs(take_profit - current_price) / current_price
        
        # Build thesis
        thesis = f"{asset} expected to {'rise' if direction == 'LONG' else 'fall'} based on {wargame.bull_thesis[:100] if direction == 'LONG' else wargame.bear_counter_thesis[:100]}"
        
        # Extract evidence and risks
        evidence = [
            f"Bull confidence: {wargame.bull_confidence:.0%}",
            f"Simulation P50: {simulation.p50_return:+.1%}",
            f"Swarm consensus: {swarm_signal.get('direction', 'neutral')}"
        ]
        
        risks = [
            f"Bear confidence: {wargame.bear_confidence:.0%}",
            f"VaR 95: {simulation.var_95:.1%}",
            f"Worst stress: {simulation.worst_stress_scenario} ({simulation.worst_stress_loss:.1%})"
        ]
        
        # Visual signal summary
        visual_summary = "No visual signals" if not visual_signals else f"{len(visual_signals)} visual signals analyzed"
        
        # Calculate confidence
        base_confidence = wargame.adjudicated_confidence * 100
        risk_adjustment = -10 if not risk_decision.get('approved', False) else 0
        simulation_adjustment = 10 if simulation.p50_return > 0.05 else -5 if simulation.p50_return < 0 else 0
        
        confidence = int(min(100, max(0, base_confidence + risk_adjustment + simulation_adjustment)))
        
        # Determine approval status
        if not risk_decision.get('approved', False):
            approval_status = ApprovalStatus.REJECTED
        elif confidence >= self.AUTO_EXECUTE_THRESHOLD:
            approval_status = ApprovalStatus.AUTO_EXECUTE
        elif confidence >= self.HUMAN_REVIEW_THRESHOLD:
            approval_status = ApprovalStatus.HUMAN_REVIEW
        else:
            approval_status = ApprovalStatus.REJECTED
        
        brief = DecisionBrief(
            asset=asset,
            direction=direction,
            venue="IBKR" if not asset.endswith('USDT') else "Binance",
            size_pct=size_pct,
            entry_price=current_price,
            stop_loss=stop_loss,
            stop_pct=stop_pct,
            take_profit=take_profit,
            target_pct=target_pct,
            horizon_days=20,
            one_sentence_thesis=thesis,
            key_evidence=evidence,
            key_risks=risks,
            swarm_direction=swarm_signal.get('direction', 'neutral'),
            swarm_strength=swarm_signal.get('strength', 0),
            swarm_dissent=swarm_signal.get('dissent_ratio', 0),
            dominant_fish=swarm_signal.get('dominant_fish', ''),
            visual_signal_summary=visual_summary,
            causal_scenarios={
                'base': simulation.p50_return,
                'fed_shock': simulation.fed_shock_impact,
                'vix_spike': simulation.vix_spike_impact,
                'oil_shock': simulation.oil_shock_impact
            },
            backtest_sharpe=backtest_results.get('sharpe_ratio', 0),
            backtest_max_dd=backtest_results.get('max_drawdown', 0),
            backtest_win_rate=backtest_results.get('win_rate', 0.5),
            simulation_p10=simulation.p10_return,
            simulation_p50=simulation.p50_return,
            simulation_p90=simulation.p90_return,
            confidence=confidence,
            approval_status=approval_status,
            genome_id=genome_info.get('genome_id', ''),
            genome_generation=genome_info.get('generation', 0),
            genome_fitness=genome_info.get('fitness_score', 0),
            audit_reference_id=f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
        
        self.decisions.append(brief)
        return brief
    
    def approval_gate(self, brief: DecisionBrief) -> Tuple[bool, str]:
        """
        Step 5: Final approval gate.
        
        Returns:
            Tuple of (approved, reason)
        """
        if brief.approval_status == ApprovalStatus.AUTO_EXECUTE:
            return True, "Auto-approved: confidence >= 75 and all risk checks passed"
        
        elif brief.approval_status == ApprovalStatus.HUMAN_REVIEW:
            return False, f"Requires human review: confidence {brief.confidence}/100"
        
        else:
            return False, f"Rejected: confidence {brief.confidence}/100 below threshold"
    
    def get_decision_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent decision history"""
        return [d.to_dict() for d in self.decisions[-limit:]]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get decision engine statistics"""
        if not self.decisions:
            return {'total_decisions': 0}
        
        approved = sum(1 for d in self.decisions if d.approval_status == ApprovalStatus.AUTO_EXECUTE)
        review = sum(1 for d in self.decisions if d.approval_status == ApprovalStatus.HUMAN_REVIEW)
        rejected = sum(1 for d in self.decisions if d.approval_status == ApprovalStatus.REJECTED)
        
        return {
            'total_decisions': len(self.decisions),
            'auto_approved': approved,
            'human_review': review,
            'rejected': rejected,
            'approval_rate': approved / len(self.decisions),
            'avg_confidence': np.mean([d.confidence for d in self.decisions]),
            'avg_position_size': np.mean([d.size_pct for d in self.decisions])
        }
