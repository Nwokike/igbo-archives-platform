# Igbo Archives REST API Documentation

## Base URL

```
/api/v1/
```

## Authentication

The API supports two authentication methods:

### Token Authentication
Include the token in the Authorization header:

```
Authorization: Token YOUR_API_TOKEN
```

**How to get a token:**
You can generate and manage your API tokens directly from the **[API & MCP Dashboard](/profile/api-dashboard/)** in your user profile. This dashboard allows you to:
- Generate new tokens
- Revoke existing tokens
- View your current rate limits

---

## Rate Limits

| User Type | Limit |
|-----------|-------|
| Anonymous | 10 requests/hour |
| Authenticated | 100 requests/hour |

---

## Endpoints

### Archives

#### List Archives

```http
GET /api/v1/archives/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in title, description, caption |
| `type` | string | Filter by archive type (image, video, audio, document) |
| `category` | string | Filter by category slug |

**Response:**

```json
[
  {
    "id": 1,
    "title": "Traditional Igbo Mask",
    "slug": "traditional-igbo-mask",
    "archive_type": "image",
    "category_name": "Cultural Artifacts",
    "author_name": "Historical Collection",
    "uploaded_by_name": "John Doe",
    "caption": "A ceremonial mask from Anambra",
    "circa_date": "1920s",
    "location": "Anambra, Nigeria",
    "thumbnail": "/media/archives/thumbnails/mask.jpg",
    "created_at": "2026-01-29T12:00:00Z"
  }
]
```

#### Get Archive Detail

```http
GET /api/v1/archives/{slug}/
```

**Response:**

```json
{
  "id": 1,
  "title": "Traditional Igbo Mask",
  "slug": "traditional-igbo-mask",
  "archive_type": "image",
  "description": "Full description of the artifact...",
  "caption": "A ceremonial mask from Anambra",
  "alt_text": "Wooden mask with carved features",
  "circa_date": "1920s",
  "location": "Anambra, Nigeria",
  "copyright_holder": "National Museum",
  "original_url": "https://source.org/artifact/123",
  "original_identity_number": "NM-2024-001",
  "category": {
    "id": 1,
    "name": "Cultural Artifacts",
    "slug": "cultural-artifacts",
    "description": "Traditional objects and artifacts"
  },
  "uploaded_by": {
    "id": 1,
    "username": "johndoe",
    "get_display_name": "John Doe"
  },
  "tags": ["mask", "igbo", "traditional"],
  "items": [
    {
      "id": 101,
      "item_number": 1,
      "item_type": "image",
      "file_url": "/media/archives/items/mask_front.jpg",
      "caption": "Front view of the mask",
      "description": "Detailed carving on the forehead."
    }
  ],
  "views_count": 150,
  "is_featured": true,
  "created_at": "2026-01-29T12:00:00Z",
  "updated_at": "2026-01-29T14:30:00Z"
}
```

#### Create Archive (Auth Required)

```http
POST /api/v1/archives/
Authorization: Token YOUR_TOKEN
Content-Type: multipart/form-data
```

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Archive title |
| `archive_type` | string | Yes | image, video, audio, document |
| `image` | file | * | Image file (for image type) |
| `video` | file | * | Video file (for video type) |
| `audio` | file | * | Audio file (for audio type) |
| `document` | file | * | Document file (for document type) |
| `description` | string | No | Full description |
| `caption` | string | No | Short caption |
| `alt_text` | string | No | Accessibility text |
| `circa_date` | string | No | Approximate date |
| `location` | string | No | Location info |
| `copyright_holder` | string | No | Copyright owner |
| `original_url` | string | No | Source URL |
| `category_id` | integer | No | Category ID |

---

### Books

#### List Book Recommendations

```http
GET /api/v1/books/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in book title, author, recommendation title |

**Response:**

```json
[
  {
    "id": 1,
    "book_title": "Things Fall Apart",
    "author": "Chinua Achebe",
    "slug": "things-fall-apart",
    "title": "A Masterpiece of African Literature",
    "cover_image": "/media/books/covers/things-fall-apart.jpg",
    "publication_year": 1958,
    "external_url": "https://amazon.com/...",
    "added_by_name": "John Doe",
    "average_rating": 4.8,
    "rating_count": 42,
    "created_at": "2026-01-29T12:00:00Z"
  }
]
```

#### Get Book Detail

```http
GET /api/v1/books/{slug}/
```

---

### Lore (Cultural Preservation)

#### List Lore Posts

```http
GET /api/v1/lore/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in title or excerpt |

**Response:**

```json
[
  {
    "id": 1,
    "title": "The Origin of Yam",
    "slug": "the-origin-of-yam",
    "excerpt": "A traditional folklore about the discovery of yam...",
    "author_name": "Onyeka Nwokike",
    "category_name": "Folklore",
    "featured_image": "/media/lore/yam.jpg",
    "created_at": "2026-03-07T12:00:00Z"
  }
]
```

#### Get Lore Post Detail

```http
GET /api/v1/lore/{slug}/
```

**Response:**

```json
{
  "id": 1,
  "title": "The Origin of Yam",
  "slug": "the-origin-of-yam",
  "content_json": {...},
  "excerpt": "A traditional folklore about the discovery of yam...",
  "featured_image": "/media/lore/yam.jpg",
  "author": {
    "id": 1,
    "username": "nwokike",
    "get_display_name": "Onyeka Nwokike"
  },
  "category": {
    "id": 2,
    "name": "Folklore",
    "slug": "folklore"
  },
  "created_at": "2026-03-07T12:00:00Z",
  "updated_at": "2026-03-07T12:00:00Z"
}
```

#### Create Lore Post (Auth Required)

```http
POST /api/v1/lore/
Authorization: Token YOUR_TOKEN
Content-Type: multipart/form-data
```

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Post title |
| `content_json` | object | Yes | EditorJS content |
| `excerpt` | string | No | Short summary |
| `featured_image` | file | No | Cover image |
| `category_id` | integer | No | Category ID |

---

### Categories

#### List Categories

```http
GET /api/v1/categories/
```

**Response:**

```json
[
  {
    "id": 1,
    "name": "Cultural Artifacts",
    "slug": "cultural-artifacts",
    "description": "Traditional objects and artifacts"
  }
]
```

#### Get Category Detail

```http
GET /api/v1/categories/{slug}/
```

---

## Model Context Protocol (MCP)

The Igbo Archives Platform supports the Model Context Protocol (MCP), allowing AI agents (like Claude or Cursor) to interact with our cultural data as tools.

**Endpoint:** `/api/mcp/`

For detailed instructions on connecting your AI tools to the Igbo Archives, see the **[MCP Documentation](/docs/MCP.md)**.

---

## Error Responses

### 400 Bad Request

```json
{
  "field_name": ["Error message"]
}
```

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found

```json
{
  "detail": "Not found."
}
```

### 429 Too Many Requests

```json
{
  "detail": "Request was throttled. Expected available in X seconds."
}
```

---

## Versioning

The API is versioned via URL path (`/api/v1/`). Future versions will be released at `/api/v2/`, etc.
