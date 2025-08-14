"""
Advanced Caching Service for Performance Optimization
Provides multi-level caching with Redis, memory, and database-level optimizations.
"""

import os
import json
import hashlib
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import threading
import time

logger = logging.getLogger(__name__)

# Try to import Redis, fall back to memory cache if unavailable
try:
    import redis
    from redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, using memory cache only")


class CacheLevel(Enum):
    """Cache level enumeration."""
    MEMORY = "memory"
    REDIS = "redis" 
    DATABASE = "database"
    HYBRID = "hybrid"


class CacheStrategy(Enum):
    """Cache strategy enumeration."""
    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    READ_THROUGH = "read_through"


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    operations: int = 0
    total_time_ms: float = 0.0
    memory_usage_bytes: int = 0
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
    
    @property
    def avg_operation_time_ms(self) -> float:
        """Calculate average operation time."""
        return (self.total_time_ms / self.operations) if self.operations > 0 else 0.0


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    level: CacheLevel = CacheLevel.HYBRID
    strategy: CacheStrategy = CacheStrategy.LRU
    default_ttl_seconds: int = 3600
    max_memory_items: int = 1000
    max_memory_size_mb: float = 100.0
    redis_url: Optional[str] = None
    key_prefix: str = "vertigo_cache"
    compression_enabled: bool = True
    serialization_format: str = "json"  # json, pickle, msgpack
    background_refresh: bool = True
    cluster_mode: bool = False


class MemoryCache:
    """High-performance in-memory cache implementation."""
    
    def __init__(self, max_items: int = 1000, max_size_mb: float = 100.0):
        """Initialize memory cache."""
        self.max_items = max_items
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, float] = {}
        self.access_counts: Dict[str, int] = {}
        self.lock = threading.RLock()
        self.current_size = 0
    
    def get(self, key: str) -> Any:
        """Get item from memory cache."""
        with self.lock:
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            
            # Check TTL
            if item.get('expires_at') and datetime.now() > item['expires_at']:
                self._remove_key(key)
                return None
            
            # Update access statistics
            self.access_times[key] = time.time()
            self.access_counts[key] = self.access_counts.get(key, 0) + 1
            
            return item['value']
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set item in memory cache."""
        with self.lock:
            # Calculate item size
            try:
                item_size = len(pickle.dumps(value))
            except Exception:
                item_size = 1024  # Estimate
            
            # Evict items if necessary
            while (len(self.cache) >= self.max_items or 
                   self.current_size + item_size > self.max_size_bytes):
                if not self._evict_one():
                    break
            
            # Calculate expiration
            expires_at = None
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
            # Store item
            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'size': item_size,
                'created_at': datetime.now()
            }
            
            self.access_times[key] = time.time()
            self.access_counts[key] = 1
            self.current_size += item_size
            
            return True
    
    def delete(self, key: str) -> bool:
        """Delete item from memory cache."""
        with self.lock:
            return self._remove_key(key)
    
    def clear(self) -> None:
        """Clear all items from memory cache."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.access_counts.clear()
            self.current_size = 0
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self.lock:
            return list(self.cache.keys())
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                'items': len(self.cache),
                'max_items': self.max_items,
                'size_bytes': self.current_size,
                'max_size_bytes': self.max_size_bytes,
                'utilization': len(self.cache) / self.max_items,
                'size_utilization': self.current_size / self.max_size_bytes
            }
    
    def _remove_key(self, key: str) -> bool:
        """Remove key from cache."""
        if key in self.cache:
            item_size = self.cache[key]['size']
            del self.cache[key]
            self.access_times.pop(key, None)
            self.access_counts.pop(key, None)
            self.current_size -= item_size
            return True
        return False
    
    def _evict_one(self) -> bool:
        """Evict one item using LRU strategy."""
        if not self.cache:
            return False
        
        # Find least recently used item
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        return self._remove_key(oldest_key)


class RedisCache:
    """Redis-based distributed cache implementation."""
    
    def __init__(self, redis_url: str, key_prefix: str = "vertigo"):
        """Initialize Redis cache."""
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis not available")
        
        self.redis_client = redis.from_url(redis_url)
        self.key_prefix = key_prefix
        self.compression_enabled = True
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info(f"Connected to Redis: {redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.key_prefix}:{key}"
    
    def get(self, key: str) -> Any:
        """Get item from Redis cache."""
        try:
            redis_key = self._make_key(key)
            data = self.redis_client.get(redis_key)
            
            if data is None:
                return None
            
            # Deserialize data
            return self._deserialize(data)
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set item in Redis cache."""
        try:
            redis_key = self._make_key(key)
            serialized_data = self._serialize(value)
            
            if ttl_seconds:
                result = self.redis_client.setex(redis_key, ttl_seconds, serialized_data)
            else:
                result = self.redis_client.set(redis_key, serialized_data)
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete item from Redis cache."""
        try:
            redis_key = self._make_key(key)
            result = self.redis_client.delete(redis_key)
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def clear(self, pattern: str = "*") -> int:
        """Clear items matching pattern."""
        try:
            pattern_key = self._make_key(pattern)
            keys = self.redis_client.keys(pattern_key)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
            
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return 0
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern."""
        try:
            pattern_key = self._make_key(pattern)
            redis_keys = self.redis_client.keys(pattern_key)
            
            # Remove prefix from keys
            prefix_len = len(self.key_prefix) + 1
            return [key.decode().replace(self.key_prefix + ":", "") for key in redis_keys]
            
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []
    
    def stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        try:
            info = self.redis_client.info()
            return {
                'connected': True,
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'connected_clients': info.get('connected_clients', 0),
                'uptime_in_seconds': info.get('uptime_in_seconds', 0)
            }
            
        except Exception as e:
            logger.error(f"Redis stats error: {e}")
            return {'connected': False, 'error': str(e)}
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            if isinstance(value, (dict, list)):
                data = json.dumps(value).encode()
            else:
                data = pickle.dumps(value)
            
            # Optional compression
            if self.compression_enabled and len(data) > 1024:
                try:
                    import zlib
                    data = zlib.compress(data)
                except ImportError:
                    pass
            
            return data
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            return b""
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try decompression
            if self.compression_enabled:
                try:
                    import zlib
                    data = zlib.decompress(data)
                except (ImportError, zlib.error):
                    pass
            
            # Try JSON first, then pickle
            try:
                return json.loads(data.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            return None


class CacheService:
    """Multi-level cache service with performance optimization."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache service."""
        self.config = config or CacheConfig()
        self.metrics = CacheMetrics()
        
        # Initialize cache layers
        self.memory_cache = MemoryCache(
            max_items=self.config.max_memory_items,
            max_size_mb=self.config.max_memory_size_mb
        )
        
        self.redis_cache = None
        if REDIS_AVAILABLE and self.config.redis_url:
            try:
                self.redis_cache = RedisCache(
                    redis_url=self.config.redis_url,
                    key_prefix=self.config.key_prefix
                )
            except Exception as e:
                logger.warning(f"Redis cache initialization failed: {e}")
        
        # Background refresh thread
        self.refresh_thread = None
        self.refresh_stop_event = threading.Event()
        
        if self.config.background_refresh:
            self.start_background_refresh()
        
        logger.info(f"CacheService initialized with level: {self.config.level.value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get item from cache with multi-level fallback."""
        start_time = time.time()
        
        try:
            # Try memory cache first
            if self.config.level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                value = self.memory_cache.get(key)
                if value is not None:
                    self._record_hit(time.time() - start_time)
                    return value
            
            # Try Redis cache
            if self.redis_cache and self.config.level in [CacheLevel.REDIS, CacheLevel.HYBRID]:
                value = self.redis_cache.get(key)
                if value is not None:
                    # Populate memory cache
                    if self.config.level == CacheLevel.HYBRID:
                        self.memory_cache.set(key, value, self.config.default_ttl_seconds)
                    
                    self._record_hit(time.time() - start_time)
                    return value
            
            # Cache miss
            self._record_miss(time.time() - start_time)
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self._record_miss(time.time() - start_time)
            return default
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set item in cache with multi-level storage."""
        start_time = time.time()
        ttl = ttl_seconds or self.config.default_ttl_seconds
        
        try:
            success = False
            
            # Store in memory cache
            if self.config.level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                success = self.memory_cache.set(key, value, ttl) or success
            
            # Store in Redis cache
            if self.redis_cache and self.config.level in [CacheLevel.REDIS, CacheLevel.HYBRID]:
                success = self.redis_cache.set(key, value, ttl) or success
            
            self._record_operation(time.time() - start_time)
            return success
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self._record_operation(time.time() - start_time)
            return False
    
    def delete(self, key: str) -> bool:
        """Delete item from all cache levels."""
        start_time = time.time()
        
        try:
            success = False
            
            # Delete from memory cache
            if self.config.level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
                success = self.memory_cache.delete(key) or success
            
            # Delete from Redis cache
            if self.redis_cache and self.config.level in [CacheLevel.REDIS, CacheLevel.HYBRID]:
                success = self.redis_cache.delete(key) or success
            
            self._record_operation(time.time() - start_time)
            return success
            
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            self._record_operation(time.time() - start_time)
            return False
    
    def clear(self, pattern: str = "*") -> bool:
        """Clear cache items matching pattern."""
        try:
            # Clear memory cache
            if pattern == "*":
                self.memory_cache.clear()
            else:
                # Pattern-based clearing for memory cache
                keys_to_delete = [k for k in self.memory_cache.keys() if self._match_pattern(k, pattern)]
                for key in keys_to_delete:
                    self.memory_cache.delete(key)
            
            # Clear Redis cache
            if self.redis_cache:
                self.redis_cache.clear(pattern)
            
            return True
            
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_or_set(self, key: str, fetch_func: Callable[[], Any], ttl_seconds: Optional[int] = None) -> Any:
        """Get item from cache or fetch and store if not found."""
        # Try to get from cache first
        value = self.get(key)
        if value is not None:
            return value
        
        # Fetch value
        try:
            value = fetch_func()
            if value is not None:
                self.set(key, value, ttl_seconds)
            return value
            
        except Exception as e:
            logger.error(f"Cache fetch function error: {e}")
            return None
    
    def invalidate_tag(self, tag: str) -> int:
        """Invalidate all cache items with specific tag."""
        pattern = f"*:tag:{tag}:*"
        
        count = 0
        
        # Invalidate from memory cache
        if self.config.level in [CacheLevel.MEMORY, CacheLevel.HYBRID]:
            keys_to_delete = [k for k in self.memory_cache.keys() if tag in k]
            for key in keys_to_delete:
                if self.memory_cache.delete(key):
                    count += 1
        
        # Invalidate from Redis cache
        if self.redis_cache and self.config.level in [CacheLevel.REDIS, CacheLevel.HYBRID]:
            count += self.redis_cache.clear(pattern)
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {
            'config': {
                'level': self.config.level.value,
                'strategy': self.config.strategy.value,
                'default_ttl': self.config.default_ttl_seconds,
                'max_memory_items': self.config.max_memory_items,
                'max_memory_size_mb': self.config.max_memory_size_mb
            },
            'performance': {
                'hits': self.metrics.hits,
                'misses': self.metrics.misses,
                'hit_ratio': self.metrics.hit_ratio,
                'operations': self.metrics.operations,
                'avg_operation_time_ms': self.metrics.avg_operation_time_ms,
                'evictions': self.metrics.evictions
            },
            'memory_cache': self.memory_cache.stats(),
            'redis_cache': self.redis_cache.stats() if self.redis_cache else None
        }
        
        return stats
    
    def start_background_refresh(self) -> None:
        """Start background refresh thread."""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return
        
        self.refresh_thread = threading.Thread(target=self._background_refresh_worker)
        self.refresh_thread.daemon = True
        self.refresh_thread.start()
        
        logger.info("Started background refresh thread")
    
    def stop_background_refresh(self) -> None:
        """Stop background refresh thread."""
        if self.refresh_thread:
            self.refresh_stop_event.set()
            self.refresh_thread.join(timeout=5)
            logger.info("Stopped background refresh thread")
    
    def _record_hit(self, duration_ms: float) -> None:
        """Record cache hit."""
        self.metrics.hits += 1
        self.metrics.operations += 1
        self.metrics.total_time_ms += duration_ms * 1000
    
    def _record_miss(self, duration_ms: float) -> None:
        """Record cache miss."""
        self.metrics.misses += 1
        self.metrics.operations += 1
        self.metrics.total_time_ms += duration_ms * 1000
    
    def _record_operation(self, duration_ms: float) -> None:
        """Record cache operation."""
        self.metrics.operations += 1
        self.metrics.total_time_ms += duration_ms * 1000
    
    def _match_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching."""
        if pattern == "*":
            return True
        return pattern.replace("*", "") in key
    
    def _background_refresh_worker(self) -> None:
        """Background worker for cache refresh."""
        while not self.refresh_stop_event.is_set():
            try:
                # Perform background maintenance tasks
                self._cleanup_expired_items()
                self._update_metrics()
                
                # Sleep for 60 seconds
                if self.refresh_stop_event.wait(60):
                    break
                    
            except Exception as e:
                logger.error(f"Background refresh error: {e}")
                time.sleep(60)
    
    def _cleanup_expired_items(self) -> None:
        """Clean up expired cache items."""
        # Memory cache cleanup is handled automatically
        pass
    
    def _update_metrics(self) -> None:
        """Update cache metrics."""
        memory_stats = self.memory_cache.stats()
        self.metrics.memory_usage_bytes = memory_stats['size_bytes']


def cached(
    key_func: Optional[Callable] = None,
    ttl_seconds: int = 3600,
    cache_service: Optional[CacheService] = None,
    tags: Optional[List[str]] = None
):
    """Decorator for caching function results."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use global cache service if none provided
            nonlocal cache_service
            if cache_service is None:
                cache_service = default_cache_service
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Generate key from function name and arguments
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
                
                # Add tags if provided
                if tags:
                    cache_key = f"{'_'.join(tags)}:{cache_key}"
            
            # Try to get from cache
            result = cache_service.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_service.set(cache_key, result, ttl_seconds)
            
            return result
        
        return wrapper
    return decorator


# Global cache service instance
cache_config = CacheConfig(
    level=CacheLevel.HYBRID,
    redis_url=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    default_ttl_seconds=3600,
    max_memory_items=2000,
    max_memory_size_mb=200.0,
    key_prefix="vertigo_cache",
    background_refresh=True
)

default_cache_service = CacheService(cache_config)