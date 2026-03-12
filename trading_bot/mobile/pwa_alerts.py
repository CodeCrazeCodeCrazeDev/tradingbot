"""
PWA Push Notification System
Mobile alerts with acknowledgment and resolution tracking
"""

import asyncio
import logging
import uuid
import json
import hashlib
from typing import Any, Awaitable, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class AlertStatus(Enum):
    """Alert status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    EXPIRED = "expired"
    FAILED = "failed"


class AlertChannel(Enum):
    """Notification channels"""
    PWA = "pwa"
    EMAIL = "email"
    SMS = "sms"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


@dataclass
class Alert:
    """Alert definition"""
    alert_id: str
    title: str
    message: str
    priority: AlertPriority
    category: str
    timestamp: datetime
    status: AlertStatus = AlertStatus.PENDING
    channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.PWA])
    data: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    delivery_attempts: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'title': self.title,
            'message': self.message,
            'priority': self.priority.value,
            'category': self.category,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'channels': [c.value for c in self.channels],
            'data': self.data,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
        }
    
    def to_push_payload(self) -> Dict[str, Any]:
        """Convert to web push payload"""
        return {
            'title': self.title,
            'body': self.message,
            'icon': self._get_icon(),
            'badge': '/badge.png',
            'tag': self.alert_id,
            'data': {
                'alert_id': self.alert_id,
                'category': self.category,
                'priority': self.priority.value,
                'timestamp': self.timestamp.isoformat(),
                **self.data
            },
            'requireInteraction': self.priority.value >= AlertPriority.HIGH.value,
            'actions': [
                {'action': 'acknowledge', 'title': 'Acknowledge'},
                {'action': 'view', 'title': 'View Details'}
            ]
        }
    
    def _get_icon(self) -> str:
        """Get icon based on priority"""
        icons = {
            AlertPriority.LOW: '/icons/info.png',
            AlertPriority.MEDIUM: '/icons/warning.png',
            AlertPriority.HIGH: '/icons/alert.png',
            AlertPriority.CRITICAL: '/icons/critical.png',
            AlertPriority.EMERGENCY: '/icons/emergency.png',
        }
        return icons.get(self.priority, '/icons/default.png')


@dataclass
class PushSubscription:
    """Web push subscription"""
    subscription_id: str
    user_id: str
    endpoint: str
    keys: Dict[str, str]
    created_at: datetime
    last_used: Optional[datetime] = None
    device_info: Optional[Dict[str, str]] = None
    enabled: bool = True


class PWAAlertSystem:
    """
    Progressive Web App alert system with push notifications
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # VAPID keys for web push
        self.vapid_private_key = self.config.get('vapid_private_key')
        self.vapid_public_key = self.config.get('vapid_public_key')
        self.vapid_claims = {
            'sub': self.config.get('vapid_email', 'mailto:admin@tradingbot.com')
        }
        
        # Subscriptions
        self.subscriptions: Dict[str, PushSubscription] = {}
        
        # Alerts
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.max_history = self.config.get('max_history', 10000)
        
        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.max_alerts_per_minute = self.config.get('max_alerts_per_minute', 10)
        
        # Callbacks
        self.on_acknowledge: Optional[Callable[[Alert], Awaitable[None]]] = None
        self.on_resolve: Optional[Callable[[Alert], Awaitable[None]]] = None
        
        # Channel handlers
        self.channel_handlers: Dict[AlertChannel, Callable] = {}
        self._setup_default_handlers()
        
        # Statistics
        self.stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_acknowledged': 0,
            'total_resolved': 0,
            'total_failed': 0,
            'avg_ack_time': 0
        }
        
        logger.info("PWA alert system initialized")
        
    def _setup_default_handlers(self):
        """Setup default channel handlers"""
        self.channel_handlers[AlertChannel.PWA] = self._send_pwa_push
        self.channel_handlers[AlertChannel.WEBHOOK] = self._send_webhook
        
    async def register_subscription(
        self,
        user_id: str,
        endpoint: str,
        keys: Dict[str, str],
        device_info: Optional[Dict[str, str]] = None
    ) -> PushSubscription:
        """
        Register a new push subscription
        """
        subscription_id = hashlib.sha256(endpoint.encode()).hexdigest()[:16]
        
        subscription = PushSubscription(
            subscription_id=subscription_id,
            user_id=user_id,
            endpoint=endpoint,
            keys=keys,
            created_at=datetime.now(),
            device_info=device_info
        )
        
        self.subscriptions[subscription_id] = subscription
        logger.info(f"Registered subscription {subscription_id} for user {user_id}")
        
        return subscription
    
    def unregister_subscription(self, subscription_id: str) -> bool:
        """Unregister a subscription"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Unregistered subscription {subscription_id}")
            return True
        return False
    
    def get_user_subscriptions(self, user_id: str) -> List[PushSubscription]:
        """Get all subscriptions for a user"""
        return [s for s in self.subscriptions.values() if s.user_id == user_id]
    
    async def send_alert(
        self,
        title: str,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        category: str = "general",
        channels: Optional[List[AlertChannel]] = None,
        data: Optional[Dict[str, Any]] = None,
        user_ids: Optional[List[str]] = None,
        expires_in: Optional[int] = None  # seconds
    ) -> Alert:
        """
        Send an alert through specified channels
        
        Args:
            title: Alert title
            message: Alert message
            priority: Alert priority
            category: Alert category
            channels: Notification channels
            data: Additional data
            user_ids: Specific users to notify (None = all)
            expires_in: Expiration time in seconds
        """
        # Rate limiting
        if not self._check_rate_limit(category):
            logger.warning(f"Rate limit exceeded for category {category}")
            raise Exception("Rate limit exceeded")
            
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            title=title,
            message=message,
            priority=priority,
            category=category,
            timestamp=datetime.now(),
            channels=channels or [AlertChannel.PWA],
            data=data or {},
            expires_at=datetime.now() + timedelta(seconds=expires_in) if expires_in else None
        )
        
        self.alerts[alert.alert_id] = alert
        
        # Send through channels
        for channel in alert.channels:
            handler = self.channel_handlers.get(channel)
            if handler:
                try:
                    await handler(alert, user_ids)
                    alert.status = AlertStatus.SENT
                    self.stats['total_sent'] += 1
                except Exception as e:
                    logger.error(f"Failed to send alert via {channel.value}: {e}")
                    alert.last_error = str(e)
                    alert.delivery_attempts += 1
                    
        logger.info(f"Alert {alert.alert_id} sent: {title}")
        return alert
    
    async def _send_pwa_push(self, alert: Alert, user_ids: Optional[List[str]] = None):
        """Send PWA push notification"""
        try:
            from pywebpush import webpush, WebPushException
        except ImportError:
            logger.warning("pywebpush not installed, using mock push")
            return await self._mock_push(alert, user_ids)
            
        payload = json.dumps(alert.to_push_payload())
        
        # Get target subscriptions
        if user_ids:
            subscriptions = [s for s in self.subscriptions.values() 
                          if s.user_id in user_ids and s.enabled]
        else:
            subscriptions = [s for s in self.subscriptions.values() if s.enabled]
            
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info={
                        'endpoint': subscription.endpoint,
                        'keys': subscription.keys
                    },
                    data=payload,
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims=self.vapid_claims
                )
                subscription.last_used = datetime.now()
                self.stats['total_delivered'] += 1
                
            except WebPushException as e:
                logger.error(f"Push failed for {subscription.subscription_id}: {e}")
                if e.response and e.response.status_code == 410:
                    # Subscription expired
                    subscription.enabled = False
                    
    async def _mock_push(self, alert: Alert, user_ids: Optional[List[str]] = None):
        """Mock push for testing"""
        logger.info(f"[MOCK PUSH] {alert.title}: {alert.message}")
        self.stats['total_delivered'] += 1
        
    async def _send_webhook(self, alert: Alert, user_ids: Optional[List[str]] = None):
        """Send alert via webhook"""
        webhook_url = self.config.get('webhook_url')
        if not webhook_url:
            return
            
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    webhook_url,
                    json=alert.to_dict(),
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        self.stats['total_delivered'] += 1
                    else:
                        logger.error(f"Webhook failed: {response.status}")
            except Exception as e:
                logger.error(f"Webhook error: {e}")
                
    def _check_rate_limit(self, category: str) -> bool:
        """Check if rate limit allows sending"""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        if category not in self.rate_limits:
            self.rate_limits[category] = []
            
        # Clean old entries
        self.rate_limits[category] = [
            t for t in self.rate_limits[category] if t > minute_ago
        ]
        
        if len(self.rate_limits[category]) >= self.max_alerts_per_minute:
            return False
            
        self.rate_limits[category].append(now)
        return True
    
    async def acknowledge_alert(
        self,
        alert_id: str,
        user_id: str
    ) -> bool:
        """
        Acknowledge an alert
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
            
        if alert.status in [AlertStatus.RESOLVED, AlertStatus.EXPIRED]:
            return False
            
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = user_id
        
        self.stats['total_acknowledged'] += 1
        self._update_ack_time(alert)
        
        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        
        if self.on_acknowledge:
            await self.on_acknowledge(alert)
            
        return True
    
    async def resolve_alert(
        self,
        alert_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> bool:
        """
        Resolve an alert
        """
        alert = self.alerts.get(alert_id)
        if not alert:
            return False
            
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        alert.resolved_by = user_id
        alert.resolution_notes = notes
        
        self.stats['total_resolved'] += 1
        
        # Move to history
        self.alert_history.append(alert)
        del self.alerts[alert_id]
        
        # Trim history
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[-self.max_history:]
            
        logger.info(f"Alert {alert_id} resolved by {user_id}")
        
        if self.on_resolve:
            await self.on_resolve(alert)
            
        return True
    
    def _update_ack_time(self, alert: Alert):
        """Update average acknowledgment time"""
        if alert.acknowledged_at:
            ack_time = (alert.acknowledged_at - alert.timestamp).total_seconds()
            total_acked = self.stats['total_acknowledged']
            if total_acked > 0:
                self.stats['avg_ack_time'] = (
                    (self.stats['avg_ack_time'] * (total_acked - 1) + ack_time) / total_acked
                )
    
    def get_active_alerts(
        self,
        priority: Optional[AlertPriority] = None,
        category: Optional[str] = None
    ) -> List[Alert]:
        """Get active (unresolved) alerts"""
        alerts = list(self.alerts.values())
        
        if priority:
            alerts = [a for a in alerts if a.priority == priority]
        if category:
            alerts = [a for a in alerts if a.category == category]
            
        return sorted(alerts, key=lambda a: (-a.priority.value, a.timestamp))
    
    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get specific alert"""
        if alert_id in self.alerts:
            return self.alerts[alert_id]
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                return alert
        return None
    
    async def check_expired_alerts(self):
        """Check and expire old alerts"""
        now = datetime.now()
        expired = []
        
        for alert_id, alert in self.alerts.items():
            if alert.expires_at and alert.expires_at < now:
                alert.status = AlertStatus.EXPIRED
                expired.append(alert_id)
                
        for alert_id in expired:
            alert = self.alerts.pop(alert_id)
            self.alert_history.append(alert)
            logger.info(f"Alert {alert_id} expired")
            
    async def run_expiry_checker(self, interval: int = 60):
        """Run periodic expiry checker"""
        while True:
            await self.check_expired_alerts()
            await asyncio.sleep(interval)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        return {
            **self.stats,
            'active_alerts': len(self.alerts),
            'subscriptions': len(self.subscriptions),
            'history_count': len(self.alert_history),
            'by_priority': {
                p.name: len([a for a in self.alerts.values() if a.priority == p])
                for p in AlertPriority
            }
        }
    
    # Convenience methods for common alerts
    async def send_trade_alert(
        self,
        symbol: str,
        action: str,
        price: float,
        quantity: float,
        pnl: Optional[float] = None
    ) -> Alert:
        """Send trade execution alert"""
        pnl_str = f" | P&L: ${pnl:,.2f}" if pnl else ""
        return await self.send_alert(
            title=f"Trade Executed: {action} {symbol}",
            message=f"{action} {quantity} {symbol} @ ${price:,.2f}{pnl_str}",
            priority=AlertPriority.MEDIUM,
            category="trade",
            data={'symbol': symbol, 'action': action, 'price': price, 'quantity': quantity, 'pnl': pnl}
        )
    
    async def send_risk_alert(
        self,
        risk_type: str,
        message: str,
        severity: str = "high"
    ) -> Alert:
        """Send risk management alert"""
        priority = AlertPriority.CRITICAL if severity == "critical" else AlertPriority.HIGH
        return await self.send_alert(
            title=f"⚠️ Risk Alert: {risk_type}",
            message=message,
            priority=priority,
            category="risk",
            data={'risk_type': risk_type, 'severity': severity}
        )
    
    async def send_system_alert(
        self,
        component: str,
        status: str,
        details: Optional[str] = None
    ) -> Alert:
        """Send system status alert"""
        priority = AlertPriority.HIGH if status == "error" else AlertPriority.MEDIUM
        return await self.send_alert(
            title=f"System Alert: {component}",
            message=f"{component} status: {status}" + (f" - {details}" if details else ""),
            priority=priority,
            category="system",
            data={'component': component, 'status': status}
        )
    
    async def send_emergency_alert(
        self,
        message: str,
        action_required: str
    ) -> Alert:
        """Send emergency alert requiring immediate action"""
        return await self.send_alert(
            title="🚨 EMERGENCY",
            message=f"{message}\n\nAction Required: {action_required}",
            priority=AlertPriority.EMERGENCY,
            category="emergency",
            channels=[AlertChannel.PWA, AlertChannel.WEBHOOK],
            data={'action_required': action_required}
        )
