# Igbo Archives Platform - Replit Documentation

## Project Overview
A comprehensive Django-based web platform for preserving and celebrating Igbo culture, history, and heritage. Museum-quality experience with heritage-inspired design featuring sepia tones and vintage aesthetics.

## Current Status (October 29, 2025)
**Production-Ready MVP** - All critical issues fixed, security hardened, fully functional.

## Recent Major Fixes (October 29, 2025)
### Security Fixes
- ✅ Removed hardcoded SECRET_KEY fallback - now requires environment variable
- ✅ Changed DEBUG default from True to False for production safety
- ✅ Proper secrets management via Replit Secrets

### Admin Panel Fixes
- ✅ Fixed FieldError in insights/admin.py - removed 'content' from search_fields
- ✅ Fixed FieldError in books/admin.py - removed 'content' from search_fields
- ✅ Admin search now works correctly for all models

### File Validation Fixes
- ✅ Removed unrealistic 2MB minimum file size requirements
- ✅ Archives now accept images of any reasonable size (max 5MB)
- ✅ Documents and audio files increased to 10MB max
- ✅ More user-friendly file upload experience

### Code Cleanup
- ✅ Removed duplicate push notification code from api/views.py
- ✅ Consolidated push notifications to api/push_views.py
- ✅ Cleaner API structure

### Error Handling
- ✅ Created 404 error page template
- ✅ Created 500 error page template  
- ✅ Created 403 error page template
- ✅ Proper error handlers configured

### Deployment
- ✅ All dependencies installed via requirements.txt
- ✅ Database migrations applied successfully
- ✅ Static files collected
- ✅ Django server running on port 5000
- ✅ No errors or warnings on startup

## Architecture

### Apps Structure
- **core**: Base templates, homepage, static pages (about, contact, terms, privacy)
- **archives**: Cultural artifacts (images, videos, documents, audio) with metadata
- **insights**: User-generated articles with Editor.js rich text editor
- **books**: Book reviews with ratings and rich content
- **users**: Custom user model, profiles, messaging, notifications
- **academy**: Educational content (coming soon placeholder)
- **api**: REST endpoints for image uploads, archive browsing, push notifications

### Key Features
- Email-based authentication with django-allauth
- Google OAuth integration support
- Rich text editing with Editor.js (JSON-based block editor)
- Push notifications support
- PWA (Progressive Web App) installable
- SEO optimized with sitemaps and meta tags
- Threaded comments with guest support
- Tag-based organization
- Dynamic HTMX filtering
- Grid/list view toggle with localStorage persistence
- Mobile-responsive design

### Database
- **Development**: SQLite (db.sqlite3)
- **Production**: PostgreSQL recommended

### Content Workflow
1. Users create content (archives, insights, books)
2. Content saved as draft or submitted for approval
3. Admin reviews and approves via Django admin
4. Approved content appears on public pages

## Environment Variables

### Required
- `SECRET_KEY`: Django secret key (set via Replit Secrets)

### Optional (with defaults)
- `DEBUG`: Set to "True" for development (default: False)
- `ALLOWED_HOSTS`: Comma-separated hosts (default: *)
- `CSRF_TRUSTED_ORIGINS`: Comma-separated origins for CSRF

### Optional Integrations
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: Google OAuth
- `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY`: reCAPTCHA (test keys included)
- `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`: Web push notifications
- `GEMINI_API_KEY`: Google Gemini AI
- `TWITTER_API_KEY`, etc: Twitter integration
- `STRIPE_PUBLIC_KEY`, `STRIPE_SECRET_KEY`: Donations
- `GOOGLE_ADSENSE_CLIENT_ID`: AdSense
- Email settings: `BREVO_EMAIL_USER`, `BREVO_API_KEY`

## Development Commands

### Run Server
```bash
python manage.py runserver 0.0.0.0:5000
```

### Database
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### Static Files
```bash
python manage.py collectstatic --noinput
```

### Backups
```bash
python manage.py backup_database
```

### Cleanup
```bash
python manage.py delete_old_drafts  # Remove drafts older than 30 days
```

## File Structure
```
igbo-archives-platform/
├── igbo_archives/          # Project settings
│   ├── settings.py         # Django configuration
│   ├── urls.py             # URL routing
│   └── wsgi.py             # WSGI application
├── core/                   # Core app
│   ├── templates/          # Base templates, error pages
│   ├── static/             # CSS, JS, images
│   └── views.py            # Homepage, static pages
├── archives/               # Archives app
│   ├── models.py           # Archive model
│   ├── views.py            # CRUD views
│   └── templates/          # Archive templates
├── insights/               # Insights app
│   ├── models.py           # InsightPost, EditSuggestion
│   ├── views.py            # Create, edit, list views
│   └── templates/          # Insight templates
├── books/                  # Books app
│   ├── models.py           # BookReview model
│   ├── views.py            # Review CRUD views
│   └── templates/          # Book templates
├── users/                  # Users app
│   ├── models.py           # CustomUser, Thread, Message
│   ├── views.py            # Profile, dashboard, messaging
│   └── templates/          # User templates
├── api/                    # API endpoints
│   ├── views.py            # Upload, archive browser
│   └── push_views.py       # Push notifications
├── academy/                # Academy app
│   └── views.py            # Coming soon page
├── media/                  # User uploads
├── static/                 # Project static files
├── staticfiles/            # Collected static files
├── db.sqlite3              # SQLite database
└── requirements.txt        # Python dependencies
```

## Known Issues / Future Improvements
- LSP diagnostics showing Django imports (normal - Django not in LSP path)
- Consider adding proper Django forms instead of manual request.POST handling
- Add rate limiting for API endpoints
- Add comprehensive test suite
- Consider Redis for caching and sessions
- Add email verification for production
- Implement full-text search with PostgreSQL

## Security Notes
- CSRF protection enabled
- Password validation active
- File upload validation in place
- User permissions enforced (@login_required decorators)
- Admin-only approval workflows
- Secrets managed via environment variables

## User Preferences
- Grid/list view stored in browser localStorage
- Theme switching (if enabled)
- Notification preferences

## Admin Access
- URL: `/admin/`
- Create superuser: `python manage.py createsuperuser`
- Full content moderation capabilities
- User management
- Category management

## Deployment Notes
For production deployment:
1. Set `DEBUG=False`
2. Update `ALLOWED_HOSTS` with actual domain
3. Configure `CSRF_TRUSTED_ORIGINS`
4. Use PostgreSQL database
5. Set up proper email backend (Brevo, SendGrid, etc.)
6. Configure static/media file serving (Whitenoise, S3, etc.)
7. Use Gunicorn: `gunicorn --bind 0.0.0.0:5000 --reuse-port igbo_archives.wsgi:application`
8. Set up SSL certificate
9. Configure proper logging
10. Set up monitoring and backups

## Support
- Email: igboarchives@gmail.com
- Website: igboarchives.com.ng
