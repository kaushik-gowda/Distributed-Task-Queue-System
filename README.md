# Distributed Task Queue System

This project is a distributed background job system for submitting, tracking, and executing asynchronous tasks. It is built with Python, FastAPI, Redis, SQLite, and a browser-based dashboard so you can understand task processing without needing a command-line workflow.

## What The Project Is For

The system is designed for workloads that should not block a user request or a main application thread. Typical examples include:

- background notifications
- report generation
- data cleanup or transformation
- scheduled or delayed work
- simulated long-running jobs while testing queue behavior

In practice, a client submits a task, the API stores the task record, Redis carries the queue item, and a worker process executes the job and updates its status.

## Where It Is Used

This kind of architecture is useful anywhere you need reliable background execution with visibility into task progress:

- web applications that need to offload slow work
- internal tools that must show task state in real time
- systems that need retries after transient failure
- demos or labs for understanding queue-based architecture
- production-style prototypes where Redis-backed task dispatch is a good fit

## How It Works

The request flow is simple:

1. A user opens the dashboard in a browser or sends an API request.
2. The API validates the payload and creates a task record in the database.
3. The task ID is pushed into Redis with a priority value.
4. A worker pulls the task from the queue and runs the matching executor.
5. The worker writes the final status, result, retry count, and timestamps back to the database.
6. The dashboard refreshes task and queue information through the API.

## Main Capabilities

- FastAPI REST API for task submission, lookup, listing, stats, and health checks
- browser dashboard for queue visibility and task submission
- Redis-based queue for asynchronous dispatch
- SQLite persistence for task metadata and status history
- priority support so urgent jobs are processed first
- retry handling with exponential backoff
- logging across API and worker execution
- sample tasks for sleep, math, and data processing workloads

## Project Structure

```
Distributed Task Queue System/
├── main.py                  # FastAPI application entry point
├── worker_main.py           # Worker process entry point
├── test_system.py           # End-to-end API/task checks
├── static/index.html        # Browser dashboard
├── src/
│   ├── api/handlers.py      # API endpoints and request handling
│   ├── api/schemas.py       # Request/response models
│   ├── db/                  # Database models, repository, and connection code
│   ├── queue/broker.py      # Redis queue implementation
│   ├── tasks/sample_tasks.py  # Built-in task executors
│   ├── worker/executor.py   # Worker-side task execution logic
│   ├── utils/               # Logging and helpers
│   └── config.py            # Environment-backed configuration
├── docker/                  # Container build files
├── docker-compose.yml       # Multi-service deployment definition
├── k8s/                     # Kubernetes manifests
├── monitoring/              # Prometheus configuration
└── requirements.txt         # Python dependencies
```


### Component Responsibilities

| Component | Responsibility | Persistence |
|------------|---------------|-------------|
| **Client / Dashboard** | Submit tasks and monitor execution | Stateless |
| **FastAPI API** | Validate requests, create task records, expose REST APIs | Writes to SQLite |
| **SQLite Database** | Stores task metadata, status, timestamps and execution results | Persistent |
| **Redis Queue** | Maintains pending tasks using priority ordering | In-memory |
| **Worker Process** | Polls Redis, executes tasks, updates task state | Stateless |
| **Dashboard** | Displays live task information using REST APIs | Stateless |

---

# Complete Task Lifecycle

## Step 1 — Task Submission

The client submits a task using either the dashboard or the REST API.

```text
Client
   │
   ▼
POST /api/task
```

Example request

```json
{
  "task_type": "sleep_task",
  "payload": {
    "duration": 5,
    "message": "Processing..."
  },
  "priority": 10
}
```

The API performs:

- Validates request payload
- Validates task type
- Validates priority
- Generates a unique Task ID
- Stores task metadata in SQLite
- Pushes Task ID into Redis Priority Queue

```text
Client
   │
   ▼
 FastAPI
   │
   ├──────────────► SQLite
   │                  │
   │             Store Task
   │
   └──────────────► Redis
                      │
                 Priority Queue
```

---

## Step 2 — Queue Polling

Worker processes continuously poll Redis.

```text
Redis Queue
      │
      ▼
 Worker Process
```

Each worker:

- Fetches highest-priority task
- Removes it from pending queue
- Loads task metadata from SQLite
- Marks task as RUNNING

---

## Step 3 — Task Execution

```text
Worker
   │
   ▼
Load Task
   │
   ▼
Execute Task
```

Execution flow

- Update status → RUNNING
- Record start timestamp
- Execute business logic
- Capture output or exception

Task execution occurs **outside the database transaction**, preventing long-running database locks.

---

## Step 4 — Successful Execution

```text
Execute Task
      │
      ▼
Completed
      │
      ├── Update SQLite
      ├── Store Result
      └── Update Redis
```

Worker updates:

- status = COMPLETED
- completed_at timestamp
- execution result
- execution duration

---

## Step 5 — Failure & Retry

If execution fails,

```text
Execution Error
        │
        ▼
Retry Available?
     ┌──┴──┐
     │     │
    YES    NO
     │     │
 Retry   Failed
```

When retries remain:

- Increment retry count
- Apply exponential backoff
- Push task back into Redis

Otherwise:

- Status = FAILED
- Save error message
- Store completion timestamp

---

# End-to-End Data Flow

```text
             Client
                │
                ▼
        FastAPI REST API
                │
      ┌─────────┴─────────┐
      │                   │
      ▼                   ▼
 SQLite Database     Redis Queue
      ▲                   │
      │                   ▼
      └──────────── Worker
                          │
                          ▼
                   Execute Task
                          │
      ┌───────────────────┴───────────────────┐
      ▼                                       ▼
 Update SQLite                          Update Redis
      │
      ▼
 Dashboard / API
```

---

# Task State Flow

```text
          PENDING
              │
              ▼
          RUNNING
         ┌────┴────┐
         ▼         ▼
   COMPLETED    FAILED
                    │
                    ▼
               RETRYING
                    │
                    ▼
                RUNNING
```

---

# Multi-Worker Execution

Multiple workers can process independent tasks simultaneously.

```text
                Redis Queue
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    Worker-1     Worker-2     Worker-3
        │            │            │
        ▼            ▼            ▼
 Execute Task   Execute Task  Execute Task
        │            │            │
        └────────────┼────────────┘
                     ▼
             Update SQLite
```

Tasks execute **in parallel**, improving throughput while maintaining queue priority.

---

# Error Handling

### Retry Mechanism

- Configurable retry attempts
- Exponential backoff
- Automatic re-queueing

### Persistent Storage

SQLite stores:

- Task metadata
- Status history
- Execution timestamps
- Results
- Error messages

### Redis Responsibilities

Redis stores:

- Pending task queue
- Priority ordering
- Temporary execution state

SQLite remains the **source of truth** for task history.

---

# Why This Architecture?

This architecture provides:

- Asynchronous background processing
- High-priority task scheduling
- Reliable persistence
- Automatic retries
- Horizontal worker scaling
- Fault tolerance
- Separation of concerns
- Real-time task monitoring