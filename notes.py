import json
import time
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP


NOTES_FILE = Path(__file__).parent / "notes_data.json"

mcp = FastMCP("Marios_Notes", json_response=True)


def _load() -> dict:
    if not NOTES_FILE.exists():
        return {}
    try:
        return json.loads(NOTES_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    NOTES_FILE.write_text(json.dumps(data, indent=2))


@mcp.tool()
def save_note(key: str, content: str) -> str:
    """Save or overwrite a note under a given key. Use descriptive keys like 'project-x/todo' or 'research/llm-notes'."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")
    if not content or not content.strip():
        raise ValueError("Content cannot be empty.")

    data = _load()
    data[key.strip()] = {
        "content": content,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save(data)
    return f"Saved note '{key}'."


@mcp.tool()
def get_note(key: str) -> str:
    """Retrieve the content of a note by its key."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")

    data = _load()
    entry = data.get(key.strip())
    if entry is None:
        raise KeyError(f"No note found for key '{key}'.")

    return entry["content"]


@mcp.tool()
def delete_note(key: str) -> str:
    """Delete a note by its key."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")

    data = _load()
    if key.strip() not in data:
        raise KeyError(f"No note found for key '{key}'.")

    del data[key.strip()]
    _save(data)
    return f"Deleted note '{key}'."


@mcp.tool()
def list_notes() -> List[dict]:
    """List all saved note keys along with their last-updated timestamps."""
    data = _load()
    return [
        {"key": k, "updated_at": v["updated_at"]}
        for k, v in sorted(data.items())
    ]


@mcp.tool()
def search_notes(query: str) -> List[dict]:
    """Search notes by keyword (case-insensitive). Returns matching keys and content snippets."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    q = query.strip().lower()
    data = _load()
    results = []
    for key, entry in data.items():
        if q in key.lower() or q in entry["content"].lower():
            snippet = entry["content"][:200].replace("\n", " ")
            results.append({
                "key": key,
                "snippet": snippet + ("..." if len(entry["content"]) > 200 else ""),
                "updated_at": entry["updated_at"],
            })
    return sorted(results, key=lambda r: r["updated_at"], reverse=True)


@mcp.tool()
def append_to_note(key: str, content: str) -> str:
    """Append text to an existing note. Creates the note if it doesn't exist yet."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")
    if not content or not content.strip():
        raise ValueError("Content cannot be empty.")

    data = _load()
    key = key.strip()
    existing = data.get(key, {}).get("content", "")
    separator = "\n\n" if existing else ""
    data[key] = {
        "content": existing + separator + content,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save(data)
    return f"Appended to note '{key}'."


if __name__ == "__main__":
    mcp.run(transport="stdio")
