# Live Data Integration Architecture Guide

## Overview

This document provides the complete technical architecture for live data integration in the Vertigo Debug Toolkit. The implementation enables real-time monitoring, advanced performance analytics, and seamless data synchronization between multiple sources.

## Architecture Components

### 1. Database Schema (`migrations/001_live_data_integration.sql`)

**New Tables:**
- `performance_metrics` - Aggregated performance data with time-series support
- `sync_status` - Tracks synchronization state across data sources
- `webhook_events` - Logs all incoming webhook events with processing status
- `live_traces` - Real-time trace data from multiple sources
- `alert_rules` - Configurable alerting rules for performance monitoring
- `alert_events` - Alert event history and acknowledgments

**Key Features:**
- Comprehensive indexing for high-performance queries
- Automatic timestamp triggers for audit trails
- JSON fields for flexible metadata storage
- Built-in data retention and cleanup capabilities

### 2. Firestore Sync Service (`app/services/firestore_sync.py`)

**Class: `FirestoreSyncService`**

**Features:**
- Incremental sync from Firestore to local SQLite
- Batch processing with configurable batch sizes
- Conflict resolution and error recovery
- Comprehensive logging and monitoring
- Thread-safe operations with proper error handling

**Key Methods:**
```python
sync_traces_from_firestore(hours_back=24) -> SyncResult
force_full_sync(hours_back=168) -> SyncResult
get_sync_statistics() -> Dict[str, Any]
```

**Configuration:**
- Collection mappings for traces and meetings
- Transformers for Firestore document formats
- Configurable sync intervals and batch sizes

### 3. Webhook Handler (`app/services/webhook_handler.py`)

**Class: `WebhookHandler`**

**Security Features:**
- HMAC signature verification (SHA256/SHA1)
- Duplicate event detection
- Rate limiting and security logging
- Environment-specific security bypasses for development

**Supported Sources:**
- LangWatch webhooks
- Langfuse webhooks  
- Custom webhook formats

**Event Types:**
- `trace.created` - New trace events
- `trace.updated` - Trace modifications
- `trace.deleted` - Trace deletions
- `evaluation.completed` - Evaluation results
- `alert.triggered` - System alerts

### 4. API Endpoints (`app/blueprints/live_data/routes.py`)

**Live Metrics API:**
- `GET /live-data/api/live-metrics` - Real-time performance metrics
- `GET /live-data/api/live-traces` - Live trace data with filtering
- `GET /live-data/api/sync-status` - Synchronization status

**Webhook Endpoints:**
- `POST /live-data/webhooks/<source>` - Secure webhook receiver

**Sync Management:**
- `POST /live-data/api/sync/trigger` - Manual sync triggering (admin only)

### 5. Performance Optimization (`app/services/cache_manager.py`)

**Class: `CacheManager`**

**Multi-Tier Caching:**
- Redis primary cache (if available)
- In-memory fallback cache
- Automatic failover and recovery
- Compression for large objects

**Cache Categories:**
- `metrics` - Performance metric data
- `traces` - Trace information  
- `sync` - Synchronization status
- `webhook` - Webhook processing data
- `api` - General API responses

**Performance Features:**
- LRU eviction policies
- TTL-based expiration
- Cache warming strategies
- Comprehensive metrics and monitoring

### 6. Security Framework (`app/security/live_data_security.py`)

**Class: `LiveDataSecurity`**

**Authentication & Authorization:**
- Role-based access control
- Admin-only operations protection
- User permission validation
- Session security enhancements

**Rate Limiting:**
- Per-user API request limiting
- Webhook request rate limiting
- Admin operation throttling
- Configurable limits per endpoint

**Security Decorators:**
```python
@require_permissions(['read_performance_data'])
@require_admin()
@rate_limit('api_requests_per_minute')
@validate_webhook_source()
```

## Implementation Guide

### Phase 1: Core Infrastructure (Sprint 1)

1. **Apply Database Migrations:**
```bash
cd vertigo-debug-toolkit
python migrations/apply_migration.py
```

2. **Configure Environment Variables:**
```bash
# Add to .env file
ENABLE_LIVE_DATA=true
ENABLE_FIRESTORE_SYNC=true
GOOGLE_CLOUD_PROJECT=your-project-id
LANGWATCH_WEBHOOK_SECRET=your-webhook-secret
REDIS_URL=redis://localhost:6379/0  # Optional
```

3. **Test Core Services:**
```python
from app.services.firestore_sync import firestore_sync_service
from app.services.webhook_handler import webhook_handler

# Test Firestore connection
stats = firestore_sync_service.get_sync_statistics()
print(f"Firestore available: {stats['is_available']}")

# Test webhook processing
result = webhook_handler.process_webhook('custom', {'test': 'data'})
print(f"Webhook processed: {result['status']}")
```

### Phase 2: Webhook Integration (Sprint 2)

1. **Configure Webhook Endpoints:**
- LangWatch: `https://your-domain.com/live-data/webhooks/langwatch`
- Langfuse: `https://your-domain.com/live-data/webhooks/langfuse`
- Custom: `https://your-domain.com/live-data/webhooks/custom`

2. **Set Up Webhook Secrets:**
```bash
export LANGWATCH_WEBHOOK_SECRET="your-langwatch-secret"
export LANGFUSE_WEBHOOK_SECRET="your-langfuse-secret"
```

3. **Test Webhook Processing:**
```bash
curl -X POST https://your-domain.com/live-data/webhooks/custom \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=..." \
  -d '{"event_type":"trace.created","data":{"id":"test-123"}}'
```

### Phase 3: Performance Optimization (Sprint 3)

1. **Enable Redis Caching:**
```bash
# Install Redis
sudo apt-get install redis-server
# or
brew install redis

# Start Redis
redis-server

# Configure in .env
REDIS_URL=redis://localhost:6379/0
```

2. **Cache Warming Setup:**
```python
from app.services.cache_manager import cache_manager, CACHE_WARMING_FUNCTIONS

# Warm cache on startup
results = cache_manager.warm_cache(CACHE_WARMING_FUNCTIONS)
print(f"Cache warming results: {results}")
```

3. **Monitor Performance:**
```python
from app.services.cache_manager import cache_manager

# Get cache statistics
stats = cache_manager.get_statistics()
print(f"Cache hit rate: {stats['performance']['hit_rate_percent']}%")
```

## Deployment

### Automated Deployment:
```bash
cd vertigo-debug-toolkit
python deploy/live_data_integration_deployment.py
```

### Manual Deployment Steps:

1. **Install Dependencies:**
```bash
pip install google-cloud-firestore>=2.11.0 redis>=4.5.0 celery>=5.3.0
```

2. **Apply Database Schema:**
```bash
python migrations/apply_migration.py
```

3. **Configure Background Sync:**
```bash
# Create systemd timer (Linux)
sudo python deploy/live_data_integration_deployment.py

# Or add cron job
crontab -e
# Add: */15 * * * * cd /path/to/vertigo-debug-toolkit && python -c "from app.services.firestore_sync import firestore_sync_service; firestore_sync_service.sync_traces_from_firestore()"
```

4. **Verify Installation:**
```bash
python -c "
from app.services import firestore_sync_service, webhook_handler, cache_manager
print('Firestore:', firestore_sync_service.is_available())
print('Webhooks:', len(webhook_handler.event_handlers))
print('Cache:', cache_manager.use_redis)
"
```

## API Usage Examples

### Get Live Performance Metrics:
```bash
curl -H "Authorization: Bearer token" \
  "https://your-domain.com/live-data/api/live-metrics?hours=24&source=all"
```

### Get Live Traces with Filtering:
```bash
curl -H "Authorization: Bearer token" \
  "https://your-domain.com/live-data/api/live-traces?status=success&limit=50&model=gemini-1.5-pro"
```

### Trigger Manual Sync (Admin Only):
```bash
curl -X POST -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"sync_type":"firestore","hours_back":24,"force_full":false}' \
  "https://your-domain.com/live-data/api/sync/trigger"
```

## Monitoring & Alerting

### Health Check Endpoints:
- `/live-data/api/sync-status` - Overall system health
- `/performance/api/metrics` - Enhanced with live data
- `/health` - Basic application health

### Key Metrics to Monitor:
1. **Sync Performance:**
   - Last successful sync timestamp
   - Records processed per sync
   - Sync error rate

2. **Webhook Processing:**
   - Events received per minute
   - Processing success rate
   - Queue depth

3. **Cache Performance:**
   - Hit rate percentage
   - Memory utilization
   - Redis connection status

4. **Data Freshness:**
   - Time since last data update
   - Source availability
   - Data volume trends

## Security Considerations

### Production Security Checklist:
- [ ] HTTPS enabled for all webhook endpoints
- [ ] Webhook signature verification enabled
- [ ] Rate limiting configured for all APIs  
- [ ] Admin operations require proper authentication
- [ ] Environment variables secured (no hardcoded secrets)
- [ ] Database backups configured
- [ ] Log monitoring and alerting enabled
- [ ] Regular security updates applied

### Development vs Production:
- Development: Webhook signature verification can be disabled
- Production: All security features must be enabled
- Testing: Use in-memory databases and mock services

## Troubleshooting

### Common Issues:

1. **Firestore Connection Failed:**
   - Check Google Cloud credentials
   - Verify project ID configuration
   - Ensure Firestore API is enabled

2. **Webhook Signature Verification Failed:**
   - Verify webhook secret configuration
   - Check signature format (sha256= prefix)
   - Ensure payload is raw bytes

3. **Redis Connection Issues:**
   - Check Redis server status
   - Verify Redis URL configuration
   - Test connection with redis-cli

4. **Sync Performance Issues:**
   - Monitor batch sizes
   - Check Firestore read quotas
   - Review sync frequency settings

### Debug Commands:
```bash
# Test Firestore connection
python -c "from app.services.firestore_sync import firestore_sync_service; print(firestore_sync_service.get_sync_statistics())"

# Test webhook processing
python -c "from app.services.webhook_handler import webhook_handler; print(webhook_handler.get_webhook_statistics())"

# Check cache performance
python -c "from app.services.cache_manager import cache_manager; print(cache_manager.get_statistics())"

# Verify database schema
python migrations/apply_migration.py --verify-only
```

## Support & Maintenance

### Regular Maintenance Tasks:
1. Monitor sync performance and adjust batch sizes
2. Clean old webhook events and performance metrics
3. Update webhook secrets periodically
4. Monitor cache hit rates and adjust TTLs
5. Review security logs for anomalies

### Performance Tuning:
1. Adjust sync intervals based on data volume
2. Optimize database indexes for query patterns
3. Configure Redis memory limits appropriately
4. Implement data archival for old records

This architecture provides a robust, secure, and scalable foundation for live data integration in the Vertigo Debug Toolkit, with clear upgrade paths and comprehensive monitoring capabilities.