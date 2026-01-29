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

To get a token, use Django admin or run:
```bash
python manage.py drf_create_token <username>
```

### Session Authentication
For browser-based clients with active Django session.

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
    "archive_type_display": "Image",
    "category": "Cultural Artifacts",
    "author": "username",
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
  "archive_type_display": "Image",
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
  "author": "username",
  "tags": ["mask", "igbo", "traditional"],
  "image": "/media/archives/mask.jpg",
  "thumbnail": "/media/archives/thumbnails/mask.jpg",
  "views_count": 150,
  "is_featured": true,
  "is_approved": true,
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
| `caption` | string | No | Short caption with source |
| `alt_text` | string | No | Accessibility text |
| `circa_date` | string | No | Approximate date |
| `location` | string | No | Location info |
| `copyright_holder` | string | No | Copyright owner |
| `original_url` | string | No | Source URL |
| `category_id` | integer | No | Category ID |
| `tags` | string | No | Comma-separated tags |

#### Featured Archives
```http
GET /api/v1/archives/featured/
```

#### Recent Archives
```http
GET /api/v1/archives/recent/
```

---

### Books

#### List Book Recommendations
```http
GET /api/v1/books/
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Search in title, author, review |

**Response:**
```json
[
  {
    "id": 1,
    "book_title": "Things Fall Apart",
    "author": "Chinua Achebe",
    "slug": "things-fall-apart",
    "review_title": "A Masterpiece of African Literature",
    "author_user": "reviewer_username",
    "cover_image": "/media/books/covers/things-fall-apart.jpg",
    "publication_year": 1958,
    "average_rating": 4.8,
    "created_at": "2026-01-29T12:00:00Z"
  }
]
```

#### Get Book Detail
```http
GET /api/v1/books/{slug}/
```

#### Top-Rated Books
```http
GET /api/v1/books/top_rated/
```

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

---

## Rate Limits

Currently no rate limits on API endpoints. This may change in future versions.

## Versioning

The API is versioned via URL path (`/api/v1/`). Future versions will be released at `/api/v2/`, etc.
