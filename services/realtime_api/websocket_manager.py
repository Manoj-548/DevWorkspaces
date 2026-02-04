"""WebSocket Connection Manager for Real-Time Dashboard"""

import json
import asyncio
import uuid
from typing import Dict, Set, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

from fastapi import WebSocket, WebSocketDisconnect
from config import WEBSOCKET_CONFIG

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"


@dataclass
class Client:
    """Represents a connected WebSocket client"""
    id: str
    websocket: WebSocket
    state: ConnectionState = ConnectionState.CONNECTING
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    user_agent: str = ""
    ip_address: str = ""
    retry_count: int = 0
    buffer: List[dict] = field(default_factory=list)
    buffer_size: int = 100


class ConnectionManager:
    """Manages WebSocket connections with support for rooms/channels"""
    
    def __init__(self):
        self.active_connections: Dict[str, Client] = {}
        self.channels: Dict[str, Set[str]] = {}  # channel_name -> set of client_ids
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the connection manager"""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("WebSocket Connection Manager started")
    
    async def stop(self):
        """Stop the connection manager"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for client in list(self.active_connections.values()):
            await self._close_client(client, reason="Server shutdown")
        
        logger.info("WebSocket Connection Manager stopped")
    
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None,
                      user_agent: str = "", ip_address: str = "") -> str:
        """Accept new WebSocket connection"""
        await websocket.accept()
        
        # Generate client ID if not provided
        if not client_id:
            client_id = str(uuid.uuid4())[:8]
        
        client = Client(
            id=client_id,
            websocket=websocket,
            state=ConnectionState.CONNECTED,
            user_agent=user_agent,
            ip_address=ip_address
        )
        
        async with self._lock:
            self.active_connections[client_id] = client
            
            # Initialize client channels
            for channel in ["system_stats", "github_events", "logs", "health", "backup", "processes"]:
                if channel not in self.channels:
                    self.channels[channel] = set()
        
        logger.info(f"Client {client_id} connected. Total: {len(self.active_connections)}")
        
        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "message": "Connected to real-time dashboard",
            "timestamp": datetime.now().isoformat(),
            "channels": list(client.subscriptions)
        })
        
        return client_id
    
    async def disconnect(self, client_id: str, reason: str = "Client disconnect"):
        """Handle client disconnection"""
        async with self._lock:
            client = self.active_connections.pop(client_id, None)
            
            if client:
                # Remove from all channels
                for channel in client.subscriptions:
                    if channel in self.channels:
                        self.channels[channel].discard(client_id)
                
                logger.info(f"Client {client_id} disconnected: {reason}. Total: {len(self.active_connections)}")
    
    async def subscribe(self, client_id: str, channel: str) -> bool:
        """Subscribe client to channel"""
        async with self._lock:
            if client_id not in self.active_connections:
                return False
            
            client = self.active_connections[client_id]
            client.subscriptions.add(channel)
            
            if channel not in self.channels:
                self.channels[channel] = set()
            self.channels[channel].add(client_id)
            
            logger.debug(f"Client {client_id} subscribed to {channel}")
            
            # Send subscription confirmation
            await self.send_to_client(client_id, {
                "type": "subscribed",
                "channel": channel,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
    
    async def unsubscribe(self, client_id: str, channel: str) -> bool:
        """Unsubscribe client from channel"""
        async with self._lock:
            if client_id not in self.active_connections:
                return False
            
            client = self.active_connections[client_id]
            client.subscriptions.discard(channel)
            
            if channel in self.channels:
                self.channels[channel].discard(client_id)
            
            logger.debug(f"Client {client_id} unsubscribed from {channel}")
            
            return True
    
    async def broadcast(self, channel: str, message: dict, exclude: Optional[Set[str]] = None):
        """Broadcast message to all clients subscribed to channel"""
        exclude = exclude or set()
        
        # Get subscribers
        async with self._lock:
            subscribers = self.channels.get(channel, set()).copy()
        
        # Send to all subscribers
        for client_id in subscribers:
            if client_id not in exclude:
                await self.send_to_client(client_id, message)
    
    async def broadcast_to_all(self, message: dict, exclude: Optional[Set[str]] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or set()
        
        async with self._lock:
            all_clients = list(self.active_connections.keys())
        
        for client_id in all_clients:
            if client_id not in exclude:
                await self.send_to_client(client_id, message)
    
    async def send_to_client(self, client_id: str, message: dict):
        """Send message to specific client"""
        async with self._lock:
            client = self.active_connections.get(client_id)
            if not client:
                return False
        
        try:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()
            
            await client.websocket.send_json(message)
            
            # Update last activity
            client.last_activity = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            
            # Mark for reconnection
            client.state = ConnectionState.DISCONNECTED
            
            # Try to buffer the message
            client.buffer.insert(0, message)
            if len(client.buffer) > client.buffer_size:
                client.buffer = client.buffer[:client.buffer_size]
            
            return False
    
    async def receive_from_client(self, client_id: str) -> Optional[dict]:
        """Receive message from client"""
        async with self._lock:
            client = self.active_connections.get(client_id)
            if not client:
                return None
        
        try:
            message = await asyncio.wait_for(
                client.websocket.receive_json(),
                timeout=WEBSOCKET_CONFIG["ping_timeout"]
            )
            
            client.last_activity = datetime.now()
            return message
            
        except asyncio.TimeoutError:
            logger.warning(f"Client {client_id} timeout")
            return None
        except Exception as e:
            logger.error(f"Error receiving from client {client_id}: {e}")
            return None
    
    async def ping_all(self):
        """Ping all clients to check connection health"""
        async with self._lock:
            clients = list(self.active_connections.values())
        
        for client in clients:
            try:
                await client.websocket.send_json({"type": "ping"})
            except Exception:
                client.state = ConnectionState.DISCONNECTED
    
    async def handle_client_message(self, client_id: str, message: dict):
        """Handle incoming message from client"""
        msg_type = message.get("type")
        
        if msg_type == "subscribe":
            channel = message.get("channel")
            if channel:
                await self.subscribe(client_id, channel)
                
        elif msg_type == "unsubscribe":
            channel = message.get("channel")
            if channel:
                await self.unsubscribe(client_id, channel)
                
        elif msg_type == "ping":
            await self.send_to_client(client_id, {"type": "pong"})
            
        elif msg_type == "get_state":
            # Send current state
            async with self._lock:
                client = self.active_connections.get(client_id)
                state = {
                    "type": "state",
                    "subscriptions": list(client.subscriptions) if client else [],
                    "buffered_messages": len(client.buffer) if client else 0,
                    "timestamp": datetime.now().isoformat()
                }
            await self.send_to_client(client_id, state)
            
        elif msg_type == "clear_buffer":
            async with self._lock:
                client = self.active_connections.get(client_id)
                if client:
                    client.buffer.clear()
            await self.send_to_client(client_id, {"type": "buffer_cleared"})
    
    async def get_connection_stats(self) -> dict:
        """Get connection statistics"""
        async with self._lock:
            total = len(self.active_connections)
            channel_counts = {ch: len(subs) for ch, subs in self.channels.items()}
            
            # Calculate active vs idle
            now = datetime.now()
            active = sum(1 for c in self.active_connections.values() 
                        if (now - c.last_activity).seconds < 60)
            
            return {
                "total_connections": total,
                "active_connections": active,
                "idle_connections": total - active,
                "channels": channel_counts,
                "timestamp": now.isoformat()
            }
    
    async def get_client_info(self, client_id: str) -> Optional[dict]:
        """Get information about specific client"""
        async with self._lock:
            client = self.active_connections.get(client_id)
            if not client:
                return None
            
            return {
                "id": client.id,
                "state": client.state.value,
                "subscriptions": list(client.subscriptions),
                "connected_at": client.connected_at.isoformat(),
                "last_activity": client.last_activity.isoformat(),
                "buffered_messages": len(client.buffer),
                "user_agent": client.user_agent,
                "ip_address": client.ip_address
            }
    
    async def _close_client(self, client: Client, reason: str = "Unknown"):
        """Close client connection"""
        try:
            await client.websocket.close()
        except Exception:
            pass
        
        client.state = ConnectionState.DISCONNECTED
        
        # Remove from all channels
        for channel in client.subscriptions:
            if channel in self.channels:
                self.channels[channel].discard(client.id)
    
    async def _periodic_cleanup(self):
        """Periodically clean up stale connections"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                now = datetime.now()
                stale_clients = []
                
                async with self._lock:
                    for client_id, client in self.active_connections.items():
                        # Check for stale connections (no activity for 5 minutes)
                        if (now - client.last_activity).seconds > 300:
                            stale_clients.append(client_id)
                
                # Remove stale clients
                for client_id in stale_clients:
                    await self.disconnect(client_id, reason="Stale connection")
                    logger.warning(f"Removed stale client {client_id}")
                
                # Ping clients if needed
                if len(self.active_connections) > 0:
                    await self.ping_all()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    async def run_client_handler(self, client_id: str):
        """Run client handler loop"""
        client = None
        try:
            async with self._lock:
                client = self.active_connections.get(client_id)
            
            if not client:
                return
            
            while client.state == ConnectionState.CONNECTED:
                message = await self.receive_from_client(client_id)
                
                if message is None:
                    # Connection might be stale
                    continue
                
                await self.handle_client_message(client_id, message)
                
        except WebSocketDisconnect:
            await self.disconnect(client_id, reason="WebSocket disconnect")
        except Exception as e:
            logger.error(f"Client handler error for {client_id}: {e}")
            await self.disconnect(client_id, reason=f"Error: {str(e)}")


# Global connection manager instance
manager = ConnectionManager()

