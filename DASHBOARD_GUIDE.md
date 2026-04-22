# Dashboard User Guide

A complete guide to using the Task Queue Dashboard UI for managing your distributed tasks.

## Quick Start (3 Simple Steps)

### Step 1: Open 3 PowerShell Terminals

You need **3 separate terminals** running these commands simultaneously.

#### Terminal 1: Start Redis (Background Service)
Make sure Redis/Memurai is already running. If it is, skip this. Otherwise:
```powershell
# If you have Redis installed locally, or use Memurai for Windows
redis-server
```

#### Terminal 2: Start the API Server
```powershell
cd "e:\Distributed Task Queue System"
.\.venv\Scripts\activate.ps1
python main.py
```

**You should see:**
```
INFO:     Application startup complete [loaded in 0.10s]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Terminal 3: Start the Worker(s)
```powershell
cd "e:\Distributed Task Queue System"
.\.venv\Scripts\activate.ps1
python worker_main.py
```

**You should see:**
```
[worker-1] Worker started, polling queue...
[worker-1] Connected to Redis queue
```

### Step 2: Open Your Browser

Go to: **http://localhost:8000**

You'll see the beautiful Dashboard! 🎉

### Step 3: Start Submitting Tasks!

---

## Dashboard Features Explained

### 1. **Stats Cards** (Top Row)
Shows real-time counts of your tasks:

- **PENDING** (Purple): Tasks waiting in the queue to be processed
- **RUNNING** (Blue): Tasks currently being executed by workers
- **COMPLETED** (Green): Tasks that finished successfully
- **FAILED** (Red): Tasks that encountered errors

These numbers update **automatically every 3 seconds**.

---

### 2. **Submit Task Panel** (Left Side)

#### Task Type Dropdown
Choose what kind of work you want to do:
- **Sleep Task** - Simulates a long-running job (good for testing)
- **Math Task** - Performs math operations (add, multiply, divide, etc.)
- **Data Processing** - Analyzes data (sum, average, unique values)

#### Priority (0-100)
- **0** = Low priority (processed after everything else)
- **50** = Medium priority
- **100** = High priority (processed first!)

**Example:** A task with priority 100 will jump the queue ahead of a priority 0 task.

#### JSON Payload
This is the **input data** for your task. It depends on the task type:

**Example for Sleep Task:**
```json
{
  "duration": 5,
  "message": "Processing user data"
}
```
This tells the worker to sleep for 5 seconds and log your message.

**Example for Math Task:**
```json
{
  "operation": "add",
  "operands": [10, 20, 30]
}
```
This adds 10 + 20 + 30 = 60

**Example for Data Processing:**
```json
{
  "data": [1, 2, 3, 4, 5],
  "action": "sum"
}
```
This sums the array: 1+2+3+4+5 = 15

#### Enqueue Task Button
Click this green button to submit your task. It will:
1. Validate your JSON
2. Send it to the queue
3. Show a "Enqueuing..." spinner while processing
4. The task appears in the Recent Activity list

---

### 3. **Recent Activity Table** (Right Side)

Shows all your tasks with:

**ID / Time Column:**
- First 8 characters of the task ID
- Time when the task was created (24-hour format)

**Type Column:**
- Which task type it is (sleep_task, math_task, etc.)
- Priority badge (PRIORITY: X)

**Status Column:**
Shows where the task is in its lifecycle:

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| **pending** | ⏰ | Purple | Waiting in queue, not started yet |
| **running** | 🔄 | Blue (pulsing) | Worker is actively processing |
| **completed** | ✓ | Green | Finished successfully |
| **failed** | ✗ | Red | Hit an error |

If a task is **failed**, you'll see the error message below.
If a task is **completed**, you'll see a snippet of the result.

---

### 4. **Filter by Status** (Top Right)
The dropdown lets you filter tasks:
- **All Statuses** - Show everything
- **Pending** - Only waiting tasks
- **Running** - Only active tasks
- **Completed** - Only finished tasks
- **Failed** - Only error tasks

---

### 5. **Refresh Button** (Top Right)
The circular arrow icon near the filter. Click it to manually refresh the dashboard immediately (normally it auto-updates every 3 seconds).

---

## Real-World Examples

### Example 1: Submit a Sleep Task

1. Make sure all 3 terminals are running
2. Go to http://localhost:8000
3. Leave Task Type as **Sleep Task**
4. Leave Priority as **0**
5. Replace JSON Payload with:
   ```json
   {
     "duration": 3,
     "message": "Testing the system"
   }
   ```
6. Click **Enqueue Task**

**What happens:**
- Task appears in Recent Activity with **PENDING** status
- Within 1 second, the Worker picks it up → **RUNNING** status (pulsing blue)
- After 3 seconds → **COMPLETED** status (green checkmark)
- You'll see the result: `{"status": "success", "message": "Slept for 3 seconds", ...}`

### Example 2: Submit Multiple Math Tasks with Priority

1. Submit task 1 (Priority 10):
   ```json
   {
     "operation": "add",
     "operands": [5, 10]
   }
   ```

2. Submit task 2 (Priority 100):
   ```json
   {
     "operation": "multiply",
     "operands": [3, 4]
   }
   ```

**What happens:**
- Task 2 (priority 100) will process **first** even though you submitted task 1 second earlier!
- Task 2 finishes in ~1 second with result: 12 (3 × 4)
- Then task 1 finishes with result: 15 (5 + 10)

---

## Troubleshooting

### ❌ Dashboard shows "Cannot connect to API server"
**Solution:** Make sure Terminal 2 is running `python main.py`. Look for the "Application startup complete" message.

### ❌ Tasks get stuck on "PENDING"
**Solution:** Make sure Terminal 3 is running `python worker_main.py`. Workers process the tasks.

### ❌ System Status shows "degraded"
**Solution:** This is normal! It means Redis is connected but the database is SQLite (which is expected). For production, switch to PostgreSQL in `.env`.

### ❌ JSON Payload error
**Solution:** Make sure your JSON is valid. Use an online JSON validator: https://jsonlint.com

### ❌ Tasks show status "FAILED"
**Solution:** This usually means:
- The task type doesn't exist
- Your JSON payload is missing required fields
- The math operation is invalid

Check the error message below the status for details.

---

## API Endpoints (Advanced)

If you want to interact programmatically (not through the dashboard):

### Submit a Task
```bash
curl -X POST http://localhost:8000/api/task \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "sleep_task",
    "payload": {"duration": 5},
    "priority": 50
  }'
```

### Get a Task Status
```bash
curl http://localhost:8000/api/task/{task_id}
```

### List All Tasks
```bash
curl "http://localhost:8000/api/tasks?limit=50&status=completed"
```

### Get Queue Stats
```bash
curl http://localhost:8000/api/stats
```

### Health Check
```bash
curl http://localhost:8000/api/health
```

---

## FAQ

**Q: Can I submit tasks while the worker is sleeping?**
A: Yes! Tasks queue up in Redis. The worker will get to them when it finishes the current task.

**Q: What happens if I close the dashboard tab?**
A: Nothing! Tasks keep running. The dashboard is just a viewer. Reopen it anytime.

**Q: Can I see task results?**
A: Yes! In the Recent Activity table, completed tasks show a snippet of their result.

**Q: How do I delete a task?**
A: The current version doesn't support deletion. You would need to clear Redis manually (advanced).

**Q: How many tasks can I submit?**
A: Unlimited! But realistically, thousands can run before you hit performance limits. For enterprise scale, add more workers: `WORKER_NUM=5 python worker_main.py`

**Q: Can customers access this dashboard?**
A: Yes! This is designed as a web app. Any user who can reach `http://your-server:8000` can use it. For security (to prevent unauthorized access), you'd need to add login authentication (advanced).

---

## Next Steps

- **Test it out:** Submit a few tasks and watch them process in real-time
- **Monitor queue health:** Keep an eye on the stats cards to see your throughput
- **Scale workers:** In a new Terminal 4, run `WORKER_NUM=2 python worker_main.py` to add more processing power
- **Deploy to production:** Once confident, use Docker to deploy: `docker-compose -f docker-compose.production.yml up -d`

Enjoy your Task Queue System! 🚀
