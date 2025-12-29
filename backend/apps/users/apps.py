"""
Users app configuration.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users & Roles'
    description = 'User management and role-based access control'
    
    def ready(self):
        import apps.users.signals

