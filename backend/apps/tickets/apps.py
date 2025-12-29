"""
Tickets app configuration.
"""

from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'
    verbose_name = 'IT Ticketing System'
    description = 'IT support ticket management system'
    
    def ready(self):
        import apps.tickets.signals

