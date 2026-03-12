"""
Adversarial Kill Phase - STEP 4

Assumes multiple adversarial roles to find failure modes:
- Trade Killer: find reasons this trade fails
- Historian: locate similar past losses
- Risk Prosecutor: assume worst-case tail event
- Execution Saboteur: assume poor fills and latency
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from .claim_system import TradeClaim, ClaimType

logger = logging.getLogger(__name__)


class AdversarialRole(Enum):
    """Adversarial roles for kill phase"""
    TRADE_KILLER = "trade_killer"
    HISTORIAN = "historian"
    RISK_PROSECUTOR = "risk_prosecutor"
    EXECUTION_SABOTEUR = "execution_saboteur"


@dataclass
class AdversarialObjection:
    """An objection raised by an adversarial role"""
    role: AdversarialRole
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    objection: str
    evidence: Dict[str, Any]
    credible: bool = True
    timestamp: datetime = field(default_factory=datetime.utcnow)


class TradeKiller:
    """
    Role: Find reasons this trade will fail
    Assumes worst-case scenarios and looks for vulnerabilities
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def find_kill_reasons(
        self,
        claims: List[TradeClaim],
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> List[AdversarialObjection]:
        """Find credible reasons why this trade will fail"""
        objections = []
        
        try:
            # Check for weak claims
            for claim in claims:
                if not claim.is_valid():
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.TRADE_KILLER,
                        severity="CRITICAL",
                        objection=f"Claim {claim.claim_type.value} failed verification",
                        evidence={'claim': claim.statement, 'score': claim.verification_score},
                        credible=True
                    ))
            
            # Check for edge density collapse
            edge_density = signal_data.get('edge_density', 0.0)
            if edge_density < 0.3:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.TRADE_KILLER,
                    severity="CRITICAL",
                    objection=f"Edge density below minimum viable threshold: {edge_density:.4f} < 0.3",
                    evidence={'edge_density': edge_density},
                    credible=True
                ))
            
            # Check for strategy dispersion collapse
            active_strategies = signal_data.get('active_strategies', 0)
            if active_strategies < 2:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.TRADE_KILLER,
                    severity="HIGH",
                    objection=f"Strategy dispersion collapsed: only {active_strategies} active",
                    evidence={'active_strategies': active_strategies},
                    credible=True
                ))
            
            # Check for regime inconsistency
            regime = market_data.get('regime', 'UNKNOWN')
            profitable_regimes = signal_data.get('profitable_regimes', [])
            if regime not in profitable_regimes:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.TRADE_KILLER,
                    severity="HIGH",
                    objection=f"Current regime '{regime}' not in profitable regimes: {profitable_regimes}",
                    evidence={'regime': regime, 'profitable_regimes': profitable_regimes},
                    credible=True
                ))
            
            # Check for signal staleness
            signal_age = signal_data.get('signal_age_seconds', 0)
            if signal_age > 60:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.TRADE_KILLER,
                    severity="MEDIUM",
                    objection=f"Signal is stale: {signal_age}s old",
                    evidence={'signal_age': signal_age},
                    credible=True
                ))
            
            # Check for overfit indicators
            in_sample_sharpe = signal_data.get('in_sample_sharpe', 0.0)
            out_sample_sharpe = signal_data.get('out_sample_sharpe', 0.0)
            if in_sample_sharpe > 0 and out_sample_sharpe > 0:
                sharpe_ratio = out_sample_sharpe / in_sample_sharpe
                if sharpe_ratio < 0.5:
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.TRADE_KILLER,
                        severity="HIGH",
                        objection=f"Severe overfit detected: out/in Sharpe ratio = {sharpe_ratio:.2f}",
                        evidence={'in_sample': in_sample_sharpe, 'out_sample': out_sample_sharpe},
                        credible=True
                    ))
            
        except Exception as e:
            logger.error(f"Trade killer analysis failed: {e}")
        
        return objections


class Historian:
    """
    Role: Locate similar past losses
    Searches historical data for analogous failures
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.loss_database = {}
        
    def find_similar_losses(
        self,
        claims: List[TradeClaim],
        market_data: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> List[AdversarialObjection]:
        """Find similar historical losses"""
        objections = []
        
        try:
            # Check for loss clustering patterns
            recent_losses = historical_data.get('recent_losses', [])
            if len(recent_losses) >= 3:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.HISTORIAN,
                    severity="HIGH",
                    objection=f"Loss clustering detected: {len(recent_losses)} recent losses",
                    evidence={'recent_losses': len(recent_losses), 'losses': recent_losses[-5:]},
                    credible=True
                ))
            
            # Check for regime transition failures
            regime = market_data.get('regime', 'UNKNOWN')
            regime_losses = historical_data.get('regime_losses', {}).get(regime, [])
            if len(regime_losses) > 0:
                avg_loss = sum(regime_losses) / len(regime_losses)
                if avg_loss < -0.02:  # Average loss > 2%
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.HISTORIAN,
                        severity="HIGH",
                        objection=f"Historical losses in {regime} regime: avg {avg_loss:.2%}",
                        evidence={'regime': regime, 'avg_loss': avg_loss, 'count': len(regime_losses)},
                        credible=True
                    ))
            
            # Check for similar market conditions that led to losses
            similar_conditions = historical_data.get('similar_conditions', [])
            loss_conditions = [c for c in similar_conditions if c.get('outcome', 0) < 0]
            if len(loss_conditions) > len(similar_conditions) * 0.6:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.HISTORIAN,
                    severity="MEDIUM",
                    objection=f"Similar conditions led to losses {len(loss_conditions)}/{len(similar_conditions)} times",
                    evidence={'loss_rate': len(loss_conditions) / len(similar_conditions)},
                    credible=True
                ))
            
            # Check for drawdown periods
            current_drawdown = historical_data.get('current_drawdown', 0.0)
            if current_drawdown > 0.10:  # 10% drawdown
                objections.append(AdversarialObjection(
                    role=AdversarialRole.HISTORIAN,
                    severity="HIGH",
                    objection=f"Currently in drawdown: {current_drawdown:.2%}",
                    evidence={'drawdown': current_drawdown},
                    credible=True
                ))
            
        except Exception as e:
            logger.error(f"Historian analysis failed: {e}")
        
        return objections


class RiskProsecutor:
    """
    Role: Assume worst-case tail event
    Prosecutes the trade from a risk perspective
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def prosecute_risk(
        self,
        claims: List[TradeClaim],
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> List[AdversarialObjection]:
        """Prosecute trade assuming worst-case scenarios"""
        objections = []
        
        try:
            # Check tail risk claim
            tail_claim = next((c for c in claims if c.claim_type == ClaimType.TAIL_RISK_EXPOSURE), None)
            if tail_claim:
                evidence = tail_claim.evidence
                
                # CVaR check
                cvar_95 = evidence.get('cvar_95', 0.0)
                if cvar_95 > 0.05:  # 5% CVaR
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.RISK_PROSECUTOR,
                        severity="CRITICAL",
                        objection=f"Excessive CVaR95: {cvar_95:.2%}",
                        evidence={'cvar_95': cvar_95},
                        credible=True
                    ))
                
                # Kurtosis check (fat tails)
                kurtosis = evidence.get('kurtosis', 3.0)
                if kurtosis > 5.0:
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.RISK_PROSECUTOR,
                        severity="HIGH",
                        objection=f"Fat tail distribution detected: kurtosis={kurtosis:.2f}",
                        evidence={'kurtosis': kurtosis},
                        credible=True
                    ))
            
            # Check portfolio concentration
            concentration = portfolio_state.get('concentration', 0.0)
            if concentration > 0.3:  # 30% in single position
                objections.append(AdversarialObjection(
                    role=AdversarialRole.RISK_PROSECUTOR,
                    severity="HIGH",
                    objection=f"Excessive portfolio concentration: {concentration:.2%}",
                    evidence={'concentration': concentration},
                    credible=True
                ))
            
            # Check correlation risk
            correlation_claim = next((c for c in claims if c.claim_type == ClaimType.CORRELATION_PORTFOLIO), None)
            if correlation_claim:
                max_correlation = correlation_claim.evidence.get('max_correlation', 0.0)
                if max_correlation > 0.8:
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.RISK_PROSECUTOR,
                        severity="HIGH",
                        objection=f"High correlation risk: {max_correlation:.2f}",
                        evidence={'max_correlation': max_correlation},
                        credible=True
                    ))
            
            # Check leverage
            leverage = portfolio_state.get('leverage', 1.0)
            if leverage > 3.0:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.RISK_PROSECUTOR,
                    severity="CRITICAL",
                    objection=f"Excessive leverage: {leverage:.1f}x",
                    evidence={'leverage': leverage},
                    credible=True
                ))
            
            # Check volatility regime
            volatility_regime = market_data.get('volatility_regime', 'NORMAL')
            if volatility_regime in ['EXTREME', 'CRISIS']:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.RISK_PROSECUTOR,
                    severity="CRITICAL",
                    objection=f"Dangerous volatility regime: {volatility_regime}",
                    evidence={'volatility_regime': volatility_regime},
                    credible=True
                ))
            
        except Exception as e:
            logger.error(f"Risk prosecutor analysis failed: {e}")
        
        return objections


class ExecutionSaboteur:
    """
    Role: Assume poor fills and latency
    Sabotages execution assumptions
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
    def sabotage_execution(
        self,
        claims: List[TradeClaim],
        market_data: Dict[str, Any]
    ) -> List[AdversarialObjection]:
        """Sabotage execution assumptions"""
        objections = []
        
        try:
            # Check execution claim
            exec_claim = next((c for c in claims if c.claim_type == ClaimType.EXECUTION_FEASIBILITY), None)
            if exec_claim:
                evidence = exec_claim.evidence
                
                # Latency check
                latency = evidence.get('latency', 0.0)
                if latency > 50:  # 50ms
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.EXECUTION_SABOTEUR,
                        severity="HIGH",
                        objection=f"High latency will cause slippage: {latency:.2f}ms",
                        evidence={'latency': latency},
                        credible=True
                    ))
                
                # Venue status check
                venue_status = evidence.get('venue_status', 'ONLINE')
                if venue_status != 'ONLINE':
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.EXECUTION_SABOTEUR,
                        severity="CRITICAL",
                        objection=f"Venue not fully online: {venue_status}",
                        evidence={'venue_status': venue_status},
                        credible=True
                    ))
            
            # Check liquidity claim
            liq_claim = next((c for c in claims if c.claim_type == ClaimType.LIQUIDITY_SLIPPAGE), None)
            if liq_claim:
                evidence = liq_claim.evidence
                
                # Spread check
                spread = evidence.get('bid_ask_spread', 0.0)
                if spread > 0.001:  # 10 bps
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.EXECUTION_SABOTEUR,
                        severity="MEDIUM",
                        objection=f"Wide spread will cause slippage: {spread:.6f}",
                        evidence={'spread': spread},
                        credible=True
                    ))
                
                # Volume check
                volume = evidence.get('volume', 0.0)
                avg_volume = evidence.get('avg_volume', 1.0)
                if avg_volume > 0:
                    volume_ratio = volume / avg_volume
                    if volume_ratio < 0.5:
                        objections.append(AdversarialObjection(
                            role=AdversarialRole.EXECUTION_SABOTEUR,
                            severity="HIGH",
                            objection=f"Low volume increases execution risk: {volume_ratio:.2f}x average",
                            evidence={'volume_ratio': volume_ratio},
                            credible=True
                        ))
                
                # Market depth check
                market_depth = evidence.get('market_depth', 0.0)
                if market_depth < 1000:
                    objections.append(AdversarialObjection(
                        role=AdversarialRole.EXECUTION_SABOTEUR,
                        severity="HIGH",
                        objection=f"Shallow market depth: {market_depth:.0f}",
                        evidence={'market_depth': market_depth},
                        credible=True
                    ))
            
            # Check market hours
            market_hours = market_data.get('market_hours', True)
            if not market_hours:
                objections.append(AdversarialObjection(
                    role=AdversarialRole.EXECUTION_SABOTEUR,
                    severity="CRITICAL",
                    objection="Trading outside market hours",
                    evidence={'market_hours': market_hours},
                    credible=True
                ))
            
        except Exception as e:
            logger.error(f"Execution saboteur analysis failed: {e}")
        
        return objections


class AdversarialKillPhase:
    """
    Orchestrates all adversarial roles to find credible failure modes.
    
    If any role produces a credible failure mode, it is flagged.
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.trade_killer = TradeKiller(config)
        self.historian = Historian(config)
        self.risk_prosecutor = RiskProsecutor(config)
        self.execution_saboteur = ExecutionSaboteur(config)
        
    def execute_kill_phase(
        self,
        claims: List[TradeClaim],
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any],
        portfolio_state: Dict[str, Any],
        historical_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute adversarial kill phase.
        
        Returns:
            Dictionary with all objections and kill decision
        """
        all_objections = []
        
        # Execute each adversarial role
        all_objections.extend(
            self.trade_killer.find_kill_reasons(claims, market_data, signal_data)
        )
        all_objections.extend(
            self.historian.find_similar_losses(claims, market_data, historical_data)
        )
        all_objections.extend(
            self.risk_prosecutor.prosecute_risk(claims, market_data, portfolio_state)
        )
        all_objections.extend(
            self.execution_saboteur.sabotage_execution(claims, market_data)
        )
        
        # Count critical objections
        critical_objections = [o for o in all_objections if o.severity == "CRITICAL" and o.credible]
        high_objections = [o for o in all_objections if o.severity == "HIGH" and o.credible]
        
        # Determine if trade should be killed
        should_kill = len(critical_objections) > 0 or len(high_objections) >= 2
        
        return {
            'should_kill': should_kill,
            'all_objections': all_objections,
            'critical_count': len(critical_objections),
            'high_count': len(high_objections),
            'total_count': len(all_objections),
            'kill_reason': self._get_kill_reason(critical_objections, high_objections)
        }
    
    def _get_kill_reason(
        self,
        critical_objections: List[AdversarialObjection],
        high_objections: List[AdversarialObjection]
    ) -> Optional[str]:
        """Get primary kill reason"""
        if critical_objections:
            return critical_objections[0].objection
        elif len(high_objections) >= 2:
            return f"Multiple high-severity objections: {', '.join([o.objection for o in high_objections[:2]])}"
        return None
