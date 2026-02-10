# 🚢 Production Deployment Guide

Complete guide for deploying Medi-Minder API to production.

---

## 📋 Pre-Deployment Checklist

### Security
- [ ] Change all default passwords
- [ ] Generate secure `SECRET_KEY` (32+ characters)
- [ ] Set `DEBUG=false`
- [ ] Review and restrict CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up firewall rules
- [ ] Configure rate limiting appropriately
- [ ] Audit all exposed endpoints
- [ ] Implement API key rotation

### Configuration
- [ ] Production database credentials
- [ ] Production Redis credentials
- [ ] Real email SMTP settings (not sandbox)
- [ ] Production SMS API keys (Africa's Talking)
- [ ] Firebase production credentials
- [ ] Environment-specific `.env` file
- [ ] Backup strategy in place

### Infrastructure
- [ ] Database backups automated
- [ ] Monitoring and alerting configured
- [ ] Log aggregation setup
- [ ] CDN for static assets (if applicable)
- [ ] Load balancer configured
- [ ] Auto-scaling rules defined
- [ ] Disaster recovery plan

### Performance
- [ ] Database indexes optimized
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] API response times tested
- [ ] Load testing completed
- [ ] Resource limits set

---

## 🏗️ Deployment Options

### Option 1: Docker Compose (Single Server)

**Best for:** Small to medium deployments, MVP, testing

**Steps:**

1. **Provision Server**
   ```bash
   # Ubuntu 22.04 LTS recommended
   # Minimum: 2 CPU, 4GB RAM, 20GB SSD
   ```

2. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

3. **Clone and Configure**
   ```bash
   git clone https://github.com/yourusername/medication-reminder-api.git
   cd medication-reminder-api

   # Create production .env
   cp .env.example .env
   nano .env  # Edit with production values
   ```

4. **Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Set up Reverse Proxy (nginx)**
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Enable SSL (Let's Encrypt)**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d api.yourdomain.com
   ```

---

### Option 2: Kubernetes (Scalable Production)

**Best for:** High availability, auto-scaling, enterprise

**Prerequisites:**
- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- kubectl configured
- Helm installed (optional but recommended)

**Deployment:**

1. **Create Kubernetes Manifests**

`k8s/namespace.yaml`:
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: medireminder
```

`k8s/secrets.yaml`:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: medireminder-secrets
  namespace: medireminder
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://..."
  SECRET_KEY: "your-secret-key"
  REDIS_URL: "redis://redis:6379"
  # Add all other secrets
```

`k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: medireminder-api
  namespace: medireminder
spec:
  replicas: 3
  selector:
    matchLabels:
      app: medireminder-api
  template:
    metadata:
      labels:
        app: medireminder-api
    spec:
      containers:
      - name: api
        image: yourdockerhub/medireminder-api:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: medireminder-secrets
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

`k8s/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: medireminder-api-service
  namespace: medireminder
spec:
  selector:
    app: medireminder-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

2. **Apply Configurations**
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

3. **Verify Deployment**
```bash
kubectl get pods -n medireminder
kubectl get services -n medireminder
kubectl logs -f deployment/medireminder-api -n medireminder
```

---

### Option 3: Cloud Platform (Managed Services)

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker medireminder-api

# Create environment
eb create production-env

# Deploy
eb deploy
```

#### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/medireminder-api

# Deploy
gcloud run deploy medireminder-api \
  --image gcr.io/PROJECT_ID/medireminder-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku

```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create medireminder-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=false

# Deploy
git push heroku main
```

---

## 🗃️ Database Setup

### PostgreSQL Production Configuration

**Managed Options (Recommended):**
- AWS RDS for PostgreSQL
- Google Cloud SQL
- Azure Database for PostgreSQL
- DigitalOcean Managed Databases

**Connection Pooling (PgBouncer):**
```bash
# Install PgBouncer
sudo apt install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
medireminder = host=db.example.com port=5432 dbname=medireminder

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

**Backup Strategy:**
```bash
# Daily backups via cron
0 2 * * * pg_dump -h localhost -U medieminder medireminder | gzip > /backups/medireminder_$(date +\%Y\%m\%d).sql.gz

# Retention: Keep last 30 days
find /backups -name "medireminder_*.sql.gz" -mtime +30 -delete
```

---

## ⚡ Redis Production Setup

**Managed Options:**
- AWS ElastiCache
- Google Cloud Memorystore
- Azure Cache for Redis
- Redis Labs

**Configuration:**
```bash
# redis.conf for production
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

---

## 📊 Monitoring & Observability

### Application Performance Monitoring

**Sentry Integration:**
```python
# In main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FastApiIntegration()],
    environment="production",
    traces_sample_rate=0.1,
)
```

**Prometheus Metrics:**
```bash
# Add to requirements.txt
prometheus-client==0.19.0
prometheus-fastapi-instrumentator==6.1.0
```

```python
# In main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)
```

### Logging

**Structured Logging (Loguru):**
```python
from loguru import logger

logger.add(
    "logs/api_{time}.log",
    rotation="500 MB",
    retention="30 days",
    compression="zip",
    format="{time} {level} {message}",
    level="INFO",
)
```

**Log Aggregation:**
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- Splunk
- CloudWatch Logs (AWS)

---

## 🔐 Security Hardening

### Environment Variables
```bash
# Never commit .env to git
# Use secrets management:
# - AWS Secrets Manager
# - Google Secret Manager
# - Azure Key Vault
# - HashiCorp Vault
```

### Rate Limiting
```python
# Update settings for production
MAX_ATTEMPTS_PER_EMAIL=5
MAX_ATTEMPTS_PER_IP=50
WINDOW_HOURS=1
COOLDOWN_MINUTES=30
```

### CORS Configuration
```python
# Restrict to your domains only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
```

---

## 🚀 CI/CD Pipeline

### GitHub Actions Example

`.github/workflows/deploy.yml`:
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: |
          docker-compose -f docker-compose.test.yml up --abort-on-container-exit

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and push Docker image
        run: |
          docker build -t yourdockerhub/medireminder-api:${{ github.sha }} .
          docker push yourdockerhub/medireminder-api:${{ github.sha }}

      - name: Deploy to production
        run: |
          ssh user@your-server "cd /app && docker-compose pull && docker-compose up -d"
```

---

## 📈 Scaling Strategies

### Horizontal Scaling
- Multiple API instances behind load balancer
- Stateless design (session data in Redis)
- Database read replicas

### Vertical Scaling
- Increase container resources
- Optimize database queries
- Add indexes

### Caching
- Redis for frequently accessed data
- CDN for static assets
- HTTP caching headers

---

## 🆘 Troubleshooting Production Issues

### High CPU Usage
```bash
# Check container stats
docker stats

# Profile Python code
pip install py-spy
py-spy top --pid <pid>
```

### Memory Leaks
```bash
# Monitor memory
docker stats --no-stream

# Python memory profiling
pip install memory_profiler
```

### Database Slow Queries
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Find slow queries
SELECT query, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## 📞 Support

For production deployment assistance:
- 📧 Email: support@yourdomain.com
- 💬 Slack: #medireminder-ops
- 📖 Docs: https://docs.yourdomain.com

---

**Remember:** Always test in staging environment before deploying to production! 🚀
