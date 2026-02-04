# Real-Time Dashboard Implementation Plan

## Requirements from User
1. **Pagination** - Streaming data without duplicates
2. **WebSockets** - Real-time data buckets
3. **Overall Logs** - Centralized logging dashboard
4. **Background Services** - All tabs run in backend in real-time
5. **Persistence** - No data loss even when server is off
6. **Zero Downtime** - No stoppages

## Implementation Architecture

### 1. Backend Services Layer
- **FastAPI WebSocket Server** - Real-time bidirectional communication
- **Redis Pub/Sub** - Message broker for real-time events
- **Background Task Workers** - Continuous monitoring without blocking
- **Persistent Queues** - SQLite/Redis for data durability

### 2. Data Management
- **Deduplication** - Use Redis sets to track seen items
- **Pagination** - Virtual scrolling with batch loading
- **Caching** - Redis for fast data access
- **Persistence** - SQLite database for logs and events

### 3. Components to Build

#### A. Backend API Service (`services/realtime_api/`)
- FastAPI with WebSocket support
- Endpoints for all dashboard tabs
- Real-time event publishing
- Authentication

#### B. WebSocket Manager (`services/websocket_manager.py`)
- Connection handling
- Room/bucket management
- Auto-reconnection
- Heartbeat机制

#### C. Background Workers (`services/workers/`)
- System monitor worker
- GitHub sync worker
- Log aggregator worker
- Health check worker

#### D. Enhanced Dashboard (`projects/comprehensive-dashboard/app.py`)
- WebSocket client integration
- Paginated data displays
- Real-time updates
- Deduplication logic

#### E. Logs Dashboard (`projects/comprehensive-dashboard/logs_dashboard.py`)
- Centralized log viewing
- Log filtering and search
- Real-time log streaming

## File Structure

```
services/
├── realtime_api/
│   ├── main.py              # FastAPI app with WebSocket
│   ├── routes/
│   │   ├── system.py        # System stats endpoints
│   │   ├── github.py        # GitHub endpoints
│   │   ├── logs.py          # Logs endpoints
│   │   └── backup.py        # Backup endpoints
│   ├── models/              # Pydantic models
│   └── utils/
│       ├── websocket.py     # WebSocket manager
│       ├── deduplication.py # Deduplication logic
│       └── pagination.py    # Pagination utilities
├── workers/
│   ├── system_monitor.py   # Continuous system monitoring
│   ├── github_sync.py      # GitHub sync worker
│   └── log_aggregator.py   # Log aggregation worker
├── database/
│   └── db.py               # SQLite + Redis setup
└── config.py               # Configuration

projects/comprehensive-dashboard/
├── app.py                  # Enhanced main dashboard
├── logs_dashboard.py      # Centralized logs
└── requirements.txt        # Updated dependencies
```

## Implementation Steps

### Step 1: Update Requirements
Add: fastapi, uvicorn, websockets, redis, sqlalchemy, alembic

### Step 2: Create Database Layer
- SQLite for persistent storage (logs, events)
- Redis for real-time data and deduplication

### Step 3: Create WebSocket Manager
- Handle multiple connections
- Subscribe to channels
- Broadcast messages
- Reconnection handling

### Step 4: Create Background Workers
- System stats collection
- GitHub API polling
- Log file monitoring
- Health checks

### Step 5: Create FastAPI Backend
- REST endpoints
- WebSocket endpoint
- Authentication

### Step 6: Enhance Dashboard
- WebSocket client
- Pagination component
- Deduplication filter
- Real-time updates

### Step 7: Create Logs Dashboard
- Centralized log view
- Search/filter
- Export functionality

## Technology Stack
- **Backend**: FastAPI + Uvicorn
- **Real-time**: WebSockets + Redis Pub/Sub
- **Caching**: Redis
- **Database**: SQLite (persistent) + Redis (cache)
- **Frontend**: Streamlit + custom JS for WebSocket

## Key Features

### 1. Deduplication
```python
# Use Redis set to track seen IDs
SEEN_ITEMS_KEY = "seen_items:{channel}"

async def add_item(channel, item_id, data):
    if not await redis.sadd(SEEN_ITEMS_KEY.format(channel), item_id):
        return False  # Duplicate
    await redis.publish(channel, json.dumps(data))
    return True
```

### 2. Pagination with Cursor
```python
async def get_paginated_data(channel, cursor=None, limit=50):
    # Get items from cursor position
    items = await redis.lrange(channel, cursor, cursor + limit)
    next_cursor = cursor + limit if len(items) == limit else None
    return items, next_cursor
```

### 3. WebSocket Heartbeat
```python
# Send ping every 30 seconds
async def heartbeat(websocket):
    while True:
        await websocket.send_json({"type": "ping"})
        await asyncio.sleep(30)
```

### 4. Background Worker Pattern
```python
async def worker(channel, task_func, interval):
    while True:
        await task_func()
        await redis.publish(channel, {"status": "heartbeat"})
        await asyncio.sleep(interval)
```

## Configuration

```yaml
# services/config.yaml
websocket:
  host: "0.0.0.0"
  port: 8765
  heartbeat_interval: 30
  max_connections: 100

redis:
  host: "localhost"
  port: 6379
  db: 0

database:
  path: "services/data/realtime.db"

workers:
  system_monitor:
    interval: 5
  github_sync:
    interval: 60
  log_aggregator:
    interval: 1
```

## Running the System

```bash
# Start Redis (required)
docker-compose up -d redis

# Start background workers
python services/workers/start_all.py &

# Start WebSocket server
python services/realtime_api/main.py &

# Start Streamlit dashboard
streamlit run projects/comprehensive-dashboard/app.py
```

## Monitoring
- Dashboard health: `/api/health`
- Worker status: `/api/workers/status`
- Connection count: `/api/ws/stats`

