"""FastAPI Real-Time API Server with WebSocket Support"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import WEBSOCKET_CONFIG
from websocket_manager import manager
from database import db
from deduplication import dedup_manager
from pagination import StreamingPaginator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="DevWorkspaces Real-Time API",
    description="Real-time WebSocket API for DevWorkspaces Dashboard",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global paginators
system_stats_paginator = StreamingPaginator(max_buffer_size=500, page_size=50)
logs_paginator = StreamingPaginator(max_buffer_size=2000, page_size=100)
processes_paginator = StreamingPaginator(max_buffer_size=200, page_size=20)


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup():
    logger.info("Starting Real-Time API Server...")
    await db.connect()
    await manager.start()
    asyncio.create_task(heartbeat_loop())
    logger.info("Real-Time API Server started")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
    await manager.stop()
    await db.close()


# ==================== WebSocket Endpoint ====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    user_agent = websocket.headers.get("user-agent", "")
    
    try:
        client_id = await manager.connect(
            websocket,
            client_id=client_id,
            user_agent=user_agent
        )
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return
    
    await manager.subscribe(client_id, "system_stats")
    await manager.subscribe(client_id, "logs")
    await manager.subscribe(client_id, "health")
    
    try:
        while True:
            message = await manager.receive_from_client(client_id)
            if message is None:
                continue
            
            msg_type = message.get("type")
            
            if msg_type == "subscribe":
                channel = message.get("channel")
                if channel:
                    await manager.subscribe(client_id, channel)
            
            elif msg_type == "unsubscribe":
                channel = message.get("channel")
                if channel:
                    await manager.unsubscribe(client_id, channel)
            
            elif msg_type == "ping":
                await manager.send_to_client(client_id, {"type": "pong"})
            
            elif msg_type == "get_stats":
                stats = await manager.get_connection_stats()
                await manager.send_to_client(client_id, {"type": "connection_stats", **stats})
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await manager.disconnect(client_id)


# ==================== REST Endpoints ====================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    details: Dict[str, Any]


@app.get("/api/health", response_model=HealthResponse)
async def get_health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "details": {
            "websocket_connections": len(manager.active_connections),
            "redis_connected": db.redis is not None
        }
    }


@app.get("/api/stats")
async def get_stats():
    return await manager.get_connection_stats()


@app.get("/api/system/stats")
async def get_system_stats():
    import psutil
    
    stats = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent,
        "network_connections": len(psutil.net_connections()),
        "timestamp": datetime.now().isoformat()
    }
    
    await system_stats_paginator.add_item(stats)
    await db.save_stats("system", stats)
    
    await manager.broadcast("system_stats", {"type": "system_stats", **stats})
    
    return stats


@app.get("/api/system/stats/history")
async def get_system_stats_history(limit: int = Query(default=100, le=1000)):
    stats = await db.get_stats("system", limit=limit)
    return {"stats": stats, "count": len(stats)}


class LogEntry(BaseModel):
    source: str
    level: str
    message: str
    metadata: Optional[Dict] = None


@app.post("/api/logs")
async def create_log(entry: LogEntry):
    await db.save_log(entry.source, entry.level, entry.message, entry.metadata)
    
    await logs_paginator.add_item({
        "source": entry.source,
        "level": entry.level,
        "message": entry.message,
        "timestamp": datetime.now().isoformat(),
        "metadata": entry.metadata
    })
    
    return {"status": "logged"}


@app.get("/api/logs")
async def get_logs(source: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    logs = await db.get_logs(source=source, level=level, limit=limit)
    return {"logs": logs, "count": len(logs)}


@app.get("/api/github/status")
async def get_github_status():
    import requests
    
    github_repo = "Manoj-548/DevWorkspaces"
    headers = {}
    github_token = os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    
    try:
        response = requests.get(
            f"https://api.github.com/repos/{github_repo}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            repo_data = response.json()
            return {
                "stars": repo_data.get('stargazers_count', 0),
                "forks": repo_data.get('forks_count', 0),
                "open_issues": repo_data.get('open_issues_count', 0),
                "timestamp": datetime.now().isoformat()
            }
        return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/processes")
async def get_processes():
    import psutil
    
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            info = proc.info
            if 'python' in info['name'].lower() or 'streamlit' in info['name'].lower():
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu_percent": info['cpu_percent'],
                    "memory_percent": info['memory_percent']
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    
    for proc in processes:
        await processes_paginator.add_item(proc)
    
    return {"processes": processes, "count": len(processes)}


@app.get("/api/dedup/stats")
async def get_dedup_stats():
    return await dedup_manager.get_stats()


@app.delete("/api/dedup/clear")
async def clear_dedup_cache(channel: Optional[str] = None):
    await dedup_manager.clear(channel=channel)
    return {"status": "cleared"}


# ==================== Background Tasks ====================

async def heartbeat_loop():
    while True:
        try:
            import psutil
            stats = {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "timestamp": datetime.now().isoformat()
            }
            
            await system_stats_paginator.add_item(stats)
            await db.save_stats("system", stats)
            
            await manager.broadcast("health", {"type": "heartbeat", **stats})
            
        except Exception as e:
            logger.error(f"Heartbeat error: {e}")
        
        await asyncio.sleep(30)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=WEBSOCKET_CONFIG["host"], port=WEBSOCKET_CONFIG["port"])
