![Igbo Archives Logo](static/images/logos/logo-light.png)

Igbo Archives is a community-driven cultural preservation platform dedicated to documenting, preserving, and celebrating the rich history and heritage of the Igbo people of Nigeria. Built with modern web technologies and optimized for a 1GB RAM constraint.

## 🚀 Features

### 📸 Cultural Archives
- **Multi-format Support**: Images, videos, audio recordings, and documents
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

### 🤖 AI Assistant (Coming Soon)
- **Igbo Archives AI**: Powered by Groq (LLaMA 3.1) and Google Gemini
- **Archive Analysis**: AI-powered image and content analysis
- **Text-to-Speech**: Listen to content being read aloud
- **Cultural Q&A**: Ask questions about Igbo culture and history

### 👥 Community Features
- **User Profiles**: Customizable profiles with social links
- **Private Messaging**: Thread-based conversations
- **Notifications**: In-app, email, and push notifications
- **Comments**: Threaded discussions with reCAPTCHA protection

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
│ └─ Django 5.2 + Gunicorn                                │
│    └─ REST endpoints, Auth, Templates                   │
│                                                         │
│ 💾 Storage Strategy                                     │
│ └─ SQLite with WAL mode (optimized for 1GB RAM)         │
│ └─ Local media storage                                  │
│                                                         │
│ 🤖 AI & External Services                               │
│ ├─ Google Gemini (Image Analysis)                       │
│ ├─ Groq LLaMA 3.1 (Chat & Text)                         │
│ └─ Brevo (Transactional Email)                          │
│                                                         │
│ ⏰ Background Tasks                                     │
│ └─ Huey (SQLite backend) for async jobs                 │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| **Backend** | Django 5.2, Python 3.11 |
| **Database** | SQLite with WAL mode |
| **Task Queue** | Huey (SQLite backend) |
| **Frontend** | Tailwind CSS, HTMX, Editor.js |
| **Server** | Gunicorn + Whitenoise |
| **PWA** | django-pwa, django-webpush |
| **Auth** | django-allauth (Email + Google OAuth) |
| **AI** | Google Gemini, Groq API |
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
├── ai/                     # AI features (coming soon)
├── static/                 # Global static files
├── media/                  # User uploads
└── backups/                # Database backups
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ (for Tailwind CSS)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Nwokike/igbo-archives-platform.git
   cd igbo-archives-platform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node dependencies (for Tailwind)**
   ```bash
   npm install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

6. **Create cache table**
   ```bash
   python manage.py createcachetable
   ```

7. **Run migrations**
   ```bash
   python manage.py migrate
   ```

8. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

9. **Build Tailwind CSS**
   ```bash
   npm run build:css
   ```

10. **Start development server**
    ```bash
    python manage.py runserver
    ```

11. **Start Huey worker (in another terminal)**
    ```bash
    python manage.py run_huey
    ```

## 🌍 Environment Variables

Copy the example environment file and configure your keys:

```bash
cp .env.example .env
```

## 🚀 Deployment

This project includes configuration for standard Django deployment:
- **WSGI**: Gunicorn
- **Static Files**: Whitenoise
- **Database**: SQLite (optimized) for low-memory environments
- **Background Tasks**: Huey

For detailed deployment instructions, please refer to the internal documentation.

## 📊 Memory Optimization (1GB RAM)

This platform is optimized for deployment on a 1GB RAM VM:

- **SQLite WAL mode**: Reduced cache (32MB) and mmap (64MB)
- **Database cache**: Uses database instead of memory cache
- **Huey workers**: Single worker for background tasks
- **Gunicorn workers**: 2 workers maximum
- **File uploads**: Disk-based, not memory-based
- **Efficient queries**: `select_related`, `prefetch_related`, `only()`

## 🔒 Security Features

- **CSRF Protection**: All forms and APIs protected
- **reCAPTCHA**: Spam protection on public forms
- **XSS Prevention**: Content sanitization with bleach
- **SQL Injection Prevention**: Parameterized queries via ORM
- **HTTPS**: Enforced in production with HSTS
- **Secure Cookies**: HttpOnly, Secure, SameSite
- **Rate Limiting**: On uploads and suggestions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## 📄 License

Copyright © 2025 Igbo Archives. All Rights Reserved.

## 👨‍💻 Author

**Nwokike** - [GitHub](https://github.com/Nwokike)

---

*Preserving Igbo culture for future generations through technology.*
