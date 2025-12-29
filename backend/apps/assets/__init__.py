"""
Assets app for IT Management Platform.
Hardware and software asset management system.
"""

from django.apps import AppConfig

class AssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.assets'
    verbose_name = 'Asset Management'
    
    def ready(self):
        import apps.assets.signals
