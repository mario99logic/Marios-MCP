# Mario's MCP

A Model Context Protocol (MCP) server that provides AI clients and agents with tools to interact with external capabilities.

## What is MCP?

MCP (Model Context Protocol) is a standard protocol for AI clients (like agents or desktop apps) to connect to external capabilities (tools) through JSON-RPC messages over a transport (usually stdio or HTTP).

## Tools

This server exposes the following tools:

### `greet`
Returns a personalized greeting.

**Parameters:**
- `name` (string): The name to greet

**Returns:** A greeting string

### `CodingChallengesSolutionFinder`
Finds solution files for coding challenges from the [CodingChallengesFYI/SharedSolutions](https://github.com/CodingChallengesFYI/SharedSolutions) repository.

**Parameters:**
- `name` (string): The challenge name (e.g., 'redis', 'wc')

**Returns:** A list of solution file paths matching the challenge name

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Marios-MCP.git
cd Marios-MCP
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install mcp requests
```

## Usage

Run the server:
```bash
python server.py
```

The server uses stdio transport by default, making it suitable for integration with MCP-compatible clients.

## Connecting to the Server

Configure your MCP client to connect to this server. For example, in Claude Desktop's configuration:

```json
{
  "mcpServers": {
    "marios-mcp": {
      "command": "python",
      "args": ["/path/to/Marios-MCP/server.py"]
    }
  }
}
```

## Dependencies

- Python 3.11+
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP server framework
- [Requests](https://requests.readthedocs.io/) - HTTP library
