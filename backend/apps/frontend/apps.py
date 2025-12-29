"""
Frontend app configuration.
"""

from django.apps import AppConfig


class FrontendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.frontend'
    verbose_name = 'Frontend Interface'
    description = 'Web interface and user interface components'

