"""
Store abstraction layer.

Provides a protocol for persistence operations and a ChromaDB implementation.
The abstraction allows swapping storage backends without changing tool or agent code.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

import chromadb
from chromadb.config import Settings

# Internal metadata keys excluded from user-facing metadata
_INTERNAL_KEYS = {"created_at", "updated_at"}

# Property embedding constants
_PROPS_DELIMITER = "\n---ANA_PROPS---\n"
_DATE_KEY_SUFFIXES = ("_date", "_at", "_time", "_due", "_deadline")
_DATE_KEY_NAMES = frozenset(("due", "deadline", "scheduled", "start", "end"))


def _filter_metadata(metadata: dict) -> dict:
    """Remove internal keys from metadata for user-facing output."""
    return {k: v for k, v in metadata.items() if k not in _INTERNAL_KEYS}


def _is_date_key(key: str) -> bool:
    """Check if a key name suggests it contains a date value."""
    key_lower = key.lower()
    return (
        any(key_lower.endswith(suffix) for suffix in _DATE_KEY_SUFFIXES)
        or key_lower in _DATE_KEY_NAMES
    )


def _format_date_value(value: str) -> str:
    """
    Convert ISO date/datetime to human-readable format.

    Examples:
        '2026-01-13' -> 'Monday January 13 2026'
        '2026-01-13T14:30:00' -> 'Monday January 13 2026 at 2:30 PM'

    Returns original value if not a recognizable date format.
    """
    # Try ISO date: YYYY-MM-DD
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if "T" in value:
            # Has time component
            return dt.strftime("%A %B %d %Y at %-I:%M %p").replace(" 0", " ")
        else:
            # Date only
            return dt.strftime("%A %B %d %Y").replace(" 0", " ")
    except (ValueError, AttributeError):
        return value


def _embed_properties(content: str, metadata: dict | None) -> str:
    """
    Embed properties into document content for semantic search.

    Appends a human-readable representation of properties after a delimiter.
    Dates are converted to readable format (e.g., 'Monday January 13 2026').

    Args:
        content: Original document content
        metadata: Properties to embed (internal keys excluded)

    Returns:
        Content with properties appended after delimiter, or original if no props.
    """
    if not metadata:
        return content

    # Filter out internal keys
    props = {k: v for k, v in metadata.items() if k not in _INTERNAL_KEYS}
    if not props:
        return content

    # Format each property, converting dates to human-readable
    lines = []
    for key, value in props.items():
        if _is_date_key(key) and isinstance(value, str):
            formatted_value = _format_date_value(value)
        else:
            formatted_value = value
        # Convert snake_case to readable format
        readable_key = key.replace("_", " ")
        lines.append(f"{readable_key}: {formatted_value}")

    return content + _PROPS_DELIMITER + "\n".join(lines)


def _strip_properties(stored_content: str) -> str:
    """
    Strip embedded properties from stored content.

    Args:
        stored_content: Content as stored in ChromaDB (may have embedded props)

    Returns:
        Original content without the properties section.
    """
    if _PROPS_DELIMITER not in stored_content:
        return stored_content

    return stored_content.split(_PROPS_DELIMITER, 1)[0]


@dataclass
class Item:
    """A stored item with content and arbitrary metadata."""
    id: str
    content: str
    metadata: dict
    created_at: str
    updated_at: str


class Store(Protocol):
    """Abstract interface for persistence operations."""

    def add(self, content: str, metadata: dict | None = None) -> Item:
        """Store a new item with content and optional metadata."""
        ...

    def get(self, id: str) -> Item | None:
        """Retrieve an item by ID."""
        ...

    def update(self, id: str, content: str | None = None, metadata: dict | None = None) -> Item | None:
        """Update an item's content and/or metadata. Returns None if not found."""
        ...

    def delete(self, id: str) -> bool:
        """Delete an item. Returns True if deleted, False if not found."""
        ...

    def upsert(self, id: str, content: str, metadata: dict | None = None) -> Item:
        """Create or update an item by ID."""
        ...

    def query(
        self,
        text: str | None = None,
        where: dict | None = None,
        limit: int = 10
    ) -> list[Item]:
        """
        Query items by semantic similarity and/or metadata filters.

        Args:
            text: Optional semantic search query
            where: Optional metadata filter (e.g., {"status": "active"})
            limit: Maximum number of results
        """
        ...


class ChromaStore:
    """ChromaDB implementation of the Store protocol."""

    def __init__(self, collection_name: str = "items", persist_dir: str = ".data"):
        """
        Initialize ChromaDB store.

        Args:
            collection_name: Name of the collection (e.g., "items", "memory")
            persist_dir: Directory for persistent storage
        """
        self._client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _now(self) -> str:
        """Get current UTC timestamp as ISO string."""
        return datetime.now(timezone.utc).isoformat()

    def _result_to_item(self, id: str, document: str, metadata: dict) -> Item:
        """Convert ChromaDB result to Item, stripping embedded properties."""
        return Item(
            id=id,
            content=_strip_properties(document),
            metadata=_filter_metadata(metadata),
            created_at=metadata.get("created_at", ""),
            updated_at=metadata.get("updated_at", "")
        )

    def add(self, content: str, metadata: dict | None = None) -> Item:
        """Store a new item."""
        item_id = str(uuid4())
        now = self._now()

        # Merge user metadata with timestamps
        full_metadata = {
            **(metadata or {}),
            "created_at": now,
            "updated_at": now
        }

        # Embed properties into document for semantic search
        stored_content = _embed_properties(content, metadata)

        self._collection.add(
            ids=[item_id],
            documents=[stored_content],
            metadatas=[full_metadata]
        )

        return Item(
            id=item_id,
            content=content,
            metadata=metadata or {},
            created_at=now,
            updated_at=now
        )

    def get(self, id: str) -> Item | None:
        """Retrieve an item by ID."""
        result = self._collection.get(ids=[id], include=["documents", "metadatas"])

        if not result["ids"]:
            return None

        return self._result_to_item(
            id=result["ids"][0],
            document=result["documents"][0],
            metadata=result["metadatas"][0]
        )

    def update(self, id: str, content: str | None = None, metadata: dict | None = None) -> Item | None:
        """Update an item's content and/or metadata."""
        existing = self.get(id)
        if not existing:
            return None

        # Build updated values
        new_content = content if content is not None else existing.content
        new_metadata = {
            **existing.metadata,
            **(metadata or {}),
            "created_at": existing.created_at,
            "updated_at": self._now()
        }

        # Embed properties for semantic search (use user-facing metadata)
        user_metadata = _filter_metadata(new_metadata)
        stored_content = _embed_properties(new_content, user_metadata)

        self._collection.update(
            ids=[id],
            documents=[stored_content],
            metadatas=[new_metadata]
        )

        return Item(
            id=id,
            content=new_content,
            metadata=user_metadata,
            created_at=existing.created_at,
            updated_at=new_metadata["updated_at"]
        )

    def delete(self, id: str) -> bool:
        """Delete an item."""
        existing = self.get(id)
        if not existing:
            return False

        self._collection.delete(ids=[id])
        return True

    def upsert(self, id: str, content: str, metadata: dict | None = None) -> Item:
        """Create or update an item by ID."""
        now = self._now()
        existing = self.get(id)

        full_metadata = {
            **(metadata or {}),
            "created_at": existing.created_at if existing else now,
            "updated_at": now,
        }

        # Embed properties for semantic search
        stored_content = _embed_properties(content, metadata)

        self._collection.upsert(
            ids=[id],
            documents=[stored_content],
            metadatas=[full_metadata]
        )

        return Item(
            id=id,
            content=content,
            metadata=_filter_metadata(full_metadata),
            created_at=full_metadata["created_at"],
            updated_at=now,
        )

    def query(
        self,
        text: str | None = None,
        where: dict | None = None,
        limit: int = 10
    ) -> list[Item]:
        """Query items by semantic similarity and/or metadata filters."""

        if text:
            # Semantic search (with optional metadata filter)
            result = self._collection.query(
                query_texts=[text],
                n_results=limit,
                where=where,
                include=["documents", "metadatas"]
            )
            # Normalize nested structure from query()
            ids = result["ids"][0]
            documents = result["documents"][0]
            metadatas = result["metadatas"][0]
        else:
            # Metadata filter or no filter — use get()
            result = self._collection.get(
                where=where,
                limit=limit,
                include=["documents", "metadatas"]
            )
            ids = result["ids"]
            documents = result["documents"]
            metadatas = result["metadatas"]

        return [
            self._result_to_item(id=ids[i], document=documents[i], metadata=metadatas[i])
            for i in range(len(ids))
        ]
