"""
Frontend app for IT Management Platform.
Static files, templates, and web interface components.
"""

from django.apps import AppConfig

class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.frontend'
    verbose_name = 'Frontend Interface'

