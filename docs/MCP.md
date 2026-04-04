# Model Context Protocol (MCP) Guide

The Igbo Archives Platform implements the **Model Context Protocol (MCP)**, which allows AI assistants (like Claude, Cursor, and others) to interact directly with our cultural archives, lore, and book recommendations as if they were built-in tools.

## Why use MCP?

Instead of copy-pasting data, an AI agent connected via MCP can:
- **Search** for specific historical artifacts or proverbs using the archives and lore tools.
- **Retrieve** full details of cultural items, including nested metadata, to provide accurate information.
- **Add** new contributions directly, including uploading media using public HTTP/HTTPS URLs.
- **Preserve** cultural context by accessing the primary database source.

## Connection Endpoint

The MCP server is available at:
```
https://igboarchives.com.ng/api/mcp/
```

## Authentication

MCP uses **Token Authentication**. You must include your token in the configuration for your AI tool.

1. Go to your **[API & MCP Dashboard](/profile/api-dashboard/)**.
2. Generate an API Token.
3. Use this token in the `Authorization` header of your client configuration.

## Available Tools

The tools follow a `verb_noun` naming convention. When retrieving a specific item, you must wrap the identifier (slug or pk) inside a `kwargs` object in the arguments.

### Authors
- `list_authors`: List all available authors.
- `retrieve_authors`: Get full bio and details. Requires `{"kwargs": {"slug": "author-slug"}}`.

### Categories
- `list_categories`: List all cultural categories.
- `retrieve_categories`: Get category details. Requires `{"kwargs": {"slug": "category-slug"}}`.

### Archives
- `list_archives`: List and filter approved cultural archives.
- `retrieve_archives`: Get full details of a specific archive. Requires `{"kwargs": {"slug": "archive-slug"}}`.
- `create_archives`: Upload new archival material (Auth required). Supports passing public media URLs.
- `featured_archives`: Get a cached random selection of featured archives.
- `recent_archives`: Get the most recently uploaded archives.

### Community Notes
- `list_archive_notes`: List community notes attached to archives.
- `retrieve_archive_notes`: Get details of a specific note. Requires `{"kwargs": {"pk": "note-id"}}`.
- `create_archive_notes`: Append new contextual notes to an existing archive (Auth required).

### Lore
- `list_lore`: Browse cultural lore, folklore, and proverbs.
- `retrieve_lore`: Read full lore content. Requires `{"kwargs": {"slug": "lore-slug"}}`.
- `create_lore`: Contribute new lore (Auth required).

### Books
- `list_books`: Search recommended books on Igbo culture.
- `retrieve_books`: Get book details and reviews. Requires `{"kwargs": {"slug": "book-slug"}}`.
- `top_rated_books`: Get the highest rated books (minimum 3 ratings).
- `rate_books`: Rate a book (Auth required).
- `ratings_books`: Get all ratings for a specific book.

## Client Configuration Examples

### Antigravity / HTTP native clients
Add this configuration to your `mcp_config.json` file:

```json
{
  "mcpServers": {
    "igbo-archives": {
      "serverUrl": "https://igboarchives.com.ng/api/mcp/",
      "headers": {
        "Authorization": "Token YOUR_API_TOKEN",
        "Content-Type": "application/json"
      }
    }
  }
}
```

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
        "https://igboarchives.com.ng/api/mcp/"
      ]
    }
  }
}
```

### Cursor / IDEs
In your IDE's MCP settings, add a new server:
- **Name:** Igbo Archives
- **Type:** HTTP
- **URL:** `https://igboarchives.com.ng/api/mcp/`
- **Headers:** `Authorization: Token YOUR_API_TOKEN`

## Responsibility & Ethics

When using AI agents to access cultural data, please be mindful of:
- **Accuracy:** Verify AI-generated summaries against the primary archive data.
- **Copyright:** Respect the licensing terms of individual contributions.
- **Culture:** Use the data to preserve and celebrate Igbo heritage.
