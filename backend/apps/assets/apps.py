"""
Assets app configuration.
"""

from django.apps import AppConfig


class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assets'
    verbose_name = 'Assets Management'
    description = 'Hardware and software asset management system'
    
    def ready(self):
        # Import signals for model-level hooks (if any)
        import apps.assets.signals
        
        # Register domain event handlers
        from apps.assets.domain.events import setup_asset_event_handlers
        setup_asset_event_handlers()

