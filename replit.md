# Igbo Archives Platform

## Overview

Igbo Archives is a Django-based cultural preservation platform dedicated to documenting and celebrating Igbo heritage. The platform enables community-driven content contribution through archives (images, videos, audio, documents), community insights (blog-style articles), and book reviews. It features an AI assistant powered by Groq and Google Gemini for cultural Q&A and archive analysis, along with a Progressive Web App (PWA) for offline access and push notifications.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **Django 5.2+** with Python 3.11+ as the core web framework
- **SQLite with WAL mode** for database storage, optimized for 1GB RAM deployment with memory-efficient caching and query patterns
- **Gunicorn** as WSGI server with sync workers (optimal for SQLite)

### Frontend Architecture
- **HTMX** for dynamic updates without full page reloads
- **Tailwind CSS** for styling with custom heritage-themed color palette
- **Editor.js** for rich block-based content editing in insights and book reviews
- **Service Worker** for PWA functionality, offline support, and push notifications

### App Structure
The project follows Django's app-based architecture:
- **core**: Shared utilities, context processors, validators, homepage, static pages
- **archives**: Cultural artifact management (images, videos, audio, documents)
- **insights**: Community blog posts with Editor.js content, edit suggestions workflow
- **books**: Book review system with ratings and cover images
- **ai**: AI chat assistant, archive analysis, text-to-speech, voice transcription
- **users**: Custom user model, profiles, messaging, notifications, admin moderation
- **api**: REST endpoints for Editor.js media browser, push subscriptions

### Authentication
- **django-allauth** for authentication with Google OAuth support
- **django-recaptcha** for spam protection on forms (optional, only if keys configured)
- Custom signup form with email-based registration (no username required)

### Content Management
- Approval workflow for user-submitted content (pending_approval → is_approved)
- Tag system via **django-taggit** for categorization
- Threaded comments via **django-threadedcomments**
- Edit suggestions system allowing community collaboration on insights

### AI Services
- **Multi-key rotation** for API keys to maximize free tier usage
- **Groq** (LLaMA 3.3 70B) for chat completions and Whisper for speech-to-text
- **Google Gemini 3.0 Flash** for vision analysis and multimodal tasks
- **gTTS** for text-to-speech generation
- Database-grounded responses with citations to archives, insights, and books

### Caching Strategy
- Django's cache framework used throughout for performance
- Cached: approved archive IDs, categories, tags, notification counts
- Cache invalidation on content updates

### File Handling
- **WhiteNoise** for static file serving
- Custom validators for file size limits (images 5MB, videos 50MB, documents/audio 10MB)
- Media files stored in configurable MEDIA_ROOT

### Background Tasks
- **Huey** for async task processing (email, push notifications)
- Memory-efficient design for 1GB RAM constraint

### SEO & Discovery
- Django sitemaps for archives, insights, books, user profiles
- IndexNow integration for instant search engine notification
- robots.txt generation
- Meta tags via **django-meta**

## External Dependencies

### AI Providers
- **Groq API**: Chat completions (LLaMA models), speech-to-text (Whisper)
- **Google Gemini API**: Vision analysis, multimodal chat, image understanding

### Authentication
- **Google OAuth** via django-allauth for social login

### Notifications
- **django-webpush** for browser push notifications (requires VAPID keys)
- Email notifications via Django's email backend

### Spam Protection
- **Google reCAPTCHA v2** for form protection (optional)

### Analytics & Monetization (Optional)
- **Google Analytics** for usage tracking
- **Google AdSense** for monetization
- **Paystack** for donation processing

### Database
- SQLite with WAL mode enabled for better concurrency
- Optimized pragmas for 1GB RAM: 32MB cache, 64MB mmap

### Key Environment Variables
```
SECRET_KEY          # Django secret key (required)
DEBUG               # Debug mode flag
SITE_URL            # Production URL
GEMINI_API_KEYS     # Comma-separated Gemini API keys
GROQ_API_KEYS       # Comma-separated Groq API keys
RECAPTCHA_PUBLIC_KEY / RECAPTCHA_PRIVATE_KEY  # reCAPTCHA (optional)
VAPID_PUBLIC_KEY / VAPID_PRIVATE_KEY          # Push notifications
```