"""
Anomaly Visualization
Spread spikes, liquidity voids, and annotated event streams
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

# Try to import visualization libraries
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logger.warning("Plotly not available. Visualization will be limited.")

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class AnomalyType(Enum):
    """Types of anomalies"""
    SPREAD_SPIKE = "spread_spike"
    LIQUIDITY_VOID = "liquidity_void"
    PRICE_GAP = "price_gap"
    VOLUME_SPIKE = "volume_spike"
    VOLATILITY_SPIKE = "volatility_spike"
    ORDER_IMBALANCE = "order_imbalance"
    FLASH_MOVE = "flash_move"
    CORRELATION_BREAK = "correlation_break"
    LATENCY_SPIKE = "latency_spike"
    ERROR_CLUSTER = "error_cluster"


class Severity(Enum):
    """Anomaly severity"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Anomaly:
    """Detected anomaly"""
    anomaly_id: str
    anomaly_type: AnomalyType
    timestamp: datetime
    symbol: str
    severity: Severity
    value: float
    threshold: float
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly_id': self.anomaly_id,
            'anomaly_type': self.anomaly_type.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'severity': self.severity.value,
            'value': self.value,
            'threshold': self.threshold,
            'description': self.description,
            'context': self.context
        }


@dataclass
class AnnotatedEvent:
    """Event with annotations for visualization"""
    timestamp: datetime
    event_type: str
    value: float
    annotation: str
    color: str = "blue"
    size: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnomalyDetector:
    """
    Detects anomalies in market data and system metrics
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Detection thresholds
        self.thresholds = {
            AnomalyType.SPREAD_SPIKE: self.config.get('spread_spike_threshold', 3.0),  # 3x normal
            AnomalyType.LIQUIDITY_VOID: self.config.get('liquidity_void_threshold', 0.3),  # 30% of normal
            AnomalyType.PRICE_GAP: self.config.get('price_gap_threshold', 0.02),  # 2%
            AnomalyType.VOLUME_SPIKE: self.config.get('volume_spike_threshold', 5.0),  # 5x normal
            AnomalyType.VOLATILITY_SPIKE: self.config.get('volatility_spike_threshold', 3.0),
            AnomalyType.FLASH_MOVE: self.config.get('flash_move_threshold', 0.01),  # 1% in 1 second
            AnomalyType.LATENCY_SPIKE: self.config.get('latency_spike_threshold', 100),  # 100ms
        }
        
        # Rolling statistics
        self.rolling_stats: Dict[str, Dict[str, float]] = {}
        self.anomaly_history: List[Anomaly] = []
        
        logger.info("Anomaly detector initialized")
        
    def detect_spread_spike(
        self,
        symbol: str,
        current_spread: float,
        normal_spread: float
    ) -> Optional[Anomaly]:
        """Detect spread spike anomaly"""
        threshold = self.thresholds[AnomalyType.SPREAD_SPIKE]
        ratio = current_spread / normal_spread if normal_spread > 0 else 0
        
        if ratio > threshold:
            severity = Severity.HIGH if ratio > threshold * 2 else Severity.MEDIUM
            anomaly = Anomaly(
                anomaly_id=f"SS_{symbol}_{datetime.now().strftime('%H%M%S')}",
                anomaly_type=AnomalyType.SPREAD_SPIKE,
                timestamp=datetime.now(),
                symbol=symbol,
                severity=severity,
                value=ratio,
                threshold=threshold,
                description=f"Spread {ratio:.1f}x normal ({current_spread:.4f} vs {normal_spread:.4f})",
                context={'current_spread': current_spread, 'normal_spread': normal_spread}
            )
            self.anomaly_history.append(anomaly)
            return anomaly
        return None
    
    def detect_liquidity_void(
        self,
        symbol: str,
        current_depth: float,
        normal_depth: float
    ) -> Optional[Anomaly]:
        """Detect liquidity void"""
        threshold = self.thresholds[AnomalyType.LIQUIDITY_VOID]
        ratio = current_depth / normal_depth if normal_depth > 0 else 0
        
        if ratio < threshold:
            severity = Severity.CRITICAL if ratio < threshold / 2 else Severity.HIGH
            anomaly = Anomaly(
                anomaly_id=f"LV_{symbol}_{datetime.now().strftime('%H%M%S')}",
                anomaly_type=AnomalyType.LIQUIDITY_VOID,
                timestamp=datetime.now(),
                symbol=symbol,
                severity=severity,
                value=ratio,
                threshold=threshold,
                description=f"Liquidity at {ratio*100:.1f}% of normal",
                context={'current_depth': current_depth, 'normal_depth': normal_depth}
            )
            self.anomaly_history.append(anomaly)
            return anomaly
        return None
    
    def detect_price_gap(
        self,
        symbol: str,
        current_price: float,
        previous_price: float
    ) -> Optional[Anomaly]:
        """Detect price gap"""
        threshold = self.thresholds[AnomalyType.PRICE_GAP]
        gap_pct = abs(current_price - previous_price) / previous_price if previous_price > 0 else 0
        
        if gap_pct > threshold:
            severity = Severity.CRITICAL if gap_pct > threshold * 3 else Severity.HIGH
            anomaly = Anomaly(
                anomaly_id=f"PG_{symbol}_{datetime.now().strftime('%H%M%S')}",
                anomaly_type=AnomalyType.PRICE_GAP,
                timestamp=datetime.now(),
                symbol=symbol,
                severity=severity,
                value=gap_pct,
                threshold=threshold,
                description=f"Price gap of {gap_pct*100:.2f}%",
                context={'current_price': current_price, 'previous_price': previous_price}
            )
            self.anomaly_history.append(anomaly)
            return anomaly
        return None
    
    def detect_volume_spike(
        self,
        symbol: str,
        current_volume: float,
        average_volume: float
    ) -> Optional[Anomaly]:
        """Detect volume spike"""
        threshold = self.thresholds[AnomalyType.VOLUME_SPIKE]
        ratio = current_volume / average_volume if average_volume > 0 else 0
        
        if ratio > threshold:
            severity = Severity.MEDIUM if ratio < threshold * 2 else Severity.HIGH
            anomaly = Anomaly(
                anomaly_id=f"VS_{symbol}_{datetime.now().strftime('%H%M%S')}",
                anomaly_type=AnomalyType.VOLUME_SPIKE,
                timestamp=datetime.now(),
                symbol=symbol,
                severity=severity,
                value=ratio,
                threshold=threshold,
                description=f"Volume {ratio:.1f}x average",
                context={'current_volume': current_volume, 'average_volume': average_volume}
            )
            self.anomaly_history.append(anomaly)
            return anomaly
        return None
    
    def get_recent_anomalies(
        self,
        minutes: int = 60,
        anomaly_type: Optional[AnomalyType] = None,
        symbol: Optional[str] = None
    ) -> List[Anomaly]:
        """Get recent anomalies"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        anomalies = [a for a in self.anomaly_history if a.timestamp > cutoff]
        
        if anomaly_type:
            anomalies = [a for a in anomalies if a.anomaly_type == anomaly_type]
        if symbol:
            anomalies = [a for a in anomalies if a.symbol == symbol]
            
        return sorted(anomalies, key=lambda a: a.timestamp, reverse=True)


class AnomalyVisualizer:
    """
    Visualizes anomalies and annotated event streams
    """
    
    # Color scheme for anomaly types
    COLORS = {
        AnomalyType.SPREAD_SPIKE: '#FF6B6B',
        AnomalyType.LIQUIDITY_VOID: '#4ECDC4',
        AnomalyType.PRICE_GAP: '#FFE66D',
        AnomalyType.VOLUME_SPIKE: '#95E1D3',
        AnomalyType.VOLATILITY_SPIKE: '#F38181',
        AnomalyType.FLASH_MOVE: '#AA96DA',
        AnomalyType.LATENCY_SPIKE: '#FCBAD3',
        AnomalyType.ERROR_CLUSTER: '#FF0000',
    }
    
    SEVERITY_SIZES = {
        Severity.LOW: 8,
        Severity.MEDIUM: 12,
        Severity.HIGH: 16,
        Severity.CRITICAL: 24,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.detector = AnomalyDetector(config)
        
        logger.info("Anomaly visualizer initialized")
        
    def create_price_chart_with_anomalies(
        self,
        price_data: List[Dict[str, Any]],
        anomalies: List[Anomaly],
        title: str = "Price Chart with Anomalies"
    ) -> Optional[Any]:
        """
        Create price chart with anomaly annotations
        
        Args:
            price_data: List of {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
            anomalies: List of detected anomalies
            title: Chart title
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly not available for visualization")
            return self._create_text_report(price_data, anomalies)
            
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Price', 'Volume', 'Anomalies')
        )
        
        # Extract data
        timestamps = [d['timestamp'] for d in price_data]
        opens = [d['open'] for d in price_data]
        highs = [d['high'] for d in price_data]
        lows = [d['low'] for d in price_data]
        closes = [d['close'] for d in price_data]
        volumes = [d.get('volume', 0) for d in price_data]
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=timestamps,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name='Price'
            ),
            row=1, col=1
        )
        
        # Volume bars
        colors = ['green' if c >= o else 'red' for o, c in zip(opens, closes)]
        fig.add_trace(
            go.Bar(x=timestamps, y=volumes, marker_color=colors, name='Volume'),
            row=2, col=1
        )
        
        # Add anomaly markers
        for anomaly in anomalies:
            color = self.COLORS.get(anomaly.anomaly_type, '#888888')
            size = self.SEVERITY_SIZES.get(anomaly.severity, 10)
            
            # Find closest price point
            closest_idx = min(
                range(len(timestamps)),
                key=lambda i: abs((timestamps[i] - anomaly.timestamp).total_seconds())
                if isinstance(timestamps[i], datetime) else float('inf')
            )
            
            y_value = highs[closest_idx] if closest_idx < len(highs) else 0
            
            fig.add_trace(
                go.Scatter(
                    x=[anomaly.timestamp],
                    y=[y_value * 1.01],  # Slightly above the candle
                    mode='markers+text',
                    marker=dict(size=size, color=color, symbol='triangle-down'),
                    text=[anomaly.anomaly_type.value],
                    textposition='top center',
                    name=anomaly.description,
                    hovertemplate=f"<b>{anomaly.anomaly_type.value}</b><br>" +
                                  f"Severity: {anomaly.severity.name}<br>" +
                                  f"Value: {anomaly.value:.4f}<br>" +
                                  f"{anomaly.description}<extra></extra>"
                ),
                row=1, col=1
            )
        
        # Anomaly timeline
        anomaly_times = [a.timestamp for a in anomalies]
        anomaly_severities = [a.severity.value for a in anomalies]
        anomaly_colors = [self.COLORS.get(a.anomaly_type, '#888888') for a in anomalies]
        
        fig.add_trace(
            go.Scatter(
                x=anomaly_times,
                y=anomaly_severities,
                mode='markers',
                marker=dict(size=12, color=anomaly_colors),
                name='Anomalies'
            ),
            row=3, col=1
        )
        
        # Update layout
        fig.update_layout(
            title=title,
            xaxis_rangeslider_visible=False,
            height=800,
            showlegend=True
        )
        
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="Severity", row=3, col=1)
        
        return fig
    
    def create_anomaly_heatmap(
        self,
        anomalies: List[Anomaly],
        time_buckets: int = 24,
        title: str = "Anomaly Heatmap"
    ) -> Optional[Any]:
        """Create heatmap of anomalies by type and time"""
        if not PLOTLY_AVAILABLE or not anomalies:
            return None
            
        # Group anomalies by type and hour
        anomaly_types = list(AnomalyType)
        hours = list(range(time_buckets))
        
        # Create matrix
        matrix = [[0 for _ in hours] for _ in anomaly_types]
        
        for anomaly in anomalies:
            type_idx = anomaly_types.index(anomaly.anomaly_type)
            hour = anomaly.timestamp.hour
            matrix[type_idx][hour] += anomaly.severity.value
            
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=[f"{h:02d}:00" for h in hours],
            y=[t.value for t in anomaly_types],
            colorscale='Reds',
            hoverongaps=False
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Hour",
            yaxis_title="Anomaly Type",
            height=400
        )
        
        return fig
    
    def create_event_stream(
        self,
        events: List[AnnotatedEvent],
        title: str = "Event Stream"
    ) -> Optional[Any]:
        """Create annotated event stream visualization"""
        if not PLOTLY_AVAILABLE or not events:
            return None
            
        fig = go.Figure()
        
        # Group events by type
        event_types = list(set(e.event_type for e in events))
        
        for event_type in event_types:
            type_events = [e for e in events if e.event_type == event_type]
            
            fig.add_trace(go.Scatter(
                x=[e.timestamp for e in type_events],
                y=[e.value for e in type_events],
                mode='markers+lines',
                name=event_type,
                marker=dict(
                    size=[e.size for e in type_events],
                    color=type_events[0].color if type_events else 'blue'
                ),
                text=[e.annotation for e in type_events],
                hovertemplate="%{text}<extra></extra>"
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Time",
            yaxis_title="Value",
            height=500,
            showlegend=True
        )
        
        return fig
    
    def create_anomaly_summary(
        self,
        anomalies: List[Anomaly],
        title: str = "Anomaly Summary"
    ) -> Dict[str, Any]:
        """Create summary statistics for anomalies"""
        if not anomalies:
            return {'total': 0, 'by_type': {}, 'by_severity': {}}
            
        by_type = {}
        by_severity = {}
        by_symbol = {}
        
        for anomaly in anomalies:
            # By type
            type_key = anomaly.anomaly_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
            
            # By severity
            sev_key = anomaly.severity.name
            by_severity[sev_key] = by_severity.get(sev_key, 0) + 1
            
            # By symbol
            by_symbol[anomaly.symbol] = by_symbol.get(anomaly.symbol, 0) + 1
            
        return {
            'total': len(anomalies),
            'by_type': by_type,
            'by_severity': by_severity,
            'by_symbol': by_symbol,
            'time_range': {
                'start': min(a.timestamp for a in anomalies).isoformat(),
                'end': max(a.timestamp for a in anomalies).isoformat()
            },
            'most_common_type': max(by_type, key=by_type.get) if by_type else None,
            'most_affected_symbol': max(by_symbol, key=by_symbol.get) if by_symbol else None
        }
    
    def _create_text_report(
        self,
        price_data: List[Dict[str, Any]],
        anomalies: List[Anomaly]
    ) -> str:
        """Create text-based report when Plotly is not available"""
        lines = [
            "=" * 60,
            "ANOMALY REPORT",
            "=" * 60,
            f"Data points: {len(price_data)}",
            f"Anomalies detected: {len(anomalies)}",
            "",
            "ANOMALIES BY TYPE:",
        ]
        
        by_type = {}
        for a in anomalies:
            by_type[a.anomaly_type.value] = by_type.get(a.anomaly_type.value, 0) + 1
            
        for atype, count in sorted(by_type.items(), key=lambda x: -x[1]):
            lines.append(f"  {atype}: {count}")
            
        lines.extend([
            "",
            "RECENT ANOMALIES:",
        ])
        
        for a in anomalies[:10]:
            lines.append(f"  [{a.severity.name}] {a.timestamp.strftime('%H:%M:%S')} - {a.description}")
            
        return "\n".join(lines)
    
    def save_chart(self, fig: Any, filepath: str):
        """Save chart to file"""
        if PLOTLY_AVAILABLE and fig:
            if filepath.endswith('.html'):
                fig.write_html(filepath)
            elif filepath.endswith('.png'):
                fig.write_image(filepath)
            elif filepath.endswith('.json'):
                fig.write_json(filepath)
            logger.info(f"Chart saved to {filepath}")
        else:
            # Save as text
            with open(filepath.replace('.html', '.txt'), 'w') as f:
                f.write(str(fig))
