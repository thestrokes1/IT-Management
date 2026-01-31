"""
Tickets Application Layer.

Contains use-case classes that orchestrate domain services.
Acts as intermediary between views (presentation layer) and domain services.
Handles cross-cutting concerns: authorization, idempotency, transaction boundaries.
"""

from apps.tickets.application.create_ticket import (
    CreateTicket,
    CreateTicketResult,
)
from apps.tickets.application.update_ticket import (
    UpdateTicket,
    UpdateTicketResult,
)
from apps.tickets.application.delete_ticket import (
    DeleteTicket,
    DeleteTicketResult,
)
from apps.tickets.application.assign_ticket import (
    AssignTicket,
    UnassignTicket,
    AssignTicketResult,
)
from apps.tickets.application.close_ticket import (
    CloseTicket,
    CloseTicketResult,
)
from apps.tickets.application.assign_ticket_to_self import (
    AssignTicketToSelf,
    AssignTicketToSelfResult,
)

__all__ = [
    'CreateTicket',
    'CreateTicketResult',
    'UpdateTicket',
    'UpdateTicketResult',
    'DeleteTicket',
    'DeleteTicketResult',
    'AssignTicket',
    'UnassignTicket',
    'AssignTicketResult',
    'AssignTicketToSelf',
    'AssignTicketToSelfResult',
    'CloseTicket',
    'CloseTicketResult',
]

