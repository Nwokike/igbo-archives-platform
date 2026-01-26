# Igbo Archives Platform

## Overview

Igbo Archives is a Django-based cultural preservation platform dedicated to documenting and celebrating Igbo heritage from Nigeria. The platform enables community-driven content creation including cultural archives (images, videos, audio, documents), community insights/articles, and book reviews. It features an AI assistant powered by Groq and Google Gemini for cultural Q&A and archive analysis, along with full PWA support for offline access and push notifications.


## System Architecture

### Backend Framework
- **Django 5.1.4** with **Python 3.12+** as the core web framework (required)
- **SQLite with WAL mode** for database storage, optimized for 1GB RAM constraints with custom configuration in `igbo_archives/sqlite_wal.py`
- **Gunicorn** for production WSGI serving with memory-optimized settings (2 workers, max 500 requests before restart)

### Application Structure
The project follows Django's app-based architecture with clear separation of concerns:

- **core**: Shared utilities, context processors, validators, static pages, and caching helpers
- **archives**: Cultural archive management (images, videos, audio, documents) with category/tag organization
- **insights**: Community articles with Editor.js block-based content, draft/publish workflow, and collaborative edit suggestions
- **books**: Book review system with ratings and cover images
- **users**: Custom user model extending AbstractUser, messaging system, notifications, and profile management
- **ai**: AI assistant with chat sessions, archive analysis, and TTS capabilities
- **api**: REST endpoints for Editor.js media browser, image uploads, and push notifications

### Frontend Architecture
- **HTMX** for dynamic page updates without full reloads
- **Tailwind CSS 3.4** with custom heritage-themed color palette (surface, text, accent, border variants for light/dark modes)
- **Editor.js** for rich block-based content editing in insights and book reviews
- **Font Awesome** for icons, Inter and Playfair Display fonts for typography

### Authentication & Authorization
- **django-allauth** for authentication with Google social login support
- **django-recaptcha** for spam protection on forms (conditionally enabled based on configuration)
- Custom user model with full_name, bio, profile_picture, and social_links fields
- Staff-only moderation dashboard for approving/rejecting community content

### Content Workflow
- User-submitted content goes through approval workflow (pending_approval → is_approved)
- Edit suggestion system allows community members to propose changes to existing insights
- Threaded comments with reCAPTCHA protection via django-threadedcomments

### Caching Strategy
- Django's cache framework used extensively for categories, tags, archive IDs, and notification counts
- Cache timeouts: 5 minutes for archive IDs, 30 minutes for tags, 1 hour for categories
- Memory-efficient random selection using cached ID lists for homepage carousel

### PWA & Notifications
- **django-pwa** for Progressive Web App manifest and service worker
- **django-webpush** for browser push notifications with VAPID keys
- Service worker handles offline caching with separate static and dynamic caches

## External Dependencies

### AI Services
- **Google Gemini** (gemini-2.5-flash, gemini-2.5-pro): Primary AI for image analysis, chat, and multimodal tasks via google-genai SDK
- **Groq** (LLaMA 3.3 70B, Whisper Large V3): Chat completions and speech-to-text transcription
- **gTTS**: Text-to-speech generation for audio responses
- Multi-key rotation system in `ai/services/key_manager.py` for maximizing free tier usage across multiple API keys
- Mode-based selection: 'fast' mode prefers Groq, 'advanced' mode prefers Gemini

### Third-Party Django Packages
- **django-allauth**: Social authentication (Google OAuth)
- **django-taggit**: Tag management for archives, insights, and books
- **django-htmx**: HTMX integration middleware
- **django-webpush**: Web push notification handling
- **django-recaptcha**: Form spam protection
- **django-dbbackup**: Database backup utilities
- **django-meta**: SEO meta tag management
- **whitenoise**: Static file serving in production

### Frontend Dependencies (npm)
- **@editorjs/*** packages: Block-based content editor with plugins for headers, images, lists, quotes, tables, etc.
- **tailwindcss + autoprefixer + postcss**: CSS build pipeline
- **@fontsource/inter, @fontsource/playfair-display**: Self-hosted fonts
- **@fortawesome/fontawesome-free**: Icon library

### Environment Variables Required
- `SECRET_KEY`: Django secret key (required)
- `DEBUG`: Development mode flag
- `ALLOWED_HOSTS`: Comma-separated list of allowed hostnames (production: actual domains, dev: localhost)
- `GEMINI_API_KEYS` / `GEMINI_API_KEY`: Google Gemini API keys (comma-separated for rotation)
- `GROQ_API_KEYS` / `GROQ_API_KEY`: Groq API keys
- `TURNSTILE_SITE_KEY` / `TURNSTILE_SECRET_KEY`: Cloudflare Turnstile credentials for spam protection
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`: Web push notification keys
- `SITE_URL`: Production site URL for absolute URLs
- `CSRF_TRUSTED_ORIGINS`: Comma-separated trusted origins for CSRF

### Build Process

#### NPM Build Steps
1. **Install dependencies**: `npm install`
2. **Copy fonts**: `npm run copy:fonts` - Copies font files from @fontsource packages to static directories
3. **Build CSS**: `npm run build:css` - Compiles Tailwind CSS with PostCSS

#### Service Worker Versioning
- Service worker cache version is defined in `static/serviceworker.js` as `CACHE_VERSION`
- **Important**: Bump `CACHE_VERSION` when making breaking changes to static assets
- Current version: `v1.5.0`
- Deployment process should ensure service worker is updated and old caches are cleared

### Background Tasks & Schedules

#### Huey Periodic Tasks (via `core/tasks.py`)
- **Daily Database Backup** (`daily_database_backup`): Runs at 3:00 AM
  - Uses `django-dbbackup` to create compressed backups
  - Cleans old backups (keeps 3 most recent)
  - Backups stored in Cloudflare R2
  
- **Chat Session Cleanup** (`cleanup_old_chat_sessions`): Runs at 2:30 AM
  - Deactivates sessions older than 30 days
  - Hard deletes inactive sessions older than 90 days
  
- **TTS File Cleanup** (`cleanup_tts_files`): Runs at 5:00 AM
  - Removes TTS audio files older than 24 hours
  
- **Notification Cleanup** (`cleanup_old_notifications`): Runs on 1st of month at 4:00 AM
  - Deletes read notifications older than 18 months
  
- **Message Cleanup** (`cleanup_old_messages`): Runs on 1st of month at 4:30 AM
  - Deletes message threads with no activity for 2+ years where all messages are read
  
- **Cache Expiration Check** (`clear_expired_cache`): Runs every 6 hours
  - DatabaseCache auto-expires entries; this is a monitoring placeholder

#### Management Commands
- **`insights.delete_old_drafts`**: Deletes draft insights older than 30 days
- **`insights.post_to_twitter`**: Posts approved insights to Twitter/X (up to 5 per run)
- **`ai.ai_usage_stats`**: Shows AI usage statistics for monitoring (chat, vision, TTS, STT)
- **`core.backup_database`**: Manual database backup command

### Python Version
- **Required**: Python 3.12+
- Managed via `uv` package manager
- `pyproject.toml` and `uv.lock` specify Python 3.12 requirement
- `manage.py` enforces Python 3.12+ requirement
