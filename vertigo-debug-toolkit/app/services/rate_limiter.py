"""
API Rate Limiting Service

Comprehensive rate limiting system with Redis backend supporting multiple strategies,
user tiers, and sophisticated rate limiting rules for the Vertigo Debug Toolkit.
"""

import os
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import request, g, current_app
from flask_login import current_user
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RateLimitTier(Enum):
    """Rate limit tiers for different user types."""
    FREE = "free"
    PREMIUM = "premium" 
    ADMIN = "admin"
    SYSTEM = "system"


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    PER_USER = "per_user"
    PER_IP = "per_ip"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    limit: int
    window_seconds: int
    strategy: RateLimitStrategy
    tier: RateLimitTier
    endpoint_pattern: Optional[str] = None
    bypass_admin: bool = True
    soft_limit: Optional[int] = None  # Warning threshold
    burst_limit: Optional[int] = None  # Short-term burst allowance


@dataclass 
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    tier: Optional[RateLimitTier] = None
    warning: bool = False


class RateLimiterService:
    """Redis-backed rate limiting service with comprehensive features."""
    
    def __init__(self, redis_url: str = None):
        """Initialize rate limiter service."""
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._redis_client = None
        self._initialized = False
        
        # Default rate limit rules by tier and strategy
        self.default_rules = {
            # API Rate Limits
            (RateLimitTier.FREE, RateLimitStrategy.PER_USER): [
                RateLimitRule(100, 3600, RateLimitStrategy.PER_USER, RateLimitTier.FREE, soft_limit=80),  # 100/hour
                RateLimitRule(10, 60, RateLimitStrategy.PER_USER, RateLimitTier.FREE, soft_limit=8),     # 10/minute
            ],
            (RateLimitTier.PREMIUM, RateLimitStrategy.PER_USER): [
                RateLimitRule(500, 3600, RateLimitStrategy.PER_USER, RateLimitTier.PREMIUM, soft_limit=400),  # 500/hour
                RateLimitRule(50, 60, RateLimitStrategy.PER_USER, RateLimitTier.PREMIUM, soft_limit=40),     # 50/minute
            ],
            (RateLimitTier.ADMIN, RateLimitStrategy.PER_USER): [
                RateLimitRule(2000, 3600, RateLimitStrategy.PER_USER, RateLimitTier.ADMIN, soft_limit=1600), # 2000/hour
                RateLimitRule(100, 60, RateLimitStrategy.PER_USER, RateLimitTier.ADMIN, soft_limit=80),      # 100/minute
            ],
            
            # IP-based limits (for unauthenticated requests)
            (RateLimitTier.FREE, RateLimitStrategy.PER_IP): [
                RateLimitRule(50, 3600, RateLimitStrategy.PER_IP, RateLimitTier.FREE),   # 50/hour per IP
                RateLimitRule(5, 60, RateLimitStrategy.PER_IP, RateLimitTier.FREE),      # 5/minute per IP
            ],
            
            # Endpoint-specific limits
            (RateLimitTier.FREE, RateLimitStrategy.PER_ENDPOINT): [
                # Heavy operations
                RateLimitRule(10, 3600, RateLimitStrategy.PER_ENDPOINT, RateLimitTier.FREE, 
                            endpoint_pattern=r'/api/(sync|analytics|prompts/test)', soft_limit=8),
                # Authentication endpoints
                RateLimitRule(5, 900, RateLimitStrategy.PER_ENDPOINT, RateLimitTier.FREE,
                            endpoint_pattern=r'/auth/(login|register)', soft_limit=3),
                # Admin endpoints
                RateLimitRule(20, 3600, RateLimitStrategy.PER_ENDPOINT, RateLimitTier.FREE,
                            endpoint_pattern=r'/admin/.*', bypass_admin=True),
            ],
        }
        
        # Custom rules loaded from configuration
        self.custom_rules: Dict[str, List[RateLimitRule]] = {}
        
        # Bypass patterns for system endpoints
        self.bypass_patterns = [
            r'/health$',
            r'/static/.*',
            r'/favicon.ico$',
        ]
    
    @property
    def redis_client(self) -> redis.Redis:
        """Get Redis client with lazy initialization."""
        if not self._redis_client:
            try:
                self._redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                self._redis_client.ping()
                self._initialized = True
                logger.info("Redis connection established for rate limiting")
            except Exception as e:
                logger.error(f"Failed to connect to Redis for rate limiting: {e}")
                # Fallback to in-memory storage (not recommended for production)
                self._redis_client = FallbackMemoryStorage()
                logger.warning("Using in-memory fallback for rate limiting (not recommended for production)")
        
        return self._redis_client
    
    def get_user_tier(self, user=None) -> RateLimitTier:
        """Determine user's rate limit tier."""
        if user is None:
            user = current_user
        
        if not user or not user.is_authenticated:
            return RateLimitTier.FREE
        
        if hasattr(user, 'is_admin') and user.is_admin:
            return RateLimitTier.ADMIN
        
        # TODO: Add premium tier logic based on user subscription
        # if hasattr(user, 'is_premium') and user.is_premium:
        #     return RateLimitTier.PREMIUM
        
        return RateLimitTier.FREE
    
    def get_identifier(self, strategy: RateLimitStrategy, endpoint: str = None) -> str:
        """Get rate limit identifier based on strategy."""
        if strategy == RateLimitStrategy.PER_USER:
            if current_user.is_authenticated:
                return f"user:{current_user.id}"
            else:
                return f"ip:{request.remote_addr}"
        
        elif strategy == RateLimitStrategy.PER_IP:
            return f"ip:{request.remote_addr}"
        
        elif strategy == RateLimitStrategy.PER_ENDPOINT:
            identifier = f"endpoint:{endpoint}"
            if current_user.is_authenticated:
                identifier += f":user:{current_user.id}"
            else:
                identifier += f":ip:{request.remote_addr}"
            return identifier
        
        elif strategy == RateLimitStrategy.GLOBAL:
            return "global"
        
        else:
            return f"unknown:{request.remote_addr}"
    
    def check_rate_limit(self, endpoint: str = None) -> RateLimitResult:
        """Check rate limit for current request."""
        if not endpoint:
            endpoint = request.endpoint or request.path
        
        # Check bypass patterns
        import re
        for pattern in self.bypass_patterns:
            if re.match(pattern, request.path):
                return RateLimitResult(
                    allowed=True,
                    limit=999999,
                    remaining=999999,
                    reset_time=int((datetime.now() + timedelta(hours=1)).timestamp())
                )
        
        user_tier = self.get_user_tier()
        
        # Get applicable rules for user tier
        applicable_rules = self._get_applicable_rules(user_tier, endpoint)
        
        # Check each rule and return the most restrictive result
        most_restrictive = None
        
        for rule in applicable_rules:
            # Check if admin should bypass this rule
            if rule.bypass_admin and user_tier == RateLimitTier.ADMIN:
                continue
            
            result = self._check_single_rule(rule, endpoint)
            
            if not result.allowed:
                return result
            
            # Track most restrictive allowed rule for headers
            if most_restrictive is None or result.remaining < most_restrictive.remaining:
                most_restrictive = result
        
        return most_restrictive or RateLimitResult(
            allowed=True,
            limit=1000,
            remaining=1000,
            reset_time=int((datetime.now() + timedelta(hours=1)).timestamp()),
            tier=user_tier
        )
    
    def _get_applicable_rules(self, tier: RateLimitTier, endpoint: str) -> List[RateLimitRule]:
        """Get applicable rate limit rules for tier and endpoint."""
        rules = []
        
        # Add default rules for tier
        for strategy in [RateLimitStrategy.PER_USER, RateLimitStrategy.PER_IP, RateLimitStrategy.PER_ENDPOINT]:
            tier_rules = self.default_rules.get((tier, strategy), [])
            for rule in tier_rules:
                if rule.strategy == RateLimitStrategy.PER_ENDPOINT:
                    # Check if endpoint matches pattern
                    if rule.endpoint_pattern:
                        import re
                        if re.search(rule.endpoint_pattern, endpoint):
                            rules.append(rule)
                    else:
                        rules.append(rule)
                else:
                    rules.append(rule)
        
        # Add custom rules
        custom_rules = self.custom_rules.get(endpoint, [])
        rules.extend(custom_rules)
        
        return rules
    
    def _check_single_rule(self, rule: RateLimitRule, endpoint: str) -> RateLimitResult:
        """Check a single rate limit rule."""
        identifier = self.get_identifier(rule.strategy, endpoint)
        key = f"rate_limit:{identifier}:{rule.window_seconds}"
        
        try:
            # Get current count and window info
            pipe = self.redis_client.pipeline()
            pipe.get(key)
            pipe.ttl(key)
            current_count, ttl = pipe.execute()
            
            current_count = int(current_count or 0)
            
            # Check if limit exceeded
            if current_count >= rule.limit:
                reset_time = int(datetime.now().timestamp()) + max(ttl, 0)
                return RateLimitResult(
                    allowed=False,
                    limit=rule.limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=max(ttl, 1),
                    tier=rule.tier
                )
            
            # Increment counter
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, rule.window_seconds)
            new_count, _ = pipe.execute()
            new_count = int(new_count)
            
            # Calculate reset time
            if ttl <= 0:
                reset_time = int((datetime.now() + timedelta(seconds=rule.window_seconds)).timestamp())
            else:
                reset_time = int(datetime.now().timestamp()) + ttl
            
            # Check soft limit warning
            warning = False
            if rule.soft_limit and new_count >= rule.soft_limit:
                warning = True
                logger.warning(f"Rate limit soft threshold reached for {identifier}: {new_count}/{rule.limit}")
            
            return RateLimitResult(
                allowed=True,
                limit=rule.limit,
                remaining=max(0, rule.limit - new_count),
                reset_time=reset_time,
                tier=rule.tier,
                warning=warning
            )
        
        except Exception as e:
            logger.error(f"Error checking rate limit for {identifier}: {e}")
            # Fail open - allow request if Redis is down
            return RateLimitResult(
                allowed=True,
                limit=rule.limit,
                remaining=rule.limit,
                reset_time=int((datetime.now() + timedelta(seconds=rule.window_seconds)).timestamp()),
                tier=rule.tier
            )
    
    def add_custom_rule(self, endpoint: str, rule: RateLimitRule):
        """Add custom rate limit rule for specific endpoint."""
        if endpoint not in self.custom_rules:
            self.custom_rules[endpoint] = []
        self.custom_rules[endpoint].append(rule)
    
    def get_rate_limit_status(self, user=None, endpoint: str = None) -> Dict[str, Any]:
        """Get current rate limit status for debugging."""
        if user is None:
            user = current_user
        
        tier = self.get_user_tier(user)
        status = {
            'tier': tier.value,
            'limits': {},
            'redis_connected': self._initialized
        }
        
        # Get status for each strategy
        for strategy in RateLimitStrategy:
            identifier = self.get_identifier(strategy, endpoint or "/api/test")
            key = f"rate_limit:{identifier}:3600"  # Check hourly limit
            
            try:
                current_count = int(self.redis_client.get(key) or 0)
                ttl = self.redis_client.ttl(key)
                
                status['limits'][strategy.value] = {
                    'current_count': current_count,
                    'reset_in_seconds': max(ttl, 0)
                }
            except Exception as e:
                status['limits'][strategy.value] = {
                    'error': str(e)
                }
        
        return status
    
    def reset_user_limits(self, user_id: int, strategy: RateLimitStrategy = None):
        """Reset rate limits for a specific user (admin function)."""
        try:
            if strategy:
                strategies = [strategy]
            else:
                strategies = list(RateLimitStrategy)
            
            for strat in strategies:
                identifier = f"user:{user_id}" if strat == RateLimitStrategy.PER_USER else f"ip:*"
                pattern = f"rate_limit:{identifier}:*"
                
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    logger.info(f"Reset rate limits for user {user_id}, strategy {strat.value}")
        
        except Exception as e:
            logger.error(f"Error resetting rate limits for user {user_id}: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics for monitoring."""
        try:
            # Get all rate limit keys
            keys = self.redis_client.keys("rate_limit:*")
            
            metrics = {
                'total_active_limits': len(keys),
                'by_strategy': {},
                'by_tier': {},
                'top_consumers': []
            }
            
            # Analyze keys for patterns
            strategy_counts = {}
            for key in keys:
                parts = key.split(':')
                if len(parts) >= 3:
                    strategy_type = parts[1].split(':')[0]  # user, ip, endpoint, global
                    strategy_counts[strategy_type] = strategy_counts.get(strategy_type, 0) + 1
            
            metrics['by_strategy'] = strategy_counts
            
            return metrics
        
        except Exception as e:
            logger.error(f"Error getting rate limit metrics: {e}")
            return {'error': str(e)}


class FallbackMemoryStorage:
    """Fallback in-memory storage when Redis is unavailable."""
    
    def __init__(self):
        self._storage = {}
        self._expiry = {}
    
    def get(self, key):
        """Get value with expiry check."""
        if key in self._expiry:
            if datetime.now() > self._expiry[key]:
                del self._storage[key]
                del self._expiry[key]
                return None
        return self._storage.get(key)
    
    def incr(self, key):
        """Increment value."""
        current = int(self.get(key) or 0)
        self._storage[key] = current + 1
        return self._storage[key]
    
    def expire(self, key, seconds):
        """Set expiration."""
        self._expiry[key] = datetime.now() + timedelta(seconds=seconds)
    
    def ttl(self, key):
        """Get time to live."""
        if key in self._expiry:
            remaining = (self._expiry[key] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return -1
    
    def pipeline(self):
        """Mock pipeline."""
        return MockPipeline(self)
    
    def keys(self, pattern):
        """Mock keys."""
        import re
        pattern_regex = pattern.replace('*', '.*')
        return [k for k in self._storage.keys() if re.match(pattern_regex, k)]
    
    def delete(self, *keys):
        """Delete keys."""
        for key in keys:
            self._storage.pop(key, None)
            self._expiry.pop(key, None)


class MockPipeline:
    """Mock Redis pipeline for fallback storage."""
    
    def __init__(self, storage):
        self.storage = storage
        self.commands = []
    
    def get(self, key):
        self.commands.append(('get', key))
        return self
    
    def incr(self, key):
        self.commands.append(('incr', key))
        return self
    
    def expire(self, key, seconds):
        self.commands.append(('expire', key, seconds))
        return self
    
    def ttl(self, key):
        self.commands.append(('ttl', key))
        return self
    
    def execute(self):
        results = []
        for cmd in self.commands:
            if cmd[0] == 'get':
                results.append(self.storage.get(cmd[1]))
            elif cmd[0] == 'incr':
                results.append(self.storage.incr(cmd[1]))
            elif cmd[0] == 'expire':
                results.append(self.storage.expire(cmd[1], cmd[2]))
            elif cmd[0] == 'ttl':
                results.append(self.storage.ttl(cmd[1]))
        self.commands = []
        return results


# Global rate limiter instance
rate_limiter = RateLimiterService()