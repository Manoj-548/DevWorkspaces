"""Log Aggregator Worker - Continuously aggregates and streams logs"""

import asyncio
import os
import glob
from datetime import datetime
from typing import Dict, Any, Optional, List, Generator
import logging
from pathlib import Path

import sys
sys.path.insert(0, '/home/manoj/DevWorkspaces')

from services.database import db
from services.websocket_manager import manager
from services.config import WORKER_INTERVALS, CHANNELS

logger = logging.getLogger(__name__)


class LogAggregator:
    """Aggregates logs from multiple sources"""
    
    def __init__(self):
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._watched_files: Dict[str, int] = {}  # path -> last position
        self._log_buffer: List[Dict] = []
        self._max_buffer_size = 1000
    
    async def start(self, interval: int = None):
        """Start the log aggregator"""
        interval = interval or WORKER_INTERVALS["log_aggregator"]
        self.running = True
        self._task = asyncio.create_task(self._run(interval))
        logger.info(f"Log aggregator started with interval {interval}s")
    
    async def stop(self):
        """Stop the log aggregator"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Log aggregator stopped")
    
    async def _run(self, interval: int):
        """Main aggregation loop"""
        while self.running:
            try:
                # Watch standard log files
                await self._watch_log_files()
                
                # Check for new log entries
                await self._process_new_entries()
                
            except Exception as e:
                logger.error(f"Log aggregation error: {e}")
            
            await asyncio.sleep(interval)
    
    async def _watch_log_files(self):
        """Watch standard log files"""
        log_patterns = [
            "/var/log/*.log",
            "/var/log/syslog",
            "/home/*/.cache/**/*.log",
            "/home/manoj/DevWorkspaces/**/*.log",
            "/home/manoj/DevWorkspaces/logs/*.log"
        ]
        
        for pattern in log_patterns:
            try:
                for file_path in glob.glob(os.path.expanduser(pattern)):
                    if os.path.isfile(file_path):
                        await self._tail_file(file_path)
            except Exception as e:
                logger.debug(f"Error watching {pattern}: {e}")
    
    async def _tail_file(self, file_path: str):
        """Tail a log file for new entries"""
        try:
            with open(file_path, 'r') as f:
                # Move to end
                if file_path not in self._watched_files:
                    f.seek(0, 2)  # Go to end
                    self._watched_files[file_path] = f.tell()
                    return
                
                # Read new content
                f.seek(self._watched_files[file_path])
                new_content = f.read()
                
                if new_content:
                    # Process new lines
                    for line in new_content.strip().split('\n'):
                        if line.strip():
                            await self._parse_and_process_log(file_path, line)
                    
                    self._watched_files[file_path] = f.tell()
        
        except Exception as e:
            logger.debug(f"Error tailing {file_path}: {e}")
    
    async def _parse_and_process_log(self, file_path: str, line: str):
        """Parse and process a log line"""
        try:
            # Try to parse common log formats
            log_entry = {
                "source": file_path,
                "raw": line,
                "timestamp": datetime.now().isoformat()
            }
            
            # Determine log level
            line_upper = line.upper()
            if "ERROR" in line_upper or "EXCEPTION" in line_upper:
                log_entry["level"] = "ERROR"
            elif "WARNING" in line_upper or "WARN" in line_upper:
                log_entry["level"] = "WARNING"
            elif "DEBUG" in line_upper:
                log_entry["level"] = "DEBUG"
            else:
                log_entry["level"] = "INFO"
            
            # Extract message (simplified)
            log_entry["message"] = line.strip()[:500]  # Limit message length
            
            # Add to buffer
            self._log_buffer.insert(0, log_entry)
            if len(self._log_buffer) > self._max_buffer_size:
                self._log_buffer = self._log_buffer[:self._max_buffer_size]
            
            # Save to database
            await db.save_log(
                source="log_aggregator",
                level=log_entry["level"],
                message=log_entry["message"],
                metadata={"source": file_path}
            )
            
            # Broadcast to subscribers
            await manager.broadcast(CHANNELS["logs"], {
                "type": "log_entry",
                **log_entry
            })
        
        except Exception as e:
            logger.debug(f"Error parsing log line: {e}")
    
    async def _process_new_entries(self):
        """Process new log entries from buffer"""
        for entry in self._log_buffer[:10]:  # Process up to 10 at a time
            # Already processed in _parse_and_process_log
            pass
    
    async def add_log_entry(self, source: str, level: str, message: str, 
                           metadata: Optional[Dict] = None):
        """Add a log entry directly"""
        entry = {
            "source": source,
            "level": level,
            "message": message,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        }
        
        self._log_buffer.insert(0, entry)
        if len(self._log_buffer) > self._max_buffer_size:
            self._log_buffer = self._log_buffer[:self._max_buffer_size]
        
        # Save to database
        await db.save_log(source, level, message, metadata)
        
        # Broadcast
        await manager.broadcast(CHANNELS["logs"], {
            "type": "log_entry",
            **entry
        })
    
    async def get_recent_logs(self, count: int = 50) -> List[Dict]:
        """Get recent logs from buffer"""
        return self._log_buffer[:count]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        return {
            "running": self.running,
            "watched_files": len(self._watched_files),
            "buffer_size": len(self._log_buffer),
            "max_buffer_size": self._max_buffer_size
        }


# Global instance
log_aggregator = LogAggregator()

