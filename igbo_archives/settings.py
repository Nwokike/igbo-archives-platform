from pathlib import Path
import os
from dotenv import load_dotenv
from huey import SqliteHuey

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable must be set")

DEBUG = os.getenv('DEBUG', 'False') == 'True'
ADMINS = [('Admin', os.getenv('ADMIN_EMAIL', 'admin@igboarchives.com.ng'))]

if DEBUG:
    ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1']
else:
    allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'igboarchives.com.ng,www.igboarchives.com.ng')
    ALLOWED_HOSTS = [h.strip() for h in allowed_hosts_env.split(',') if h.strip()]
    if not ALLOWED_HOSTS:
        ALLOWED_HOSTS = ['igboarchives.com.ng', 'www.igboarchives.com.ng']

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
    'dbbackup',
    'webpush',
    'huey.contrib.djhuey',
    'csp',
    'rest_framework',
    'rest_framework.authtoken',
    'core.apps.CoreConfig',
    'users.apps.UsersConfig',
    'archives.apps.ArchivesConfig',
    'insights.apps.InsightsConfig',
    'books.apps.BooksConfig',
    'ai.apps.AiConfig',
    'api.apps.ApiConfig',
    'django_cleanup.apps.CleanupConfig',
]

REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '500/hour',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
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
                'core.context_processors.pwa_settings',
                'core.context_processors.monetization_settings',
                'core.context_processors.notification_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'igbo_archives.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}

CONN_MAX_AGE = 600
CONN_HEALTH_CHECKS = True

DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880
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
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Storage Configuration
if DEBUG:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    
    DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
    DBBACKUP_STORAGE_OPTIONS = {'location': BASE_DIR / 'backups'}

else:
    R2_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN', '')
    if R2_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{R2_CUSTOM_DOMAIN}/'

    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": os.getenv("R2_ACCESS_KEY_ID", ""),
                "secret_key": os.getenv("R2_SECRET_ACCESS_KEY", ""),
                "bucket_name": os.getenv("R2_BUCKET_NAME", ""),
                "endpoint_url": os.getenv("R2_ENDPOINT_URL", ""),
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
        'access_key': os.getenv('R2_ACCESS_KEY_ID', ''),
        'secret_key': os.getenv('R2_SECRET_ACCESS_KEY', ''),
        'bucket_name': 'igboarchives-backup',
        'endpoint_url': os.getenv('R2_ENDPOINT_URL', ''),
        'default_acl': 'private',
        'location': 'backups',
        'addressing_style': 'path',
        'signature_version': 's3v4',
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.CustomUser'
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

LOGIN_REDIRECT_URL = '/profile/dashboard/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
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
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_QUERY_EMAIL = False

PWA_APP_NAME = 'Igbo Archives'
PWA_APP_DESCRIPTION = 'Preserving the Past, Inspiring the Future'
PWA_APP_THEME_COLOR = '#3D2817'
PWA_APP_BACKGROUND_COLOR = '#FFFFFF'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_SCOPE = '/'
PWA_APP_ORIENTATION = 'any'
PWA_APP_START_URL = '/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {'src': '/static/images/logos/logo-light.png', 'sizes': '192x192', 'type': 'image/png'},
    {'src': '/static/images/logos/logo-light.png', 'sizes': '512x512', 'type': 'image/png'},
]
PWA_APP_ICONS_APPLE = [
    {'src': '/static/images/logos/logo-light.png', 'sizes': '180x180'},
]
PWA_APP_SPLASH_SCREEN = [{'src': '/static/images/logos/logo-light.png', 'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'}]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'en-US'
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, 'static', 'serviceworker.js')

TURNSTILE_SITE_KEY = os.getenv('TURNSTILE_SITE_KEY', '')
TURNSTILE_SECRET_KEY = os.getenv('TURNSTILE_SECRET_KEY', '')

WEBPUSH_SETTINGS = {
    "VAPID_PUBLIC_KEY": os.getenv('VAPID_PUBLIC_KEY', ''),
    "VAPID_PRIVATE_KEY": os.getenv('VAPID_PRIVATE_KEY', ''),
    "VAPID_ADMIN_EMAIL": os.getenv('ADMIN_EMAIL', 'admin@igboarchives.com.ng')
}

COMMENTS_APP = 'threadedcomments'

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_API_KEYS = os.getenv('GEMINI_API_KEYS', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_KEYS = os.getenv('GROQ_API_KEYS', '')
YARNGPT_API_KEY = os.getenv('YARNGPT_API_KEY', '')

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
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@igboarchives.com.ng')

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

DBBACKUP_CLEANUP_KEEP = 3
DBBACKUP_DATE_FORMAT = '%Y-%m-%d-%H-%M-%S'
DBBACKUP_FILENAME_TEMPLATE = 'igbo-archives-{datetime}.{extension}'

DBBACKUP_CONNECTORS = {
    'default': {
        'CONNECTOR': 'dbbackup.db.sqlite.SqliteConnector',
    }
}

GOOGLE_ADSENSE_CLIENT_ID = os.getenv('GOOGLE_ADSENSE_CLIENT_ID', '')
ENABLE_ADSENSE = bool(GOOGLE_ADSENSE_CLIENT_ID)

PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '')
PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '')
ENABLE_DONATIONS = bool(PAYSTACK_SECRET_KEY)

GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
ENABLE_ANALYTICS = bool(GOOGLE_ANALYTICS_ID)

INDEXNOW_API_KEY = os.getenv('INDEXNOW_API_KEY', '')
INDEXNOW_API_URL = "https://api.indexnow.org/indexnow"

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

HUEY = SqliteHuey(
    filename=str(BASE_DIR / 'huey.db'),
    immediate=False,
    results=False,
    store_none=True,
    utc=True,
)

SESSION_COOKIE_AGE = 86400 * 7
SESSION_SAVE_EVERY_REQUEST = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

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

CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://*.google.com",
    "https://*.gstatic.com",
    "https://*.doubleclick.net",
    "https://*.googletagmanager.com",
    "https://*.googlesyndication.com",
    "https://*.cloudflare.com",
    "https://*.adtrafficquality.google",
)
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "blob:", "https:")
CSP_CONNECT_SRC = (
    "'self'",
    "https://www.google-analytics.com",
    "https://api.indexnow.org",
    "https://challenges.cloudflare.com",
    "https://www.googletagmanager.com",
    "https://pagead2.googlesyndication.com",
    "https://*.adtrafficquality.google"
)
CSP_FRAME_SRC = (
    "'self'",
    "https://challenges.cloudflare.com",
    "https://googleads.g.doubleclick.net"
)

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