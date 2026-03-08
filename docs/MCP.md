# Model Context Protocol (MCP) Guide

The Igbo Archives Platform implements the **Model Context Protocol (MCP)**, which allows AI assistants (like Claude, Cursor, and others) to interact directly with our cultural archives, lore, and book recommendations as if they were built-in tools.

## Why use MCP?

Instead of copy-pasting data, an AI agent connected via MCP can:
- **Search** for specific historical artifacts or proverbs.
- **Retrieve** full details of cultural items to provide accurate information.
- **Add** new contributions (with your permission and token).
- **Preserve** cultural context by having direct access to the source material.

## Connection Endpoint

The MCP server is available at:
```
https://archives.kiri.ng/api/mcp/
```

## Authentication

MCP uses the same **Token Authentication** as our REST API. You must include your token in the configuration for your AI tool.

1. Go to your **[API & MCP Dashboard](/profile/api-dashboard/)**.
2. Generate an API Token.
3. Use this token in your client configuration.

## Available Tools

The following tools are exposed via the MCP endpoint:

### Archives
- `archives_list`: List and filter approved cultural archives.
- `archives_retrieve`: Get full details of a specific archive.
- `archives_create`: Upload new archival material (Auth required).

### Lore
- `lore_list`: Browse cultural lore, folklore, and proverbs.
- `lore_retrieve`: Read full lore content.
- `lore_create`: Contribute new lore (Auth required).

### Books
- `books_list`: Search recommended books on Igbo culture.
- `books_retrieve`: Get book details and reviews.

### Categories
- `categories_list`: List all cultural categories.

## Client Configuration Examples

### Claude Desktop
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "igbo-archives": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Authorization: Token YOUR_API_TOKEN",
        "-H", "Content-Type: application/json",
        "https://archives.kiri.ng/api/mcp/"
      ]
    }
  }
}
```
*(Note: Most MCP clients require a bridge or a specific implementation. Our server uses the standard JSON-RPC over HTTP transport.)*

### Cursor / IDEs
In your IDE's MCP settings, add a new server:
- **Name:** Igbo Archives
- **Type:** SSE (Server-Sent Events) or HTTP
- **URL:** `https://archives.kiri.ng/api/mcp/`
- **Headers:** `Authorization: Token YOUR_API_TOKEN`

## Responsibility & Ethics

When using AI agents to access cultural data, please be mindful of:
- **Accuracy:** Verify AI-generated summaries against the primary archive data.
- **Copyright:** Respect the licensing terms of individual contributions.
- **Culture:** Use the data to preserve and celebrate Igbo heritage.

---
Copyright © 2026 Kiri Research Labs
