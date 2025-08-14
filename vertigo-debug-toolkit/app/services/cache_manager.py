"""
Cache Manager for Performance Optimization
Provides Redis-based caching and in-memory fallback for live data integration.
"""

import os
import json
import pickle
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Callable
from functools import wraps
import threading
import time

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = {}
        self.access_times = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key not in self.cache:
                return None
            
            value, expiry = self.cache[key]
            
            # Check if expired
            if expiry and datetime.utcnow() > expiry:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return None
            
            # Update access time
            self.access_times[key] = datetime.utcnow()
            return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        with self.lock:
            # Calculate expiry
            ttl = ttl or self.default_ttl
            expiry = datetime.utcnow() + timedelta(seconds=ttl) if ttl > 0 else None
            
            # Add to cache
            self.cache[key] = (value, expiry)
            self.access_times[key] = datetime.utcnow()
            
            # Enforce size limit
            if len(self.cache) > self.max_size:
                self._evict_lru()
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cached items."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def _evict_lru(self) -> None:
        """Evict least recently used items."""
        if not self.access_times:
            return
        
        # Find LRU key
        lru_key = min(self.access_times, key=self.access_times.get)
        
        # Remove from cache
        if lru_key in self.cache:
            del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_items = len(self.cache)
            expired_items = 0
            
            current_time = datetime.utcnow()
            for value, expiry in self.cache.values():
                if expiry and current_time > expiry:
                    expired_items += 1
            
            return {
                'total_items': total_items,
                'expired_items': expired_items,
                'active_items': total_items - expired_items,
                'max_size': self.max_size,
                'utilization': round((total_items / self.max_size) * 100, 2)
            }

class CacheManager:
    """
    Unified cache manager supporting Redis and in-memory fallback.
    
    Features:
    - Automatic Redis/in-memory fallback
    - TTL support
    - Compression for large objects
    - Cache warming strategies
    - Metrics and monitoring
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = InMemoryCache(max_size=2000, default_ttl=300)
        self.use_redis = False
        self.compression_threshold = 1024  # Compress objects > 1KB
        
        # Performance metrics
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'redis_errors': 0,
            'start_time': datetime.utcnow()
        }
        
        self._init_redis()
        
        # Cache prefixes for different data types
        self.prefixes = {
            'metrics': 'vertigo:metrics:',
            'traces': 'vertigo:traces:',
            'sync': 'vertigo:sync:',
            'webhook': 'vertigo:webhook:',
            'api': 'vertigo:api:'
        }
    
    def _init_redis(self):
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory cache only")
            return
        
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}. Using in-memory cache.")
            self.redis_client = None
            self.use_redis = False
    
    def get(self, key: str, cache_type: str = 'api') -> Optional[Any]:
        """Get value from cache."""
        full_key = self._build_key(key, cache_type)
        
        try:
            # Try Redis first if available
            if self.use_redis:
                try:
                    data = self.redis_client.get(full_key)
                    if data is not None:
                        self.metrics['hits'] += 1
                        return self._deserialize(data)
                except Exception as e:
                    logger.warning(f"Redis get error: {e}")
                    self.metrics['redis_errors'] += 1
            
            # Fallback to memory cache
            result = self.memory_cache.get(full_key)
            if result is not None:
                self.metrics['hits'] += 1
                return result
            
            self.metrics['misses'] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {full_key}: {e}")
            self.metrics['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300, cache_type: str = 'api') -> bool:
        """Set value in cache."""
        full_key = self._build_key(key, cache_type)
        
        try:
            # Try Redis first if available
            if self.use_redis:
                try:
                    serialized = self._serialize(value)
                    self.redis_client.setex(full_key, ttl, serialized)
                    self.metrics['sets'] += 1
                    return True
                except Exception as e:
                    logger.warning(f"Redis set error: {e}")
                    self.metrics['redis_errors'] += 1
            
            # Always set in memory cache as fallback
            self.memory_cache.set(full_key, value, ttl)
            self.metrics['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {full_key}: {e}")
            return False
    
    def delete(self, key: str, cache_type: str = 'api') -> bool:
        """Delete key from cache."""
        full_key = self._build_key(key, cache_type)
        
        try:
            deleted = False
            
            # Delete from Redis
            if self.use_redis:
                try:
                    self.redis_client.delete(full_key)
                    deleted = True
                except Exception as e:
                    logger.warning(f"Redis delete error: {e}")
                    self.metrics['redis_errors'] += 1
            
            # Delete from memory cache
            if self.memory_cache.delete(full_key):
                deleted = True
            
            if deleted:
                self.metrics['deletes'] += 1
            
            return deleted
            
        except Exception as e:
            logger.error(f"Cache delete error for key {full_key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str, cache_type: str = 'api') -> int:
        """Clear all keys matching a pattern."""
        full_pattern = self._build_key(pattern, cache_type)
        deleted_count = 0
        
        try:
            # Clear from Redis
            if self.use_redis:
                try:
                    keys = self.redis_client.keys(full_pattern)
                    if keys:
                        deleted_count += self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Redis pattern delete error: {e}")
                    self.metrics['redis_errors'] += 1
            
            # Clear from memory cache (basic pattern matching)
            memory_keys_to_delete = [
                k for k in self.memory_cache.cache.keys() 
                if full_pattern.replace('*', '') in k
            ]
            
            for key in memory_keys_to_delete:
                self.memory_cache.delete(key)
                deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache pattern clear error: {e}")
            return 0
    
    def _build_key(self, key: str, cache_type: str) -> str:
        """Build full cache key with prefix."""
        prefix = self.prefixes.get(cache_type, 'vertigo:general:')
        return f"{prefix}{key}"
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Use JSON for simple types
            if isinstance(value, (str, int, float, bool, list, dict)) and not isinstance(value, bytes):
                data = json.dumps(value, default=str).encode('utf-8')
            else:
                # Use pickle for complex objects
                data = pickle.dumps(value)
            
            # Compress if large
            if len(data) > self.compression_threshold:
                import gzip
                data = gzip.compress(data)
                data = b'GZIP:' + data
            
            return data
            
        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Check for compression
            if data.startswith(b'GZIP:'):
                import gzip
                data = gzip.decompress(data[5:])
            
            # Try JSON first
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fallback to pickle
                return pickle.loads(data)
                
        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise
    
    def warm_cache(self, warming_functions: List[Callable]) -> Dict[str, Any]:
        """Warm cache with commonly accessed data."""
        results = {}
        
        for func in warming_functions:
            try:
                start_time = time.time()
                func_name = func.__name__
                
                # Execute warming function
                func()
                
                duration = time.time() - start_time
                results[func_name] = {
                    'success': True,
                    'duration_seconds': round(duration, 3)
                }
                
                logger.info(f"Cache warming completed for {func_name} in {duration:.3f}s")
                
            except Exception as e:
                logger.error(f"Cache warming failed for {func.__name__}: {e}")
                results[func.__name__] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            total_operations = self.metrics['hits'] + self.metrics['misses']
            hit_rate = (self.metrics['hits'] / total_operations * 100) if total_operations > 0 else 0
            
            uptime_seconds = (datetime.utcnow() - self.metrics['start_time']).total_seconds()
            
            stats = {
                'cache_backend': 'redis' if self.use_redis else 'memory_only',
                'performance': {
                    'total_operations': total_operations,
                    'hits': self.metrics['hits'],
                    'misses': self.metrics['misses'],
                    'hit_rate_percent': round(hit_rate, 2),
                    'sets': self.metrics['sets'],
                    'deletes': self.metrics['deletes']
                },
                'uptime_seconds': round(uptime_seconds, 1),
                'memory_cache': self.memory_cache.stats()
            }
            
            # Add Redis stats if available
            if self.use_redis:
                try:
                    redis_info = self.redis_client.info('memory')
                    stats['redis'] = {
                        'connected': True,
                        'memory_usage_mb': round(redis_info.get('used_memory', 0) / 1024 / 1024, 2),
                        'keyspace_hits': redis_info.get('keyspace_hits', 0),
                        'keyspace_misses': redis_info.get('keyspace_misses', 0),
                        'errors': self.metrics['redis_errors']
                    }
                except Exception as e:
                    stats['redis'] = {
                        'connected': False,
                        'error': str(e),
                        'errors': self.metrics['redis_errors']
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache statistics: {e}")
            return {'error': str(e)}

# Cache decorators for easy use
def cached(ttl: int = 300, cache_type: str = 'api', key_func: Optional[Callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds
        cache_type: Cache category
        key_func: Optional function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
                
                key_string = "_".join(key_parts)
                cache_key = hashlib.md5(key_string.encode()).hexdigest()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key, cache_type)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl, cache_type)
            
            return result
        return wrapper
    return decorator

# Global cache manager instance
cache_manager = CacheManager()

# Cache warming functions
def warm_performance_metrics():
    """Warm cache with common performance metrics."""
    from app.services.langwatch_client import langwatch_client
    
    # Common time ranges
    for hours in [1, 6, 24, 168]:
        langwatch_client.get_performance_metrics(hours=hours)
        langwatch_client.get_latency_time_series(hours=hours)

def warm_sync_status():
    """Warm cache with sync status data."""
    from app.services.firestore_sync import firestore_sync_service
    firestore_sync_service.get_sync_statistics()

# Register warming functions
CACHE_WARMING_FUNCTIONS = [
    warm_performance_metrics,
    warm_sync_status
]