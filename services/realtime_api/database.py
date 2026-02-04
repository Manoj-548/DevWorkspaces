"""Database layer for Real-Time API with SQLite persistence and Redis caching"""

import json
import asyncio
import aiosqlite
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging
import os

from config import DATABASE_CONFIG, REDIS_CONFIG, DATA_RETENTION

logger = logging.getLogger(__name__)


class RealtimeDatabase:
    """Database manager combining SQLite (persistent) and Redis (cache/pub-sub)"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.db_path = DATABASE_CONFIG["path"]
        self._initialized = False
        
    async def connect(self):
        """Initialize connections to Redis and SQLite"""
        # Connect to Redis using environment variable or default
        redis_host = os.getenv("REDIS_HOST", REDIS_CONFIG["host"])
        redis_port = int(os.getenv("REDIS_PORT", REDIS_CONFIG["port"]))
        
        try:
            self.redis = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=REDIS_CONFIG["db"],
                password=REDIS_CONFIG.get("password"),
                decode_responses=True
            )
            await self.redis.ping()
            logger.info(f"Redis connected successfully at {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without Redis.")
            self.redis = None
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite
        await self._init_db()
        self._initialized = True
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
        
    async def _init_db(self):
        """Initialize SQLite database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT,
                    level TEXT,
                    message TEXT,
                    timestamp TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Events table (for deduplication)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT,
                    event_id TEXT UNIQUE,
                    data TEXT,
                    channel TEXT,
                    timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Stats history table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_type TEXT,
                    data TEXT,
                    timestamp TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Connection history
            await db.execute("""
                CREATE TABLE IF NOT EXISTS connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_id TEXT,
                    connected_at TEXT,
                    disconnected_at TEXT,
                    last_activity TEXT
                )
            """)
            
            # Health history
            await db.execute("""
                CREATE TABLE IF NOT EXISTS health_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT,
                    details TEXT,
                    timestamp TEXT
                )
            """)
            
            await db.commit()
            logger.info("SQLite database initialized")
    
    # ==================== Redis Operations ====================
    
    async def publish(self, channel: str, message: Dict[str, Any]):
        """Publish message to Redis channel"""
        if self.redis:
            try:
                await self.redis.publish(channel, json.dumps(message))
            except Exception as e:
                logger.debug(f"Redis publish error: {e}")
    
    async def subscribe(self, channel: str):
        """Subscribe to Redis channel"""
        if self.redis:
            try:
                pubsub = self.redis.pubsub()
                await pubsub.subscribe(channel)
                return pubsub
            except Exception as e:
                logger.debug(f"Redis subscribe error: {e}")
        return None
    
    async def set_cache(self, key: str, value: Any, ttl: int = 300):
        """Set value in Redis cache"""
        if self.redis:
            try:
                await self.redis.setex(
                    f"{REDIS_CONFIG['key_prefix']}{key}",
                    ttl,
                    json.dumps(value)
                )
            except Exception as e:
                logger.debug(f"Redis set_cache error: {e}")
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if self.redis:
            try:
                data = await self.redis.get(f"{REDIS_CONFIG['key_prefix']}{key}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.debug(f"Redis get_cache error: {e}")
        return None
    
    async def add_to_set(self, key: str, *values: str):
        """Add values to Redis set (for deduplication)"""
        if self.redis:
            try:
                await self.redis.sadd(f"{REDIS_CONFIG['key_prefix']}{key}", *values)
            except Exception as e:
                logger.debug(f"Redis add_to_set error: {e}")
    
    async def is_in_set(self, key: str, value: str) -> bool:
        """Check if value is in Redis set"""
        if self.redis:
            try:
                return await self.redis.sismember(f"{REDIS_CONFIG['key_prefix']}{key}", value)
            except Exception as e:
                logger.debug(f"Redis is_in_set error: {e}")
        return False
    
    async def get_set_members(self, key: str) -> set:
        """Get all members of a Redis set"""
        if self.redis:
            try:
                return await self.redis.smembers(f"{REDIS_CONFIG['key_prefix']}{key}")
            except Exception as e:
                logger.debug(f"Redis get_set_members error: {e}")
        return set()
    
    async def push_to_list(self, key: str, *values: str, max_len: int = 1000):
        """Push to list with max length (for streaming buffers)"""
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.lpush(key, *values)
                pipe.ltrim(key, 0, max_len - 1)
                pipe.expire(key, 3600)  # 1 hour TTL
                await pipe.execute()
            except Exception as e:
                logger.debug(f"Redis push_to_list error: {e}")
    
    async def get_list_range(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get range from Redis list"""
        if self.redis:
            try:
                return await self.redis.lrange(key, start, end)
            except Exception as e:
                logger.debug(f"Redis get_list_range error: {e}")
        return []
    
    # ==================== SQLite Operations ====================
    
    async def save_log(self, source: str, level: str, message: str, 
                       metadata: Optional[Dict] = None):
        """Save log entry to SQLite"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO logs (source, level, message, timestamp, metadata) 
                   VALUES (?, ?, ?, ?, ?)""",
                (source, level, message, datetime.now().isoformat(), 
                 json.dumps(metadata) if metadata else None)
            )
            await db.commit()
        
        # Also publish to Redis for real-time subscribers
        await self.publish("channel:logs", {
            "source": source,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        })
    
    async def save_event(self, event_type: str, event_id: str, data: Dict,
                         channel: str) -> bool:
        """Save event (returns False if duplicate)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO events (event_type, event_id, data, channel, timestamp) 
                   VALUES (?, ?, ?, ?, ?)""",
                (event_type, event_id, json.dumps(data), channel, 
                 datetime.now().isoformat())
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def get_events(self, event_type: Optional[str] = None, 
                         limit: int = 100) -> List[Dict]:
        """Get events from SQLite"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if event_type:
                cursor = await db.execute(
                    """SELECT * FROM events WHERE event_type = ? 
                       ORDER BY timestamp DESC LIMIT ?""",
                    (event_type, limit)
                )
            else:
                cursor = await db.execute(
                    """SELECT * FROM events ORDER BY timestamp DESC LIMIT ?""",
                    (limit,)
                )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def save_stats(self, stat_type: str, data: Dict):
        """Save stats to SQLite and Redis buffer"""
        timestamp = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO stats_history (stat_type, data, timestamp) 
                   VALUES (?, ?, ?)""",
                (stat_type, json.dumps(data), timestamp)
            )
            await db.commit()
        
        # Also add to Redis buffer for real-time access
        if self.redis:
            await self.push_to_list(
                f"stats:{stat_type}",
                json.dumps({"data": data, "timestamp": timestamp}),
                max_len=100
            )
        
        await self.publish(f"channel:stats", {"type": stat_type, "data": data})
    
    async def get_stats(self, stat_type: str, limit: int = 100) -> List[Dict]:
        """Get stats history"""
        # Try Redis first
        if self.redis:
            cached = await self.get_list_range(f"stats:{stat_type}", 0, limit - 1)
            if cached:
                return [json.loads(c) for c in cached]
        
        # Fallback to SQLite
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM stats_history WHERE stat_type = ? 
                   ORDER BY timestamp DESC LIMIT ?""",
                (stat_type, limit)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def save_health(self, status: str, details: Dict):
        """Save health check result"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """INSERT INTO health_history (status, details, timestamp) 
                   VALUES (?, ?, ?)""",
                (status, json.dumps(details), datetime.now().isoformat())
            )
            await db.commit()
    
    async def get_health_history(self, limit: int = 100) -> List[Dict]:
        """Get health check history"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM health_history ORDER BY timestamp DESC LIMIT ?""",
                (limit,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_logs(self, source: Optional[str] = None, 
                       level: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """Get logs from SQLite"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """SELECT * FROM logs WHERE 1=1"""
            params = []
            
            if source:
                query += " AND source = ?"
                params.append(source)
            if level:
                query += " AND level = ?"
                params.append(level)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = await db.execute(query, tuple(params))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== Deduplication ====================
    
    async def check_duplicate(self, event_type: str, event_id: str) -> bool:
        """Check if event is duplicate using both Redis and SQLite"""
        # Check Redis first (faster)
        if self.redis:
            if await self.is_in_set(f"seen:{event_type}", event_id):
                return True
        
        # Check SQLite
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """SELECT 1 FROM events WHERE event_type = ? AND event_id = ?""",
                (event_type, event_id)
            )
            row = await cursor.fetchone()
            if row:
                return True
        
        return False
    
    async def mark_seen(self, event_type: str, event_id: str):
        """Mark event as seen in both Redis and SQLite"""
        # Mark in Redis
        if self.redis:
            await self.add_to_set(f"seen:{event_type}", event_id)
        
        # Save to SQLite for persistence
        await self.save_event(event_type, event_id, {}, "system")
    
    # ==================== Cleanup ====================
    
    async def _periodic_cleanup(self):
        """Periodically clean up old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self.cleanup_old_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def cleanup_old_data(self):
        """Remove data older than retention period"""
        now = datetime.now()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Clean logs
            log_cutoff = now - timedelta(days=DATA_RETENTION["logs_days"])
            await db.execute(
                "DELETE FROM logs WHERE created_at < ?",
                (log_cutoff.isoformat(),)
            )
            
            # Clean events
            event_cutoff = now - timedelta(days=DATA_RETENTION["events_days"])
            await db.execute(
                "DELETE FROM events WHERE created_at < ?",
                (event_cutoff.isoformat(),)
            )
            
            # Clean stats
            stats_cutoff = now - timedelta(days=DATA_RETENTION["stats_days"])
            await db.execute(
                "DELETE FROM stats_history WHERE created_at < ?",
                (stats_cutoff.isoformat(),)
            )
            
            await db.commit()
        
        logger.info("Database cleanup completed")
    
    async def close(self):
        """Close all connections"""
        if self.redis:
            await self.redis.close()


# Global database instance
db = RealtimeDatabase()
