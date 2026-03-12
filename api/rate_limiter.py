"""
Rate limiting middleware for API protection
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import asyncio

# Set up logger
logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for API endpoints.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst_size: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst_size = burst_size
        
        # Track requests by IP
        self.minute_buckets: Dict[str, list] = defaultdict(list)
        self.hour_buckets: Dict[str, list] = defaultdict(list)
        
        # Track violations
        self.violations: Dict[str, int] = defaultdict(int)
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Block duration
        self.block_duration = timedelta(minutes=15)
        
        logger.info("✅ Rate Limiter initialized")
        logger.info(f"   Limits: {requests_per_minute}/min, {requests_per_hour}/hour")
    
    async def check_rate_limit(self, request: Request) -> bool:
        """
        Check if request is within rate limits.
        
        Returns:
            True if allowed, raises HTTPException if blocked
        """
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            block_until = self.blocked_ips[client_ip]
            if datetime.now() < block_until:
                remaining = (block_until - datetime.now()).total_seconds()
                raise HTTPException(
                    status_code=429,
                    detail=f"IP blocked for {remaining:.0f} more seconds due to rate limit violations"
                )
            else:
                # Unblock
                del self.blocked_ips[client_ip]
                self.violations[client_ip] = 0
        
        now = datetime.now()
        
        # Clean old requests
        self._clean_old_requests(client_ip, now)
        
        # Check minute limit
        minute_requests = len(self.minute_buckets[client_ip])
        if minute_requests >= self.requests_per_minute:
            self._handle_violation(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )
        
        # Check hour limit
        hour_requests = len(self.hour_buckets[client_ip])
        if hour_requests >= self.requests_per_hour:
            self._handle_violation(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
            )
        
        # Check burst limit
        recent_requests = [
            t for t in self.minute_buckets[client_ip]
            if (now - t).total_seconds() < 1
        ]
        if len(recent_requests) >= self.burst_size:
            self._handle_violation(client_ip)
            raise HTTPException(
                status_code=429,
                detail=f"Burst limit exceeded: {self.burst_size} requests per second"
            )
        
        # Record request
        self.minute_buckets[client_ip].append(now)
        self.hour_buckets[client_ip].append(now)
        
        return True
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Use client host
        return request.client.host if request.client else "unknown"
    
    def _clean_old_requests(self, client_ip: str, now: datetime):
        """Remove old requests from buckets."""
        # Clean minute bucket
        minute_ago = now - timedelta(minutes=1)
        self.minute_buckets[client_ip] = [
            t for t in self.minute_buckets[client_ip]
            if t > minute_ago
        ]
        
        # Clean hour bucket
        hour_ago = now - timedelta(hours=1)
        self.hour_buckets[client_ip] = [
            t for t in self.hour_buckets[client_ip]
            if t > hour_ago
        ]
    
    def _handle_violation(self, client_ip: str):
        """Handle rate limit violation."""
        self.violations[client_ip] += 1
        
        logger.warning(f"⚠️ Rate limit violation from {client_ip} (count: {self.violations[client_ip]})")
        
        # Block IP after 3 violations
        if self.violations[client_ip] >= 3:
            block_until = datetime.now() + self.block_duration
            self.blocked_ips[client_ip] = block_until
            logger.warning(f"🚫 Blocked IP {client_ip} until {block_until}")
    
    def get_stats(self, client_ip: Optional[str] = None) -> Dict:
        """Get rate limiter statistics."""
        if client_ip:
            now = datetime.now()
            self._clean_old_requests(client_ip, now)
            
            return {
                'client_ip': client_ip,
                'requests_last_minute': len(self.minute_buckets[client_ip]),
                'requests_last_hour': len(self.hour_buckets[client_ip]),
                'violations': self.violations[client_ip],
                'blocked': client_ip in self.blocked_ips,
                'limits': {
                    'per_minute': self.requests_per_minute,
                    'per_hour': self.requests_per_hour,
                    'burst': self.burst_size
                }
            }
        else:
            return {
                'total_clients': len(set(list(self.minute_buckets.keys()) + list(self.hour_buckets.keys()))),
                'blocked_ips': len(self.blocked_ips),
                'total_violations': sum(self.violations.values()),
                'limits': {
                    'per_minute': self.requests_per_minute,
                    'per_hour': self.requests_per_hour,
                    'burst': self.burst_size
                }
            }
    
    def whitelist_ip(self, client_ip: str):
        """Whitelist an IP address (remove from blocks and violations)."""
        if client_ip in self.blocked_ips:
            del self.blocked_ips[client_ip]
        
        if client_ip in self.violations:
            del self.violations[client_ip]
        
        logger.info(f"✅ Whitelisted IP: {client_ip}")
    
    def blacklist_ip(self, client_ip: str, duration_minutes: int = 60):
        """Blacklist an IP address for specified duration."""
        block_until = datetime.now() + timedelta(minutes=duration_minutes)
        self.blocked_ips[client_ip] = block_until
        logger.warning(f"🚫 Blacklisted IP {client_ip} until {block_until}")


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting."""
        try:
            # Check rate limit
            await self.rate_limiter.check_rate_limit(request)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            client_ip = self.rate_limiter._get_client_ip(request)
            stats = self.rate_limiter.get_stats(client_ip)
            
            response.headers["X-RateLimit-Limit-Minute"] = str(self.rate_limiter.requests_per_minute)
            response.headers["X-RateLimit-Remaining-Minute"] = str(
                self.rate_limiter.requests_per_minute - stats['requests_last_minute']
            )
            response.headers["X-RateLimit-Limit-Hour"] = str(self.rate_limiter.requests_per_hour)
            response.headers["X-RateLimit-Remaining-Hour"] = str(
                self.rate_limiter.requests_per_hour - stats['requests_last_hour']
            )
            
            return response
            
        except HTTPException as e:
            # Return rate limit error
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.rate_limiter.requests_per_minute)
                }
            )
