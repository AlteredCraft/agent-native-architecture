"""Tests for store module, focusing on property embedding for semantic search."""

import tempfile

import pytest

from agent_native_app.store import (
    ChromaStore,
    _embed_properties,
    _format_date_value,
    _is_date_key,
    _PROPS_DELIMITER,
    _strip_properties,
)


class TestIsDateKey:
    """Tests for _is_date_key helper."""

    def test_keys_with_date_suffix(self):
        assert _is_date_key("due_date") is True
        assert _is_date_key("start_date") is True
        assert _is_date_key("end_date") is True

    def test_keys_with_at_suffix(self):
        assert _is_date_key("created_at") is True
        assert _is_date_key("updated_at") is True
        assert _is_date_key("deleted_at") is True

    def test_keys_with_time_suffix(self):
        assert _is_date_key("start_time") is True
        assert _is_date_key("end_time") is True

    def test_keys_with_due_suffix(self):
        assert _is_date_key("task_due") is True

    def test_keys_with_deadline_suffix(self):
        assert _is_date_key("project_deadline") is True

    def test_exact_date_key_names(self):
        assert _is_date_key("due") is True
        assert _is_date_key("deadline") is True
        assert _is_date_key("scheduled") is True
        assert _is_date_key("start") is True
        assert _is_date_key("end") is True

    def test_case_insensitive(self):
        assert _is_date_key("DUE_DATE") is True
        assert _is_date_key("Due_Date") is True
        assert _is_date_key("DEADLINE") is True

    def test_non_date_keys(self):
        assert _is_date_key("status") is False
        assert _is_date_key("priority") is False
        assert _is_date_key("type") is False
        assert _is_date_key("project") is False
        assert _is_date_key("name") is False


class TestFormatDateValue:
    """Tests for _format_date_value helper."""

    def test_iso_date_only(self):
        result = _format_date_value("2026-01-13")
        assert "January" in result
        assert "13" in result
        assert "2026" in result
        # Should include day of week
        assert "Tuesday" in result

    def test_iso_datetime(self):
        result = _format_date_value("2026-01-13T14:30:00")
        assert "January" in result
        assert "13" in result
        assert "2026" in result
        assert "2:30 PM" in result

    def test_iso_datetime_with_timezone(self):
        result = _format_date_value("2026-01-13T14:30:00Z")
        assert "January" in result
        assert "2:30 PM" in result

    def test_non_date_value_returned_unchanged(self):
        assert _format_date_value("not-a-date") == "not-a-date"
        assert _format_date_value("active") == "active"
        assert _format_date_value("123") == "123"

    def test_empty_string(self):
        assert _format_date_value("") == ""


class TestEmbedProperties:
    """Tests for _embed_properties helper."""

    def test_basic_embedding(self):
        content = "Buy groceries"
        metadata = {"type": "task", "status": "active"}
        result = _embed_properties(content, metadata)

        assert result.startswith("Buy groceries")
        assert _PROPS_DELIMITER in result
        assert "type: task" in result
        assert "status: active" in result

    def test_date_formatting(self):
        content = "Review report"
        metadata = {"due_date": "2026-01-13"}
        result = _embed_properties(content, metadata)

        assert "due date: Tuesday January 13 2026" in result

    def test_snake_case_to_readable(self):
        content = "Task"
        metadata = {"due_date": "2026-01-13", "start_time": "2026-01-13T09:00:00"}
        result = _embed_properties(content, metadata)

        assert "due date:" in result
        assert "start time:" in result
        # Original snake_case should not appear
        assert "due_date:" not in result
        assert "start_time:" not in result

    def test_none_metadata(self):
        assert _embed_properties("Hello", None) == "Hello"

    def test_empty_metadata(self):
        assert _embed_properties("Hello", {}) == "Hello"

    def test_internal_keys_excluded(self):
        content = "Task"
        metadata = {"type": "task", "created_at": "2026-01-01", "updated_at": "2026-01-02"}
        result = _embed_properties(content, metadata)

        assert "type: task" in result
        assert "created_at" not in result
        assert "updated_at" not in result

    def test_preserves_original_content(self):
        content = "Multi\nline\ncontent"
        metadata = {"type": "note"}
        result = _embed_properties(content, metadata)

        assert result.startswith("Multi\nline\ncontent")


class TestStripProperties:
    """Tests for _strip_properties helper."""

    def test_strips_embedded_properties(self):
        stored = f"Buy groceries{_PROPS_DELIMITER}type: task\nstatus: active"
        result = _strip_properties(stored)
        assert result == "Buy groceries"

    def test_content_without_delimiter_unchanged(self):
        content = "Plain content without properties"
        assert _strip_properties(content) == content

    def test_only_splits_on_first_delimiter(self):
        # Edge case: delimiter appears in properties section
        stored = f"Content{_PROPS_DELIMITER}prop: value{_PROPS_DELIMITER}extra"
        result = _strip_properties(stored)
        assert result == "Content"

    def test_preserves_multiline_content(self):
        stored = f"Line 1\nLine 2\nLine 3{_PROPS_DELIMITER}type: note"
        result = _strip_properties(stored)
        assert result == "Line 1\nLine 2\nLine 3"


class TestChromaStoreIntegration:
    """Integration tests for ChromaStore with property embedding."""

    @pytest.fixture
    def store(self):
        """Create a temporary ChromaStore for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ChromaStore(collection_name="test_items", persist_dir=tmpdir)

    def test_add_embeds_properties(self, store):
        item = store.add(
            content="Review report",
            metadata={"type": "task", "due_date": "2026-01-13"}
        )

        # Returned content should be clean
        assert item.content == "Review report"
        assert _PROPS_DELIMITER not in item.content

        # Stored content should have embedded props
        raw = store._collection.get(ids=[item.id], include=["documents"])
        stored_doc = raw["documents"][0]
        assert _PROPS_DELIMITER in stored_doc
        assert "January 13 2026" in stored_doc

    def test_get_strips_properties(self, store):
        item = store.add(
            content="Task content",
            metadata={"status": "active"}
        )

        retrieved = store.get(item.id)
        assert retrieved.content == "Task content"
        assert _PROPS_DELIMITER not in retrieved.content

    def test_query_strips_properties(self, store):
        store.add(content="First task", metadata={"type": "task"})
        store.add(content="Second task", metadata={"type": "task"})

        results = store.query(text="task", limit=10)
        for item in results:
            assert _PROPS_DELIMITER not in item.content

    def test_query_finds_by_date(self, store):
        store.add(
            content="Meeting with client",
            metadata={"type": "task", "due_date": "2026-01-15"}
        )

        # Semantic search should find by date
        results = store.query(text="January 15 Wednesday", limit=5)
        assert len(results) > 0
        assert "Meeting with client" in results[0].content

    def test_update_reembeds_properties(self, store):
        item = store.add(
            content="Original task",
            metadata={"status": "active"}
        )

        # Update with new property
        updated = store.update(item.id, metadata={"priority": "high"})
        assert updated.content == "Original task"

        # Check stored doc has both properties
        raw = store._collection.get(ids=[item.id], include=["documents"])
        stored_doc = raw["documents"][0]
        assert "status: active" in stored_doc
        assert "priority: high" in stored_doc

    def test_update_content_reembeds(self, store):
        item = store.add(
            content="Original",
            metadata={"type": "task"}
        )

        updated = store.update(item.id, content="Updated content")
        assert updated.content == "Updated content"

        raw = store._collection.get(ids=[item.id], include=["documents"])
        stored_doc = raw["documents"][0]
        assert stored_doc.startswith("Updated content")
        assert "type: task" in stored_doc

    def test_upsert_embeds_properties(self, store):
        item = store.upsert(
            id="custom-id",
            content="Upserted item",
            metadata={"category": "test"}
        )

        assert item.content == "Upserted item"

        raw = store._collection.get(ids=["custom-id"], include=["documents"])
        stored_doc = raw["documents"][0]
        assert "category: test" in stored_doc

    def test_metadata_still_works_for_filtering(self, store):
        store.add(content="Active task", metadata={"status": "active"})
        store.add(content="Completed task", metadata={"status": "completed"})

        # Metadata filtering should still work
        active_results = store.query(where={"status": "active"}, limit=10)
        assert len(active_results) == 1
        assert "Active task" in active_results[0].content

    def test_legacy_content_without_delimiter(self, store):
        # Simulate legacy item without embedded props
        store._collection.add(
            ids=["legacy-id"],
            documents=["Legacy content without props"],
            metadatas=[{"type": "old", "created_at": "2025-01-01", "updated_at": "2025-01-01"}]
        )

        # Should retrieve cleanly
        item = store.get("legacy-id")
        assert item.content == "Legacy content without props"
