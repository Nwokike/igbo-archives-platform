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

## Rate Limits

| User Type | Limit |
|-----------|-------|
| Anonymous | 10 requests/hour |
| Authenticated | 50 requests/hour |

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

**Response:**

```json
{
  "id": 1,
  "book_title": "Things Fall Apart",
  "author": "Chinua Achebe",
  "isbn": "978-0385474542",
  "slug": "things-fall-apart",
  "title": "A Masterpiece of African Literature",
  "content_json": {...},
  "external_url": "https://amazon.com/...",
  "cover_image": "/media/books/covers/things-fall-apart.jpg",
  "cover_image_back": null,
  "alternate_cover": null,
  "publisher": "Anchor Books",
  "publication_year": 1958,
  "added_by": {
    "id": 1,
    "username": "johndoe",
    "get_display_name": "John Doe"
  },
  "average_rating": 4.8,
  "rating_count": 42,
  "is_published": true,
  "is_approved": true,
  "created_at": "2026-01-29T12:00:00Z",
  "updated_at": "2026-01-30T10:00:00Z"
}
```

#### Create Book Recommendation (Auth Required)

```http
POST /api/v1/books/
Authorization: Token YOUR_TOKEN
Content-Type: multipart/form-data
```

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `book_title` | string | Yes | Book title |
| `author` | string | Yes | Book author |
| `title` | string | Yes | Recommendation title |
| `content_json` | object | No | EditorJS content |
| `isbn` | string | No | ISBN/ASIN |
| `external_url` | string | No | URL to book info/purchase |
| `publisher` | string | No | Publisher name |
| `publication_year` | integer | No | Publication year |
| `cover_image` | file | No | Front cover image |
| `cover_image_back` | file | No | Back cover image |
| `alternate_cover` | file | No | Alternate edition cover |

**Note:** Created books are pending approval and not immediately published.

#### Update Book (Owner Only)

```http
PUT /api/v1/books/{slug}/
Authorization: Token YOUR_TOKEN
```

#### Delete Book (Owner Only)

```http
DELETE /api/v1/books/{slug}/
Authorization: Token YOUR_TOKEN
```

#### Top-Rated Books

```http
GET /api/v1/books/top_rated/
```

#### Rate a Book (Auth Required)

```http
POST /api/v1/books/{slug}/rate/
Authorization: Token YOUR_TOKEN
Content-Type: application/json
```

**Body:**

```json
{
  "rating": 5,
  "review_text": "An excellent book that captures..."
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `rating` | integer | Yes | Rating 1-5 |
| `review_text` | string | No | Optional review |

**Response:** Returns the created/updated rating.

#### Get Book Ratings

```http
GET /api/v1/books/{slug}/ratings/
```

**Response:**

```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "reader",
      "get_display_name": "Book Reader"
    },
    "rating": 5,
    "review_text": "Excellent book!",
    "created_at": "2026-01-30T12:00:00Z",
    "updated_at": "2026-01-30T12:00:00Z"
  }
]
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

### 429 Too Many Requests

```json
{
  "detail": "Request was throttled. Expected available in X seconds."
}
```

---

## Versioning

The API is versioned via URL path (`/api/v1/`). Future versions will be released at `/api/v2/`, etc.
