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
        # Import signals for model-level hooks (if any)
        import apps.tickets.signals
        
        # Register domain event handlers
        from apps.tickets.domain.events import setup_ticket_event_handlers
        setup_ticket_event_handlers()

