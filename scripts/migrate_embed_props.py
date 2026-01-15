#!/usr/bin/env python
"""
Migrate existing items to embed properties in document content.

This re-saves all items so their properties are embedded for semantic search.
Safe to run multiple times - idempotent.
"""

import sys
sys.path.insert(0, ".")

from agent_native_app.store import ChromaStore, _embed_properties, _PROPS_DELIMITER


def migrate_collection(collection_name: str, persist_dir: str = ".data") -> int:
    """
    Re-save all items in a collection to embed properties.

    Returns count of migrated items.
    """
    store = ChromaStore(collection_name=collection_name, persist_dir=persist_dir)

    # Get all items (no filter, high limit)
    result = store._collection.get(
        include=["documents", "metadatas"],
        limit=10000
    )

    if not result["ids"]:
        print(f"  No items in '{collection_name}'")
        return 0

    migrated = 0
    skipped = 0

    for i, item_id in enumerate(result["ids"]):
        doc = result["documents"][i]
        metadata = result["metadatas"][i]

        # Check if already migrated
        if _PROPS_DELIMITER in doc:
            skipped += 1
            continue

        # Strip internal keys for embedding
        user_metadata = {
            k: v for k, v in metadata.items()
            if k not in {"created_at", "updated_at"}
        }

        # Embed properties
        new_doc = _embed_properties(doc, user_metadata)

        # Update in place
        store._collection.update(
            ids=[item_id],
            documents=[new_doc]
        )
        migrated += 1
        print(f"  Migrated: {doc[:50]}...")

    print(f"  {migrated} migrated, {skipped} already had embedded props")
    return migrated


def main():
    print("Migrating items collection...")
    items_count = migrate_collection("items")

    print("\nMigrating global_context collection...")
    gc_count = migrate_collection("global_context")

    print(f"\nDone! Total migrated: {items_count + gc_count}")


if __name__ == "__main__":
    main()
