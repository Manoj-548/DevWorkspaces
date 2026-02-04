"""System Monitor Worker - Continuously monitors system resources"""

import asyncio
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
import logging

import sys
sys.path.insert(0, '/home/manoj/DevWorkspaces')

from services.database import db
from services.websocket_manager import manager
from services.config import WORKER_INTERVALS, CHANNELS

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Continuously monitors system resources"""
    
    def __init__(self):
        self.running = False
        self.stats_history = []
        self._task: Optional[asyncio.Task] = None
    
    async def start(self, interval: int = None):
        """Start the system monitor"""
        interval = interval or WORKER_INTERVALS["system_monitor"]
        self.running = True
        self._task = asyncio.create_task(self._run(interval))
        logger.info(f"System monitor started with interval {interval}s")
    
    async def stop(self):
        """Stop the system monitor"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("System monitor stopped")
    
    async def _run(self, interval: int):
        """Main monitoring loop"""
        while self.running:
            try:
                stats = await self._collect_stats()
                
                # Add to history
                self.stats_history.append(stats)
                if len(self.stats_history) > 100:  # Keep last 100
                    self.stats_history = self.stats_history[-100:]
                
                # Save to database
                await db.save_stats("system", stats)
                
                # Broadcast to subscribers
                await manager.broadcast(CHANNELS["system_stats"], {
                    "type": "system_stats",
                    **stats
                })
                
                # Check thresholds and send alerts
                await self._check_thresholds(stats)
                
            except Exception as e:
                logger.error(f"Error collecting system stats: {e}")
            
            await asyncio.sleep(interval)
    
    async def _collect_stats(self) -> Dict[str, Any]:
        """Collect current system statistics"""
        return {
            "cpu_percent": psutil.cpu_percent(interval=None),
            "cpu_count": psutil.cpu_count(),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_used_gb": psutil.virtual_memory().used / (1024**3),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "disk_used_gb": psutil.disk_usage('/').used / (1024**3),
            "disk_free_gb": psutil.disk_usage('/').free / (1024**3),
            "network_connections": len(psutil.net_connections()),
            "boot_time": psutil.boot_time(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _check_thresholds(self, stats: Dict[str, Any]):
        """Check thresholds and send alerts if exceeded"""
        alerts = []
        
        # CPU threshold (90%)
        if stats["cpu_percent"] >= 90:
            alerts.append({
                "type": "alert",
                "severity": "critical",
                "metric": "cpu",
                "value": stats["cpu_percent"],
                "message": f"CPU usage is critically high: {stats['cpu_percent']}%"
            })
        elif stats["cpu_percent"] >= 80:
            alerts.append({
                "type": "alert",
                "severity": "warning",
                "metric": "cpu",
                "value": stats["cpu_percent"],
                "message": f"CPU usage is high: {stats['cpu_percent']}%"
            })
        
        # Memory threshold (90%)
        if stats["memory_percent"] >= 90:
            alerts.append({
                "type": "alert",
                "severity": "critical",
                "metric": "memory",
                "value": stats["memory_percent"],
                "message": f"Memory usage is critically high: {stats['memory_percent']}%"
            })
        elif stats["memory_percent"] >= 80:
            alerts.append({
                "type": "alert",
                "severity": "warning",
                "metric": "memory",
                "value": stats["memory_percent"],
                "message": f"Memory usage is high: {stats['memory_percent']}%"
            })
        
        # Disk threshold (90%)
        if stats["disk_usage_percent"] >= 90:
            alerts.append({
                "type": "alert",
                "severity": "critical",
                "metric": "disk",
                "value": stats["disk_usage_percent"],
                "message": f"Disk usage is critically high: {stats['disk_usage_percent']}%"
            })
        elif stats["disk_usage_percent"] >= 80:
            alerts.append({
                "type": "alert",
                "severity": "warning",
                "metric": "disk",
                "value": stats["disk_usage_percent"],
                "message": f"Disk usage is high: {stats['disk_usage_percent']}%"
            })
        
        # Broadcast alerts
        for alert in alerts:
            await manager.broadcast(CHANNELS["health"], alert)
            await db.save_log(
                source="system_monitor",
                level=alert["severity"],
                message=alert["message"],
                metadata={"metric": alert["metric"], "value": alert["value"]}
            )
    
    async def get_current_stats(self) -> Dict[str, Any]:
        """Get current system stats"""
        return await self._collect_stats()
    
    async def get_history(self, count: int = 100) -> list:
        """Get historical stats"""
        return self.stats_history[-count:]


# Global instance
system_monitor = SystemMonitor()

