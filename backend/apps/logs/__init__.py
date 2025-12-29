"""
Logs app for IT Management Platform.
Comprehensive activity logging and audit trail system.
"""

from django.apps import AppConfig

class LogsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.logs'
    verbose_name = 'Activity Logging & Audit'
    
    def ready(self):
        import apps.logs.signals
