"""
Claim Decomposition System - STEP 2

Decomposes trades into independent falsifiable claims.
No claims → no trade.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClaimType(Enum):
    """Mandatory claim types for every trade"""
    REGIME_VALIDITY = "regime_validity"
    SIGNAL_EXPECTANCY = "signal_expectancy"
    VOLATILITY_SUITABILITY = "volatility_suitability"
    LIQUIDITY_SLIPPAGE = "liquidity_slippage"
    CORRELATION_PORTFOLIO = "correlation_portfolio"
    TAIL_RISK_EXPOSURE = "tail_risk_exposure"
    EXECUTION_FEASIBILITY = "execution_feasibility"


@dataclass
class TradeClaim:
    """
    A falsifiable claim about a trade.
    Each claim must be independently verifiable.
    """
    claim_type: ClaimType
    statement: str
    evidence: Dict[str, Any]
    timestamp: datetime
    verified: bool = False
    verification_score: float = 0.0
    verification_methods: List[str] = field(default_factory=list)
    failure_modes: List[str] = field(default_factory=list)
    
    def is_valid(self) -> bool:
        """Check if claim has been verified and passes threshold"""
        return self.verified and self.verification_score >= 0.6


@dataclass
class ClaimVerification:
    """Result of verifying a claim"""
    claim_type: ClaimType
    verified: bool
    score: float
    method: str
    evidence: Dict[str, Any]
    failure_reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ClaimDecomposer:
    """
    Decomposes trade proposals into mandatory falsifiable claims.
    
    RULE: No claims → no trade
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.mandatory_claims = list(ClaimType)
        
    def decompose_trade(
        self,
        symbol: str,
        direction: str,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> List[TradeClaim]:
        """
        Decompose trade into mandatory falsifiable claims.
        
        Returns:
            List of TradeClaim objects (empty if decomposition fails)
        """
        claims = []
        
        try:
            # CLAIM 1: Regime Validity
            regime_claim = self._create_regime_claim(
                symbol, direction, market_data, signal_data
            )
            if regime_claim:
                claims.append(regime_claim)
            
            # CLAIM 2: Signal Expectancy
            expectancy_claim = self._create_expectancy_claim(
                symbol, direction, signal_data
            )
            if expectancy_claim:
                claims.append(expectancy_claim)
            
            # CLAIM 3: Volatility Suitability
            volatility_claim = self._create_volatility_claim(
                symbol, market_data, signal_data
            )
            if volatility_claim:
                claims.append(volatility_claim)
            
            # CLAIM 4: Liquidity & Slippage
            liquidity_claim = self._create_liquidity_claim(
                symbol, market_data
            )
            if liquidity_claim:
                claims.append(liquidity_claim)
            
            # CLAIM 5: Correlation & Portfolio Interaction
            correlation_claim = self._create_correlation_claim(
                symbol, direction, portfolio_state
            )
            if correlation_claim:
                claims.append(correlation_claim)
            
            # CLAIM 6: Tail Risk Exposure
            tail_risk_claim = self._create_tail_risk_claim(
                symbol, direction, market_data, portfolio_state
            )
            if tail_risk_claim:
                claims.append(tail_risk_claim)
            
            # CLAIM 7: Execution Feasibility
            execution_claim = self._create_execution_claim(
                symbol, direction, market_data
            )
            if execution_claim:
                claims.append(execution_claim)
            
            # Verify all mandatory claims present
            if len(claims) < len(self.mandatory_claims):
                logger.error(
                    f"Failed to create all mandatory claims. "
                    f"Created {len(claims)}/{len(self.mandatory_claims)}"
                )
                return []
            
            return claims
            
        except Exception as e:
            logger.error(f"Claim decomposition failed: {e}")
            return []
    
    def _create_regime_claim(
        self,
        symbol: str,
        direction: str,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create regime validity claim"""
        try:
            regime = market_data.get('regime', 'UNKNOWN')
            volatility = market_data.get('volatility', 0.0)
            trend_strength = market_data.get('trend_strength', 0.0)
            
            statement = (
                f"Current market regime '{regime}' is valid for {direction} trade "
                f"with volatility={volatility:.4f}, trend_strength={trend_strength:.4f}"
            )
            
            evidence = {
                'regime': regime,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'regime_duration': market_data.get('regime_duration', 0),
                'regime_stability': market_data.get('regime_stability', 0.0),
            }
            
            return TradeClaim(
                claim_type=ClaimType.REGIME_VALIDITY,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create regime claim: {e}")
            return None
    
    def _create_expectancy_claim(
        self,
        symbol: str,
        direction: str,
        signal_data: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create signal expectancy claim"""
        try:
            expectancy = signal_data.get('expectancy', 0.0)
            win_rate = signal_data.get('win_rate', 0.0)
            avg_win = signal_data.get('avg_win', 0.0)
            avg_loss = signal_data.get('avg_loss', 0.0)
            sample_size = signal_data.get('sample_size', 0)
            
            statement = (
                f"Signal has positive expectancy={expectancy:.4f} "
                f"with win_rate={win_rate:.2%}, avg_win={avg_win:.4f}, "
                f"avg_loss={avg_loss:.4f}, sample_size={sample_size}"
            )
            
            evidence = {
                'expectancy': expectancy,
                'win_rate': win_rate,
                'avg_win': avg_win,
                'avg_loss': avg_loss,
                'sample_size': sample_size,
                'profit_factor': signal_data.get('profit_factor', 0.0),
                'sharpe_ratio': signal_data.get('sharpe_ratio', 0.0),
            }
            
            return TradeClaim(
                claim_type=ClaimType.SIGNAL_EXPECTANCY,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create expectancy claim: {e}")
            return None
    
    def _create_volatility_claim(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal_data: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create volatility suitability claim"""
        try:
            current_vol = market_data.get('volatility', 0.0)
            historical_vol = market_data.get('historical_volatility', 0.0)
            vol_percentile = market_data.get('volatility_percentile', 50.0)
            
            statement = (
                f"Current volatility={current_vol:.4f} is suitable "
                f"(historical={historical_vol:.4f}, percentile={vol_percentile:.1f})"
            )
            
            evidence = {
                'current_volatility': current_vol,
                'historical_volatility': historical_vol,
                'volatility_percentile': vol_percentile,
                'volatility_regime': market_data.get('volatility_regime', 'NORMAL'),
                'vol_of_vol': market_data.get('vol_of_vol', 0.0),
            }
            
            return TradeClaim(
                claim_type=ClaimType.VOLATILITY_SUITABILITY,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create volatility claim: {e}")
            return None
    
    def _create_liquidity_claim(
        self,
        symbol: str,
        market_data: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create liquidity & slippage claim"""
        try:
            bid_ask_spread = market_data.get('bid_ask_spread', 0.0)
            volume = market_data.get('volume', 0.0)
            avg_volume = market_data.get('avg_volume', 0.0)
            market_depth = market_data.get('market_depth', 0.0)
            
            statement = (
                f"Liquidity is adequate with spread={bid_ask_spread:.6f}, "
                f"volume={volume:.0f}, avg_volume={avg_volume:.0f}, "
                f"depth={market_depth:.2f}"
            )
            
            evidence = {
                'bid_ask_spread': bid_ask_spread,
                'volume': volume,
                'avg_volume': avg_volume,
                'market_depth': market_depth,
                'expected_slippage': market_data.get('expected_slippage', 0.0),
                'liquidity_score': market_data.get('liquidity_score', 0.0),
            }
            
            return TradeClaim(
                claim_type=ClaimType.LIQUIDITY_SLIPPAGE,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create liquidity claim: {e}")
            return None
    
    def _create_correlation_claim(
        self,
        symbol: str,
        direction: str,
        portfolio_state: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create correlation & portfolio interaction claim"""
        try:
            positions = portfolio_state.get('positions', {})
            correlations = portfolio_state.get('correlations', {})
            
            max_correlation = 0.0
            correlated_positions = []
            
            for pos_symbol, pos_data in positions.items():
                if pos_symbol == symbol:
                    continue
                corr = correlations.get(f"{symbol}_{pos_symbol}", 0.0)
                if abs(corr) > 0.7:
                    max_correlation = max(max_correlation, abs(corr))
                    correlated_positions.append((pos_symbol, corr))
            
            statement = (
                f"Portfolio correlation acceptable with max_correlation={max_correlation:.2f}, "
                f"correlated_positions={len(correlated_positions)}"
            )
            
            evidence = {
                'max_correlation': max_correlation,
                'correlated_positions': correlated_positions,
                'portfolio_concentration': portfolio_state.get('concentration', 0.0),
                'sector_exposure': portfolio_state.get('sector_exposure', {}),
            }
            
            return TradeClaim(
                claim_type=ClaimType.CORRELATION_PORTFOLIO,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create correlation claim: {e}")
            return None
    
    def _create_tail_risk_claim(
        self,
        symbol: str,
        direction: str,
        market_data: Dict[str, Any],
        portfolio_state: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create tail risk exposure claim"""
        try:
            var_95 = portfolio_state.get('var_95', 0.0)
            cvar_95 = portfolio_state.get('cvar_95', 0.0)
            max_drawdown = portfolio_state.get('max_drawdown', 0.0)
            tail_ratio = market_data.get('tail_ratio', 1.0)
            
            statement = (
                f"Tail risk acceptable with VaR95={var_95:.4f}, "
                f"CVaR95={cvar_95:.4f}, max_dd={max_drawdown:.4f}, "
                f"tail_ratio={tail_ratio:.2f}"
            )
            
            evidence = {
                'var_95': var_95,
                'cvar_95': cvar_95,
                'max_drawdown': max_drawdown,
                'tail_ratio': tail_ratio,
                'skewness': market_data.get('skewness', 0.0),
                'kurtosis': market_data.get('kurtosis', 3.0),
            }
            
            return TradeClaim(
                claim_type=ClaimType.TAIL_RISK_EXPOSURE,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create tail risk claim: {e}")
            return None
    
    def _create_execution_claim(
        self,
        symbol: str,
        direction: str,
        market_data: Dict[str, Any]
    ) -> Optional[TradeClaim]:
        """Create execution feasibility claim"""
        try:
            latency = market_data.get('latency', 0.0)
            order_book_depth = market_data.get('order_book_depth', 0.0)
            execution_quality = market_data.get('execution_quality', 0.0)
            
            statement = (
                f"Execution feasible with latency={latency:.2f}ms, "
                f"book_depth={order_book_depth:.2f}, "
                f"quality={execution_quality:.2f}"
            )
            
            evidence = {
                'latency': latency,
                'order_book_depth': order_book_depth,
                'execution_quality': execution_quality,
                'venue_status': market_data.get('venue_status', 'ONLINE'),
                'market_hours': market_data.get('market_hours', True),
            }
            
            return TradeClaim(
                claim_type=ClaimType.EXECUTION_FEASIBILITY,
                statement=statement,
                evidence=evidence,
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Failed to create execution claim: {e}")
            return None
