# Dashboard Quick Reference

## What You See When You Open http://localhost:8000

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD HEADER                                    │
│  Overview                    Real-time distributed task monitoring    🔄    │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┬──────────────┬──────────────┬──────────────┐
│   PENDING    │   RUNNING    │  COMPLETED   │   FAILED     │
│              │              │              │              │
│      8       │      2       │     156      │      3       │
│  ⏰ (Purple)  │  🔄 (Blue)   │  ✓ (Green)   │  ✗ (Red)     │
└──────────────┴──────────────┴──────────────┴──────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ LEFT PANEL                              │ RIGHT PANEL                       │
│                                         │                                   │
│ 📋 SUBMIT TASK                          │ 📊 RECENT ACTIVITY                │
│                                         │ [Filter: All Statuses ▼]         │
│ Task Type:                              │                                   │
│ [Sleep Task ▼]                          │ ID / Time | Type | Status        │
│                                         │ ──────────────────────────────── │
│ Priority (0-100):                       │ a1b2c3d4  │sleep│⏰ pending      │
│ [50]                                    │ 10:23 AM  │task │               │
│                                         │           │     │               │
│ JSON Payload:                           │ e5f6g7h8  │math │✓ completed   │
│ ┌─────────────────────────────────────┐│ 10:22 AM  │task │Result: 42    │
│ │{                                    ││           │     │               │
│ │  "duration": 3,                     ││ i9j0k1l2  │data │🔄 running    │
│ │  "message": "Hello"                 ││ 10:21 AM  │task │               │
│ │}                                    ││           │     │               │
│ └─────────────────────────────────────┘│ m3n4o5p6  │math │✗ failed      │
│                                         │ 10:20 AM  │task │Error: timeout│
│ [Enqueue Task] 🟢                       │           │     │               │
│                                         │           │     │               │
│ (Button turns spinner when loading)     │ (Auto-updates every 3 seconds)  │
│                                         │                                   │
└─────────────────────────────────────────┴───────────────────────────────────┘
```

---

## Step-by-Step: How to Submit Your First Task

### Step 1: Pick a Task Type
Click the dropdown under "Task Type":
- **Sleep Task** ← Start here! (Easiest for testing)
- Math Task
- Data Processing Task

### Step 2: Set Priority (Optional)
Type a number from 0 to 100:
- `0` = Low (process after others)
- `50` = Medium
- `100` = High (jump the queue!)

### Step 3: Write the JSON Payload
Replace the example JSON with your actual task data.

**For Sleep Task:**
```json
{
  "duration": 5,
  "message": "My first task!"
}
```

**For Math Task:**
```json
{
  "operation": "add",
  "operands": [10, 20, 30]
}
```

**For Data Processing:**
```json
{
  "data": [1, 2, 3, 4, 5],
  "action": "sum"
}
```

### Step 4: Click "Enqueue Task"
- Green button at the bottom of the left panel
- Button shows "Enqueuing..." while processing

### Step 5: Watch in Recent Activity
- Task appears instantly in the right panel
- Status changes: `pending` → `running` → `completed` (or `failed`)
- Check the result when done!

---

## Status Colors & Icons

| Status | Color | Icon | Meaning |
|--------|-------|------|---------|
| **pending** | 🟣 Purple | ⏰ | Waiting to start |
| **running** | 🔵 Blue | 🔄 | Currently processing |
| **completed** | 🟢 Green | ✓ | Success! |
| **failed** | 🔴 Red | ✗ | Error occurred |

---

## What Each Number Means

**PENDING: 8**
→ 8 tasks are waiting in the queue, not started yet

**RUNNING: 2**
→ 2 workers are actively processing tasks right now

**COMPLETED: 156**
→ 156 tasks finished successfully (all time)

**FAILED: 3**
→ 3 tasks hit errors and couldn't complete

---

## Keyboard Shortcuts

- **Auto-refresh:** Dashboard updates itself every 3 seconds (no action needed)
- **Manual refresh:** Click the circular arrow button at the top right
- **Filter tasks:** Use the dropdown to show only Pending, Running, Completed, or Failed tasks

---

## Common Scenarios

### Scenario 1: Task Won't Start
**Check:** Is Terminal 2 running `python worker_main.py`?
- If NO → Start it! Workers are what actually process tasks.
- If YES → Check the logs for errors

### Scenario 2: Task Completed but Result is Empty
**Normal!** Some tasks don't return much data. Check the full task details by clicking on it (advanced feature).

### Scenario 3: I See "Cannot Connect to API Server"
**Check:** Is Terminal 1 running `python main.py`?
- If NO → Start it! This is the API server.
- If YES → Check that port 8000 isn't used by another program

### Scenario 4: Multiple Tasks Running at Once
**Expected behavior!** If you have `WORKER_NUM=2` (or more), multiple workers process tasks in parallel. Watch the "RUNNING" counter jump up!

---

## Pro Tips

✅ **Tip 1:** Create a Sleep Task with `duration: 30` to test the dashboard while task is running

✅ **Tip 2:** Submit 10 Low-Priority tasks, then 1 High-Priority task. Watch the High-Priority one jump ahead!

✅ **Tip 3:** Leave the dashboard open in a browser tab. It auto-updates. Check back after a minute to see your results.

✅ **Tip 4:** Add more workers to increase throughput. In a new terminal:
```powershell
cd "e:\Distributed Task Queue System"
.\.venv\Scripts\activate.ps1
WORKER_NUM=4 python worker_main.py
```

---

## Still Confused?

Read the full guide: **[DASHBOARD_GUIDE.md](./DASHBOARD_GUIDE.md)**

Or check the API docs directly at: **[http://localhost:8000/docs](http://localhost:8000/docs)**
