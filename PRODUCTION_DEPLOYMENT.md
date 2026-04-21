# Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Distributed Task Queue System to production environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Single Server Deployment](#single-server-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Docker Compose Production](#docker-compose-production)
6. [Cloud Platforms](#cloud-platforms)
7. [Monitoring & Logging](#monitoring--logging)
8. [Scaling](#scaling)
9. [Security](#security)
10. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

- [ ] Python 3.11+ installed
- [ ] Redis 7+ deployed
- [ ] Database (PostgreSQL recommended for production)
- [ ] SSL/TLS certificates obtained
- [ ] Monitoring system configured
- [ ] Log aggregation setup
- [ ] Backup strategy defined
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented

---

## Infrastructure Setup

### Required Services

```
┌─────────────────┐
│  Load Balancer  │ (Nginx/HAProxy)
└────────┬────────┘
         │
    ┌────┴──────────────────┐
    │                       │
┌───▼────────┐      ┌──────▼────┐
│ API Pod 1  │      │ API Pod 2  │ ... (scale horizontally)
└───┬─────────┘      └──────┬────┘
    │                       │
    └───────────┬───────────┘
                │
        ┌───────▼────────┐
        │  Redis Cluster │ (HA setup)
        └────────────────┘
                │
        ┌───────▼────────────┐
        │ PostgreSQL Database│ (with replication)
        └────────────────────┘
```

### Minimum VM Specs

| Component | CPU  | Memory | Storage |
|-----------|------|--------|---------|
| API Node  | 2    | 2GB    | 20GB    |
| Worker    | 2    | 2GB    | 20GB    |
| Redis     | 2    | 4GB    | 100GB   |
| Database  | 4    | 8GB    | 500GB   |

---

## Single Server Deployment

### 1. Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    build-essential \
    redis-server \
    postgresql \
    postgresql-contrib \
    nginx \
    curl \
    git

# Install Redis 7
curl https://repo.redis.io/redis-stable.tar.gz | tar xz
cd redis-stable && make && sudo make install
```

### 2. Deploy Using Script

```bash
# Make script executable
chmod +x deploy-production.sh

# Run deployment
sudo ./deploy-production.sh
```

### 3. Configure Environment

```bash
# Edit production configuration
sudo nano /opt/task-queue/.env

# Set the following:
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_secure_password
DB_PATH=/var/lib/task-queue/tasks.db
WORKER_NUM=4
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### 4. Start Services

```bash
# Start API service
sudo systemctl start task-queue-api
sudo systemctl enable task-queue-api

# Start worker service
sudo systemctl start task-queue-worker
sudo systemctl enable task-queue-worker

# Check status
sudo systemctl status task-queue-api
sudo systemctl status task-queue-worker
```

### 5. Configure Nginx

```bash
# Enable the Nginx site
sudo ln -s /etc/nginx/sites-available/task-queue /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Kubernetes Deployment

### 1. Build Docker Image

```bash
# Build the image
docker build -f docker/Dockerfile -t task-queue:1.0.0 .

# Push to registry
docker tag task-queue:1.0.0 your-registry/task-queue:1.0.0
docker push your-registry/task-queue:1.0.0
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace task-queue

# Create ConfigMap for configuration
kubectl create configmap task-queue-config \
  --from-file=.env.production \
  -n task-queue

# Create Secret for sensitive data
kubectl create secret generic task-queue-secrets \
  --from-literal=redis_password=your_password \
  --from-literal=db_password=your_db_password \
  -n task-queue

# Deploy resources
kubectl apply -f k8s/redis.yaml -n task-queue
kubectl apply -f k8s/api-deployment.yaml -n task-queue
kubectl apply -f k8s/worker-deployment.yaml -n task-queue
kubectl apply -f k8s/service.yaml -n task-queue
kubectl apply -f k8s/ingress.yaml -n task-queue

# Verify deployment
kubectl get all -n task-queue
kubectl logs -f deployment/task-queue-api -n task-queue
```

### 3. Scale Workers

```bash
# Scale API replicas
kubectl scale deployment task-queue-api --replicas=3 -n task-queue

# Scale workers
kubectl scale deployment task-queue-worker --replicas=5 -n task-queue

# Check replicas
kubectl get deployment -n task-queue
```

---

## Docker Compose Production

### 1. Deploy with Docker Compose

```bash
# Start services with production config
docker-compose -f docker-compose.production.yml up -d

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale worker=3

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f api
```

### 2. Update Configuration

Edit `.env` before deployment:

```env
API_WORKERS=4
REDIS_PASSWORD=secure_password
LOG_LEVEL=INFO
WORKER_REPLICAS=2
GRAFANA_PASSWORD=secure_grafana_password
```

---

## Cloud Platforms

### AWS Deployment

```bash
# Using Elastic Beanstalk
eb init task-queue --platform python-3.11

# Create environment
eb create task-queue-prod

# Deploy
eb deploy

# Scale
eb scale 3

# Monitor
eb logs
```

### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/task-queue

# Deploy API
gcloud run deploy task-queue-api \
  --image gcr.io/PROJECT_ID/task-queue \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars REDIS_HOST=10.0.0.2,WORKER_ENABLED=False

# Deploy Workers
gcloud run deploy task-queue-worker \
  --image gcr.io/PROJECT_ID/task-queue \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars "WORKER_NUM=2"
```

### Azure Container Instances

```bash
# Create resource group
az group create --name task-queue --location eastus

# Deploy using compose
az container create \
  --resource-group task-queue \
  --name task-queue-prod \
  --image-registry-login-password $PASSWORD \
  --file docker-compose.production.yml
```

---

## Monitoring & Logging

### 1. Prometheus Metrics

Access metrics at: `http://localhost:9090`

Key metrics to monitor:
- `api_requests_total` - Total API requests
- `api_request_duration_seconds` - Request latency
- `task_queue_size` - Pending tasks
- `task_execution_duration_seconds` - Task execution time
- `worker_tasks_processed_total` - Tasks processed

### 2. Grafana Dashboards

Access Grafana at: `http://localhost:3000`

Default credentials: `admin:admin`

Pre-built dashboards:
- Task Queue Overview
- API Performance
- Worker Statistics
- Resource Usage

### 3. Centralized Logging

```bash
# Configure logging to ELK Stack
export ELK_HOST=logging.internal.example.com
export ELK_PORT=9200

# Or use other services:
# - Datadog: export DATADOG_API_KEY=...
# - CloudWatch: export AWS_LOG_GROUP=task-queue
# - Splunk: export SPLUNK_HEC_URL=...
```

### 4. Alerting

Configure alerts in Prometheus:

```yaml
groups:
  - name: task_queue
    rules:
      - alert: HighErrorRate
        expr: rate(api_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: LargePendingQueue
        expr: task_queue_size > 1000
        for: 10m
        annotations:
          summary: "Too many pending tasks"
      
      - alert: WorkerDown
        expr: count(up{job="worker"}) < 2
        for: 2m
        annotations:
          summary: "Worker node is down"
```

---

## Scaling

### Horizontal Scaling

```bash
# Add more API servers
docker-compose -f docker-compose.production.yml up -d --scale api=2

# Add more workers
docker-compose -f docker-compose.production.yml up -d --scale worker=5

# Or with Kubernetes
kubectl scale deployment task-queue-api --replicas=5
kubectl scale deployment task-queue-worker --replicas=10
```

### Vertical Scaling

Update resource limits in docker-compose or Kubernetes:

```yaml
resources:
  limits:
    cpus: "4"
    memory: 4G
  reservations:
    cpus: "2"
    memory: 2G
```

### Redis Clustering

```bash
# Setup Redis Cluster
redis-cli --cluster create \
  127.0.0.1:7000 \
  127.0.0.1:7001 \
  127.0.0.1:7002 \
  127.0.0.1:7003 \
  127.0.0.1:7004 \
  127.0.0.1:7005 \
  --cluster-replicas 1
```

---

## Security

### SSL/TLS Configuration

```bash
# Generate self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# For production, use Let's Encrypt
sudo certbot certonly --standalone -d task-queue.example.com

# Update .env
SSL_CERT_PATH=/etc/letsencrypt/live/task-queue.example.com/fullchain.pem
SSL_KEY_PATH=/etc/letsencrypt/live/task-queue.example.com/privkey.pem
```

### API Authentication

```bash
# Enable API key authentication
ENABLE_API_KEY_AUTH=True
API_KEY_SECRET=your_secure_secret_key_here

# Clients must send: Authorization: Bearer <api_key>
```

### Database Security

```bash
# Use strong PostgreSQL password
# Configure pg_hba.conf for SSL connections
# Enable row-level security if needed

# Backup strategy
pg_dump task_queue > backup_$(date +%Y%m%d).sql
```

### Network Security

```bash
# Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 6379/tcp  # Redis (internal only)
sudo ufw enable
```

---

## Troubleshooting

### Check Service Status

```bash
# API server
curl -i http://localhost:8000/api/health

# Worker logs
sudo journalctl -u task-queue-worker -f

# Redis connectivity
redis-cli -h redis.internal.example.com ping

# Database connectivity
psql -h db.internal.example.com -U taskqueue -d task_queue
```

### Common Issues

**Issue: "Connection refused" to Redis**
```bash
# Verify Redis is running
sudo systemctl status redis-server

# Check Redis is listening
netstat -tlnp | grep 6379

# Test connection
redis-cli -h redis-host -p 6379 -a password ping
```

**Issue: API returning 503 Service Unavailable**
```bash
# Check API logs
sudo tail -f /var/log/task-queue/api.log

# Check system resources
free -h
df -h
top -b -n 1 | head -20
```

**Issue: Tasks not being processed**
```bash
# Check queue size
redis-cli -h redis-host ZCARD task_queue:pending

# Check worker status
sudo systemctl status task-queue-worker

# Check worker logs
sudo tail -f /var/log/task-queue/worker.log

# Manually test task execution
python -c "from src.tasks import execute_task; print(execute_task('math_task', {'operation': 'add', 'operands': [1, 2, 3]}))"
```

---

## Performance Tuning

### Redis Configuration

```bash
# In redis.conf
maxmemory 4gb
maxmemory-policy allkeys-lru
timeout 0
tcp-backlog 511
```

### PostgreSQL Configuration

```bash
# In postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
```

### Application Tuning

Edit `.env`:

```env
# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
REDIS_POOL_SIZE=50

# Request handling
REQUEST_TIMEOUT=60
API_WORKERS=4

# Worker settings
WORKER_NUM=4
POLL_INTERVAL=0.5
```

---

## Next Steps

1. **Set up monitoring**: Configure Prometheus and Grafana
2. **Enable logging**: Setup centralized log aggregation
3. **Configure backups**: Backup Redis and database regularly
4. **Test failover**: Verify disaster recovery procedures
5. **Load testing**: Use tools like `locust` or `k6` to test capacity
6. **Security audit**: Regular penetration testing
7. **Auto-scaling**: Configure based on metrics

---

## Support

For issues or questions:
1. Check logs: `/var/log/task-queue/`
2. Review documentation: `README.md`
3. Run diagnostics: `python run_validation.py`
4. Contact support with logs attached

