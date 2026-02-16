"""
Django settings for Igbo Archives project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# --- Environment Setup ---
load_dotenv()

def get_bool_from_env(key, default_value='False'):
    """Helper to convert environment variable strings to booleans safely."""
    return str(os.getenv(key, default_value)).lower() in ('true', '1', 't', 'y', 'yes')

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Core Security ---
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = 'insecure-dev-key-do-not-use-in-production'
    else:
        raise ValueError("The SECRET_KEY environment variable must be set.")

DEBUG = get_bool_from_env('DEBUG', 'False')

ADMINS = [('Admin', os.getenv('ADMIN_EMAIL', 'admin@igboarchives.com.ng'))]

# --- Hosts & Trusted Origins ---
if DEBUG:
    ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']  # SECURITY: never deploy with DEBUG=True
else:
    allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'igboarchives.com.ng,www.igboarchives.com.ng')
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('CSRF_TRUSTED_ORIGINS', 'https://igboarchives.com.ng,https://www.igboarchives.com.ng').split(',') if o.strip()]
SITE_URL = os.getenv('SITE_URL', 'https://igboarchives.com.ng')

# --- Application Definition ---
INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',

    # 3. Third-Party Apps
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
    'dbbackup',
    'webpush',
    'csp', 
    'rest_framework',
    'rest_framework.authtoken',
    'django_cleanup.apps.CleanupConfig',

    # 4. Project Apps
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'archives.apps.ArchivesConfig',
    'insights.apps.InsightsConfig',
    'books.apps.BooksConfig',
    'ai.apps.AiConfig',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware', 
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
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                # Custom
                'core.context_processors.pwa_settings',
                'core.context_processors.monetization_settings',
                'core.context_processors.notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'igbo_archives.wsgi.application'

# --- Database & Caching ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 30,
            'transaction_mode': 'IMMEDIATE',
            'init_command': (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA synchronous=NORMAL;"
                "PRAGMA cache_size=-32000;"
                "PRAGMA foreign_keys=ON;"
                "PRAGMA busy_timeout=5000;"
            ),
        }
    }
}

CONN_MAX_AGE = None  # Django 6.0 persistent connection pooling
CONN_HEALTH_CHECKS = True

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}

# --- Password Validation ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- Internationalization ---
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# --- Static & Media Files (Storage) ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

R2_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN', '')

# Unified STORAGES config
if DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
    DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}
else:
    if R2_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{R2_CUSTOM_DOMAIN}/'

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": os.getenv("R2_ACCESS_KEY_ID"),
                "secret_key": os.getenv("R2_SECRET_ACCESS_KEY"),
                "bucket_name": os.getenv("R2_BUCKET_NAME"),
                "endpoint_url": os.getenv("R2_ENDPOINT_URL"),
                "custom_domain": R2_CUSTOM_DOMAIN,
                "default_acl": "public-read",
                "querystring_auth": False,
                "file_overwrite": False,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    DBBACKUP_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    DBBACKUP_STORAGE_OPTIONS = {
        'access_key': os.getenv('R2_ACCESS_KEY_ID'),
        'secret_key': os.getenv('R2_SECRET_ACCESS_KEY'),
        'bucket_name': 'igboarchives-backup',
        'endpoint_url': os.getenv('R2_ENDPOINT_URL'),
        'default_acl': 'private',
        'location': 'backups',
        'addressing_style': 'path',
        'signature_version': 's3v4',
    }

# --- Auth & AllAuth ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/profile/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
SOCIALACCOUNT_LOGIN_ON_GET = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True  
ACCOUNT_USER_MODEL_USERNAME_FIELD = "username"
ACCOUNT_FORMS = {
    'signup': 'users.forms.CustomSignupForm',
    'login': 'users.forms.CustomLoginForm',
}

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
            'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'}
    }
}

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_ADAPTER = 'users.adapters.CustomSocialAccountAdapter'
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True

# --- Upload Limits ---
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB — safe for 1GB RAM VM
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB — actual files go to disk via TemporaryFileUploadHandler
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

# --- API (DRF) ---
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10/hour',
        'user': '50/hour',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# --- PWA Settings ---
PWA_APP_NAME = 'Igbo Archives'
PWA_APP_SHORT_NAME = 'IgboArchives'
PWA_APP_DESCRIPTION = 'Preserving the Past, Inspiring the Future'
PWA_APP_THEME_COLOR = '#3D2817'
PWA_APP_BACKGROUND_COLOR = '#FFFFFF'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_ICONS = [
    {'src': '/static/images/logos/icon-192.png', 'sizes': '192x192', 'type': 'image/png'},
    {'src': '/static/images/logos/icon-512.png', 'sizes': '512x512', 'type': 'image/png'},
]
PWA_APP_ICONS_APPLE = [
    {'src': '/static/images/logos/icon-192.png', 'sizes': '192x192'},
]
PWA_SERVICE_WORKER_PATH = BASE_DIR / 'static' / 'serviceworker.js'

# --- API Keys & Integrations ---
TURNSTILE_SITE_KEY = os.getenv('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.getenv('TURNSTILE_SECRET_KEY', '')

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": os.getenv('VAPID_PUBLIC_KEY', ''),
    "VAPID_PRIVATE_KEY": os.getenv('VAPID_PRIVATE_KEY', ''),
    "VAPID_ADMIN_EMAIL": os.getenv('ADMIN_EMAIL', ADMINS[0][1])
}
COMMENTS_APP = 'threadedcomments'

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_API_KEYS = os.getenv('GEMINI_API_KEYS', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_KEYS = os.getenv('GROQ_API_KEYS', '')
YARNGPT_API_KEY = os.getenv('YARNGPT_API_KEY', '')

GOOGLE_ADSENSE_CLIENT_ID = os.getenv('GOOGLE_ADSENSE_CLIENT_ID', '')
ENABLE_ADSENSE = bool(GOOGLE_ADSENSE_CLIENT_ID)
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
ENABLE_ANALYTICS = bool(GOOGLE_ANALYTICS_ID)
INDEXNOW_API_KEY = os.getenv('INDEXNOW_API_KEY', '')

PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '')
ENABLE_DONATIONS = bool(PAYSTACK_SECRET_KEY)

# --- Email ---
if os.getenv('BREVO_EMAIL_USER') and os.getenv('BREVO_SMTP_KEY'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp-relay.brevo.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv('BREVO_EMAIL_USER')
    EMAIL_HOST_PASSWORD = os.getenv('BREVO_SMTP_KEY')
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@igboarchives.com.ng')

# --- Meta ---
META_SITE_PROTOCOL = 'https'
META_USE_OG_PROPERTIES = True
META_USE_TWITTER_PROPERTIES = True
META_USE_SCHEMAORG_PROPERTIES = True
META_SITE_TYPE = 'website'
META_SITE_NAME = 'Igbo Archives'
META_DEFAULT_KEYWORDS = ['Igbo culture', 'Nigerian heritage', 'Igbo history', 'cultural preservation']
META_DEFAULT_IMAGE = '/static/images/logos/og-image.png'

# --- Backup ---
DBBACKUP_CLEANUP_KEEP = 3
DBBACKUP_DATE_FORMAT = '%Y-%m-%d-%H-%M-%S'
DBBACKUP_FILENAME_TEMPLATE = 'igbo-archives-{datetime}.{extension}'
DBBACKUP_CONNECTORS = {'default': {'CONNECTOR': 'dbbackup.db.sqlite.SqliteConnector'}}

# --- Tasks (Django 6) ---
TASKS = {
    'default': {
        'BACKEND': 'django.tasks.backends.immediate.ImmediateBackend',
    },
}
# Note: For production with persistent queue, consider 'django.tasks.backends.redis.RedisBackend'
# or similar once infra is available. For now, immediate handles 1GB RAM constraints best.

# --- Security Headers ---
SESSION_COOKIE_AGE = 86400 * 7
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# --- Content Security Policy (CSP) ---

CONTENT_SECURITY_POLICY = {
    'DIRECTIVES': {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'unsafe-inline'",
            "https://*.google.com",
            "https://*.gstatic.com",
            "https://*.doubleclick.net",
            "https://*.googletagmanager.com",
            "https://*.googlesyndication.com",
            "https://*.cloudflare.com",
            "https://challenges.cloudflare.com",
            "https://static.cloudflareinsights.com",
            "https://*.adtrafficquality.google",
            "https://paystack.co",
            "https://paystack.com",
            "https://*.paystack.co",
            "https://*.paystack.com",
            "https://js.paystack.co",
            "https://pagead2.googlesyndication.com",
            "https://cdn.jsdelivr.net",
        ],
        'style-src': [
            "'self'",
            "'unsafe-inline'",
            "https://fonts.googleapis.com",
            "https://paystack.co",
            "https://paystack.com",
            "https://*.paystack.co",
            "https://*.paystack.com",
        ],
        'font-src': [
            "'self'",
            "https://fonts.gstatic.com",
        ],
        'img-src': [
            "'self'",
            "data:",
            "blob:",
            "https:",
        ],
        'connect-src': [
            "'self'",
            "https://www.google-analytics.com",
            "https://api.indexnow.org",
            "https://challenges.cloudflare.com",
            "https://www.googletagmanager.com",
            "https://pagead2.googlesyndication.com",
            "https://*.adtrafficquality.google",
            "https://csi.gstatic.com",
            "https://paystack.co",
            "https://paystack.com",
            "https://*.paystack.co",
            "https://*.paystack.com",
            "https://stats.g.doubleclick.net",
        ],
        'frame-src': [
            "'self'",
            "https://challenges.cloudflare.com",
            "https://googleads.g.doubleclick.net",
            "https://*.google.com",
            "https://*.adtrafficquality.google",
            "https://paystack.co",
            "https://paystack.com",
            "https://*.paystack.co",
            "https://*.paystack.com",
            "https://www.youtube.com",
            "https://player.vimeo.com",
        ],
        'worker-src': ["'self'", "blob:"],
        'manifest-src': ["'self'"],
        'media-src': ["'self'", "https:", "data:", "blob:"],
    }
}

# --- Logging ---
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
    },
}