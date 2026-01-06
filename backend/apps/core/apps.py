# Core app configuration.
# Registers event handlers at application startup.

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuration for the core application."""
    
    name = 'apps.core'
    verbose_name = 'Core'
    
    def ready(self):
        """
        Called by Django when the application is ready.
        Register event handlers here.
        """
        # Import and setup event handlers
        from apps.core.handlers import register_audit_handlers
        register_audit_handlers()

