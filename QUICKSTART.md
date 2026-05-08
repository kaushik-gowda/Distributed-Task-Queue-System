# Quick Start Guide

Get the Distributed Task Queue System up and running in 5 minutes!

## Prerequisites

- Python 3.11+
- Redis
- pip

## Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Start Redis

**Option A: Local Redis**
```bash
# macOS (with Homebrew)
brew services start redis

# Linux (with apt)
sudo apt-get install redis-server
sudo systemctl start redis-server

# Windows (if using WSL)
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:7-alpine
```

**Option B: Docker Compose**
```bash
docker-compose up -d redis
```

Verify Redis is running:
```bash
redis-cli ping
# Should return: PONG
```

## Step 3: Start API Server & Worker

### Option A: Automated Startup

**Windows:**
```bash
start_windows.bat
```

**macOS/Linux:**
```bash
chmod +x start.sh
./start.sh
```

### Option B: Manual Startup (Use separate terminals)

**Terminal 1 - API Server:**
```bash
python main.py
```

**Terminal 2 - Worker:**
```bash
python worker_main.py
```

## Step 4: Test the System

**Terminal 3 - Run tests:**
```bash
python test_system.py
```

Or manually test with curl:

```bash
# Submit a task
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sleep_task",
    "payload": {"duration": 5},
    "priority": 0
  }'

# You'll get a response like:
# {"task_id": "550e8400-e29b-41d4-a716-446655440000", ...}

# Get task status
curl http://localhost:8000/api/task/550e8400-e29b-41d4-a716-446655440000

# View stats
curl http://localhost:8000/api/stats

# Health check
curl http://localhost:8000/api/health
```

## API Documentation

Interactive API docs available at: **http://localhost:8000/docs**

## Available Task Types

### 1. Sleep Task
Simulates long-running work
```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sleep_task",
    "payload": {
      "duration": 10,
      "message": "Processing data..."
    }
  }'
```

### 2. Math Task
Performs math operations
```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "math_task",
    "payload": {
      "operation": "add",
      "operands": [10, 20, 30]
    }
  }'
```

Operations: `add`, `subtract`, `multiply`, `divide`

### 3. Data Processing Task
Processes data
```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "data_processing_task",
    "payload": {
      "data": [1, 2, 3, 4, 5],
      "action": "sum"
    }
  }'
```

Actions: `sum`, `average`, `unique`

## Common Commands

### View Logs
```bash
# API logs
tail -f logs/api.log

# Worker logs
tail -f logs/worker.log
```

### Monitor Queue
```bash
redis-cli
> KEYS *
> ZCARD task_queue:pending
```

### Check Database
```bash
sqlite3 tasks.db
> SELECT * FROM tasks;
> SELECT COUNT(*) FROM tasks;
```

### Scale Workers
```bash
# Change WORKER_NUM in .env
WORKER_NUM=4

# Restart worker
python worker_main.py
```

## Troubleshooting

### Redis Connection Error
```
Failed to connect to Redis
```
**Fix:** Start Redis with `redis-server`

### Port Already in Use
```
Address already in use: ('0.0.0.0', 8000)
```
**Fix:** Change port in `.env` or kill existing process:
```bash
# macOS/Linux
lsof -i :8000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Tasks Not Processing
1. Check if worker is running
2. Check if Redis is running: `redis-cli ping`
3. Check logs: `tail -f logs/worker.log`
4. Verify .env is configured correctly

### Database Locked
```
database is locked
```
**Fix:** This occurs with SQLite. For production, use PostgreSQL.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [API Reference](#api-documentation) for all endpoints
- Review [Configuration](#configuration) for customization options
- Explore Docker deployment with `docker-compose`

## Docker Quick Start

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale worker=3

# Stop services
docker-compose down
```

## Need Help?

1. Check the [README.md](README.md) for comprehensive documentation
2. Review logs in the `logs/` directory
3. Check system health: `curl http://localhost:8000/api/health`
4. Run the test suite: `python test_system.py`
