from mcp.server.fastmcp import FastMCP

# Create MCP server.
mcp = FastMCP("Marios_MCP", json_response=True)


@mcp.tool()
def greet(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello {name}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
