# PythonAnywhere Web App Configuration
# Save this as /var/www/yourusername_pythonanywhere_com_wsgi.py

import os
import sys

# Add your project directory to sys.path
project_home = '/home/yourusername/it-management-platform/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

# Import WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

