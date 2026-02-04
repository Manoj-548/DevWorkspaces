"""Deduplication utility for preventing duplicate messages in real-time streams"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict
import logging

from config import DEDUPLICATION

logger = logging.getLogger(__name__)


@dataclass
class DedupEntry:
    """Entry in deduplication cache"""
    hash: str
    data: Any
    timestamp: datetime
    channel: str


class DeduplicationManager:
    """Manages deduplication of messages using sliding window and bloom filter"""
    
    def __init__(self):
        self._cache: OrderedDict[str, DedupEntry] = OrderedDict()
        self._seen_hashes: Set[str] = set()
        self._lock = asyncio.Lock()
        self._max_size = DEDUPLICATION["max_queue_size"]
        self._ttl = DEDUPLICATION["ttl"]
        self._bloom_filter_size = 100000  # Bloom filter size
        self._bloom_filter: bytearray = bytearray((self._bloom_filter_size + 7) // 8)
    
    def _compute_hash(self, data: Any, channel: str = "") -> str:
        """Compute hash for data"""
        if isinstance(data, dict):
            # Include channel in hash for channel-specific deduplication
            content = json.dumps(data, sort_keys=True)
            if channel:
                content = f"{channel}:{content}"
        else:
            content = str(data)
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _check_bloom_filter(self, hash_value: str) -> bool:
        """Check if hash is in bloom filter"""
        # Simple bloom filter implementation
        hash_int = int(hash_value, 16)
        bit_positions = [
            hash_int % self._bloom_filter_size,
            (hash_int // 2) % self._bloom_filter_size,
            (hash_int // 4) % self._bloom_filter_size,
        ]
        
        for pos in bit_positions:
            byte_idx = pos // 8
            bit_idx = pos % 8
            if not (self._bloom_filter[byte_idx] & (1 << bit_idx)):
                return False
        
        return True
    
    def _add_to_bloom_filter(self, hash_value: str):
        """Add hash to bloom filter"""
        hash_int = int(hash_value, 16)
        bit_positions = [
            hash_int % self._bloom_filter_size,
            (hash_int // 2) % self._bloom_filter_size,
            (hash_int // 4) % self._bloom_filter_size,
        ]
        
        for pos in bit_positions:
            byte_idx = pos // 8
            bit_idx = pos % 8
            self._bloom_filter[byte_idx] |= (1 << bit_idx)
    
    async def is_duplicate(self, data: Any, channel: str = "") -> bool:
        """Check if data is duplicate"""
        hash_value = self._compute_hash(data, channel)
        
        async with self._lock:
            # Check bloom filter first (fast)
            if self._check_bloom_filter(hash_value):
                # Check cache for confirmation
                if hash_value in self._seen_hashes:
                    return True
                
            return False
    
    async def add(self, data: Any, channel: str = "") -> bool:
        """Add data to deduplication cache (returns False if duplicate)"""
        hash_value = self._compute_hash(data, channel)
        
        async with self._lock:
            # Check bloom filter first
            if self._check_bloom_filter(hash_value):
                # Check cache
                if hash_value in self._seen_hashes:
                    return False  # Duplicate
            
            # Add to cache
            entry = DedupEntry(
                hash=hash_value,
                data=data,
                timestamp=datetime.now(),
                channel=channel
            )
            
            self._cache[hash_value] = entry
            self._seen_hashes.add(hash_value)
            self._add_to_bloom_filter(hash_value)
            
            # Cleanup old entries
            await self._cleanup_locked()
            
            return True
    
    async def add_batch(self, data_list: List[Dict], channel: str = "",
                       id_field: str = "id") -> List[bool]:
        """Add batch of data, checking for duplicates by ID field"""
        results = []
        
        for item in data_list:
            # Use ID field if available
            if id_field in item:
                key = f"{channel}:{item[id_field]}"
                hash_value = hash(key)
            else:
                hash_value = self._compute_hash(item, channel)
            
            async with self._lock:
                if hash_value in self._seen_hashes:
                    results.append(False)  # Duplicate
                else:
                    entry = DedupEntry(
                        hash=hash_value,
                        data=item,
                        timestamp=datetime.now(),
                        channel=channel
                    )
                    self._cache[hash_value] = entry
                    self._seen_hashes.add(hash_value)
                    self._add_to_bloom_filter(hash_value)
                    results.append(True)  # New
        
        async with self._lock:
            await self._cleanup_locked()
        
        return results
    
    async def mark_seen(self, hash_value: str):
        """Mark a specific hash as seen"""
        async with self._lock:
            self._seen_hashes.add(hash_value)
            self._add_to_bloom_filter(hash_value)
    
    async def remove(self, hash_value: str):
        """Remove entry from cache"""
        async with self._lock:
            self._cache.pop(hash_value, None)
            self._seen_hashes.discard(hash_value)
    
    async def clear(self, channel: Optional[str] = None):
        """Clear cache"""
        async with self._lock:
            if channel:
                # Remove entries for specific channel
                to_remove = [h for h, e in self._cache.items() if e.channel == channel]
                for h in to_remove:
                    self._cache.pop(h, None)
                    self._seen_hashes.discard(h)
            else:
                self._cache.clear()
                self._seen_hashes.clear()
                self._bloom_filter = bytearray((self._bloom_filter_size + 7) // 8)
    
    async def get_count(self, channel: Optional[str] = None) -> int:
        """Get count of entries"""
        async with self._lock:
            if channel:
                return sum(1 for e in self._cache.values() if e.channel == channel)
            return len(self._cache)
    
    async def get_stats(self) -> dict:
        """Get deduplication statistics"""
        async with self._lock:
            return {
                "total_entries": len(self._cache),
                "unique_hashes": len(self._seen_hashes),
                "bloom_filter_size": self._bloom_filter_size,
                "by_channel": {}
            }
    
    async def _cleanup_locked(self):
        """Cleanup old entries (must be called with lock held)"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self._ttl)
        
        # Remove expired entries
        expired = [h for h, e in self._cache.items() if e.timestamp < cutoff]
        for h in expired:
            self._cache.pop(h, None)
            self._seen_hashes.discard(h)
        
        # Enforce max size (remove oldest)
        while len(self._cache) > self._max_size:
            oldest_hash = next(iter(self._cache))
            self._cache.pop(oldest_hash, None)
            self._seen_hashes.discard(oldest_hash)
    
    async def periodic_cleanup(self):
        """Run periodic cleanup"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                async with self._lock:
                    await self._cleanup_locked()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Deduplication cleanup error: {e}")


class EventDeduplicator:
    """Event-specific deduplicator using Redis-like patterns"""
    
    def __init__(self, db):
        self.db = db
        self._local_cache: Dict[str, Set[str]] = {}
    
    async def check_and_process(self, event_type: str, event_id: str, 
                                data: Dict, channel: str) -> tuple[bool, bool]:
        """
        Check for duplicate and process event if new
        
        Returns:
            (is_new, was_duplicate)
        """
        # Check Redis first (if available)
        if self.db.redis:
            if await self.db.is_in_set(f"seen:{event_type}", event_id):
                return False, True
        
        # Check local cache
        cache_key = f"{event_type}:{event_id}"
        if cache_key in self._local_cache:
            return False, True
        
        # Mark as seen
        if self.db.redis:
            await self.db.add_to_set(f"seen:{event_type}", event_id)
        
        self._local_cache[cache_key] = event_id
        
        # Save to database
        await self.db.save_event(event_type, event_id, data, channel)
        
        return True, False
    
    async def get_seen_events(self, event_type: str) -> Set[str]:
        """Get all seen event IDs for a type"""
        if self.db.redis:
            return await self.db.get_set_members(f"seen:{event_type}")
        return self._local_cache.get(event_type, set()).copy()


class StreamingDeduplicator:
    """Deduplicator for streaming data with pagination support"""
    
    def __init__(self, page_size: int = 50):
        self._page_size = page_size
        self._seen_ids: Set[str] = set()
        self._pages: List[Dict] = []
        self._current_page = 0
        self._lock = asyncio.Lock()
    
    async def add_item(self, item_id: str, item_data: Dict) -> tuple[bool, int]:
        """
        Add item to stream (deduplicated)
        
        Returns:
            (is_new, page_number)
        """
        async with self._lock:
            if item_id in self._seen_ids:
                return False, -1
            
            self._seen_ids.add(item_id)
            
            # Add to current page or create new page
            page_idx = len(self._pages) - 1
            if page_idx < 0 or len(self._pages[page_idx]["items"]) >= self._page_size:
                # Create new page
                self._pages.append({
                    "page": len(self._pages),
                    "items": [{**item_data, "_id": item_id}],
                    "has_next": True
                })
                # Update previous page
                if page_idx >= 0:
                    self._pages[page_idx]["has_next"] = True
                return True, len(self._pages) - 1
            else:
                self._pages[page_idx]["items"].append({**item_data, "_id": item_id})
                return True, page_idx
    
    async def add_items(self, items: List[Dict], id_field: str = "id") -> List[bool]:
        """Add multiple items"""
        results = []
        for item in items:
            item_id = str(item.get(id_field, ""))
            if not item_id:
                item_id = str(hash(json.dumps(item, sort_keys=True)))
            
            is_new, _ = await self.add_item(item_id, item)
            results.append(is_new)
        
        return results
    
    async def get_page(self, page: int = 0) -> Optional[Dict]:
        """Get page of items"""
        async with self._lock:
            if 0 <= page < len(self._pages):
                return self._pages[page]
            return None
    
    async def get_all_items(self) -> List[Dict]:
        """Get all items from all pages"""
        async with self._lock:
            all_items = []
            for page in self._pages:
                all_items.extend(page["items"])
            return all_items
    
    async def get_item_count(self) -> int:
        """Get total item count"""
        async with self._lock:
            return len(self._seen_ids)
    
    async def clear(self):
        """Clear all data"""
        async with self._lock:
            self._seen_ids.clear()
            self._pages = []
            self._current_page = 0


# Global instances
dedup_manager = DeduplicationManager()
event_deduplicator = None  # Will be initialized with database
streaming_deduplicator = StreamingDeduplicator()

