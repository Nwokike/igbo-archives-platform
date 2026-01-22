# Igbo Archives Platform

## Overview

Igbo Archives is a Django-based cultural preservation platform dedicated to documenting and celebrating Igbo heritage from Nigeria. The platform enables community-driven content creation including cultural archives (images, videos, audio, documents), community insights/articles, and book reviews. It features an AI assistant powered by Groq and Google Gemini for cultural Q&A and archive analysis, along with full PWA support for offline access and push notifications.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Django 5.2** with Python 3.11+ as the core web framework
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
- **Google Gemini** (gemini-3.0-flash, gemini-3.0-pro): Primary AI for image analysis, chat, and multimodal tasks via google-genai SDK
- **Groq** (LLaMA 3.3 70B, Whisper Large V3): Chat completions and speech-to-text transcription
- **gTTS**: Text-to-speech generation for audio responses
- Multi-key rotation system in `ai/services/key_manager.py` for maximizing free tier usage across multiple API keys

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
- `GEMINI_API_KEYS` / `GEMINI_API_KEY`: Google Gemini API keys (comma-separated for rotation)
- `GROQ_API_KEYS` / `GROQ_API_KEY`: Groq API keys
- `RECAPTCHA_PUBLIC_KEY` / `RECAPTCHA_PRIVATE_KEY`: reCAPTCHA credentials
- `VAPID_PUBLIC_KEY` / `VAPID_PRIVATE_KEY`: Web push notification keys
- `SITE_URL`: Production site URL for absolute URLs
- `CSRF_TRUSTED_ORIGINS`: Comma-separated trusted origins for CSRF