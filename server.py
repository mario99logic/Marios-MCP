import re
import requests
from typing import List
from urllib.parse import urljoin


from mcp.server.fastmcp import FastMCP


REPO_NAME = "SharedSolutions"
REPO_OWNER = "CodingChallengesFYI"
URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/"

# Create MCP server.
mcp = FastMCP("Marios_MCP", json_response=True)


def _fetch(url: str) -> str:
    """Fetch text content from a URL, raising a descriptive error on failure."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch '{url}': {str(e)}") from e


def _fetch_readme() -> str:
    return _fetch(urljoin(URL, "README.md"))


@mcp.tool()
def CodingChallengesSolutionFinder(name: str) -> List[str]:
    """Find solution files for a specific coding challenge by name (e.g., 'redis', 'wc')."""
    if not name or not name.strip():
        raise ValueError("Challenge name cannot be empty")

    solutions = []
    for line in _fetch_readme().splitlines():
        # Look for markdown links containing "Solutions/" and the challenge name.
        if "Solutions/" in line and f"challenge-{name.lower()}" in line.lower():
            # Extract the file path from markdown links like [text](path).
            matches = re.findall(r"\(([^)]*Solutions/challenge-[^)]+\.md)\)", line)
            solutions.extend(matches)

    return solutions


@mcp.tool()
def ReadSolution(path: str) -> str:
    """Fetch and return the full content of a solution file given its relative path (e.g., 'Solutions/challenge-wc/solution.md')."""
    if not path or not path.strip():
        raise ValueError("Path cannot be empty.")

    return _fetch(urljoin(URL, path.lstrip("/")))


@mcp.tool()
def ListAllChallenges() -> List[str]:
    """List the names of all available coding challenges in the SharedSolutions repository."""
    challenges = set()
    for line in _fetch_readme().splitlines():
        matches = re.findall(r"challenge-([a-zA-Z0-9_-]+)", line)
        challenges.update(matches)

    return sorted(challenges)


if __name__ == "__main__":
    mcp.run(transport="stdio")
