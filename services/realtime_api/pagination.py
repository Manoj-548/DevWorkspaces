"""Pagination utilities for streaming data with cursor-based pagination"""

import asyncio
from typing import Any, Dict, Generic, List, Optional, TypeVar, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from config import PAGINATION

logger = logging.getLogger(__name__)


class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


T = TypeVar("T")


@dataclass
class Cursor:
    """Cursor for pagination"""
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)


@dataclass
class PageInfo:
    """Pagination info"""
    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
    total_count: Optional[int] = None
    current_page: int = 0
    total_pages: int = 0


@dataclass
class Edge(Generic[T]):
    """Edge in a connection"""
    node: T
    cursor: str


@dataclass
class Connection(Generic[T]):
    """Connection with edges and page info"""
    edges: List[Edge[T]]
    page_info: PageInfo
    total_count: int = 0


class PaginationManager(Generic[T]):
    """Manages cursor-based pagination for data streams"""
    
    def __init__(self, page_size: int = None, max_page_size: int = None):
        self._default_page_size = page_size or PAGINATION["default_page_size"]
        self._max_page_size = max_page_size or PAGINATION["max_page_size"]
        self._cache: Dict[str, List[T]] = {}  # cursor -> items
        self._index: Dict[int, T] = {}  # position -> item
        self._total_count = 0
        self._lock = asyncio.Lock()
        self._items: List[T] = []
    
    async def add_item(self, item: T, position: int = None):
        """Add item to pagination"""
        async with self._lock:
            if position is None:
                position = len(self._items)
            
            self._items.insert(position, item)
            self._total_count = len(self._items)
    
    async def add_items(self, items: List[T], prepend: bool = False):
        """Add multiple items"""
        async with self._lock:
            if prepend:
                self._items = items + self._items
            else:
                self._items.extend(items)
            self._total_count = len(self._items)
    
    async def get_page(self, after: str = None, first: int = None) -> Connection[T]:
        """Get page of items using cursor"""
        async with self._lock:
            first = min(first or self._default_page_size, self._max_page_size)
            
            # Find start index
            if after:
                start_idx = await self._decode_cursor(after)
                if start_idx is None:
                    start_idx = 0
                start_idx += 1
            else:
                start_idx = 0
            
            # Get items
            end_idx = min(start_idx + first, len(self._items))
            page_items = self._items[start_idx:end_idx]
            
            # Create edges
            edges = []
            for i, item in enumerate(page_items):
                cursor = await self._encode_cursor(start_idx + i, item)
                edges.append(Edge(node=item, cursor=cursor))
            
            # Create page info
            page_info = PageInfo(
                has_next_page=end_idx < len(self._items),
                has_previous_page=start_idx > 0,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                total_count=self._total_count,
                current_page=start_idx // first,
                total_pages=(self._total_count + first - 1) // first if first > 0 else 0
            )
            
            return Connection(
                edges=edges,
                page_info=page_info,
                total_count=self._total_count
            )
    
    async def get_by_offset(self, offset: int = 0, limit: int = None) -> tuple[List[T], PageInfo]:
        """Get items by offset"""
        async with self._lock:
            limit = min(limit or self._default_page_size, self._max_page_size)
            
            end_idx = min(offset + limit, len(self._items))
            items = self._items[offset:end_idx]
            
            page_info = PageInfo(
                has_next_page=end_idx < len(self._items),
                has_previous_page=offset > 0,
                total_count=self._total_count,
                current_page=offset // limit,
                total_pages=(self._total_count + limit - 1) // limit if limit > 0 else 0
            )
            
            return items, page_info
    
    async def get_recent(self, limit: int = None) -> List[T]:
        """Get most recent items (for live feeds)"""
        async with self._lock:
            limit = min(limit or self._default_page_size, self._max_page_size)
            return self._items[-limit:] if limit > 0 else []
    
    async def clear(self):
        """Clear all items"""
        async with self._lock:
            self._items.clear()
            self._total_count = 0
    
    async def count(self) -> int:
        """Get item count"""
        async with self._lock:
            return len(self._items)
    
    async def _encode_cursor(self, position: int, item: T) -> str:
        """Encode position and item into cursor"""
        import base64
        cursor_data = f"{position}:{datetime.now().isoformat()}"
        return base64.urlsafe_b64encode(cursor_data.encode()).decode()
    
    async def _decode_cursor(self, cursor: str) -> Optional[int]:
        """Decode cursor to position"""
        import base64
        try:
            cursor_data = base64.urlsafe_b64decode(cursor.encode()).decode()
            position = int(cursor_data.split(":")[0])
            return position
        except:
            return None


class StreamingPaginator(Generic[T]):
    """Paginator optimized for streaming data with real-time updates"""
    
    def __init__(self, max_buffer_size: int = 1000, page_size: int = 50):
        self._buffer: List[T] = []
        self._max_buffer_size = max_buffer_size
        self._page_size = page_size
        self._lock = asyncio.Lock()
        self._seen_ids: set = set()
        self._total_streamed = 0
        self._total_unique = 0
    
    async def add_item(self, item: T, id_fn: Callable[[T], str] = None):
        """Add item with deduplication"""
        async with self._lock:
            if id_fn:
                item_id = id_fn(item)
                if item_id in self._seen_ids:
                    return False  # Duplicate
                self._seen_ids.add(item_id)
            
            self._buffer.insert(0, item)  # Add to front for newest first
            
            # Trim buffer
            if len(self._buffer) > self._max_buffer_size:
                self._buffer = self._buffer[:self._max_buffer_size]
            
            self._total_unique += 1
            return True  # New item added
    
    async def add_items(self, items: List[T], id_fn: Callable[[T], str] = None):
        """Add multiple items"""
        added_count = 0
        for item in items:
            if await self.add_item(item, id_fn):
                added_count += 1
        return added_count
    
    async def get_page(self, page: int = 0, sort: SortDirection = SortDirection.DESC) -> List[T]:
        """Get page of items"""
        async with self._lock:
            start_idx = page * self._page_size
            end_idx = start_idx + self._page_size
            
            if sort == SortDirection.DESC:
                # Newest first
                page_items = self._buffer[start_idx:end_idx]
            else:
                # Oldest first
                page_items = list(reversed(self._buffer))[-start_idx-1:-end_idx-1:-1] if end_idx < len(self._buffer) else []
                page_items = list(reversed(page_items))
            
            return page_items
    
    async def get_stream(self, batch_size: int = 10, delay: float = 0.5) -> AsyncGenerator[List[T], None]:
        """Generator that yields batches of new items"""
        last_count = 0
        while True:
            async with self._lock:
                current_count = self._total_unique
                new_items = []
                
                if current_count > last_count:
                    # Get new items since last check
                    new_count = current_count - last_count
                    batch = min(new_count, batch_size)
                    new_items = self._buffer[:batch]
                    last_count = current_count
            
            if new_items:
                yield new_items
            else:
                yield []
            
            await asyncio.sleep(delay)
    
    async def get_total_unique(self) -> int:
        """Get count of unique items"""
        async with self._lock:
            return self._total_unique
    
    async def get_stats(self) -> dict:
        """Get statistics"""
        async with self._lock:
            return {
                "buffer_size": len(self._buffer),
                "max_buffer_size": self._max_buffer_size,
                "total_unique": self._total_unique,
                "total_streamed": self._total_streamed,
                "deduplication_rate": (
                    (1 - self._total_unique / max(self._total_streamed, 1)) * 100
                    if self._total_streamed > 0 else 0
                )
            }
    
    async def clear(self):
        """Clear buffer"""
        async with self._lock:
            self._buffer.clear()
            self._seen_ids.clear()
            self._total_streamed = 0
            self._total_unique = 0


class QueryPager(Generic[T]):
    """Pager for query results with filtering"""
    
    def __init__(self):
        self._data: List[T] = []
        self._filters: Dict[str, Any] = {}
        self._sort_field: str = "timestamp"
        self._sort_direction: SortDirection = SortDirection.DESC
        self._lock = asyncio.Lock()
    
    async def set_data(self, data: List[T]):
        """Set source data"""
        async with self._lock:
            self._data = data
    
    async def add_filter(self, field: str, value: Any, operator: str = "eq"):
        """Add filter"""
        async with self._lock:
            self._filters[field] = {"value": value, "operator": operator}
    
    async def remove_filter(self, field: str):
        """Remove filter"""
        async with self._lock:
            self._filters.pop(field, None)
    
    async def clear_filters(self):
        """Clear all filters"""
        async with self._lock:
            self._filters.clear()
    
    async def set_sort(self, field: str, direction: SortDirection = SortDirection.DESC):
        """Set sort field and direction"""
        async with self._lock:
            self._sort_field = field
            self._sort_direction = direction
    
    async def _apply_filters(self, items: List[T]) -> List[T]:
        """Apply filters to items"""
        if not self._filters:
            return items
        
        filtered = []
        for item in items:
            match = True
            for field, filter_def in self._filters.items():
                value = getattr(item, field, None)
                op_value = filter_def["value"]
                operator = filter_def["operator"]
                
                if operator == "eq" and value != op_value:
                    match = False
                elif operator == "ne" and value == op_value:
                    match = False
                elif operator == "contains" and op_value not in str(value):
                    match = False
                elif operator == "gt" and value <= op_value:
                    match = False
                elif operator == "lt" and value >= op_value:
                    match = False
                elif operator == "gte" and value < op_value:
                    match = False
                elif operator == "lte" and value > op_value:
                    match = False
            
            if match:
                filtered.append(item)
        
        return filtered
    
    async def _apply_sort(self, items: List[T]) -> List[T]:
        """Apply sorting to items"""
        return sorted(
            items,
            key=lambda x: getattr(x, self._sort_field, ""),
            reverse=self._sort_direction == SortDirection.DESC
        )
    
    async def query(self, offset: int = 0, limit: int = 50) -> tuple[List[T], int]:
        """Execute query with filters and sorting"""
        async with self._lock:
            # Apply filters
            filtered = await self._apply_filters(self._data)
            
            # Apply sort
            sorted_items = await self._apply_sort(filtered)
            
            # Get total count
            total = len(sorted_items)
            
            # Apply pagination
            result = sorted_items[offset:offset + limit]
            
            return result, total
    
    async def get_all(self) -> List[T]:
        """Get all filtered items"""
        result, _ = await self.query(offset=0, limit=999999)
        return result

