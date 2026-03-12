"""
Trade Triage Module
Immediately classifies and collects data for losing trades.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import json

logger = logging.getLogger(__name__)


class LossCategory(Enum):
    """Loss severity categories."""
    LOSS_SMALL = "small"  # <0.5% equity
    LOSS_MEDIUM = "medium"  # 0.5-2% equity
    LOSS_LARGE = "large"  # >2% equity
    LOSS_CRITICAL = "critical"  # Exceeds MAX_DRAWDOWN


@dataclass
class TradeData:
    """Complete trade information."""
    ticket_id: str
    entry_time: datetime
    exit_time: datetime
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_price: float
    exit_price: float
    size: float
    sl: Optional[float]
    tp: Optional[float]
    pnl: float
    fees: float
    slippage: float = 0.0
    execution_latency_ms: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        try:
            data = asdict(self)
            data['entry_time'] = self.entry_time.isoformat()
            data['exit_time'] = self.exit_time.isoformat()
            return data
        except Exception as e:
            logger.error(f"Error in to_dict: {e}")
            raise


@dataclass
class SignalContext:
    """Signal and indicator context at trade time."""
    indicators_used: List[str]
    indicator_values: Dict[str, float]
    model_confidence: float
    timeframe: str
    market_regime: str
    multi_tf_agreement: bool = True
    signal_drift: float = 0.0  # Post-entry vs pre-entry
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MarketSnapshot:
    """Market data snapshot around trade."""
    candles_before: List[Dict]  # N candles before entry
    candles_after: List[Dict]  # N candles after entry
    atr: float
    spread: float
    volume_avg: float
    volatility_spike: bool = False
    news_events: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SystemMetrics:
    """System performance metrics at trade time."""
    cpu_usage: float
    memory_usage: float
    latency_ms: float
    order_fill_type: str  # 'full', 'partial', 'rejected'
    errors_in_logs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TriageDiagnostic:
    """Initial diagnostic output from triage."""
    trade_id: str
    timestamp: datetime
    loss_category: LossCategory
    pnl: float
    pnl_pct: float  # Percentage of equity
    size: float
    regime: str
    signal_confidence: float
    anomalies: List[str]
    
    # Full context
    trade_data: TradeData
    signal_context: SignalContext
    market_snapshot: MarketSnapshot
    system_metrics: SystemMetrics
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'trade_id': self.trade_id,
            'timestamp': self.timestamp.isoformat(),
            'loss_category': self.loss_category.value,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'size': self.size,
            'regime': self.regime,
            'signal_confidence': self.signal_confidence,
            'anomalies': self.anomalies,
            'trade_data': self.trade_data.to_dict(),
            'signal_context': self.signal_context.to_dict(),
            'market_snapshot': self.market_snapshot.to_dict(),
            'system_metrics': self.system_metrics.to_dict(),
        }


class TradeTriage:
    """
    Triage module for immediate classification and data collection of losing trades.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize triage module.
        
        Args:
            config: Configuration dictionary with thresholds
        """
        try:
            self.config = config
            self.loss_small_threshold = config.get('loss_small_threshold', 0.005)  # 0.5%
            self.loss_medium_threshold = config.get('loss_medium_threshold', 0.02)  # 2%
            self.max_drawdown = config.get('max_drawdown', 0.20)  # 20%
            self.candles_lookback = config.get('candles_lookback', 200)
            self.news_window_minutes = config.get('news_window_minutes', 30)
        
            logger.info("TradeTriage initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify_loss(self, pnl: float, equity: float) -> LossCategory:
        """
        Classify loss severity based on percentage of equity.
        
        Args:
            pnl: Profit/loss amount (negative for loss)
            equity: Current account equity
            
        Returns:
            LossCategory enum
        """
        try:
            pnl_pct = abs(pnl) / equity if equity > 0 else 0
        
            if pnl_pct >= self.max_drawdown:
                return LossCategory.LOSS_CRITICAL
            elif pnl_pct >= self.loss_medium_threshold:
                return LossCategory.LOSS_LARGE
            elif pnl_pct >= self.loss_small_threshold:
                return LossCategory.LOSS_MEDIUM
            else:
                return LossCategory.LOSS_SMALL
        except Exception as e:
            logger.error(f"Error in classify_loss: {e}")
            raise
    
    def collect_trade_data(self, trade: Dict[str, Any]) -> TradeData:
        """
        Extract and validate trade data.
        
        Args:
            trade: Raw trade dictionary
            
        Returns:
            TradeData object
        """
        return TradeData(
            ticket_id=str(trade['ticket_id']),
            entry_time=trade['entry_time'] if isinstance(trade['entry_time'], datetime) 
                      else datetime.fromisoformat(trade['entry_time']),
            exit_time=trade['exit_time'] if isinstance(trade['exit_time'], datetime)
                     else datetime.fromisoformat(trade['exit_time']),
            symbol=trade['symbol'],
            side=trade['side'],
            entry_price=float(trade['entry_price']),
            exit_price=float(trade['exit_price']),
            size=float(trade['size']),
            sl=float(trade['sl']) if trade.get('sl') else None,
            tp=float(trade['tp']) if trade.get('tp') else None,
            pnl=float(trade['pnl']),
            fees=float(trade.get('fees', 0)),
            slippage=float(trade.get('slippage', 0)),
            execution_latency_ms=float(trade.get('execution_latency_ms', 0))
        )
    
    def collect_signal_context(self, signal_data: Dict[str, Any]) -> SignalContext:
        """
        Collect signal and indicator context.
        
        Args:
            signal_data: Signal context dictionary
            
        Returns:
            SignalContext object
        """
        return SignalContext(
            indicators_used=signal_data.get('indicators_used', []),
            indicator_values=signal_data.get('indicator_values', {}),
            model_confidence=float(signal_data.get('model_confidence', 0.5)),
            timeframe=signal_data.get('timeframe', 'unknown'),
            market_regime=signal_data.get('market_regime', 'unknown'),
            multi_tf_agreement=signal_data.get('multi_tf_agreement', True),
            signal_drift=float(signal_data.get('signal_drift', 0.0))
        )
    
    def collect_market_snapshot(self, market_data: Dict[str, Any]) -> MarketSnapshot:
        """
        Collect market data snapshot around trade.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            MarketSnapshot object
        """
        return MarketSnapshot(
            candles_before=market_data.get('candles_before', []),
            candles_after=market_data.get('candles_after', []),
            atr=float(market_data.get('atr', 0)),
            spread=float(market_data.get('spread', 0)),
            volume_avg=float(market_data.get('volume_avg', 0)),
            volatility_spike=market_data.get('volatility_spike', False),
            news_events=market_data.get('news_events', [])
        )
    
    def collect_system_metrics(self, system_data: Dict[str, Any]) -> SystemMetrics:
        """
        Collect system performance metrics.
        
        Args:
            system_data: System metrics dictionary
            
        Returns:
            SystemMetrics object
        """
        return SystemMetrics(
            cpu_usage=float(system_data.get('cpu_usage', 0)),
            memory_usage=float(system_data.get('memory_usage', 0)),
            latency_ms=float(system_data.get('latency_ms', 0)),
            order_fill_type=system_data.get('order_fill_type', 'full'),
            errors_in_logs=system_data.get('errors_in_logs', [])
        )
    
    def detect_anomalies(self, 
                        trade_data: TradeData,
                        signal_context: SignalContext,
                        market_snapshot: MarketSnapshot,
                        system_metrics: SystemMetrics) -> List[str]:
        """
        Detect immediate anomalies in trade execution.
        
        Args:
            trade_data: Trade data
            signal_context: Signal context
            market_snapshot: Market snapshot
            system_metrics: System metrics
            
        Returns:
            List of anomaly descriptions
        """
        try:
            anomalies = []
        
            # Check signal confidence
            if signal_context.model_confidence < 0.5:
                anomalies.append(f"Low signal confidence: {signal_context.model_confidence:.2f}")
        
            # Check multi-timeframe agreement
            if not signal_context.multi_tf_agreement:
                anomalies.append("Multi-timeframe disagreement detected")
        
            # Check slippage
            if abs(trade_data.slippage) > 0.005:  # 0.5%
                anomalies.append(f"High slippage: {trade_data.slippage:.4f}")
        
            # Check execution latency
            if trade_data.execution_latency_ms > 1000:  # 1 second
                anomalies.append(f"High execution latency: {trade_data.execution_latency_ms:.0f}ms")
        
            # Check volatility spike
            if market_snapshot.volatility_spike:
                anomalies.append("Volatility spike detected during trade")
        
            # Check news events
            if market_snapshot.news_events:
                anomalies.append(f"News events during trade: {len(market_snapshot.news_events)}")
        
            # Check system errors
            if system_metrics.errors_in_logs:
                anomalies.append(f"System errors detected: {len(system_metrics.errors_in_logs)}")
        
            # Check partial fills
            if system_metrics.order_fill_type != 'full':
                anomalies.append(f"Order fill type: {system_metrics.order_fill_type}")
        
            # Check stop loss placement
            if trade_data.sl and market_snapshot.atr > 0:
                sl_distance = abs(trade_data.entry_price - trade_data.sl)
                atr_ratio = sl_distance / market_snapshot.atr
                if atr_ratio < 1.0:
                    anomalies.append(f"Stop loss too tight: {atr_ratio:.2f} ATR")
        
            return anomalies
        except Exception as e:
            logger.error(f"Error in detect_anomalies: {e}")
            raise
    
    def triage_trade(self,
                    trade: Dict[str, Any],
                    signal_data: Dict[str, Any],
                    market_data: Dict[str, Any],
                    system_data: Dict[str, Any],
                    equity: float) -> TriageDiagnostic:
        """
        Perform complete triage on a losing trade.
        
        Args:
            trade: Trade dictionary
            signal_data: Signal context dictionary
            market_data: Market data dictionary
            system_data: System metrics dictionary
            equity: Current account equity
            
        Returns:
            TriageDiagnostic with complete analysis
        """
        # Collect all data
        try:
            trade_data = self.collect_trade_data(trade)
            signal_context = self.collect_signal_context(signal_data)
            market_snapshot = self.collect_market_snapshot(market_data)
            system_metrics = self.collect_system_metrics(system_data)
        
            # Classify loss
            loss_category = self.classify_loss(trade_data.pnl, equity)
            pnl_pct = abs(trade_data.pnl) / equity if equity > 0 else 0
        
            # Detect anomalies
            anomalies = self.detect_anomalies(
                trade_data, signal_context, market_snapshot, system_metrics
            )
        
            # Create diagnostic
            diagnostic = TriageDiagnostic(
                trade_id=trade_data.ticket_id,
                timestamp=datetime.now(),
                loss_category=loss_category,
                pnl=trade_data.pnl,
                pnl_pct=pnl_pct,
                size=trade_data.size,
                regime=signal_context.market_regime,
                signal_confidence=signal_context.model_confidence,
                anomalies=anomalies,
                trade_data=trade_data,
                signal_context=signal_context,
                market_snapshot=market_snapshot,
                system_metrics=system_metrics
            )
        
            logger.info(f"Triage complete for trade {trade_data.ticket_id}: "
                       f"{loss_category.value}, {len(anomalies)} anomalies")
        
            return diagnostic
        except Exception as e:
            logger.error(f"Error in triage_trade: {e}")
            raise
