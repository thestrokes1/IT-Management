"""
WSGI configuration for IT Management Platform.
Production WSGI configuration for Render deployment.
"""

import os
import sys
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Add the project directory to the path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Set Django settings module - use render settings on Render
RENDER = os.environ.get('RENDER', False)

if RENDER:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.render')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# Get the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# WhiteNoise for static files (already configured in settings)
# No need for StaticFilesHandler when using WhiteNoise

# Gunicorn will set the application object
__all__ = ['application']
