"""Configuration for Real-Time API Service"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    "host": "0.0.0.0",
    "port": 8765,
    "heartbeat_interval": 30,
    "max_connections": 100,
    "ping_timeout": 60,
}

# Redis Configuration
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD", None),
    "key_prefix": "realtime:",
}

# SQLite Database for persistence
DATABASE_CONFIG = {
    "path": str(BASE_DIR / "data" / "realtime.db"),
}

# Worker Intervals (seconds)
WORKER_INTERVALS = {
    "system_monitor": 5,
    "github_sync": 60,
    "log_aggregator": 2,
    "health_check": 30,
    "backup_monitor": 300,
}

# Channels for Pub/Sub
CHANNELS = {
    "system_stats": "channel:system_stats",
    "github_events": "channel:github_events",
    "logs": "channel:logs",
    "health": "channel:health",
    "backup": "channel:backup",
    "processes": "channel:processes",
}

# Deduplication Settings
DEDUPLICATION = {
    "ttl": 3600,  # Track items for 1 hour
    "max_queue_size": 10000,
}

# Pagination Settings
PAGINATION = {
    "default_page_size": 50,
    "max_page_size": 100,
}

# Logging Configuration
LOGGING = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": str(BASE_DIR / "logs" / "realtime_api.log"),
}

# GitHub Configuration
GITHUB_CONFIG = {
    "api_url": "https://api.github.com",
    "poll_interval": 60,
}

# Data retention
DATA_RETENTION = {
    "logs_days": 7,
    "events_days": 1,
    "stats_days": 30,
}

