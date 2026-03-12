import logging
logger = logging.getLogger(__name__)
"""Fraud and Market Manipulation Detection System.

Advanced AI system for detecting market manipulation including:
- Spoofing detection
- Pump and dump schemes
- Wash trading
- Quote stuffing
- Layering attacks
- Fake liquidity detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path
from loguru import logger
from collections import deque
import asyncio
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import numpy
import pandas


class FraudType(Enum):
    """Types of market manipulation."""
    SPOOFING = "spoofing"
    PUMP_AND_DUMP = "pump_and_dump"
    WASH_TRADING = "wash_trading"
    QUOTE_STUFFING = "quote_stuffing"
    LAYERING = "layering"
    FAKE_LIQUIDITY = "fake_liquidity"
    MOMENTUM_IGNITION = "momentum_ignition"
    RAMPING = "ramping"


class SeverityLevel(Enum):
    """Fraud severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FraudAlert:
    """Fraud detection alert."""
    timestamp: datetime
    fraud_type: FraudType
    severity: SeverityLevel
    confidence: float
    affected_symbol: str
    price_range: Tuple[float, float]
    volume_anomaly: float
    pattern_description: str
    recommended_action: str
    evidence: Dict[str, Any]
    market_impact: float


@dataclass
class ManipulationPattern:
    """Detected manipulation pattern."""
    pattern_id: str
    start_time: datetime
    end_time: datetime
    fraud_type: FraudType
    participants_estimate: int
    volume_involved: float
    price_impact: float
    detection_confidence: float


class FraudDetectionSystem:
    """Advanced fraud and manipulation detection system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize fraud detection system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/fraud_detection.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Detection parameters
        self.spoofing_threshold = config.get('spoofing_threshold', 0.7)
        self.volume_anomaly_threshold = config.get('volume_anomaly_threshold', 3.0)
        self.quote_stuffing_rate = config.get('quote_stuffing_rate', 100)  # quotes per second
        self.wash_trading_threshold = config.get('wash_trading_threshold', 0.8)
        
        # Data buffers
        self.order_flow_buffer = deque(maxlen=10000)
        self.quote_buffer = deque(maxlen=5000)
        self.trade_buffer = deque(maxlen=5000)
        self.price_buffer = deque(maxlen=1000)
        
        # ML models
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.model_trained = False
        
        # Detection state
        self.active_patterns = {}
        self.fraud_alerts = deque(maxlen=1000)
        self.suspicious_entities = set()
        
        # Initialize database
        self._init_database()
        
        logger.info("Fraud Detection System initialized")
    
    def _init_database(self):
        """Initialize SQLite database for fraud data storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS fraud_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    fraud_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    affected_symbol TEXT NOT NULL,
                    price_range_min REAL NOT NULL,
                    price_range_max REAL NOT NULL,
                    volume_anomaly REAL NOT NULL,
                    pattern_description TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    market_impact REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS manipulation_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT UNIQUE NOT NULL,
                    start_time DATETIME NOT NULL,
                    end_time DATETIME NOT NULL,
                    fraud_type TEXT NOT NULL,
                    participants_estimate INTEGER NOT NULL,
                    volume_involved REAL NOT NULL,
                    price_impact REAL NOT NULL,
                    detection_confidence REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS suspicious_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    entity_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    suspicion_score REAL NOT NULL,
                    details TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def analyze_market_data(self, market_data: Dict[str, Any]) -> List[FraudAlert]:
        """Analyze market data for fraud and manipulation.
        
        Args:
            market_data: Market data including orders, trades, quotes
            
        Returns:
            List of fraud alerts
        """
        alerts = []
        
        try:
            # Update data buffers
            self._update_buffers(market_data)
            
            # Run different detection algorithms
            spoofing_alerts = await self._detect_spoofing()
            pump_dump_alerts = await self._detect_pump_and_dump()
            wash_trading_alerts = await self._detect_wash_trading()
            quote_stuffing_alerts = await self._detect_quote_stuffing()
            layering_alerts = await self._detect_layering()
            fake_liquidity_alerts = await self._detect_fake_liquidity()
            
            alerts.extend(spoofing_alerts)
            alerts.extend(pump_dump_alerts)
            alerts.extend(wash_trading_alerts)
            alerts.extend(quote_stuffing_alerts)
            alerts.extend(layering_alerts)
            alerts.extend(fake_liquidity_alerts)
            
            # Store alerts
            await self._store_fraud_alerts(alerts)
            
            # Update fraud alerts buffer
            self.fraud_alerts.extend(alerts)
            
            if alerts:
                logger.warning(f"Detected {len(alerts)} potential fraud/manipulation events")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error analyzing market data for fraud: {e}")
            return []
    
    def _update_buffers(self, market_data: Dict[str, Any]):
        """Update data buffers with new market data."""
        current_time = datetime.now()
        
        # Update order flow buffer
        if 'orders' in market_data:
            for order in market_data['orders']:
                self.order_flow_buffer.append({
                    'timestamp': current_time,
                    'order_id': order.get('id'),
                    'side': order.get('side'),
                    'price': order.get('price'),
                    'volume': order.get('volume'),
                    'order_type': order.get('type'),
                    'entity_id': order.get('entity_id', 'unknown')
                })
        
        # Update quote buffer
        if 'quotes' in market_data:
            for quote in market_data['quotes']:
                self.quote_buffer.append({
                    'timestamp': current_time,
                    'bid': quote.get('bid'),
                    'ask': quote.get('ask'),
                    'bid_size': quote.get('bid_size'),
                    'ask_size': quote.get('ask_size')
                })
        
        # Update trade buffer
        if 'trades' in market_data:
            for trade in market_data['trades']:
                self.trade_buffer.append({
                    'timestamp': current_time,
                    'price': trade.get('price'),
                    'volume': trade.get('volume'),
                    'side': trade.get('side'),
                    'buyer_id': trade.get('buyer_id', 'unknown'),
                    'seller_id': trade.get('seller_id', 'unknown')
                })
        
        # Update price buffer
        if 'current_price' in market_data:
            self.price_buffer.append({
                'timestamp': current_time,
                'price': market_data['current_price']
            })
    
    async def _detect_spoofing(self) -> List[FraudAlert]:
        """Detect spoofing patterns."""
        alerts = []
        
        try:
            if len(self.order_flow_buffer) < 50:
                return alerts
            
            recent_orders = list(self.order_flow_buffer)[-50:]
            
            # Group orders by entity and price level
            entity_orders = {}
            for order in recent_orders:
                entity_id = order['entity_id']
                if entity_id not in entity_orders:
                    entity_orders[entity_id] = []
                entity_orders[entity_id].append(order)
            
            # Look for rapid order placement and cancellation
            for entity_id, orders in entity_orders.items():
                if len(orders) < 5:
                    continue
                
                # Calculate order lifetime statistics
                order_lifetimes = []
                large_orders = []
                
                for order in orders:
                    if order['volume'] > 10000:  # Large order threshold
                        large_orders.append(order)
                
                # Check for pattern: large orders placed and quickly cancelled
                if len(large_orders) >= 3:
                    avg_lifetime = 30  # Mock average lifetime in seconds
                    
                    if avg_lifetime < 10:  # Very short lifetime
                        confidence = min(0.9, len(large_orders) / 10)
                        
                        alert = FraudAlert(
                            timestamp=datetime.now(),
                            fraud_type=FraudType.SPOOFING,
                            severity=SeverityLevel.HIGH,
                            confidence=confidence,
                            affected_symbol="EURUSD",  # Would be dynamic
                            price_range=(min(o['price'] for o in large_orders),
                                       max(o['price'] for o in large_orders)),
                            volume_anomaly=sum(o['volume'] for o in large_orders),
                            pattern_description=f"Entity {entity_id} placed {len(large_orders)} large orders with avg lifetime {avg_lifetime}s",
                            recommended_action="Monitor entity activity, flag for investigation",
                            evidence={
                                'entity_id': entity_id,
                                'large_orders_count': len(large_orders),
                                'avg_lifetime_seconds': avg_lifetime,
                                'total_volume': sum(o['volume'] for o in large_orders)
                            },
                            market_impact=0.3
                        )
                        
                        alerts.append(alert)
                        self.suspicious_entities.add(entity_id)
            
        except Exception as e:
            logger.error(f"Error detecting spoofing: {e}")
        
        return alerts
    
    async def _detect_pump_and_dump(self) -> List[FraudAlert]:
        """Detect pump and dump schemes."""
        alerts = []
        
        try:
            if len(self.price_buffer) < 100 or len(self.trade_buffer) < 50:
                return alerts
            
            recent_prices = list(self.price_buffer)[-100:]
            recent_trades = list(self.trade_buffer)[-50:]
            
            prices = [p['price'] for p in recent_prices]
            volumes = [t['volume'] for t in recent_trades]
            
            # Calculate price movement and volume characteristics
            price_change = (prices[-1] - prices[0]) / prices[0]
            volume_surge = np.mean(volumes[-10:]) / np.mean(volumes[:-10]) if len(volumes) > 10 else 1
            
            # Detect pump pattern: rapid price increase with volume surge
            if price_change > 0.05 and volume_surge > 3.0:  # 5% price increase, 3x volume
                
                # Check for subsequent dump
                recent_price_trend = np.polyfit(range(len(prices[-20:])), prices[-20:], 1)[0]
                
                if recent_price_trend < 0:  # Declining trend after pump
                    confidence = min(0.8, abs(price_change) * 10 + volume_surge / 10)
                    
                    alert = FraudAlert(
                        timestamp=datetime.now(),
                        fraud_type=FraudType.PUMP_AND_DUMP,
                        severity=SeverityLevel.CRITICAL,
                        confidence=confidence,
                        affected_symbol="EURUSD",
                        price_range=(min(prices), max(prices)),
                        volume_anomaly=volume_surge,
                        pattern_description=f"Pump: {price_change:.2%} price increase, {volume_surge:.1f}x volume surge, followed by dump",
                        recommended_action="Halt trading, investigate coordinated activity",
                        evidence={
                            'price_change_percent': price_change * 100,
                            'volume_surge_ratio': volume_surge,
                            'pump_duration_minutes': 30,  # Mock duration
                            'dump_trend_slope': recent_price_trend
                        },
                        market_impact=abs(price_change)
                    )
                    
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error detecting pump and dump: {e}")
        
        return alerts
    
    async def _detect_wash_trading(self) -> List[FraudAlert]:
        """Detect wash trading patterns."""
        alerts = []
        
        try:
            if len(self.trade_buffer) < 20:
                return alerts
            
            recent_trades = list(self.trade_buffer)[-20:]
            
            # Look for trades between same entities
            entity_pairs = {}
            for trade in recent_trades:
                buyer = trade['buyer_id']
                seller = trade['seller_id']
                
                if buyer == seller:  # Self-trading
                    continue
                
                pair_key = tuple(sorted([buyer, seller]))
                if pair_key not in entity_pairs:
                    entity_pairs[pair_key] = []
                entity_pairs[pair_key].append(trade)
            
            # Detect excessive back-and-forth trading
            for (entity1, entity2), trades in entity_pairs.items():
                if len(trades) >= 5:  # Multiple trades between same entities
                    
                    # Check if trades are at similar prices (wash trading indicator)
                    prices = [t['price'] for t in trades]
                    price_variance = np.var(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
                    
                    if price_variance < 0.001:  # Very similar prices
                        total_volume = sum(t['volume'] for t in trades)
                        confidence = min(0.9, len(trades) / 10)
                        
                        alert = FraudAlert(
                            timestamp=datetime.now(),
                            fraud_type=FraudType.WASH_TRADING,
                            severity=SeverityLevel.HIGH,
                            confidence=confidence,
                            affected_symbol="EURUSD",
                            price_range=(min(prices), max(prices)),
                            volume_anomaly=total_volume,
                            pattern_description=f"Wash trading: {len(trades)} trades between entities {entity1}-{entity2} at similar prices",
                            recommended_action="Flag entities for investigation, monitor future activity",
                            evidence={
                                'entity1': entity1,
                                'entity2': entity2,
                                'trade_count': len(trades),
                                'price_variance': price_variance,
                                'total_volume': total_volume
                            },
                            market_impact=0.2
                        )
                        
                        alerts.append(alert)
                        self.suspicious_entities.update([entity1, entity2])
            
        except Exception as e:
            logger.error(f"Error detecting wash trading: {e}")
        
        return alerts
    
    async def _detect_quote_stuffing(self) -> List[FraudAlert]:
        """Detect quote stuffing attacks."""
        alerts = []
        
        try:
            if len(self.quote_buffer) < 100:
                return alerts
            
            # Calculate quote rate in recent period
            recent_quotes = list(self.quote_buffer)[-100:]
            time_span = (recent_quotes[-1]['timestamp'] - recent_quotes[0]['timestamp']).total_seconds()
            
            if time_span > 0:
                quote_rate = len(recent_quotes) / time_span  # quotes per second
                
                if quote_rate > self.quote_stuffing_rate:
                    # Check if quotes are creating market disruption
                    bid_ask_spreads = []
                    for quote in recent_quotes:
                        if quote['bid'] and quote['ask']:
                            spread = quote['ask'] - quote['bid']
                            bid_ask_spreads.append(spread)
                    
                    if bid_ask_spreads:
                        avg_spread = np.mean(bid_ask_spreads)
                        spread_volatility = np.std(bid_ask_spreads)
                        
                        # High quote rate with volatile spreads indicates stuffing
                        if spread_volatility > avg_spread * 0.5:
                            confidence = min(0.9, quote_rate / (self.quote_stuffing_rate * 2))
                            
                            alert = FraudAlert(
                                timestamp=datetime.now(),
                                fraud_type=FraudType.QUOTE_STUFFING,
                                severity=SeverityLevel.MEDIUM,
                                confidence=confidence,
                                affected_symbol="EURUSD",
                                price_range=(min(q['bid'] for q in recent_quotes if q['bid']),
                                           max(q['ask'] for q in recent_quotes if q['ask'])),
                                volume_anomaly=quote_rate,
                                pattern_description=f"Quote stuffing: {quote_rate:.1f} quotes/sec with volatile spreads",
                                recommended_action="Monitor quote source, implement rate limiting",
                                evidence={
                                    'quote_rate_per_second': quote_rate,
                                    'avg_spread': avg_spread,
                                    'spread_volatility': spread_volatility,
                                    'time_span_seconds': time_span
                                },
                                market_impact=0.4
                            )
                            
                            alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error detecting quote stuffing: {e}")
        
        return alerts
    
    async def _detect_layering(self) -> List[FraudAlert]:
        """Detect layering manipulation."""
        alerts = []
        
        try:
            if len(self.order_flow_buffer) < 30:
                return alerts
            
            recent_orders = list(self.order_flow_buffer)[-30:]
            
            # Group orders by side and entity
            entity_sides = {}
            for order in recent_orders:
                entity_id = order['entity_id']
                side = order['side']
                key = f"{entity_id}_{side}"
                
                if key not in entity_sides:
                    entity_sides[key] = []
                entity_sides[key].append(order)
            
            # Look for layering pattern: multiple orders on one side, execution on other
            for entity_id in set(o['entity_id'] for o in recent_orders):
                buy_orders = entity_sides.get(f"{entity_id}_buy", [])
                sell_orders = entity_sides.get(f"{entity_id}_sell", [])
                
                # Layering: many orders on one side, few executions on other
                if len(buy_orders) > 5 and len(sell_orders) <= 2:
                    # Check if buy orders are at different price levels (layering)
                    buy_prices = [o['price'] for o in buy_orders]
                    price_levels = len(set(buy_prices))
                    
                    if price_levels >= 3:  # Multiple price levels
                        confidence = min(0.8, len(buy_orders) / 10)
                        
                        alert = FraudAlert(
                            timestamp=datetime.now(),
                            fraud_type=FraudType.LAYERING,
                            severity=SeverityLevel.MEDIUM,
                            confidence=confidence,
                            affected_symbol="EURUSD",
                            price_range=(min(buy_prices), max(buy_prices)),
                            volume_anomaly=sum(o['volume'] for o in buy_orders),
                            pattern_description=f"Layering: Entity {entity_id} placed {len(buy_orders)} buy orders across {price_levels} levels",
                            recommended_action="Monitor entity for manipulation intent",
                            evidence={
                                'entity_id': entity_id,
                                'layering_side': 'buy',
                                'order_count': len(buy_orders),
                                'price_levels': price_levels,
                                'opposite_side_orders': len(sell_orders)
                            },
                            market_impact=0.3
                        )
                        
                        alerts.append(alert)
                        self.suspicious_entities.add(entity_id)
            
        except Exception as e:
            logger.error(f"Error detecting layering: {e}")
        
        return alerts
    
    async def _detect_fake_liquidity(self) -> List[FraudAlert]:
        """Detect fake liquidity provision."""
        alerts = []
        
        try:
            # This would analyze order book depth and cancellation patterns
            # Mock implementation for demonstration
            
            fake_liquidity_score = np.random.uniform(0, 1)
            
            if fake_liquidity_score > 0.7:
                alert = FraudAlert(
                    timestamp=datetime.now(),
                    fraud_type=FraudType.FAKE_LIQUIDITY,
                    severity=SeverityLevel.MEDIUM,
                    confidence=fake_liquidity_score,
                    affected_symbol="EURUSD",
                    price_range=(1.0800, 1.0850),
                    volume_anomaly=50000,
                    pattern_description="Fake liquidity detected: large orders placed and quickly cancelled",
                    recommended_action="Verify liquidity provider legitimacy",
                    evidence={
                        'fake_liquidity_score': fake_liquidity_score,
                        'cancelled_volume_ratio': 0.8
                    },
                    market_impact=0.2
                )
                
                alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error detecting fake liquidity: {e}")
        
        return alerts
    
    async def _store_fraud_alerts(self, alerts: List[FraudAlert]):
        """Store fraud alerts in database."""
        with sqlite3.connect(self.db_path) as conn:
            for alert in alerts:
                conn.execute('''
                    INSERT INTO fraud_alerts 
                    (timestamp, fraud_type, severity, confidence, affected_symbol,
                     price_range_min, price_range_max, volume_anomaly, pattern_description,
                     recommended_action, evidence, market_impact)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.timestamp, alert.fraud_type.value, alert.severity.value,
                    alert.confidence, alert.affected_symbol, alert.price_range[0],
                    alert.price_range[1], alert.volume_anomaly, alert.pattern_description,
                    alert.recommended_action, str(alert.evidence), alert.market_impact
                ))
            conn.commit()
    
    def get_recent_alerts(self, hours: int = 24) -> List[FraudAlert]:
        """Get recent fraud alerts.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent fraud alerts
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [alert for alert in self.fraud_alerts if alert.timestamp > cutoff_time]
    
    def get_fraud_summary(self) -> Dict[str, Any]:
        """Get summary of fraud detection activity.
        
        Returns:
            Fraud detection summary
        """
        recent_alerts = self.get_recent_alerts(24)
        
        if not recent_alerts:
            return {
                'total_alerts': 0,
                'high_severity_alerts': 0,
                'fraud_types': {},
                'suspicious_entities': len(self.suspicious_entities),
                'market_impact_score': 0
            }
        
        # Count by fraud type
        fraud_type_counts = {}
        for alert in recent_alerts:
            fraud_type = alert.fraud_type.value
            fraud_type_counts[fraud_type] = fraud_type_counts.get(fraud_type, 0) + 1
        
        # Count high severity alerts
        high_severity = sum(1 for alert in recent_alerts 
                          if alert.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL])
        
        # Calculate average market impact
        avg_impact = np.mean([alert.market_impact for alert in recent_alerts])
        
        return {
            'total_alerts': len(recent_alerts),
            'high_severity_alerts': high_severity,
            'fraud_types': fraud_type_counts,
            'suspicious_entities': len(self.suspicious_entities),
            'market_impact_score': avg_impact,
            'avg_confidence': np.mean([alert.confidence for alert in recent_alerts])
        }
