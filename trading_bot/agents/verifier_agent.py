"""
Verifier Agent - Independent safety checks with veto power

Runs in separate process for independence. Can reject planner proposals
and close existing positions if risk limits violated.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from .planner_agent import TradeProposal

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of trade verification"""
    approved: bool
    reason: str
    checks_passed: Dict[str, bool]
    risk_metrics: Dict[str, float]


class VerifierAgent:
    """
    Verifier Agent - Independent safety validator
    
    Checks:
    - Position size within limits
    - Correlation exposure acceptable
    - Total portfolio risk < threshold
    - Forecast confidence > minimum
    - No conflicting positions
    - Risk:reward ratio acceptable
    """
    
    def __init__(
        self,
        max_position_size: float = 0.50,
        max_portfolio_risk: float = 0.05,
        max_correlation_exposure: float = 0.70,
        min_confidence: float = 0.60,
        min_risk_reward: float = 1.5,
        max_total_exposure: float = 2.0
    ):
        try:
            self.max_position_size = max_position_size
            self.max_portfolio_risk = max_portfolio_risk
            self.max_correlation_exposure = max_correlation_exposure
            self.min_confidence = min_confidence
            self.min_risk_reward = min_risk_reward
            self.max_total_exposure = max_total_exposure
        
            self.verification_history: List[VerificationResult] = []
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def verify_proposal(
        self,
        proposal: TradeProposal,
        current_positions: List[Dict],
        current_equity: float,
        correlation_matrix: Optional[Dict] = None
    ) -> VerificationResult:
        """
        Verify trade proposal against all safety checks
        
        Args:
            proposal: Trade proposal from planner
            current_positions: List of current open positions
            current_equity: Current account equity
            correlation_matrix: Asset correlation matrix
            
        Returns:
            VerificationResult with approval status
        """
        try:
            checks = {}
        
            # Check 1: Position size
            checks['position_size'] = self._check_position_size(proposal)
        
            # Check 2: Confidence threshold
            checks['confidence'] = self._check_confidence(proposal)
        
            # Check 3: Risk:reward ratio
            checks['risk_reward'] = self._check_risk_reward(proposal)
        
            # Check 4: Portfolio risk
            checks['portfolio_risk'] = self._check_portfolio_risk(
                proposal, current_positions, current_equity
            )
        
            # Check 5: Correlation exposure
            checks['correlation'] = self._check_correlation(
                proposal, current_positions, correlation_matrix
            )
        
            # Check 6: Total exposure
            checks['total_exposure'] = self._check_total_exposure(
                proposal, current_positions, current_equity
            )
        
            # Check 7: Conflicting positions
            checks['conflicts'] = self._check_conflicts(proposal, current_positions)
        
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                proposal, current_positions, current_equity
            )
        
            # Determine approval
            all_passed = all(checks.values())
        
            if all_passed:
                reason = "All safety checks passed"
                approved = True
            else:
                failed_checks = [k for k, v in checks.items() if not v]
                reason = f"Failed checks: {', '.join(failed_checks)}"
                approved = False
        
            result = VerificationResult(
                approved=approved,
                reason=reason,
                checks_passed=checks,
                risk_metrics=risk_metrics
            )
        
            self.verification_history.append(result)
        
            logger.info(
                f"Verification {'APPROVED' if approved else 'REJECTED'}: "
                f"{proposal.symbol} {proposal.action} - {reason}"
            )
        
            return result
        except Exception as e:
            logger.error(f"Error in verify_proposal: {e}")
            raise
    
    def _check_position_size(self, proposal: TradeProposal) -> bool:
        """Check if position size is within limits"""
        return proposal.lots <= self.max_position_size
    
    def _check_confidence(self, proposal: TradeProposal) -> bool:
        """Check if confidence meets minimum threshold"""
        return proposal.confidence >= self.min_confidence
    
    def _check_risk_reward(self, proposal: TradeProposal) -> bool:
        """Check if risk:reward ratio is acceptable"""
        return proposal.risk_reward_ratio >= self.min_risk_reward
    
    def _check_portfolio_risk(
        self,
        proposal: TradeProposal,
        current_positions: List[Dict],
        current_equity: float
    ) -> bool:
        """Check if adding this trade keeps portfolio risk acceptable"""
        # Current portfolio risk
        try:
            current_risk = sum(
                pos.get('risk_amount', 0) for pos in current_positions
            )
        
            # New trade risk
            new_risk = proposal.expected_risk
        
            # Total risk
            total_risk = current_risk + new_risk
        
            # Risk as percentage of equity
            risk_pct = total_risk / current_equity if current_equity > 0 else 1.0
        
            return risk_pct <= self.max_portfolio_risk
        except Exception as e:
            logger.error(f"Error in _check_portfolio_risk: {e}")
            raise
    
    def _check_correlation(
        self,
        proposal: TradeProposal,
        current_positions: List[Dict],
        correlation_matrix: Optional[Dict]
    ) -> bool:
        """Check correlation exposure"""
        try:
            if not correlation_matrix or not current_positions:
                return True
        
            # Calculate correlation-weighted exposure
            total_corr_exposure = 0.0
        
            for pos in current_positions:
                pos_symbol = pos.get('symbol')
                if pos_symbol and pos_symbol in correlation_matrix:
                    corr = correlation_matrix.get(pos_symbol, {}).get(proposal.symbol, 0)
                
                    # If same direction and high correlation, add exposure
                    if pos.get('action') == proposal.action and abs(corr) > 0.5:
                        total_corr_exposure += abs(corr) * pos.get('lots', 0)
        
            return total_corr_exposure <= self.max_correlation_exposure
        except Exception as e:
            logger.error(f"Error in _check_correlation: {e}")
            raise
    
    def _check_total_exposure(
        self,
        proposal: TradeProposal,
        current_positions: List[Dict],
        current_equity: float
    ) -> bool:
        """Check total exposure across all positions"""
        # Current exposure
        try:
            current_exposure = sum(pos.get('lots', 0) for pos in current_positions)
        
            # New exposure
            total_exposure = current_exposure + proposal.lots
        
            return total_exposure <= self.max_total_exposure
        except Exception as e:
            logger.error(f"Error in _check_total_exposure: {e}")
            raise
    
    def _check_conflicts(
        self,
        proposal: TradeProposal,
        current_positions: List[Dict]
    ) -> bool:
        """Check for conflicting positions (opposite direction on same symbol)"""
        try:
            for pos in current_positions:
                if pos.get('symbol') == proposal.symbol:
                    # Opposite direction = conflict
                    if pos.get('action') != proposal.action:
                        return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _check_conflicts: {e}")
            raise
    
    def _calculate_risk_metrics(
        self,
        proposal: TradeProposal,
        current_positions: List[Dict],
        current_equity: float
    ) -> Dict[str, float]:
        """Calculate comprehensive risk metrics"""
        # Portfolio risk
        try:
            current_risk = sum(pos.get('risk_amount', 0) for pos in current_positions)
            new_risk = proposal.expected_risk
            total_risk = current_risk + new_risk
            portfolio_risk_pct = (total_risk / current_equity * 100) if current_equity > 0 else 0
        
            # Exposure
            current_exposure = sum(pos.get('lots', 0) for pos in current_positions)
            total_exposure = current_exposure + proposal.lots
        
            # Concentration (max single position)
            all_positions = [p.get('lots', 0) for p in current_positions] + [proposal.lots]
            max_concentration = max(all_positions) if all_positions else 0
        
            return {
                'portfolio_risk_pct': portfolio_risk_pct,
                'total_exposure_lots': total_exposure,
                'max_concentration_lots': max_concentration,
                'num_positions': len(current_positions) + 1,
                'new_trade_risk_pct': (new_risk / current_equity * 100) if current_equity > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error in _calculate_risk_metrics: {e}")
            raise
    
    def should_close_position(
        self,
        position: Dict,
        current_equity: float,
        drawdown_pct: float
    ) -> Tuple[bool, str]:
        """
        Determine if existing position should be closed
        
        Args:
            position: Position details
            current_equity: Current equity
            drawdown_pct: Current drawdown percentage
            
        Returns:
            Tuple of (should_close, reason)
        """
        # Emergency close if drawdown too large
        try:
            if drawdown_pct > 15:
                return True, f"Emergency: Drawdown {drawdown_pct:.1f}% > 15%"
        
            # Close if position loss exceeds threshold
            pnl = position.get('pnl', 0)
            if pnl < 0:
                loss_pct = abs(pnl) / current_equity * 100
                if loss_pct > 2:
                    return True, f"Position loss {loss_pct:.1f}% > 2%"
        
            # Close if position held too long
            duration_hours = position.get('duration_hours', 0)
            if duration_hours > 72:  # 3 days
                return True, f"Position held {duration_hours:.0f}h > 72h"
        
            return False, "Position OK"
        except Exception as e:
            logger.error(f"Error in should_close_position: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create verifier
    verifier = VerifierAgent(
        max_position_size=0.50,
        max_portfolio_risk=0.05,
        min_confidence=0.60
    )
    
    # Create sample proposal
    from datetime import datetime
    proposal = TradeProposal(
        proposal_id="TEST_001",
        timestamp=datetime.now(),
        symbol="EURUSD",
        action="long",
        lots=0.30,
        reasoning="Test proposal",
        confidence=0.75,
        expected_return=50.0,
        expected_risk=25.0,
        stop_loss_pips=25.0,
        take_profit_pips=50.0,
        technical_score=0.7,
        fundamental_score=0.6,
        sentiment_score=0.8,
        forecast_score=0.75,
        market_regime="trending_bullish",
        volatility_regime="normal",
        trend_strength=0.8,
        risk_reward_ratio=2.0,
        win_probability=0.65,
        kelly_fraction=0.15
    )
    
    # Current positions
    current_positions = [
        {'symbol': 'GBPUSD', 'action': 'long', 'lots': 0.20, 'risk_amount': 20.0}
    ]
    
    # Verify
    result = verifier.verify_proposal(
        proposal,
        current_positions,
        current_equity=10000.0
    )
    
    print("\n" + "="*60)
    logger.info("VERIFICATION RESULT")
    print("="*60)
    logger.info(f"Approved: {result.approved}")
    logger.info(f"Reason: {result.reason}")
    logger.info(f"\nChecks:")
    for check, passed in result.checks_passed.items():
        status = "✓" if passed else "✗"
        logger.info(f"  {status} {check}")
    logger.info(f"\nRisk Metrics:")
    for metric, value in result.risk_metrics.items():
        logger.info(f"  {metric}: {value:.2f}")
    print("="*60)
