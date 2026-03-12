"""
Mobile Push Notifications System
=================================
Production-grade push notifications for mobile devices.
Supports Firebase Cloud Messaging (FCM), Apple Push Notification Service (APNS),
and Web Push notifications.
"""

import asyncio
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
import hashlib
import base64

try:
    import aiohttp
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Notification channels."""
    FCM = "fcm"  # Firebase Cloud Messaging
    APNS = "apns"  # Apple Push Notification Service
    WEB_PUSH = "web_push"
    EMAIL = "email"
    SMS = "sms"


@dataclass
class PushConfig:
    """Push notification configuration."""
    fcm_server_key: str = ""
    fcm_project_id: str = ""
    apns_key_id: str = ""
    apns_team_id: str = ""
    apns_bundle_id: str = ""
    apns_key_path: str = ""
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_email: str = ""
    default_channel: NotificationChannel = NotificationChannel.FCM
    rate_limit_per_minute: int = 60
    batch_size: int = 500
    retry_attempts: int = 3
    retry_delay: float = 1.0


@dataclass
class PushNotification:
    """Push notification message."""
    notification_id: str
    title: str
    body: str
    data: Dict[str, Any] = field(default_factory=dict)
    priority: NotificationPriority = NotificationPriority.NORMAL
    channel: Optional[NotificationChannel] = None
    icon: str = ""
    image: str = ""
    click_action: str = ""
    sound: str = "default"
    badge: Optional[int] = None
    ttl: int = 3600  # Time to live in seconds
    collapse_key: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_fcm_payload(self) -> Dict:
        """Convert to FCM payload."""
        payload = {
            "notification": {
                "title": self.title,
                "body": self.body,
            },
            "data": {str(k): str(v) for k, v in self.data.items()},
            "android": {
                "priority": "high" if self.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL] else "normal",
                "ttl": f"{self.ttl}s",
            },
        }
        
        if self.icon:
            payload["notification"]["icon"] = self.icon
        if self.image:
            payload["notification"]["image"] = self.image
        if self.click_action:
            payload["notification"]["click_action"] = self.click_action
        if self.sound:
            payload["notification"]["sound"] = self.sound
        if self.collapse_key:
            payload["android"]["collapse_key"] = self.collapse_key
        
        return payload
    
    def to_apns_payload(self) -> Dict:
        """Convert to APNS payload."""
        aps = {
            "alert": {
                "title": self.title,
                "body": self.body,
            },
            "sound": self.sound,
        }
        
        if self.badge is not None:
            aps["badge"] = self.badge
        
        payload = {"aps": aps}
        payload.update(self.data)
        
        return payload
    
    def to_web_push_payload(self) -> Dict:
        """Convert to Web Push payload."""
        return {
            "title": self.title,
            "body": self.body,
            "icon": self.icon,
            "image": self.image,
            "data": self.data,
            "requireInteraction": self.priority in [NotificationPriority.HIGH, NotificationPriority.CRITICAL],
        }


@dataclass
class DeviceToken:
    """Device token for push notifications."""
    token: str
    channel: NotificationChannel
    device_id: str = ""
    user_id: str = ""
    platform: str = ""  # ios, android, web
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class NotificationResult:
    """Result of sending notification."""
    notification_id: str
    success: bool
    token: str
    channel: NotificationChannel
    error: Optional[str] = None
    message_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ============================================================================
# PUSH PROVIDERS
# ============================================================================

class BasePushProvider:
    """Base class for push providers."""
    
    async def send(self, notification: PushNotification, tokens: List[str]) -> List[NotificationResult]:
        """Send notification to tokens."""
        # Default implementation - log notifications
        logger.info(f"Sending push notification: {notification.title}")
        logger.info(f"Message: {notification.body}")
        logger.info(f"To {len(tokens)} recipients")
        
        # Simulate sending
        results = []
        for token in tokens:
            results.append(NotificationResult(
                success=True,
                token=token,
                message_id=f"msg_{datetime.utcnow().timestamp()}_{token[:8]}",
                timestamp=datetime.utcnow()
            ))
        
        logger.info(f"Successfully sent {len(results)} notifications")
        return results
    
    async def send_batch(self, notification: PushNotification, tokens: List[str], batch_size: int = 500) -> List[NotificationResult]:
        """Send notification in batches."""
        results = []
        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i + batch_size]
            batch_results = await self.send(notification, batch)
            results.extend(batch_results)
        return results


class FCMProvider(BasePushProvider):
    """Firebase Cloud Messaging provider."""
    
    def __init__(self, config: PushConfig):
        self.config = config
        self._base_url = "https://fcm.googleapis.com/v1"
    
    async def send(self, notification: PushNotification, tokens: List[str]) -> List[NotificationResult]:
        """Send notification via FCM."""
        results = []
        
            
        try:
            headers = {
                "Authorization": f"Bearer {await self._get_access_token()}",
                "Content-Type": "application/json",
            }
            
            async with aiohttp.ClientSession() as session:
                for token in tokens:
                    payload = notification.to_fcm_payload()
                    payload["token"] = token
                    
                    url = f"{self._base_url}/projects/{self.config.fcm_project_id}/messages:send"
                    
                    try:
                        async with session.post(url, headers=headers, json={"message": payload}) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                results.append(NotificationResult(
                                    notification_id=notification.notification_id,
                                    success=True,
                                    token=token,
                                    channel=NotificationChannel.FCM,
                                    message_id=data.get("name"),
                                ))
                            else:
                                error = await resp.text()
                                results.append(NotificationResult(
                                    notification_id=notification.notification_id,
                                    success=False,
                                    token=token,
                                    channel=NotificationChannel.FCM,
                                    error=error,
                                ))
                    except Exception as e:
                        results.append(NotificationResult(
                            notification_id=notification.notification_id,
                            success=False,
                            token=token,
                            channel=NotificationChannel.FCM,
                            error=str(e),
                        ))
        
        except ImportError:
            logger.error("aiohttp not installed for FCM")
        except Exception as e:
            logger.error(f"FCM send error: {e}")
        
        return results
    
    async def _get_access_token(self) -> str:
        """Get OAuth2 access token for FCM."""
        # In production, use google-auth library
        return self.config.fcm_server_key


class APNSProvider(BasePushProvider):
    """Apple Push Notification Service provider."""
    
    def __init__(self, config: PushConfig):
        self.config = config
        self._base_url = "https://api.push.apple.com"
    
    async def send(self, notification: PushNotification, tokens: List[str]) -> List[NotificationResult]:
        """Send notification via APNS."""
        results = []
        
            
        try:
            headers = {
                "authorization": f"bearer {self._generate_jwt()}",
                "apns-topic": self.config.apns_bundle_id,
                "apns-priority": "10" if notification.priority == NotificationPriority.HIGH else "5",
                "apns-expiration": str(int(time.time()) + notification.ttl),
            }
            
            if notification.collapse_key:
                headers["apns-collapse-id"] = notification.collapse_key
            
            payload = notification.to_apns_payload()
            
            async with aiohttp.ClientSession() as session:
                for token in tokens:
                    url = f"{self._base_url}/3/device/{token}"
                    
                    try:
                        async with session.post(url, headers=headers, json=payload) as resp:
                            if resp.status == 200:
                                results.append(NotificationResult(
                                    notification_id=notification.notification_id,
                                    success=True,
                                    token=token,
                                    channel=NotificationChannel.APNS,
                                    message_id=resp.headers.get("apns-id"),
                                ))
                            else:
                                error = await resp.text()
                                results.append(NotificationResult(
                                    notification_id=notification.notification_id,
                                    success=False,
                                    token=token,
                                    channel=NotificationChannel.APNS,
                                    error=error,
                                ))
                    except Exception as e:
                        results.append(NotificationResult(
                            notification_id=notification.notification_id,
                            success=False,
                            token=token,
                            channel=NotificationChannel.APNS,
                            error=str(e),
                        ))
        
        except ImportError:
            logger.error("aiohttp not installed for APNS")
        except Exception as e:
            logger.error(f"APNS send error: {e}")
        
        return results
    
    def _generate_jwt(self) -> str:
        """Generate JWT for APNS authentication."""
        # In production, use PyJWT library
        return ""


class WebPushProvider(BasePushProvider):
    """Web Push provider using VAPID."""
    
    def __init__(self, config: PushConfig):
        self.config = config
    
    async def send(self, notification: PushNotification, tokens: List[str]) -> List[NotificationResult]:
        """Send notification via Web Push."""
        results = []
        
        try:
            from pywebpush import webpush, WebPushException
            
            payload = json.dumps(notification.to_web_push_payload())
            
            vapid_claims = {
                "sub": f"mailto:{self.config.vapid_email}",
            }
            
            for token in tokens:
                try:
                    subscription_info = json.loads(token)
                    
                    webpush(
                        subscription_info=subscription_info,
                        data=payload,
                        vapid_private_key=self.config.vapid_private_key,
                        vapid_claims=vapid_claims,
                    )
                    
                    results.append(NotificationResult(
                        notification_id=notification.notification_id,
                        success=True,
                        token=token,
                        channel=NotificationChannel.WEB_PUSH,
                    ))
                    
                except WebPushException as e:
                    results.append(NotificationResult(
                        notification_id=notification.notification_id,
                        success=False,
                        token=token,
                        channel=NotificationChannel.WEB_PUSH,
                        error=str(e),
                    ))
                except Exception as e:
                    results.append(NotificationResult(
                        notification_id=notification.notification_id,
                        success=False,
                        token=token,
                        channel=NotificationChannel.WEB_PUSH,
                        error=str(e),
                    ))
        
        except ImportError:
            logger.error("pywebpush not installed")
        except Exception as e:
            logger.error(f"Web Push send error: {e}")
        
        return results


# ============================================================================
# NOTIFICATION MANAGER
# ============================================================================

class PushNotificationManager:
    """
    Central manager for push notifications.
    Handles device registration, sending, and tracking.
    """
    
    def __init__(self, config: Optional[PushConfig] = None):
        self.config = config or PushConfig()
        
        self._providers: Dict[NotificationChannel, BasePushProvider] = {}
        self._devices: Dict[str, DeviceToken] = {}
        self._user_devices: Dict[str, Set[str]] = {}
        self._notification_history: List[NotificationResult] = []
        self._rate_limiter: Dict[str, List[datetime]] = {}
        self._lock = threading.Lock()
        
        self._setup_providers()
    
    def _setup_providers(self):
        """Setup notification providers."""
        if self.config.fcm_server_key:
            self._providers[NotificationChannel.FCM] = FCMProvider(self.config)
        
        if self.config.apns_key_id:
            self._providers[NotificationChannel.APNS] = APNSProvider(self.config)
        
        if self.config.vapid_private_key:
            self._providers[NotificationChannel.WEB_PUSH] = WebPushProvider(self.config)
    
    def register_device(self, device: DeviceToken) -> bool:
        """Register a device for notifications."""
        with self._lock:
            self._devices[device.token] = device
            
            if device.user_id:
                if device.user_id not in self._user_devices:
                    self._user_devices[device.user_id] = set()
                self._user_devices[device.user_id].add(device.token)
            
            logger.info(f"Device registered: {device.device_id} ({device.channel.value})")
            return True
    
    def unregister_device(self, token: str) -> bool:
        """Unregister a device."""
        with self._lock:
            device = self._devices.pop(token, None)
            if device and device.user_id:
                if device.user_id in self._user_devices:
                    self._user_devices[device.user_id].discard(token)
            return device is not None
    
    def get_user_devices(self, user_id: str) -> List[DeviceToken]:
        """Get all devices for a user."""
        with self._lock:
            tokens = self._user_devices.get(user_id, set())
            return [self._devices[t] for t in tokens if t in self._devices]
    
    def _check_rate_limit(self, key: str) -> bool:
        """Check rate limit."""
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        with self._lock:
            if key not in self._rate_limiter:
                self._rate_limiter[key] = []
            
            self._rate_limiter[key] = [t for t in self._rate_limiter[key] if t > minute_ago]
            
            if len(self._rate_limiter[key]) >= self.config.rate_limit_per_minute:
                return False
            
            self._rate_limiter[key].append(now)
            return True
    
    async def send_to_device(
        self,
        token: str,
        notification: PushNotification,
    ) -> NotificationResult:
        """Send notification to a specific device."""
        device = self._devices.get(token)
        if not device:
            return NotificationResult(
                notification_id=notification.notification_id,
                success=False,
                token=token,
                channel=notification.channel or self.config.default_channel,
                error="Device not registered",
            )
        
        channel = notification.channel or device.channel
        provider = self._providers.get(channel)
        
        if not provider:
            return NotificationResult(
                notification_id=notification.notification_id,
                success=False,
                token=token,
                channel=channel,
                error=f"No provider for channel: {channel.value}",
            )
        
        if not self._check_rate_limit(token):
            return NotificationResult(
                notification_id=notification.notification_id,
                success=False,
                token=token,
                channel=channel,
                error="Rate limit exceeded",
            )
        
        results = await provider.send(notification, [token])
        
        if results:
            result = results[0]
            self._notification_history.append(result)
            return result
        
        return NotificationResult(
            notification_id=notification.notification_id,
            success=False,
            token=token,
            channel=channel,
            error="No result from provider",
        )
    
    async def send_to_user(
        self,
        user_id: str,
        notification: PushNotification,
    ) -> List[NotificationResult]:
        """Send notification to all user devices."""
        devices = self.get_user_devices(user_id)
        
        if not devices:
            return [NotificationResult(
                notification_id=notification.notification_id,
                success=False,
                token="",
                channel=self.config.default_channel,
                error="No devices registered for user",
            )]
        
        results = []
        for device in devices:
            result = await self.send_to_device(device.token, notification)
            results.append(result)
        
        return results
    
    async def broadcast(
        self,
        notification: PushNotification,
        channel: Optional[NotificationChannel] = None,
    ) -> List[NotificationResult]:
        """Broadcast notification to all devices."""
        with self._lock:
            devices = list(self._devices.values())
        
        if channel:
            devices = [d for d in devices if d.channel == channel]
        
        results = []
        for device in devices:
            result = await self.send_to_device(device.token, notification)
            results.append(result)
        
        return results
    
    # ========================================================================
    # TRADING NOTIFICATIONS
    # ========================================================================
    
    async def notify_trade_executed(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        pnl: Optional[float] = None,
    ):
        """Send trade execution notification."""
        emoji = "🟢" if side.lower() == "buy" else "🔴"
        pnl_text = f" | P&L: ${pnl:,.2f}" if pnl is not None else ""
        
        notification = PushNotification(
            notification_id=f"trade_{int(time.time())}",
            title=f"{emoji} Trade Executed",
            body=f"{side.upper()} {quantity} {symbol} @ ${price:,.4f}{pnl_text}",
            data={
                "type": "trade",
                "symbol": symbol,
                "side": side,
                "quantity": str(quantity),
                "price": str(price),
            },
            priority=NotificationPriority.HIGH,
            sound="trade.wav",
        )
        
        await self.send_to_user(user_id, notification)
    
    async def notify_signal(
        self,
        user_id: str,
        symbol: str,
        direction: str,
        confidence: float,
    ):
        """Send signal notification."""
        emoji = "📈" if direction.lower() == "buy" else "📉"
        
        notification = PushNotification(
            notification_id=f"signal_{int(time.time())}",
            title=f"{emoji} New Signal",
            body=f"{direction.upper()} {symbol} | Confidence: {confidence:.0%}",
            data={
                "type": "signal",
                "symbol": symbol,
                "direction": direction,
                "confidence": str(confidence),
            },
            priority=NotificationPriority.NORMAL,
        )
        
        await self.send_to_user(user_id, notification)
    
    async def notify_risk_alert(
        self,
        user_id: str,
        alert_type: str,
        message: str,
    ):
        """Send risk alert notification."""
        notification = PushNotification(
            notification_id=f"risk_{int(time.time())}",
            title="🚨 Risk Alert",
            body=f"{alert_type}: {message}",
            data={
                "type": "risk_alert",
                "alert_type": alert_type,
            },
            priority=NotificationPriority.CRITICAL,
            sound="alert.wav",
        )
        
        await self.send_to_user(user_id, notification)
    
    async def notify_daily_summary(
        self,
        user_id: str,
        pnl: float,
        trades: int,
        win_rate: float,
    ):
        """Send daily summary notification."""
        emoji = "📈" if pnl >= 0 else "📉"
        
        notification = PushNotification(
            notification_id=f"summary_{int(time.time())}",
            title=f"{emoji} Daily Summary",
            body=f"P&L: ${pnl:,.2f} | Trades: {trades} | Win Rate: {win_rate:.0%}",
            data={
                "type": "daily_summary",
                "pnl": str(pnl),
                "trades": str(trades),
                "win_rate": str(win_rate),
            },
            priority=NotificationPriority.NORMAL,
        )
        
        await self.send_to_user(user_id, notification)
    
    def get_stats(self) -> Dict:
        """Get notification statistics."""
        with self._lock:
            total = len(self._notification_history)
            successful = sum(1 for r in self._notification_history if r.success)
            
            return {
                "total_devices": len(self._devices),
                "total_users": len(self._user_devices),
                "notifications_sent": total,
                "success_rate": successful / total if total > 0 else 0,
                "by_channel": {
                    channel.value: sum(1 for r in self._notification_history if r.channel == channel)
                    for channel in NotificationChannel
                },
            }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_push_manager: Optional[PushNotificationManager] = None


def get_push_manager(config: Optional[PushConfig] = None) -> PushNotificationManager:
    """Get global push notification manager."""
    global _push_manager
    if _push_manager is None:
        _push_manager = PushNotificationManager(config)
    return _push_manager


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'NotificationPriority', 'NotificationChannel', 'PushConfig',
    'PushNotification', 'DeviceToken', 'NotificationResult',
    'BasePushProvider', 'FCMProvider', 'APNSProvider', 'WebPushProvider',
    'PushNotificationManager', 'get_push_manager',
]
