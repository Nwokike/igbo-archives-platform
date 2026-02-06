![Igbo Archives Logo](static/images/logos/logo-light.png)

Igbo Archives is a community-driven cultural preservation platform dedicated to documenting, preserving, and celebrating the rich history and heritage of the Igbo people of Nigeria. A project by **Kiri Research Labs**, built with modern web technologies and optimized for a 1GB RAM constraint.

## 🚀 Features

### 📸 Cultural Archives
- **Multi-format Support**: Images, videos, audio recordings, and documents
- **Multi-item Collections**: Upload up to 5 items (photos/videos) per archive entry
- **Rich Metadata**: Location, date, original author, and cultural context
- **Community Uploads**: User-contributed content with moderation workflow
- **Smart Tagging**: Category-based organization with tag system

### ✍️ Community Insights
- **Editor.js Integration**: Rich block-based content editor
- **Collaborative Editing**: Edit suggestions from the community
- **Draft/Publish Workflow**: Save drafts, submit for approval, publish
- **Related Archives**: Link insights to cultural artifacts

### 📚 Book Reviews
- **Igbo Literature**: Reviews of books on Igbo culture and history
- **Rating System**: 5-star rating with detailed reviews
- **Cover Images**: Front and back cover display
- **Publication Details**: ISBN, publisher, year

### 🤖 AI Assistant
- **Igbo-Optimized Models**: Kimi K2 (best Igbo), Llama-4 Scout, Qwen3-32B via Groq
- **Gemini Flash**: Vision analysis with gemini-2.5-flash and gemini-3-flash
- **YarnGPT TTS**: Nigerian-native text-to-speech for Igbo audio output
- **NaijaLingo ASR**: Local speech-to-text for Igbo, Yoruba, Hausa, Nigerian English
- **Cultural Q&A**: Intelligent grounded responses with live archive links

### 🔌 REST API
- **RESTful Endpoints**: `/api/v1/archives/`, `/api/v1/books/`, `/api/v1/categories/`
- **Token Auth**: Secure API token authentication
- **Full Documentation**: See [docs/API.md](docs/API.md)

### 👥 Community Features
- **User Profiles**: Customizable profiles with social links
- **Private Messaging**: Thread-based conversations
- **Notifications**: In-app, email, and push notifications
- **Comments**: Threaded discussions with Cloudflare Turnstile protection

### 📱 Progressive Web App
- **Installable**: Add to home screen on mobile/desktop
- **Offline Ready**: Service worker with caching strategy
- **Push Notifications**: Real-time updates
- **Fast Loading**: Optimized assets and lazy loading

## 🏗️ Architecture


```

┌─────────────────────────────────────────────────────────┐
│                   CLIENT SIDE (Browser)                 │
│ 🎨 UI & Interactivity                                   │
│ └─ HTMX for dynamic updates                             │
│ └─ Tailwind CSS for styling                             │
│ └─ Editor.js for rich content                           │
│ └─ Service Worker for offline/push                      │
└───────────────────────────┬─────────────────────────────┘
│
┌───────────────────────────▼─────────────────────────────┐
│                   SERVER SIDE (Django)                  │
├─────────────────────────────────────────────────────────┤
│ 🎮 Application Layer                                    │
│ └─ Django 5.2 LTS + Gunicorn                            │
│    └─ REST API, Auth, Templates                         │
│                                                         │
│ 💾 Storage Strategy                                     │
│ └─ SQLite with WAL mode (optimized for 1GB RAM)         │
│ └─ Local media storage                                  │
│                                                         │
│ 🤖 AI & External Services                               │
│ ├─ Google Gemini Flash (Vision Analysis)                │
│ ├─ Groq Kimi K2/Llama-4 Scout (Chat)                    │
│ ├─ YarnGPT (Igbo TTS)                                   │
│ ├─ NaijaLingo ASR (Nigerian STT)                        │
│ └─ Brevo (Transactional Email)                          │
│                                                         │
│ ⏰ Background Tasks                                     │
│ └─ Huey (SQLite backend) for async jobs                 │
└─────────────────────────────────────────────────────────┘

```

## 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 6.0, Python 3.13 (uv), Django REST Framework |
| **Database** | SQLite with WAL mode |
| **Task Queue** | Huey (SQLite backend) |
| **Frontend** | Tailwind CSS, HTMX, Editor.js |
| **Server** | Gunicorn + Whitenoise |
| **PWA** | django-pwa, django-webpush |
| **Auth** | django-allauth (Email + Google OAuth) |
| **AI** | Groq (Kimi K2, Llama-4 Scout), Google Gemini Flash, YarnGPT, NaijaLingo ASR |
| **Email** | Brevo (Sendinblue) |

## 📁 Project Structure


```

igbo-archives-platform/
├── igbo_archives/          # Django project settings
│   ├── settings.py         # Main configuration
│   ├── urls.py             # URL routing
│   ├── sqlite_wal.py       # SQLite optimization
│   └── wsgi.py             # WSGI entry point
├── core/                   # Core functionality
│   ├── templates/          # Base templates
│   ├── static/             # CSS, JS, images
│   ├── context_processors.py
│   ├── tasks.py            # Huey background tasks
│   └── validators.py       # Shared validators
├── users/                  # Authentication & profiles
├── archives/               # Cultural archives
├── insights/               # Community articles
├── books/                  # Book reviews
├── api/                    # API endpoints
├── ai/                     # AI assistant features
├── static/                 # Global static files
├── media/                  # User uploads
└── LICENSE                 # Copyright & Licensing terms

```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.13+
- `uv` (Fast Python package manager)
- Node.js 18+ (for Tailwind CSS)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone [https://github.com/Nwokike/igbo-archives-platform.git](https://github.com/Nwokike/igbo-archives-platform.git)
   cd igbo-archives-platform

```

2. **Install dependencies and setup environment**
```bash
uv sync

```


3. **Install Node dependencies (for Tailwind)**
```bash
npm install

```


4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your values

```


5. **Run migrations**
```bash
uv run python manage.py migrate

```


6. **Create cache table**
```bash
uv run python manage.py createcachetable

```


7. **Create superuser**
```bash
uv run python manage.py createsuperuser

```


8. **Build Tailwind CSS**
```bash
npm run build:css

```


9. **Start development server**
```bash
uv run python manage.py runserver

```


10. **Start Huey worker**
```bash
uv run python manage.py run_huey

```



## 🌍 Environment Variables

Copy the example environment file and configure your keys:

```bash
cp .env.example .env

```

## 🚀 Deployment

This project is optimized for deployment on low-memory VMs (1GB RAM) using a `uv`-based workflow:

* **Dependency Management**: `uv` for fast, deterministic builds.
* **WSGI**: Gunicorn (2 workers max).
* **Static Files**: Whitenoise for efficient serving.
* **Database**: SQLite with WAL mode (optimized concurrency).
* **Background Tasks**: Huey (single worker).
* **Automated Cleanup**: GitHub Actions automatically prunes `uv` cache and vacuums system logs.

For detailed deployment instructions, please refer to the internal documentation.

## 📊 Memory Optimization (1GB RAM)

This platform is optimized for deployment on a 1GB RAM VM:

* **SQLite WAL mode**: Reduced cache (32MB) and mmap (64MB)
* **Database cache**: Uses database instead of memory cache
* **Huey workers**: Single worker for background tasks
* **Gunicorn workers**: 2 workers maximum
* **File uploads**: Disk-based, not memory-based
* **Efficient queries**: `select_related`, `prefetch_related`, `only()`

## 🔒 Security Features

* **CSRF Protection**: All forms and APIs protected
* **Cloudflare Turnstile**: Spam protection on public forms
* **SQL Injection Prevention**: Parameterized queries via ORM
* **HTTPS**: Enforced in production with HSTS
* **Secure Cookies**: HttpOnly, Secure, SameSite
* **Rate Limiting**: On uploads, suggestions, and REST API endpoints

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 Licensing & Attribution

Copyright © 2025–2026 **Kiri Research Labs**. All Rights Reserved.

**Igbo Archives Platform** is a proprietary cultural preservation initiative. For the full licensing terms, please see the [LICENSE](https://www.google.com/search?q=file:///c:/Users/nwoki/Desktop/igbo-archives-platform/LICENSE) file.

Operated by Kiri Research Labs.
[Contact Us](mailto:hello@kiriresearch.com) for inquiries.

---

*Preserving Igbo culture for future generations through technology.*