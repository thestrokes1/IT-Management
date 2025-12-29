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
        import apps.assets.signals

