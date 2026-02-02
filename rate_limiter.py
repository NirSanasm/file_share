"""
Rate limiting middleware for preventing abuse.
"""
import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Rate limit configuration
RATE_LIMIT_UPLOADS = 10  # Max uploads per window
RATE_LIMIT_WINDOW = 3600  # Time window in seconds (1 hour)
RATE_LIMIT_VIEWS = 100  # Max views per window
RATE_LIMIT_VIEW_WINDOW = 3600  # Time window for views (1 hour)

# Temporary ban configuration
BAN_THRESHOLD = 20  # Number of violations before ban
BAN_DURATION = 86400  # Ban duration in seconds (24 hours)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        # Structure: {ip: [(timestamp, action), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        # Structure: {ip: (ban_until_timestamp, violation_count)}
        self.banned_ips: Dict[str, Tuple[float, int]] = {}
        # Last cleanup timestamp
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory bloat."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes
        if current_time - self.last_cleanup < 300:
            return
        
        # Clean up request history
        for ip in list(self.requests.keys()):
            self.requests[ip] = [
                (ts, action) for ts, action in self.requests[ip]
                if current_time - ts < max(RATE_LIMIT_WINDOW, RATE_LIMIT_VIEW_WINDOW)
            ]
            if not self.requests[ip]:
                del self.requests[ip]
        
        # Clean up expired bans
        for ip in list(self.banned_ips.keys()):
            ban_until, _ = self.banned_ips[ip]
            if current_time > ban_until:
                del self.banned_ips[ip]
        
        self.last_cleanup = current_time
    
    def is_banned(self, ip: str) -> Tuple[bool, float]:
        """
        Check if IP is banned.
        Returns (is_banned, time_remaining)
        """
        if ip in self.banned_ips:
            ban_until, _ = self.banned_ips[ip]
            current_time = time.time()
            if current_time < ban_until:
                return True, ban_until - current_time
            else:
                # Ban expired
                del self.banned_ips[ip]
        return False, 0
    
    def check_rate_limit(self, ip: str, action: str = 'upload') -> Tuple[bool, int, int]:
        """
        Check if request should be rate limited.
        Returns (is_allowed, remaining, reset_time)
        """
        self._cleanup_old_entries()
        
        # Check if IP is banned
        is_banned, time_remaining = self.is_banned(ip)
        if is_banned:
            return False, 0, int(time_remaining)
        
        current_time = time.time()
        
        # Determine rate limit based on action
        if action == 'upload':
            limit = RATE_LIMIT_UPLOADS
            window = RATE_LIMIT_WINDOW
        else:  # view
            limit = RATE_LIMIT_VIEWS
            window = RATE_LIMIT_VIEW_WINDOW
        
        # Get requests within the time window for this action
        window_start = current_time - window
        recent_requests = [
            (ts, act) for ts, act in self.requests[ip]
            if ts > window_start and act == action
        ]
        
        # Check if limit exceeded
        if len(recent_requests) >= limit:
            # Calculate when the oldest request will expire
            oldest_timestamp = min(ts for ts, _ in recent_requests)
            reset_time = int(oldest_timestamp + window - current_time)
            
            # Track violations
            self._record_violation(ip)
            
            return False, 0, reset_time
        
        # Allow request
        remaining = limit - len(recent_requests) - 1
        return True, remaining, int(window)
    
    def record_request(self, ip: str, action: str = 'upload'):
        """Record a successful request."""
        current_time = time.time()
        self.requests[ip].append((current_time, action))
    
    def _record_violation(self, ip: str):
        """Record a rate limit violation and ban if threshold exceeded."""
        current_time = time.time()
        
        if ip in self.banned_ips:
            ban_until, violation_count = self.banned_ips[ip]
            violation_count += 1
        else:
            violation_count = 1
        
        # Ban if threshold exceeded
        if violation_count >= BAN_THRESHOLD:
            ban_until = current_time + BAN_DURATION
            self.banned_ips[ip] = (ban_until, violation_count)
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check for forwarded IP (if behind proxy)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return 'unknown'


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to specific endpoints.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for static files
        if request.url.path.startswith('/static') or request.url.path.startswith('/uploads'):
            return await call_next(request)
        
        ip = rate_limiter.get_client_ip(request)
        
        # Check if IP is banned
        is_banned, time_remaining = rate_limiter.is_banned(ip)
        if is_banned:
            hours = int(time_remaining // 3600)
            minutes = int((time_remaining % 3600) // 60)
            return JSONResponse(
                status_code=429,
                content={
                    'error': 'Too many requests',
                    'message': f'Your IP has been temporarily banned due to excessive requests. Ban expires in {hours}h {minutes}m.',
                    'retry_after': int(time_remaining)
                },
                headers={'Retry-After': str(int(time_remaining))}
            )
        
        # Determine action type
        action = 'upload' if request.url.path == '/api/upload' else 'view'
        
        # Only rate limit upload endpoint and view endpoint
        if request.url.path == '/api/upload' or (request.method == 'GET' and len(request.url.path) > 1):
            is_allowed, remaining, reset_time = rate_limiter.check_rate_limit(ip, action)
            
            if not is_allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        'error': 'Rate limit exceeded',
                        'message': f'Too many {action}s. Please try again later.',
                        'retry_after': reset_time
                    },
                    headers={
                        'X-RateLimit-Limit': str(RATE_LIMIT_UPLOADS if action == 'upload' else RATE_LIMIT_VIEWS),
                        'X-RateLimit-Remaining': '0',
                        'X-RateLimit-Reset': str(reset_time),
                        'Retry-After': str(reset_time)
                    }
                )
            
            # Record the request
            rate_limiter.record_request(ip, action)
            
            # Add rate limit headers to response
            response = await call_next(request)
            response.headers['X-RateLimit-Limit'] = str(RATE_LIMIT_UPLOADS if action == 'upload' else RATE_LIMIT_VIEWS)
            response.headers['X-RateLimit-Remaining'] = str(remaining)
            response.headers['X-RateLimit-Reset'] = str(reset_time)
            
            return response
        
        return await call_next(request)
