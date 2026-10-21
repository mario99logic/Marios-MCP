import pytest

import snippets


@pytest.fixture(autouse=True)
def temp_store(tmp_path, monkeypatch):
    """Point the snippet store at a throwaway file so real snippets are untouched."""
    monkeypatch.setattr(snippets, "SNIPPETS_FILE", tmp_path / "snippets_data.json")


def test_save_then_get_roundtrip():
    snippets.save_snippet("python/bisect", "lo = 0", language="Python", description="  binary search  ")

    entry = snippets.get_snippet("python/bisect")

    assert entry["code"] == "lo = 0"
    assert entry["language"] == "python"  # normalized to lowercase
    assert entry["description"] == "binary search"
    assert entry["updated_at"]


def test_language_and_description_default_to_empty():
    snippets.save_snippet("k", "code")

    entry = snippets.get_snippet("k")

    assert entry["language"] == ""
    assert entry["description"] == ""


def test_get_missing_snippet_raises():
    with pytest.raises(KeyError):
        snippets.get_snippet("nope")


@pytest.mark.parametrize("key, code", [("", "code"), ("  ", "code"), ("k", ""), ("k", "   ")])
def test_save_rejects_blank_input(key, code):
    with pytest.raises(ValueError):
        snippets.save_snippet(key, code)


def test_delete_removes_snippet():
    snippets.save_snippet("k", "code")
    assert snippets.delete_snippet("k") == "Deleted snippet 'k'."
    with pytest.raises(KeyError):
        snippets.get_snippet("k")


def test_delete_missing_snippet_raises():
    with pytest.raises(KeyError):
        snippets.delete_snippet("nope")


def test_list_is_sorted_and_omits_code():
    snippets.save_snippet("b", "code b", language="go")
    snippets.save_snippet("a", "code a", language="python")

    listed = snippets.list_snippets()

    assert [entry["key"] for entry in listed] == ["a", "b"]
    assert "code" not in listed[0]


def test_list_filters_by_language_case_insensitively():
    snippets.save_snippet("py", "code", language="python")
    snippets.save_snippet("go", "code", language="go")

    assert [entry["key"] for entry in snippets.list_snippets(language="PYTHON")] == ["py"]


def test_list_empty_store():
    assert snippets.list_snippets() == []


@pytest.mark.parametrize("query", ["binary", "search", "needle"])
def test_search_matches_key_description_and_code(query):
    snippets.save_snippet("python/binary", "needle = 1", description="a search helper")
    snippets.save_snippet("other", "unrelated", description="nothing")

    assert [r["key"] for r in snippets.search_snippets(query)] == ["python/binary"]


def test_search_preview_truncates_long_code():
    snippets.save_snippet("long", "x" * 250)

    (result,) = snippets.search_snippets("long")

    assert result["preview"] == "x" * 200 + "..."


def test_search_preview_flattens_newlines():
    snippets.save_snippet("multi", "line one\nline two")

    (result,) = snippets.search_snippets("multi")

    assert result["preview"] == "line one line two"


def test_search_rejects_blank_query():
    with pytest.raises(ValueError):
        snippets.search_snippets("   ")


def test_corrupt_store_is_treated_as_empty():
    snippets.SNIPPETS_FILE.write_text("{not json")
    assert snippets.list_snippets() == []
