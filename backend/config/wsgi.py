"""
WSGI configuration for IT Management Platform.
Production WSGI configuration for PythonAnywhere deployment.
"""

import os
import sys

# Add the project directory to the path
path = '/home/your-username/mysite/it_management_platform/backend'
if path not in sys.path:
    sys.path.insert(0, path)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

# For PythonAnywhere - set the application object
application = get_wsgi_application()

# Static files serving (optional - can be handled by web server)
from django.contrib.staticfiles.handlers import StaticFilesHandler
application = StaticFilesHandler(application)
