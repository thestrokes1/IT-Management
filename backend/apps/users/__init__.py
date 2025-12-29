"""
Users app for IT Management Platform.
Custom user model with role-based access control.
"""

from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'User Management'
    
    def ready(self):
        import apps.users.signals
