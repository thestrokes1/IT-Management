"""
Logs app configuration.
"""

from django.apps import AppConfig


class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.logs'
    verbose_name = 'Logs & Audit'
    description = 'Activity logging and audit trail system'
    
    def ready(self):
        import apps.logs.signals

