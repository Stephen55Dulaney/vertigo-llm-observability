"""
Cache management routes for performance optimization.
"""

from flask import render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from app.blueprints.performance import performance_bp
from app.services.cache_service import default_cache_service, CacheLevel, CacheStrategy
from app.services.performance_optimizer import performance_optimizer
import logging

logger = logging.getLogger(__name__)


@performance_bp.route('/cache')
@login_required
def cache_dashboard():
    """Cache performance dashboard."""
    try:
        cache_stats = default_cache_service.get_stats()
        return render_template('performance/cache.html', cache_stats=cache_stats)
        
    except Exception as e:
        logger.error(f"Error loading cache dashboard: {e}")
        return render_template('error.html', error="Failed to load cache dashboard"), 500


@performance_bp.route('/api/cache/stats')
@login_required
def get_cache_stats():
    """Get detailed cache statistics."""
    try:
        stats = default_cache_service.get_stats()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """Clear cache with optional pattern matching."""
    try:
        data = request.get_json() or {}
        pattern = data.get('pattern', '*')
        
        # Clear cache
        success = default_cache_service.clear(pattern)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Cache cleared successfully (pattern: {pattern})"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to clear cache"
            }), 400
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/invalidate', methods=['POST'])
@login_required
def invalidate_cache_tag():
    """Invalidate cache by tag."""
    try:
        data = request.get_json() or {}
        tag = data.get('tag')
        
        if not tag:
            return jsonify({
                "success": False,
                "error": "Tag parameter is required"
            }), 400
        
        # Invalidate tagged items
        count = default_cache_service.invalidate_tag(tag)
        
        return jsonify({
            "success": True,
            "invalidated_count": count,
            "message": f"Invalidated {count} items with tag: {tag}"
        })
        
    except Exception as e:
        logger.error(f"Error invalidating cache tag: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/keys')
@login_required
def get_cache_keys():
    """Get cache keys with optional pattern matching."""
    try:
        pattern = request.args.get('pattern', '*')
        limit = request.args.get('limit', 100, type=int)
        
        # Get keys from memory cache
        memory_keys = default_cache_service.memory_cache.keys()
        
        # Get keys from Redis cache if available
        redis_keys = []
        if default_cache_service.redis_cache:
            redis_keys = default_cache_service.redis_cache.keys(pattern)
        
        # Apply pattern filtering for memory cache
        if pattern != '*':
            pattern_clean = pattern.replace('*', '')
            memory_keys = [k for k in memory_keys if pattern_clean in k]
        
        # Limit results
        memory_keys = memory_keys[:limit]
        redis_keys = redis_keys[:limit]
        
        return jsonify({
            "success": True,
            "memory_keys": memory_keys,
            "redis_keys": redis_keys,
            "total_keys": len(memory_keys) + len(redis_keys)
        })
        
    except Exception as e:
        logger.error(f"Error getting cache keys: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/get/<key>')
@login_required
def get_cache_item(key):
    """Get specific cache item by key."""
    try:
        value = default_cache_service.get(key)
        
        if value is not None:
            return jsonify({
                "success": True,
                "key": key,
                "value": value,
                "found": True
            })
        else:
            return jsonify({
                "success": True,
                "key": key,
                "value": None,
                "found": False,
                "message": "Key not found in cache"
            })
        
    except Exception as e:
        logger.error(f"Error getting cache item: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/set', methods=['POST'])
@login_required
def set_cache_item():
    """Set cache item."""
    try:
        data = request.get_json()
        
        if not data or 'key' not in data or 'value' not in data:
            return jsonify({
                "success": False,
                "error": "Key and value are required"
            }), 400
        
        key = data['key']
        value = data['value']
        ttl_seconds = data.get('ttl_seconds')
        
        # Set cache item
        success = default_cache_service.set(key, value, ttl_seconds)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Cache item set successfully: {key}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to set cache item"
            }), 400
        
    except Exception as e:
        logger.error(f"Error setting cache item: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/delete/<key>', methods=['DELETE'])
@login_required
def delete_cache_item(key):
    """Delete specific cache item."""
    try:
        success = default_cache_service.delete(key)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Cache item deleted successfully: {key}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to delete cache item or item not found"
            }), 400
        
    except Exception as e:
        logger.error(f"Error deleting cache item: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/config', methods=['GET', 'POST'])
@login_required
def cache_config():
    """Get or update cache configuration."""
    if request.method == 'GET':
        try:
            config = {
                'level': default_cache_service.config.level.value,
                'strategy': default_cache_service.config.strategy.value,
                'default_ttl_seconds': default_cache_service.config.default_ttl_seconds,
                'max_memory_items': default_cache_service.config.max_memory_items,
                'max_memory_size_mb': default_cache_service.config.max_memory_size_mb,
                'key_prefix': default_cache_service.config.key_prefix,
                'compression_enabled': default_cache_service.config.compression_enabled,
                'background_refresh': default_cache_service.config.background_refresh
            }
            
            return jsonify({
                "success": True,
                "config": config
            })
            
        except Exception as e:
            logger.error(f"Error getting cache config: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    else:  # POST
        try:
            data = request.get_json() or {}
            
            # Update cache configuration
            if 'default_ttl_seconds' in data:
                default_cache_service.config.default_ttl_seconds = max(60, min(data['default_ttl_seconds'], 86400))
            
            if 'max_memory_items' in data:
                default_cache_service.config.max_memory_items = max(100, min(data['max_memory_items'], 10000))
            
            if 'max_memory_size_mb' in data:
                default_cache_service.config.max_memory_size_mb = max(10, min(data['max_memory_size_mb'], 1000))
            
            if 'compression_enabled' in data:
                default_cache_service.config.compression_enabled = bool(data['compression_enabled'])
            
            return jsonify({
                "success": True,
                "message": "Cache configuration updated successfully"
            })
            
        except Exception as e:
            logger.error(f"Error updating cache config: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


@performance_bp.route('/api/cache/optimize', methods=['POST'])
@login_required
def optimize_cache():
    """Optimize cache performance based on current usage patterns."""
    try:
        # Get current cache statistics
        stats = default_cache_service.get_stats()
        
        optimizations_applied = []
        
        # Check hit ratio and adjust TTL if needed
        hit_ratio = stats['performance']['hit_ratio']
        if hit_ratio < 0.7:
            # Increase TTL to improve hit ratio
            old_ttl = default_cache_service.config.default_ttl_seconds
            new_ttl = min(old_ttl * 1.5, 7200)  # Max 2 hours
            default_cache_service.config.default_ttl_seconds = int(new_ttl)
            optimizations_applied.append(f"Increased default TTL from {old_ttl}s to {new_ttl}s")
        
        # Check memory utilization and adjust if needed
        memory_utilization = stats['memory_cache']['utilization']
        if memory_utilization > 0.9:
            # Increase memory cache size
            old_max_items = default_cache_service.config.max_memory_items
            new_max_items = min(old_max_items * 1.2, 5000)
            default_cache_service.config.max_memory_items = int(new_max_items)
            optimizations_applied.append(f"Increased max memory items from {old_max_items} to {new_max_items}")
        
        # Apply general performance optimizations
        performance_results = performance_optimizer.auto_optimize()
        if performance_results.get('applied'):
            optimizations_applied.extend(performance_results['applied'])
        
        return jsonify({
            "success": True,
            "optimizations_applied": optimizations_applied,
            "message": f"Applied {len(optimizations_applied)} cache optimizations"
        })
        
    except Exception as e:
        logger.error(f"Error optimizing cache: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@performance_bp.route('/api/cache/benchmark', methods=['POST'])
@login_required
def benchmark_cache():
    """Run cache performance benchmark."""
    try:
        data = request.get_json() or {}
        iterations = min(data.get('iterations', 1000), 10000)  # Max 10k iterations
        
        import time
        import random
        import string
        
        # Benchmark cache performance
        results = {
            'iterations': iterations,
            'set_operations': {'times': [], 'total_time': 0},
            'get_operations': {'times': [], 'total_time': 0},
            'hit_operations': {'times': [], 'total_time': 0},
            'miss_operations': {'times': [], 'total_time': 0}
        }
        
        # Test data
        test_keys = [f"benchmark_key_{i}" for i in range(iterations)]
        test_values = [''.join(random.choices(string.ascii_letters, k=100)) for _ in range(iterations)]
        
        # Benchmark SET operations
        start_time = time.time()
        for i in range(iterations):
            op_start = time.time()
            default_cache_service.set(test_keys[i], test_values[i], 300)
            op_time = (time.time() - op_start) * 1000
            results['set_operations']['times'].append(op_time)
        results['set_operations']['total_time'] = (time.time() - start_time) * 1000
        
        # Benchmark GET operations (hits)
        start_time = time.time()
        for i in range(min(iterations, 500)):  # Test subset for hits
            op_start = time.time()
            value = default_cache_service.get(test_keys[i])
            op_time = (time.time() - op_start) * 1000
            results['hit_operations']['times'].append(op_time)
        results['hit_operations']['total_time'] = (time.time() - start_time) * 1000
        
        # Benchmark GET operations (misses)
        miss_keys = [f"nonexistent_key_{i}" for i in range(min(iterations, 500))]
        start_time = time.time()
        for key in miss_keys:
            op_start = time.time()
            value = default_cache_service.get(key)
            op_time = (time.time() - op_start) * 1000
            results['miss_operations']['times'].append(op_time)
        results['miss_operations']['total_time'] = (time.time() - start_time) * 1000
        
        # Calculate statistics
        for operation in ['set_operations', 'hit_operations', 'miss_operations']:
            times = results[operation]['times']
            if times:
                results[operation]['avg_time_ms'] = sum(times) / len(times)
                results[operation]['min_time_ms'] = min(times)
                results[operation]['max_time_ms'] = max(times)
                results[operation]['ops_per_second'] = len(times) / (results[operation]['total_time'] / 1000)
        
        # Clean up test data
        for key in test_keys:
            default_cache_service.delete(key)
        
        return jsonify({
            "success": True,
            "benchmark_results": results,
            "summary": {
                "total_operations": iterations * 2,
                "avg_set_time_ms": results['set_operations'].get('avg_time_ms', 0),
                "avg_hit_time_ms": results['hit_operations'].get('avg_time_ms', 0),
                "avg_miss_time_ms": results['miss_operations'].get('avg_time_ms', 0),
                "set_ops_per_second": results['set_operations'].get('ops_per_second', 0),
                "get_ops_per_second": results['hit_operations'].get('ops_per_second', 0)
            }
        })
        
    except Exception as e:
        logger.error(f"Error running cache benchmark: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500