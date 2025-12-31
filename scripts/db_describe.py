#!/usr/bin/env python3
"""
Describe ChromaDB collections and their contents.

Usage:
    uv run python scripts/db_describe.py [--samples N]
"""

import argparse
import json
from pathlib import Path

import chromadb
from chromadb.config import Settings


def describe_db(persist_dir: str = ".data", show_samples: int = 0):
    """Describe all collections in the ChromaDB."""

    db_path = Path(persist_dir)
    if not db_path.exists():
        print(f"Database not found at {persist_dir}")
        return

    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )

    collections = client.list_collections()

    if not collections:
        print("No collections found.")
        return

    # Resolve absolute path for CLI commands
    abs_path = db_path.resolve()

    print(f"Database: {persist_dir}")
    print(f"Collections: {len(collections)}")
    print("=" * 60)

    for collection in collections:
        print(f"\n📁 Collection: {collection.name}")
        print("-" * 40)

        # CLI browse command
        print(f"  Browse: chroma browse {collection.name} --path {abs_path}")

        # Collection metadata
        if collection.metadata:
            print(f"  Config: {collection.metadata}")

        # Get count
        count = collection.count()
        print(f"  Items: {count}")

        if count == 0:
            continue

        # Get all items to analyze metadata keys
        result = collection.get(
            limit=min(count, 100),  # Sample up to 100 for analysis
            include=["metadatas"]
        )

        # Collect unique metadata keys and their types
        metadata_keys: dict[str, set] = {}
        for meta in result["metadatas"]:
            for key, value in meta.items():
                if key not in metadata_keys:
                    metadata_keys[key] = set()
                metadata_keys[key].add(type(value).__name__)

        if metadata_keys:
            print(f"  Metadata fields:")
            for key, types in sorted(metadata_keys.items()):
                types_str = ", ".join(sorted(types))
                print(f"    - {key}: {types_str}")

        # Collect unique values for categorical fields (excluding timestamps)
        categorical_fields = ["type", "status", "priority", "key", "value_type"]
        for field in categorical_fields:
            if field in metadata_keys:
                values = set()
                for meta in result["metadatas"]:
                    if field in meta:
                        values.add(str(meta[field]))
                if values and len(values) <= 10:  # Only show if reasonable number
                    print(f"  {field} values: {', '.join(sorted(values))}")

        # Show sample items
        if show_samples > 0:
            sample_result = collection.get(
                limit=show_samples,
                include=["documents", "metadatas"]
            )
            print(f"\n  Sample items ({min(show_samples, count)}):")
            for i, item_id in enumerate(sample_result["ids"]):
                doc = sample_result["documents"][i]
                meta = sample_result["metadatas"][i]
                # Truncate long content
                doc_preview = doc[:80] + "..." if len(doc) > 80 else doc
                print(f"\n    [{item_id[:8]}] {doc_preview}")
                # Show non-timestamp metadata, pretty printed
                filtered_meta = {k: v for k, v in meta.items()
                               if k not in ("created_at", "updated_at")}
                if filtered_meta:
                    pretty = json.dumps(filtered_meta, indent=2)
                    # Indent each line for alignment
                    indented = "\n".join("      " + line for line in pretty.split("\n"))
                    print(indented)

    # Footer with CLI docs link
    print("\n" + "=" * 60)
    print("Chroma CLI: https://docs.trychroma.com/docs/cli/install")


def main():
    parser = argparse.ArgumentParser(description="Describe ChromaDB collections")
    parser.add_argument(
        "--samples", "-s",
        type=int,
        default=0,
        help="Number of sample items to show per collection"
    )
    parser.add_argument(
        "--db", "-d",
        type=str,
        default=".data",
        help="Path to ChromaDB directory (default: .data)"
    )

    args = parser.parse_args()
    describe_db(persist_dir=args.db, show_samples=args.samples)


if __name__ == "__main__":
    main()
