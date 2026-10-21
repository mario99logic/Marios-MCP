import pytest

import notes


@pytest.fixture(autouse=True)
def temp_store(tmp_path, monkeypatch):
    """Point the notes store at a throwaway file so real notes are untouched."""
    monkeypatch.setattr(notes, "NOTES_FILE", tmp_path / "notes_data.json")


def test_save_then_get_roundtrip():
    notes.save_note("project-x/todo", "ship the thing")
    assert notes.get_note("project-x/todo") == "ship the thing"


def test_save_overwrites_existing_note():
    notes.save_note("k", "first")
    notes.save_note("k", "second")
    assert notes.get_note("k") == "second"


def test_keys_are_stripped():
    notes.save_note("  spaced  ", "body")
    assert notes.get_note("spaced") == "body"


def test_get_missing_note_raises():
    with pytest.raises(KeyError):
        notes.get_note("nope")


@pytest.mark.parametrize("key, content", [("", "body"), ("   ", "body"), ("k", ""), ("k", "  ")])
def test_save_rejects_blank_input(key, content):
    with pytest.raises(ValueError):
        notes.save_note(key, content)


def test_delete_removes_note():
    notes.save_note("k", "body")
    assert notes.delete_note("k") == "Deleted note 'k'."
    with pytest.raises(KeyError):
        notes.get_note("k")


def test_delete_missing_note_raises():
    with pytest.raises(KeyError):
        notes.delete_note("nope")


def test_list_notes_is_sorted_by_key():
    notes.save_note("b", "second")
    notes.save_note("a", "first")

    listed = notes.list_notes()

    assert [entry["key"] for entry in listed] == ["a", "b"]
    assert all(entry["updated_at"] for entry in listed)


def test_list_notes_empty_store():
    assert notes.list_notes() == []


def test_search_matches_key_and_content_case_insensitively():
    notes.save_note("research/llm", "Notes about EMBEDDINGS")
    notes.save_note("other", "unrelated")

    by_content = notes.search_notes("embeddings")
    by_key = notes.search_notes("RESEARCH")

    assert [r["key"] for r in by_content] == ["research/llm"]
    assert [r["key"] for r in by_key] == ["research/llm"]


def test_search_truncates_long_content_with_ellipsis():
    notes.save_note("long", "x" * 250)

    (result,) = notes.search_notes("long")

    assert result["snippet"] == "x" * 200 + "..."


def test_search_flattens_newlines_in_snippet():
    notes.save_note("multi", "line one\nline two")

    (result,) = notes.search_notes("multi")

    assert result["snippet"] == "line one line two"


def test_search_rejects_blank_query():
    with pytest.raises(ValueError):
        notes.search_notes("  ")


def test_append_creates_note_when_missing():
    notes.append_to_note("fresh", "first line")
    assert notes.get_note("fresh") == "first line"


def test_append_joins_with_blank_line():
    notes.save_note("k", "first")
    notes.append_to_note("k", "second")
    assert notes.get_note("k") == "first\n\nsecond"


def test_append_rejects_blank_content():
    with pytest.raises(ValueError):
        notes.append_to_note("k", "")


def test_corrupt_store_is_treated_as_empty():
    notes.NOTES_FILE.write_text("{not json")
    assert notes.list_notes() == []
