# 📊 Performance Benchmarking & Load Testing

This guide explains how to run load tests and interpret results for the Medication Reminder API.

## 🚀 Quick Start

### Install Locust

```bash
pip install locust
```

### Run Load Test

```bash
# Start the API first
python -m uvicorn main:app --reload

# In another terminal, run load test
locust -f tests/load_test.py --host=http://localhost:8000

# Open browser: http://localhost:8089
# - Number of users: 100
# - Spawn rate: 10 users/sec
# - Click "Start swarming"
```

---

## 📈 Test Scenarios

### Scenario 1: Normal Traffic (Baseline)

```
Users: 50
Spawn rate: 5 users/sec
Duration: 5 minutes
Expected: <200ms p95 latency
```

**Test command:**
```bash
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5 \
  --run-time=5m \
  --headless
```

### Scenario 2: Peak Traffic

```
Users: 500
Spawn rate: 25 users/sec
Duration: 10 minutes
Expected: <500ms p95 latency
```

```bash
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --users=500 \
  --spawn-rate=25 \
  --run-time=10m \
  --headless
```

### Scenario 3: Stress Test

```
Users: 2000
Spawn rate: 50 users/sec
Duration: 15 minutes
Expected: System breaks at some point
```

```bash
locust -f tests/load_test.py \
  --host=http://localhost:8000 \
  --users=2000 \
  --spawn-rate=50 \
  --run-time=15m \
  --headless
```

### Scenario 4: Spike Test

```
Gradual ramp: 0 → 100 users over 2 min
Spike: Jump to 500 users in 30 sec
Measure: Recovery time
```

---

## 📊 Key Metrics to Monitor

### 1. Response Time Percentiles

```
p50 (median):   < 100ms    ✅ Good
p95 (95th):     < 300ms    ✅ Good
p99 (99th):     < 1000ms   ⚠️ Watch
```

### 2. Request Rate

```
RPS (requests/sec):  Target: 1000+ RPS for 500 users
Throughput:          Requests per second sustained
```

### 3. Error Rate

```
Target: < 0.1% failure rate
- 5xx errors: Database issues, API crashes
- 4xx errors: Client errors (should be minimal)
```

### 4. Resource Utilization

Monitor while load testing:

```bash
# CPU usage
top -b -n 1 | grep python

# Memory
free -h

# Database connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"

# Redis memory
redis-cli info memory
```

---

## 🔍 Analyzing Results

### Export Results to CSV

```bash
# Locust automatically generates CSV:
# - stats.csv (request statistics)
# - stats_history.csv (over time)
# - failures.csv (errors)
```

### Example Results

```
Type      Name                      Requests    Min    Avg    Max    p95
GET       /medications/get_all       15000      23ms   87ms  2100ms  180ms
POST      /medications/create        5000       45ms  120ms  3200ms  280ms
GET       /reminders                 8000       15ms   65ms  1500ms  150ms
POST      /logs/create               6000       35ms  110ms  2800ms  220ms
```

### Good vs Bad Indicators

✅ **Good:**
- p95 latency < 300ms
- Error rate < 0.1%
- CPU < 80%
- Memory usage stable

❌ **Bad:**
- p95 latency > 1000ms
- Error rate > 1%
- CPU > 90% (not improving with load)
- Memory constantly increasing (memory leak)

---

## 🛠️ Performance Optimization

### If Response Times Are High

**Check database:**
```sql
-- Slow queries
SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;

-- Missing indexes
SELECT * FROM pg_stat_user_tables WHERE seq_scan > 1000;
```

**Add indexes:**
```python
# In migrations/versions/xxxxx.py
def upgrade():
    op.create_index('ix_medications_user_id', 'medications', ['user_id'])
    op.create_index('ix_reminders_medication_id', 'reminders', ['medication_id'])
```

**Enable query caching:**
```python
# In settings.py
CACHE_REMINDERS_TTL = 300  # 5 minutes
CACHE_MEDICATIONS_TTL = 600  # 10 minutes
```

### If CPU Is High

**Reduce workers:**
```bash
# gunicorn -w 2 (instead of 4)
# or use: gunicorn -w $(nproc - 1)
```

**Profile code:**
```python
# pip install py-spy
py-spy record -o profile.svg -- python -m uvicorn main:app
```

### If Memory Leaks

```python
# Check for unclosed connections
async def close_resources():
    await db.close()
    await redis.close()

@app.on_event("shutdown")
async def shutdown():
    await close_resources()
```

---

## 📐 Load Test Results Baseline

Current performance (measured Feb 2026):

```
Test Configuration:
- Users: 100
- Spawn rate: 10/sec
- Duration: 5 min
- Server: 2 CPU, 4GB RAM

Results:
├─ Total Requests: 45,320
├─ Requests/sec: 150 RPS
├─ Error Rate: 0.02% (9 failures)
├─ Response Times:
│  ├─ Min: 12ms
│  ├─ Avg: 67ms
│  ├─ p95: 210ms
│  ├─ p99: 580ms
│  └─ Max: 3,200ms
├─ Database Connections: 25/50 max
├─ Redis Connections: 10/100 max
└─ CPU Usage: ~45%

✅ Performance: GOOD
```

---

## 🚢 Pre-Deployment Checklist

- [ ] Load test completed on staging environment
- [ ] p95 latency < 300ms confirmed
- [ ] Error rate < 0.1% confirmed
- [ ] No memory leaks detected
- [ ] Database indexes verified
- [ ] Connection pools configured
- [ ] Rate limiting tested
- [ ] Cache strategy validated
- [ ] Monitoring alerts configured

---

## 📝 Continuous Performance Monitoring

### Recommended Tools

1. **DataDog** - Full APM
   ```python
   from ddtrace import patch_all
   patch_all()
   ```

2. **New Relic** - Application monitoring
   ```bash
   pip install newrelic
   ```

3. **Prometheus + Grafana** - Self-hosted
   ```python
   from prometheus_client import Counter
   requests_total = Counter('requests_total', 'Total requests')
   ```

4. **Sentry** - Error tracking
   ```python
   import sentry_sdk
   sentry_sdk.init("your-dsn")
   ```

---

## 🎯 Performance Goals

| Metric | Target | Current |
|--------|--------|---------|
| RPS | 500+ | TBD |
| p95 latency | < 300ms | TBD |
| Error rate | < 0.1% | TBD |
| CPU util | < 70% | TBD |
| Memory util | < 80% | TBD |
| DB connections | < 50 | TBD |

---

## 🆘 Troubleshooting

### "Too many open files" error

```bash
# Increase file descriptor limit
ulimit -n 4096

# Permanently (add to ~/.bashrc)
echo "ulimit -n 4096" >> ~/.bashrc
```

### Connection pool exhausted

```python
# In settings.py
SQLALCHEMY_ENGINE_POOL_SIZE = 20
SQLALCHEMY_ENGINE_MAX_OVERFLOW = 40
```

### Redis connection timeouts

```bash
# Increase Redis timeout
redis-cli CONFIG SET timeout 300
```

### High CPU but low requests

```bash
# Check for blocking operations
pip install py-spy
py-spy record --duration 60 -o profile.svg -- locust -f tests/load_test.py --headless
```
