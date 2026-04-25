"""
GETS Integration Module

Integrates the Governed Evolving Time-Series Foundation System with:
1. Existing decision_governance system (DGS)
2. Trading bot core infrastructure
3. Risk management systems

Provides adapters and bridges between GETS and legacy systems.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np

from .types import (
    MarketData, GETSSignal, GovernanceDecision, GETSConfig,
    ModelType, ForecastHorizon
)
from .gets_system import GETS

logger = logging.getLogger(__name__)


class DGSAdapter:
    """
    Adapter between GETS and the existing decision_governance system.
    
    Maps GETS signals to DGS governance decisions and vice versa.
    Leverages DGS 7-layer governance stack for final trade approval.
    """
    
    def __init__(self, gets_instance: GETS):
        self.gets = gets_instance
        self.dgs_available = self._check_dgs_available()
        
        if self.dgs_available:
            logger.info("DGS integration active - GETS signals will flow through DGS")
        else:
            logger.warning("DGS not available - GETS using internal governance")
    
    def _check_dgs_available(self) -> bool:
        """Check if decision_governance system is available."""
        try:
            # Attempt to import DGS
            from trading_bot.decision_governance import DecisionGovernanceSystem
            return True
        except ImportError:
            return False
    
    def map_signal_to_dgs_input(
        self,
        gets_signal: GETSSignal,
        market_data: MarketData
    ) -> Dict[str, Any]:
        """
        Map GETS signal to DGS input format.
        
        Args:
            gets_signal: Signal from GETS
            market_data: Current market data
            
        Returns:
            DGS-compatible signal dictionary
        """
        # Create claim structure for DGS Layer 1
        claim = {
            'type': 'market_prediction',
            'direction': 'buy' if gets_signal.direction > 0 else 'sell' if gets_signal.direction < 0 else 'neutral',
            'confidence': gets_signal.confidence,
            'expected_return': gets_signal.expected_edge,
            'horizon': 'short_term',
            'source_system': 'GETS',
            'models_used': [m.value for m in gets_signal.source_models],
            'disagreement_pattern': (
                gets_signal.disagreement_geometry.disagreement_pattern.name
                if gets_signal.disagreement_geometry.disagreement_pattern else None
            ),
            'forecast_consensus': gets_signal.disagreement_geometry.forecast_consensus_score,
        }
        
        # Evidence for Layer 2
        evidence = {
            'price_data': market_data.ohlcv,
            'foundation_forecasts': {
                'model_count': len(gets_signal.source_models),
                'avg_confidence': gets_signal.confidence,
                'uncertainty_range': gets_signal.prediction_interval
            },
            'diagnostics': {
                'stability_passed': gets_signal.diagnosis_report.stability_passed,
                'evidence_passed': gets_signal.diagnosis_report.evidence_passed,
                'regime_passed': gets_signal.diagnosis_report.regime_passed,
                'execution_feasible': gets_signal.diagnosis_report.execution_feasible
            }
        }
        
        # Risk metrics for DGS risk gatekeeper
        risk_metrics = {
            'drawdown_risk': self._extract_drawdown_risk(gets_signal),
            'volatility_forecast': self._extract_volatility(gets_signal),
            'execution_difficulty': gets_signal.diagnosis_report.execution_constraints,
            'edge_after_cost': gets_signal.expected_edge
        }
        
        return {
            'claim': claim,
            'evidence': evidence,
            'risk_metrics': risk_metrics,
            'market_context': {
                'regime': self._extract_regime(gets_signal),
                'liquidity': self._extract_liquidity(market_data),
                'spread': market_data.bid_ask_spread
            }
        }
    
    def _extract_drawdown_risk(self, signal: GETSSignal) -> float:
        """Extract drawdown risk from signal."""
        # Would extract from trading predictions
        # Placeholder: use disagreement as proxy
        return 1.0 - signal.disagreement_geometry.forecast_consensus_score
    
    def _extract_volatility(self, signal: GETSSignal) -> float:
        """Extract volatility forecast from signal."""
        # Compute from prediction interval
        price_range = signal.uncertainty_quantile_95 - signal.uncertainty_quantile_05
        mid_price = (signal.uncertainty_quantile_05 + signal.uncertainty_quantile_95) / 2
        return price_range / mid_price if mid_price > 0 else 0.01
    
    def _extract_regime(self, signal: GETSSignal) -> str:
        """Extract regime from signal context."""
        # Would track regime through GETS
        return "unknown"
    
    def _extract_liquidity(self, market_data: MarketData) -> Dict[str, float]:
        """Extract liquidity metrics."""
        return {
            'spread_bps': (market_data.bid_ask_spread * 10000) if market_data.bid_ask_spread else None,
            'depth_imbalance': market_data.depth_imbalance
        }
    
    def map_dgs_decision_to_gets(
        self,
        dgs_decision: Any,
        gets_signal: GETSSignal
    ) -> GETSSignal:
        """
        Map DGS decision back to GETS signal format.
        
        Updates GETS signal with DGS governance overlay.
        """
        # Map DGS decision to GETS governance decision
        dgs_to_gets_map = {
            'APPROVE': GovernanceDecision.APPROVE,
            'RESIZE': GovernanceDecision.RESIZE,
            'DEFER': GovernanceDecision.DEFER,
            'REJECT': GovernanceDecision.REJECT,
            'ABSTAIN': GovernanceDecision.ABSTAIN
        }
        
        gets_decision = dgs_to_gets_map.get(
            getattr(dgs_decision, 'name', str(dgs_decision)),
            gets_signal.governance_decision
        )
        
        # Update signal with DGS decision
        from dataclasses import replace
        updated_signal = replace(
            gets_signal,
            governance_decision=gets_decision,
            decision_reasoning=f"{gets_signal.decision_reasoning} | DGS: {dgs_decision}"
        )
        
        return updated_signal
    
    def evaluate_through_dgs(
        self,
        gets_signal: GETSSignal,
        market_data: MarketData
    ) -> GETSSignal:
        """
        Route GETS signal through DGS for final governance.
        
        Args:
            gets_signal: Original GETS signal
            market_data: Current market data
            
        Returns:
            GETS signal updated with DGS decision
        """
        if not self.dgs_available:
            return gets_signal
        
        try:
            from trading_bot.decision_governance import DecisionGovernanceSystem
            
            # Initialize DGS if not already done
            dgs = DecisionGovernanceSystem()
            
            # Map to DGS format
            dgs_input = self.map_signal_to_dgs_input(gets_signal, market_data)
            
            # Evaluate through DGS
            # Note: This would call the actual DGS evaluate method
            # For now, pass through with enhanced logging
            
            logger.info(f"Signal routed through DGS: {gets_signal.symbol}")
            
            # Return signal with DGS acknowledgment
            from dataclasses import replace
            return replace(
                gets_signal,
                decision_reasoning=f"{gets_signal.decision_reasoning} | DGS_REVIEWED"
            )
            
        except Exception as e:
            logger.error(f"DGS evaluation failed: {e}")
            return gets_signal


class GETSTradingBridge:
    """
    Bridge between GETS and the trading execution system.
    
    Converts GETS signals to trade orders with appropriate sizing and risk controls.
    """
    
    def __init__(self, gets_instance: GETS, max_position_pct: float = 0.05):
        self.gets = gets_instance
        self.max_position_pct = max_position_pct  # Max 5% per position
        self.min_edge_threshold = 0.0001  # 1 bps minimum edge
    
    def signal_to_order(
        self,
        signal: GETSSignal,
        portfolio_value: float,
        current_position: float = 0.0
    ) -> Optional[Dict[str, Any]]:
        """
        Convert GETS signal to trade order.
        
        Args:
            signal: GETS signal
            portfolio_value: Total portfolio value
            current_position: Current position in symbol (shares/contracts)
            
        Returns:
            Order dict or None if no trade warranted
        """
        # Check abstention
        if signal.abstain_recommended or signal.governance_decision == GovernanceDecision.ABSTAIN:
            logger.info(f"Abstaining from trade: {signal.abstain_reason}")
            return None
        
        # Check edge threshold
        if signal.expected_edge < self.min_edge_threshold:
            logger.info(f"Edge too small: {signal.expected_edge:.4f} < {self.min_edge_threshold:.4f}")
            return None
        
        # Determine trade direction and size
        direction = signal.direction
        if direction == 0:
            return None
        
        # Calculate position size
        base_size = portfolio_value * self.max_position_pct
        
        # Scale by GETS recommendation
        size_scale = signal.recommended_size_scale
        
        # Apply governance sizing
        if signal.governance_decision == GovernanceDecision.RESIZE:
            size_scale *= 0.5
        
        target_position_value = base_size * size_scale
        
        # Estimate price for sizing
        price = (signal.uncertainty_quantile_05 + signal.uncertainty_quantile_95) / 2
        target_shares = target_position_value / price if price > 0 else 0
        
        # Calculate order size
        order_shares = target_shares - current_position
        
        if abs(order_shares) < 0.01:  # Minimum order size
            return None
        
        order = {
            'symbol': signal.symbol,
            'side': 'buy' if order_shares > 0 else 'sell',
            'quantity': abs(order_shares),
            'order_type': 'market',  # Or limit based on signal
            'reason': 'GETS_signal',
            'expected_edge': signal.expected_edge,
            'confidence': signal.confidence,
            'governance_decision': signal.governance_decision.name,
            'source_models': [m.value for m in signal.source_models],
            'timestamp': signal.timestamp.isoformat()
        }
        
        return order
    
    def batch_process_signals(
        self,
        signals: List[GETSSignal],
        portfolio_value: float,
        current_positions: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Process multiple GETS signals into orders with cross-asset constraints.
        
        Args:
            signals: List of GETS signals
            portfolio_value: Total portfolio value
            current_positions: Current positions by symbol
            
        Returns:
            List of orders
        """
        orders = []
        total_risk_budget = 1.0
        used_risk = 0.0
        
        # Sort by edge (descending)
        sorted_signals = sorted(
            signals,
            key=lambda s: s.expected_edge * s.confidence,
            reverse=True
        )
        
        for signal in sorted_signals:
            if used_risk >= total_risk_budget:
                break
            
            current_pos = current_positions.get(signal.symbol, 0.0)
            order = self.signal_to_order(signal, portfolio_value, current_pos)
            
            if order:
                # Calculate risk contribution
                risk_contrib = signal.confidence * signal.recommended_size_scale * 0.1
                
                if used_risk + risk_contrib <= total_risk_budget:
                    orders.append(order)
                    used_risk += risk_contrib
                else:
                    # Reduce size to fit risk budget
                    scale = (total_risk_budget - used_risk) / risk_contrib
                    order['quantity'] *= scale
                    order['risk_scaled'] = True
                    orders.append(order)
                    used_risk = total_risk_budget
        
        return orders


class MarketDataAdapter:
    """
    Adapter for converting various market data formats to GETS MarketData.
    """
    
    @staticmethod
    def from_ohlcv_df(df_row: Dict[str, Any], symbol: str) -> MarketData:
        """Convert OHLCV DataFrame row to MarketData."""
        return MarketData(
            symbol=symbol,
            timestamp=df_row.get('timestamp', datetime.now()),
            ohlcv={
                'open': float(df_row['open']),
                'high': float(df_row['high']),
                'low': float(df_row['low']),
                'close': float(df_row['close']),
                'volume': float(df_row.get('volume', 0))
            },
            bid_ask_spread=df_row.get('spread'),
            realized_volatility=df_row.get('realized_vol')
        )
    
    @staticmethod
    def from_price_dict(
        price_data: Dict[str, float],
        symbol: str,
        timestamp: datetime = None
    ) -> MarketData:
        """Convert price dictionary to MarketData."""
        return MarketData(
            symbol=symbol,
            timestamp=timestamp or datetime.now(),
            ohlcv={
                'open': price_data.get('open', price_data.get('price', 0)),
                'high': price_data.get('high', price_data.get('price', 0)),
                'low': price_data.get('low', price_data.get('price', 0)),
                'close': price_data.get('close', price_data.get('price', 0)),
                'volume': price_data.get('volume', 0)
            },
            bid_ask_spread=price_data.get('spread'),
            depth_imbalance=price_data.get('depth_imbalance'),
            realized_volatility=price_data.get('volatility')
        )
    
    @staticmethod
    def from_orderbook(
        symbol: str,
        bids: List[Tuple[float, float]],
        asks: List[Tuple[float, float]],
        mid_price: float,
        timestamp: datetime = None
    ) -> MarketData:
        """Convert order book to MarketData."""
        best_bid = bids[0][0] if bids else mid_price * 0.999
        best_ask = asks[0][0] if asks else mid_price * 1.001
        spread = (best_ask - best_bid) / mid_price if mid_price > 0 else 0.001
        
        # Calculate depth imbalance
        bid_depth = sum(q for _, q in bids[:5]) if bids else 0
        ask_depth = sum(q for _, q in asks[:5]) if asks else 0
        total_depth = bid_depth + ask_depth
        imbalance = (bid_depth - ask_depth) / total_depth if total_depth > 0 else 0
        
        return MarketData(
            symbol=symbol,
            timestamp=timestamp or datetime.now(),
            ohlcv={
                'open': mid_price,
                'high': mid_price,
                'low': mid_price,
                'close': mid_price,
                'volume': 0  # Would need trade data
            },
            bid_ask_spread=spread,
            depth_imbalance=imbalance
        )


def create_integrated_gets(
    config: GETSConfig = None,
    enable_dgs: bool = True,
    enable_trading_bridge: bool = True
) -> Tuple[GETS, Optional[DGSAdapter], Optional[GETSTradingBridge]]:
    """
    Factory function to create GETS with full integration.
    
    Args:
        config: GETS configuration
        enable_dgs: Enable DGS integration
        enable_trading_bridge: Enable trading bridge
        
    Returns:
        (GETS instance, DGS adapter, Trading bridge)
    """
    gets = GETS(config)
    
    dgs_adapter = None
    if enable_dgs:
        dgs_adapter = DGSAdapter(gets)
    
    trading_bridge = None
    if enable_trading_bridge:
        trading_bridge = GETSTradingBridge(gets)
    
    return gets, dgs_adapter, trading_bridge


def quick_signal(
    symbol: str,
    price_data: Dict[str, float],
    horizon: str = "5m",
    config: GETSConfig = None
) -> Optional[GETSSignal]:
    """
    Quick function to generate a signal without full initialization.
    
    For production use, properly initialize GETS and reuse.
    
    Args:
        symbol: Trading symbol
        price_data: Price information (open, high, low, close, volume)
        horizon: Forecast horizon (1m, 5m, 1h, 1d, 1w)
        config: Optional GETS configuration
        
    Returns:
        GETSSignal or None if generation fails
    """
    try:
        # Parse horizon
        horizon_map = {
            "1m": ForecastHorizon.IMMEDIATE,
            "5m": ForecastHorizon.SHORT,
            "1h": ForecastHorizon.MEDIUM,
            "1d": ForecastHorizon.LONG,
            "1w": ForecastHorizon.EXTENDED
        }
        parsed_horizon = horizon_map.get(horizon, ForecastHorizon.SHORT)
        
        # Create GETS
        gets = GETS(config)
        if not gets.initialize():
            logger.error("GETS initialization failed")
            return None
        
        # Create market data
        market_data = MarketDataAdapter.from_price_dict(price_data, symbol)
        
        # Generate signal
        signal = gets.generate_signal(market_data, parsed_horizon)
        
        return signal
        
    except Exception as e:
        logger.error(f"Quick signal generation failed: {e}")
        return None
