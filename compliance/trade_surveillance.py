"""
Trade surveillance and compliance monitoring for AlphaAlgo 2.0
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from enum import Enum

# Set up logger
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


@dataclass
class ComplianceAlert:
    """Compliance alert details."""
    level: AlertLevel
    rule_id: str
    message: str
    details: Dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class TradeSurveillance:
    """
    Real-time trade surveillance system.
    Monitors trading activity for compliance violations.
    """
    
    def __init__(
        self,
        max_position_value: float = 1000000.0,  # $1M max position
        max_daily_trades: int = 1000,
        max_order_size: float = 100000.0,      # $100K max order
        wash_sale_window: int = 30             # 30 days
    ):
        self.max_position_value = max_position_value
        self.max_daily_trades = max_daily_trades
        self.max_order_size = max_order_size
        self.wash_sale_window = wash_sale_window
        
        # Compliance rules
        self.rules = {
            'position_limit': self._check_position_limit,
            'trade_frequency': self._check_trade_frequency,
            'order_size': self._check_order_size,
            'wash_sale': self._check_wash_sale,
            'price_manipulation': self._check_price_manipulation,
            'insider_trading': self._check_insider_trading,
            'market_hours': self._check_market_hours,
            'restricted_symbols': self._check_restricted_symbols
        }
        
        # Alert history
        self.alerts: List[ComplianceAlert] = []
        
        # Trading activity
        self.daily_trades = {}
        self.positions = {}
        self.trade_history = []
        
        # Restricted list
        self.restricted_symbols = set()
        
        logger.info("✅ Trade Surveillance initialized")
    
    def monitor_trade(
        self,
        trade: Dict,
        market_data: Dict
    ) -> List[ComplianceAlert]:
        """
        Monitor trade for compliance violations.
        
        Args:
            trade: Trade details
            market_data: Current market data
        
        Returns:
            List of compliance alerts if any
        """
        alerts = []
        
        try:
            # Run all compliance checks
            for rule_id, check_func in self.rules.items():
                alert = check_func(trade, market_data)
                if alert:
                    alerts.append(alert)
                    self.alerts.append(alert)
            
            # Update trading activity
            self._update_trading_activity(trade)
            
            # Log alerts
            if alerts:
                logger.warning(f"⚠️ Generated {len(alerts)} compliance alerts")
                for alert in alerts:
                    logger.warning(f"   {alert.level.value}: {alert.message}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error monitoring trade: {str(e)}")
            return []
    
    def _check_position_limit(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check position size limits."""
        symbol = trade['symbol']
        
        # Calculate new position value
        current_position = self.positions.get(symbol, 0)
        new_position = current_position + trade['quantity']
        position_value = new_position * trade['price']
        
        if abs(position_value) > self.max_position_value:
            return ComplianceAlert(
                level=AlertLevel.VIOLATION,
                rule_id='position_limit',
                message=f"Position value exceeds limit for {symbol}",
                details={
                    'symbol': symbol,
                    'position_value': position_value,
                    'limit': self.max_position_value
                }
            )
        
        return None
    
    def _check_trade_frequency(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check trading frequency limits."""
        date = trade['timestamp'].date()
        symbol = trade['symbol']
        
        # Update daily trades
        if date not in self.daily_trades:
            self.daily_trades[date] = {}
        if symbol not in self.daily_trades[date]:
            self.daily_trades[date][symbol] = 0
        
        self.daily_trades[date][symbol] += 1
        
        # Check limit
        if self.daily_trades[date][symbol] > self.max_daily_trades:
            return ComplianceAlert(
                level=AlertLevel.WARNING,
                rule_id='trade_frequency',
                message=f"Excessive trading in {symbol}",
                details={
                    'symbol': symbol,
                    'trades': self.daily_trades[date][symbol],
                    'limit': self.max_daily_trades
                }
            )
        
        return None
    
    def _check_order_size(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check order size limits."""
        order_value = abs(trade['quantity'] * trade['price'])
        
        if order_value > self.max_order_size:
            return ComplianceAlert(
                level=AlertLevel.WARNING,
                rule_id='order_size',
                message=f"Large order in {trade['symbol']}",
                details={
                    'symbol': trade['symbol'],
                    'order_value': order_value,
                    'limit': self.max_order_size
                }
            )
        
        return None
    
    def _check_wash_sale(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check for wash sale violations."""
        symbol = trade['symbol']
        
        # Get recent trades
        recent_trades = [
            t for t in self.trade_history
            if (t['symbol'] == symbol and
                t['timestamp'] > trade['timestamp'] - timedelta(days=self.wash_sale_window))
        ]
        
        if recent_trades:
            # Check for offsetting trades
            for old_trade in recent_trades:
                if (
                    old_trade['side'] != trade['side'] and
                    abs(old_trade['price'] - trade['price']) / old_trade['price'] < 0.01
                ):
                    return ComplianceAlert(
                        level=AlertLevel.VIOLATION,
                        rule_id='wash_sale',
                        message=f"Potential wash sale in {symbol}",
                        details={
                            'symbol': symbol,
                            'current_trade': trade,
                            'previous_trade': old_trade
                        }
                    )
        
        return None
    
    def _check_price_manipulation(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check for price manipulation."""
        symbol = trade['symbol']
        
        if symbol not in market_data:
            return None
        
        # Check for large price impact
        price_impact = abs(trade['price'] - market_data[symbol]['last_price'])
        price_impact_pct = price_impact / market_data[symbol]['last_price']
        
        if price_impact_pct > 0.01:  # 1% price impact
            return ComplianceAlert(
                level=AlertLevel.WARNING,
                rule_id='price_manipulation',
                message=f"Large price impact in {symbol}",
                details={
                    'symbol': symbol,
                    'impact_pct': price_impact_pct,
                    'trade_price': trade['price'],
                    'market_price': market_data[symbol]['last_price']
                }
            )
        
        return None
    
    def _check_insider_trading(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check for potential insider trading."""
        symbol = trade['symbol']
        
        # Check if symbol has pending news
        if market_data.get('pending_news', {}).get(symbol):
            return ComplianceAlert(
                level=AlertLevel.CRITICAL,
                rule_id='insider_trading',
                message=f"Trading ahead of news in {symbol}",
                details={
                    'symbol': symbol,
                    'news': market_data['pending_news'][symbol]
                }
            )
        
        return None
    
    def _check_market_hours(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check trading hours compliance."""
        timestamp = trade['timestamp']
        
        # Check if within market hours (9:30 AM - 4:00 PM EST)
        if not (
            9 <= timestamp.hour <= 16 and
            (timestamp.hour != 9 or timestamp.minute >= 30) and
            timestamp.hour != 16 or timestamp.minute == 0
        ):
            return ComplianceAlert(
                level=AlertLevel.WARNING,
                rule_id='market_hours',
                message=f"Trading outside market hours",
                details={
                    'timestamp': timestamp,
                    'symbol': trade['symbol']
                }
            )
        
        return None
    
    def _check_restricted_symbols(
        self,
        trade: Dict,
        market_data: Dict
    ) -> Optional[ComplianceAlert]:
        """Check restricted symbol list."""
        symbol = trade['symbol']
        
        if symbol in self.restricted_symbols:
            return ComplianceAlert(
                level=AlertLevel.CRITICAL,
                rule_id='restricted_symbols',
                message=f"Trading restricted symbol {symbol}",
                details={
                    'symbol': symbol,
                    'restriction_reason': 'Symbol on restricted list'
                }
            )
        
        return None
    
    def _update_trading_activity(self, trade: Dict):
        """Update trading activity records."""
        symbol = trade['symbol']
        
        # Update position
        if symbol not in self.positions:
            self.positions[symbol] = 0
        self.positions[symbol] += trade['quantity']
        
        # Add to history
        self.trade_history.append(trade)
        
        # Clean old history
        self._clean_old_data()
    
    def _clean_old_data(self):
        """Clean old trading data."""
        now = datetime.now()
        
        # Clean old daily trades
        self.daily_trades = {
            date: trades
            for date, trades in self.daily_trades.items()
            if (now - datetime.combine(date, datetime.min.time())).days < 30
        }
        
        # Clean old trade history
        self.trade_history = [
            trade for trade in self.trade_history
            if (now - trade['timestamp']).days < self.wash_sale_window
        ]
        
        # Clean old alerts
        self.alerts = [
            alert for alert in self.alerts
            if (now - alert.timestamp).days < 30
        ]
    
    def add_restricted_symbol(self, symbol: str, reason: str = None):
        """Add symbol to restricted list."""
        self.restricted_symbols.add(symbol)
        logger.info(f"✅ Added {symbol} to restricted list")
        if reason:
            logger.info(f"   Reason: {reason}")
    
    def remove_restricted_symbol(self, symbol: str):
        """Remove symbol from restricted list."""
        if symbol in self.restricted_symbols:
            self.restricted_symbols.remove(symbol)
            logger.info(f"✅ Removed {symbol} from restricted list")
    
    def get_compliance_summary(self) -> Dict:
        """Get compliance monitoring summary."""
        now = datetime.now()
        recent_alerts = [
            alert for alert in self.alerts
            if (now - alert.timestamp).total_seconds() < 86400  # Last 24h
        ]
        
        return {
            'alert_count': len(recent_alerts),
            'violations': sum(1 for a in recent_alerts if a.level == AlertLevel.VIOLATION),
            'warnings': sum(1 for a in recent_alerts if a.level == AlertLevel.WARNING),
            'critical': sum(1 for a in recent_alerts if a.level == AlertLevel.CRITICAL),
            'restricted_symbols': len(self.restricted_symbols),
            'monitored_positions': len(self.positions),
            'recent_alerts': [
                {
                    'level': alert.level.value,
                    'message': alert.message,
                    'timestamp': alert.timestamp
                }
                for alert in recent_alerts
            ]
        }
    
    def generate_compliance_report(self) -> str:
        """Generate detailed compliance report."""
        summary = self.get_compliance_summary()
        
        report = [
            "COMPLIANCE MONITORING REPORT",
            "=" * 50,
            f"\nAlert Summary (24h):",
            f"- Total Alerts: {summary['alert_count']}",
            f"- Violations: {summary['violations']}",
            f"- Warnings: {summary['warnings']}",
            f"- Critical: {summary['critical']}",
            
            f"\nMonitoring Status:",
            f"- Restricted Symbols: {summary['restricted_symbols']}",
            f"- Monitored Positions: {summary['monitored_positions']}",
            
            "\nRecent Alerts:"
        ]
        
        for alert in summary['recent_alerts']:
            report.append(
                f"- [{alert['level'].upper()}] {alert['message']} "
                f"({alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')})"
            )
        
        return "\n".join(report)
