"""
Production settings for IT Management Platform.
Production-ready settings for PythonAnywhere deployment.
"""

from .base import *
from decouple import config
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Production hosts (update with actual domain)
ALLOWED_HOSTS = ['your-domain.pythonanywhere.com', 'localhost', '127.0.0.1']

# Database configuration for PostgreSQL (PythonAnywhere)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='it_management_db'),
        'USER': config('DB_USER', default='it_management_user'),
        'PASSWORD': config('DB_PASSWORD', default='your-db-password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'charset': 'utf8',
        },
        'TEST': {
            'NAME': 'test_it_management_db',
        },
    }
}

# Cache configuration for production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'KEY_PREFIX': 'it_mgmt',
        'VERSION': 1,
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# Static files configuration for production
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/your-domain_pythonanywhere_com/staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files configuration for production
MEDIA_URL = '/media/'
MEDIA_ROOT = '/var/www/your-domain_pythonanywhere_com/media'

# Whitenoise for serving static files
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise
] + MIDDLEWARE[1:]  # Keep other middleware

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Email backend for production (configure with your email service)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@your-domain.com')

# Production logging configuration
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
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/production.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'it_management_platform': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# CORS settings for production (restrict to your domain)
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.pythonanywhere.com",
    "https://www.your-domain.pythonanywhere.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://your-domain.pythonanywhere.com",
    "https://www.your-domain.pythonanywhere.com",
]

# Rate limiting (if using django-ratelimit)
RATELIMIT_USE_CACHE = 'default'

# Admin configuration
ADMIN_URL = 'admin/'

# File upload settings
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Timezone
TIME_ZONE = 'UTC'
USE_TZ = True

# Disable debug toolbar in production
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG and request.META.get('REMOTE_ADDR') in INTERNAL_IPS,
}

# Remove development-only apps
INSTALLED_APPS = [
    app for app in INSTALLED_APPS 
    if app not in ['debug_toolbar', 'silk', 'django_extensions']
]

# Security headers
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Sentry integration (optional)
# SENTRY_DSN = config('SENTRY_DSN', default='')
# if SENTRY_DSN:
#     import sentry_sdk
#     from sentry_sdk.integrations.django import DjangoIntegration
#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration()],
#         traces_sample_rate=0.1,
#         send_default_pii=True
#     )

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)
