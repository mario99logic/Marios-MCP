import re
import requests
from typing import List

from mcp.server.fastmcp import FastMCP

REPO_NAME = "SharedSolutions"
REPO_OWNER = "CodingChallengesFYI"

# Create MCP server.
mcp = FastMCP("Marios_MCP", json_response=True)


@mcp.tool()
def greet(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello {name}"


@mcp.tool()
def CodingChallengesSolutionFinder(name: str) -> List[str]:
    """Find solution files for a specific coding challenge by name (e.g., 'redis', 'wc')."""
    if not name or not name.strip():
        raise ValueError("Challenge name cannot be empty")

    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/README.md"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to fetch README.md: {str(e)}") from e

    # Parse the README to find solution links matching the name.
    solutions = []
    for line in response.text.splitlines():
        # Look for markdown links containing "Solutions/" and the challenge name.
        if "Solutions/" in line and f"challenge-{name.lower()}" in line.lower():
            # Extract the file path from markdown links like [text](path).
            matches = re.findall(r"\(([^)]*Solutions/challenge-[^)]+\.md)\)", line)
            solutions.extend(matches)

    return solutions


@mcp.tool()
def marioCalculate():
    print("calculate2")


if __name__ == "__main__":
    mcp.run(transport="stdio")
