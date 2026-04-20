"""
Render Production settings for IT Management Platform.
Optimized for Render deployment with Python 3.13.
"""

from .base import *
from decouple import config
import os

# =============================================================================
# RENDER-SPECIFIC CONFIGURATION
# =============================================================================

# Environment detection
RENDER = config('RENDER', default=False, cast=bool)

# Security settings
DEBUG = False

# Production hosts - Render provides RENDER_EXTERNAL_HOSTNAME
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',  # Allow all Render subdomains
    'it-management-e72k.onrender.com',  # Your specific domain
]

# Get secret key from Render environment variable
SECRET_KEY = config('DJANGO_SECRET_KEY')

# =============================================================================
# DATABASE CONFIGURATION (PostgreSQL on Render)
# =============================================================================

# Use PostgreSQL on Render (requires dj-database-url)
import dj_database_url

if RENDER:
    # Parse DATABASE_URL from Render environment
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=60,
            ssl_require=True
        )
    }
else:
    # Fallback to SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =============================================================================
# CACHE CONFIGURATION (Redis on Render)
# =============================================================================

if RENDER:
    # Use Redis on Render (requires django-redis)
    REDIS_URL = config('REDIS_URL', default='')
    
    if REDIS_URL:
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.redis.RedisCache',
                'LOCATION': REDIS_URL,
                'OPTIONS': {
                    'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                    'CONNECTION_POOL_KWARGS': {'max_connections': 50},
                    'SOCKET_CONNECT_TIMEOUT': 5,
                    'SOCKET_TIMEOUT': 5,
                },
                'KEY_PREFIX': 'it_mgmt',
            }
        }
    else:
        # Fallback to local memory cache
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                'LOCATION': 'unique-snowflake',
            }
        }
else:
    # Local development cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

# WhiteNoise for serving static files on Render
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
] + [m for m in MIDDLEWARE if m != 'django.middleware.security.SecurityMiddleware']

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# =============================================================================
# CORS SETTINGS (Configure for your frontend)
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://it-management-frontend.onrender.com",  # Your frontend URL
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://it-management-frontend.onrender.com",
]

# =============================================================================
# EMAIL CONFIGURATION
# =============================================================================

# Use Render's SendGrid or other SMTP service
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.sendgrid.net')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='apikey')  # SendGrid uses 'apikey'
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@it-management.onrender.com')

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
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
        'it_management_platform': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# =============================================================================
# FILE UPLOAD SETTINGS
# =============================================================================

FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB max upload

# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================

ADMIN_URL = 'admin/'

# =============================================================================
# RENDER BUILD CONFIGURATION
# =============================================================================

# Create required directories on startup
def create_render_dirs():
    """Create necessary directories for Render deployment."""
    import os
    dirs = [
        STATIC_ROOT,
        MEDIA_ROOT,
        BASE_DIR / 'logs',
    ]
    for dir_path in dirs:
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)

# Run directory creation on module import
create_render_dirs()

