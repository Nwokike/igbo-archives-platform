"""
Django settings for Igbo Archives platform.
Optimized for Google Cloud 1GB RAM VM deployment.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'https://igboarchives.com.ng').split(',')

SITE_URL = os.getenv('SITE_URL', 'https://igboarchives.com.ng')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    
    'django_comments',
    'threadedcomments',
    'taggit',
    'django_htmx',
    'pwa',
    'meta',
    'django_recaptcha',
    'dbbackup',
    'webpush',
    'huey.contrib.djhuey',
    
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'archives.apps.ArchivesConfig',
    'insights.apps.InsightsConfig',
    'books.apps.BooksConfig',
    'ai.apps.AiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'igbo_archives.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'core' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'core.context_processors.pwa_settings',
                'core.context_processors.monetization_settings',
                'core.context_processors.notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'igbo_archives.wsgi.application'

# Database - SQLite with WAL mode for 1GB RAM constraint
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'init_command': (
                'PRAGMA journal_mode=WAL;'
                'PRAGMA synchronous=NORMAL;'
                'PRAGMA cache_size=-32000;'
                'PRAGMA temp_store=MEMORY;'
                'PRAGMA mmap_size=67108864;'
                'PRAGMA busy_timeout=5000;'
                'PRAGMA foreign_keys=ON;'
            ),
        },
        'ATOMIC_REQUESTS': True,
    }
}

CONN_MAX_AGE = 600
CONN_HEALTH_CHECKS = True

# Memory constraints for 1GB RAM
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'core' / 'static',
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudflare R2 Storage (optional - falls back to local if not configured)
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID', '')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY', '')
R2_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', '')
R2_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL', '')
R2_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN', '')

if R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY and R2_BUCKET_NAME:
    # Use R2 for media storage
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_ACCESS_KEY_ID = R2_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = R2_SECRET_ACCESS_KEY
    AWS_STORAGE_BUCKET_NAME = R2_BUCKET_NAME
    AWS_S3_ENDPOINT_URL = R2_ENDPOINT_URL
    AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')
    AWS_S3_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN', default=None)
    AWS_DEFAULT_ACL = 'public-read'
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_FILE_OVERWRITE = False
    MEDIA_URL = f'https://{R2_CUSTOM_DOMAIN}/' if R2_CUSTOM_DOMAIN else f'{R2_ENDPOINT_URL}/{R2_BUCKET_NAME}/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.CustomUser'

SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
    'login': 'users.forms.CustomLoginForm',
}

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = False

# PWA Configuration
PWA_APP_NAME = 'Igbo Archives'
PWA_APP_DESCRIPTION = 'Preserving the Past, Inspiring the Future'
PWA_APP_THEME_COLOR = '#3D2817'
PWA_APP_BACKGROUND_COLOR = '#FFFFFF'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [{'src': '/static/images/logos/logo-light.png', 'sizes': '160x160'}]
PWA_APP_ICONS_APPLE = [{'src': '/static/images/logos/logo-light.png', 'sizes': '160x160'}]
PWA_APP_SPLASH_SCREEN = [{'src': '/static/images/logos/logo-light.png', 'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'}]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'

# reCAPTCHA - No fallback keys for security
RECAPTCHA_PUBLIC_KEY = os.getenv('RECAPTCHA_PUBLIC_KEY', '')
RECAPTCHA_PRIVATE_KEY = os.getenv('RECAPTCHA_PRIVATE_KEY', '')

# Web Push Notifications
WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": os.getenv('VAPID_PUBLIC_KEY', ''),
    "VAPID_PRIVATE_KEY": os.getenv('VAPID_PRIVATE_KEY', ''),
    "VAPID_ADMIN_EMAIL": os.getenv('ADMIN_EMAIL', 'admin@igboarchives.com.ng')
}

COMMENTS_APP = 'threadedcomments'

# AI Integration - Multi-Key Support for Free Tier Maximization
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')  # Single key fallback
GEMINI_API_KEYS = os.getenv('GEMINI_API_KEYS', '')  # Comma-separated keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')  # Single key fallback
GROQ_API_KEYS = os.getenv('GROQ_API_KEYS', '')  # Comma-separated keys

# Payments (Paystack)
PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '')

# Email Configuration
if os.getenv('BREVO_EMAIL_USER') and os.getenv('BREVO_API_KEY'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp-relay.brevo.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('BREVO_EMAIL_USER')
    EMAIL_HOST_PASSWORD = os.getenv('BREVO_API_KEY')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@igboarchives.com.ng')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@igboarchives.com.ng')

# SEO Meta Tags
META_SITE_PROTOCOL = 'https'
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True
META_USE_SCHEMAORG_PROPERTIES = True
META_SITE_TYPE = 'website'
META_SITE_NAME = 'Igbo Archives'
META_DEFAULT_KEYWORDS = ['Igbo culture', 'Nigerian heritage', 'Igbo history', 'cultural preservation', 'Igbo language', 'African culture']
META_INCLUDE_KEYWORDS = ['Igbo', 'archives', 'cultural', 'heritage', 'history']
META_DEFAULT_IMAGE = '/static/images/logos/og-image.png'
META_IMAGE_URL = '/static/images/logos/og-image.png'
META_USE_SITES = True
META_OG_NAMESPACES = ['og', 'fb']

# Database Backup
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
DBBACKUP_CLEANUP_KEEP = 10
DBBACKUP_CLEANUP_KEEP_MEDIA = 10
DBBACKUP_DATE_FORMAT = '%Y-%m-%d-%H-%M-%S'
DBBACKUP_FILENAME_TEMPLATE = 'igbo-archives-{datetime}.{extension}'
DBBACKUP_MEDIA_FILENAME_TEMPLATE = 'igbo-archives-media-{datetime}.{extension}'

# Monetization
GOOGLE_ADSENSE_CLIENT_ID = os.getenv('GOOGLE_ADSENSE_CLIENT_ID', '')
ENABLE_ADSENSE = bool(GOOGLE_ADSENSE_CLIENT_ID)
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
ENABLE_DONATIONS = bool(STRIPE_SECRET_KEY)

# Analytics
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
ENABLE_ANALYTICS = bool(GOOGLE_ANALYTICS_ID)

# IndexNow SEO
INDEXNOW_API_KEY = os.getenv('INDEXNOW_API_KEY', '')
INDEXNOW_API_URL = "https://api.indexnow.org/indexnow"

# Caching - Database cache for shared access and persistence
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
        'OPTIONS': {
            'MAX_ENTRIES': 500,
        }
    }
}

# Huey Task Queue - Optimized for 1GB RAM
from huey import SqliteHuey

HUEY = SqliteHuey(
    filename=str(BASE_DIR / 'huey.db'),
    immediate=DEBUG,
    results=False,
    store_none=True,
    utc=True,
)

# Security Settings for Production
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'huey': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
