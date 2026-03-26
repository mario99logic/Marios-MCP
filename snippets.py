import json
import time
from pathlib import Path
from typing import List, Optional

from mcp.server.fastmcp import FastMCP


SNIPPETS_FILE = Path(__file__).parent / "snippets_data.json"

mcp = FastMCP("Marios_Snippets", json_response=True)


def _load() -> dict:
    if not SNIPPETS_FILE.exists():
        return {}
    try:
        return json.loads(SNIPPETS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    SNIPPETS_FILE.write_text(json.dumps(data, indent=2))


@mcp.tool()
def save_snippet(key: str, code: str, language: str = "", description: str = "") -> str:
    """Save a reusable code snippet under a given key. Use descriptive keys like 'python/binary-search' or 'go/http-client'."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")
    if not code or not code.strip():
        raise ValueError("Code cannot be empty.")

    data = _load()
    data[key.strip()] = {
        "code": code,
        "language": language.strip().lower(),
        "description": description.strip(),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    _save(data)
    return f"Saved snippet '{key}'."


@mcp.tool()
def get_snippet(key: str) -> dict:
    """Retrieve a code snippet by its key. Returns the code, language, and description."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")

    data = _load()
    entry = data.get(key.strip())
    if entry is None:
        raise KeyError(f"No snippet found for key '{key}'.")

    return entry


@mcp.tool()
def delete_snippet(key: str) -> str:
    """Delete a code snippet by its key."""
    if not key or not key.strip():
        raise ValueError("Key cannot be empty.")

    data = _load()
    if key.strip() not in data:
        raise KeyError(f"No snippet found for key '{key}'.")

    del data[key.strip()]
    _save(data)
    return f"Deleted snippet '{key}'."


@mcp.tool()
def list_snippets(language: Optional[str] = None) -> List[dict]:
    """List all saved snippets. Optionally filter by language (e.g., 'python', 'go')."""
    data = _load()
    results = []
    for key, entry in sorted(data.items()):
        if language and entry.get("language") != language.strip().lower():
            continue
        results.append({
            "key": key,
            "language": entry.get("language", ""),
            "description": entry.get("description", ""),
            "updated_at": entry["updated_at"],
        })
    return results


@mcp.tool()
def search_snippets(query: str) -> List[dict]:
    """Search snippets by keyword across keys, descriptions, and code (case-insensitive)."""
    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    q = query.strip().lower()
    data = _load()
    results = []
    for key, entry in data.items():
        if (
            q in key.lower()
            or q in entry.get("description", "").lower()
            or q in entry["code"].lower()
        ):
            snippet = entry["code"][:200].replace("\n", " ")
            results.append({
                "key": key,
                "language": entry.get("language", ""),
                "description": entry.get("description", ""),
                "preview": snippet + ("..." if len(entry["code"]) > 200 else ""),
                "updated_at": entry["updated_at"],
            })
    return sorted(results, key=lambda r: r["updated_at"], reverse=True)


if __name__ == "__main__":
    mcp.run(transport="stdio")
