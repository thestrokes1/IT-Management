"""
Tickets app for IT Management Platform.
IT support ticket management system with role-based access control.
"""

from django.apps import AppConfig

class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'
    verbose_name = 'Ticket Management'
    
    def ready(self):
        import apps.tickets.signals
