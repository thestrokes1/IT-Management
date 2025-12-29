"""
Security app for IT Management Platform.
Provides security utilities, validators, and middleware.
"""

from django.apps import AppConfig

class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.security'
    verbose_name = 'Security & Protection'
    
    def ready(self):
        """Import signals when the app is ready."""
        import apps.security.signals

