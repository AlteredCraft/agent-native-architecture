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


def _filter_metadata(metadata: dict) -> dict:
    """Remove internal keys from metadata for user-facing output."""
    return {k: v for k, v in metadata.items() if k not in _INTERNAL_KEYS}


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
        """Convert ChromaDB result to Item."""
        return Item(
            id=id,
            content=document,
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

        self._collection.add(
            ids=[item_id],
            documents=[content],
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

        self._collection.update(
            ids=[id],
            documents=[new_content],
            metadatas=[new_metadata]
        )

        return Item(
            id=id,
            content=new_content,
            metadata=_filter_metadata(new_metadata),
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
