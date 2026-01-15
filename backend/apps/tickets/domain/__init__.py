"""
Tickets domain layer.

Contains pure domain logic for tickets.
"""

from apps.tickets.domain.services.ticket_authority import (
    can_create_ticket,
    can_read_ticket,
    can_update_ticket,
    can_delete_ticket,
    can_assign_ticket,
    can_close_ticket,
    get_ticket_permissions,
    assert_can_update,
    assert_can_delete,
    assert_can_assign,
    assert_can_close,
)

__all__ = [
    'can_create_ticket',
    'can_read_ticket',
    'can_update_ticket',
    'can_delete_ticket',
    'can_assign_ticket',
    'can_close_ticket',
    'get_ticket_permissions',
    'assert_can_update',
    'assert_can_delete',
    'assert_can_assign',
    'assert_can_close',
]

