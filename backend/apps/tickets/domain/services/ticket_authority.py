"""
Ticket authorization domain service.

Pure domain logic for ticket permissions based on strict role hierarchy.
Uses role utilities and ownership checks - no status or workflow logic.
"""

from apps.core.domain.roles import (
    ROLE_RANKS,
    has_higher_role,
    has_strictly_higher_role,
    is_superadmin_or_manager,
)
from apps.core.domain.authorization import AuthorizationError


# Role constants
_ROLE_SUPERADMIN = 'SUPERADMIN'
_ROLE_MANAGER = 'MANAGER'
_ROLE_IT_ADMIN = 'IT_ADMIN'
_ROLE_TECHNICIAN = 'TECHNICIAN'
_ROLE_VIEWER = 'VIEWER'


def can_create_ticket(user) -> bool:
    """
    Check if user can create tickets.
    
    Rules:
    - All roles except VIEWER can create tickets
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user can create tickets
    """
    return user.role != _ROLE_VIEWER


def can_read_ticket(user, ticket) -> bool:
    """
    Check if user can read/view a ticket.
    
    Rules:
    - All roles can read tickets
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can view the ticket
    """
    return True


def can_update_ticket(user, ticket) -> bool:
    """
    Check if user can update a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed if ticket.created_by.role rank is lower
    - TECHNICIAN: allowed only if ticket.created_by == user
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can update the ticket
    """
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can update if created_by has lower role rank
    if user.role == _ROLE_IT_ADMIN:
        if has_strictly_higher_role(user.role, ticket.created_by.role):
            return True
    
    # TECHNICIAN can only update their own created tickets
    if user.role == _ROLE_TECHNICIAN:
        return ticket.created_by_id == user.id
    
    # VIEWER cannot update
    return False


def can_delete_ticket(user, ticket) -> bool:
    """
    Check if user can delete a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed if ticket.created_by.role rank is lower
    - TECHNICIAN: allowed only if ticket.created_by == user
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can delete the ticket
    """
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can delete if created_by has lower role rank
    if user.role == _ROLE_IT_ADMIN:
        if has_strictly_higher_role(user.role, ticket.created_by.role):
            return True
    
    # TECHNICIAN can only delete their own created tickets
    if user.role == _ROLE_TECHNICIAN:
        return ticket.created_by_id == user.id
    
    # VIEWER cannot delete
    return False


def can_assign_ticket(user, ticket, assignee) -> bool:
    """
    Check if user can assign a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed (hierarchy applies)
    - TECHNICIAN: allowed ONLY if user created the ticket AND assignee == user
    - VIEWER: never allowed
    
    Args:
        user: User instance attempting to assign
        ticket: Ticket instance being assigned
        assignee: User instance to assign the ticket to
        
    Returns:
        bool: True if user can assign the ticket
    """
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can assign (hierarchy applies)
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN can ONLY assign their own tickets to themselves
    if user.role == _ROLE_TECHNICIAN:
        # Can they assign this ticket to themselves?
        if assignee is None:
            # Ticket is unassigned - technician can claim it
            return ticket.created_by_id == user.id
        return ticket.created_by_id == user.id and assignee.id == user.id
    
    # VIEWER cannot assign
    return False


def can_close_ticket(user, ticket) -> bool:
    """
    Check if user can close a ticket.
    
    Rules (same as UPDATE):
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed if ticket.created_by.role rank is lower
    - TECHNICIAN: allowed only if ticket.created_by == user
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can close the ticket
    """
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can close if created_by has lower role rank
    if user.role == _ROLE_IT_ADMIN:
        if has_strictly_higher_role(user.role, ticket.created_by.role):
            return True
    
    # TECHNICIAN can only close their own created tickets
    if user.role == _ROLE_TECHNICIAN:
        return ticket.created_by_id == user.id
    
    # VIEWER cannot close
    return False


def can_resolve_ticket(user, ticket) -> bool:
    """
    Check if user can resolve a ticket.
    
    Rules (same as UPDATE/CLOSE):
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed if ticket.created_by.role rank is lower
    - TECHNICIAN: allowed only if ticket.created_by == user
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can resolve the ticket
    """
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can resolve if created_by has lower role rank
    if user.role == _ROLE_IT_ADMIN:
        if has_strictly_higher_role(user.role, ticket.created_by.role):
            return True
    
    # TECHNICIAN can only resolve their own created tickets
    if user.role == _ROLE_TECHNICIAN:
        return ticket.created_by_id == user.id
    
    # VIEWER cannot resolve
    return False


def can_reopen_ticket(user, ticket) -> bool:
    """
    Check if user can reopen a ticket.
    
    Rules:
    - Ticket MUST be in RESOLVED status
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed if ticket.created_by.role rank is lower
    - TECHNICIAN: allowed ONLY if ticket.created_by == user (their own ticket)
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can reopen the ticket
    """
    # Ticket must be RESOLVED to be reopened
    if ticket.status != 'RESOLVED':
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can reopen if created_by has lower role rank
    if user.role == _ROLE_IT_ADMIN:
        if has_strictly_higher_role(user.role, ticket.created_by.role):
            return True
    
    # TECHNICIAN can only reopen their own created tickets
    if user.role == _ROLE_TECHNICIAN:
        return ticket.created_by_id == user.id
    
    # VIEWER cannot reopen
    return False


def can_assign_self(user, ticket) -> bool:
    """
    Check if user can assign a ticket to themselves.
    
    Rules:
    - SUPERADMIN, MANAGER, IT_ADMIN: always allowed
    - TECHNICIAN: allowed ONLY if ticket.created_by == user and ticket not already assigned to self
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can assign the ticket to themselves
    """
    # Admin roles can always assign
    if is_superadmin_or_manager(user.role) or user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN can only claim their own unassigned tickets
    if user.role == _ROLE_TECHNICIAN:
        # Can claim if they created it and it's not already assigned to them
        return ticket.created_by_id == user.id and ticket.assigned_to_id != user.id
    
    # VIEWER cannot assign
    return False


def get_ticket_permissions(user, ticket) -> dict:
    """
    Get all permissions for a user on a specific ticket.
    
    Returns a dictionary with permission checks for UI rendering.
    No side effects - pure read-only permission check.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values:
            - can_assign_self: User can assign ticket to themselves
            - can_edit: User can update the ticket
            - can_resolve: User can resolve the ticket
            - can_reopen: User can reopen the ticket (only if RESOLVED)
    """
    return {
        'can_assign_self': can_assign_self(user, ticket),
        'can_edit': can_update_ticket(user, ticket),
        'can_resolve': can_resolve_ticket(user, ticket),
        'can_reopen': can_reopen_ticket(user, ticket),
    }


def assert_can_update(user, ticket):
    if not can_update_ticket(user, ticket):
        raise AuthorizationError("Cannot update ticket")

def assert_can_delete(user, ticket):
    if not can_delete_ticket(user, ticket):
        raise AuthorizationError("Cannot delete ticket")

def assert_can_assign(user, ticket):
    if not can_assign_ticket(user, ticket):
        raise AuthorizationError("Cannot assign ticket")

def assert_can_close(user, ticket):
    if not can_close_ticket(user, ticket):
        raise AuthorizationError("Cannot close ticket")

def assert_can_resolve(user, ticket):
    if not can_resolve_ticket(user, ticket):
        raise AuthorizationError("Cannot resolve ticket")

def assert_can_reopen(user, ticket):
    if not can_reopen_ticket(user, ticket):
        raise AuthorizationError("Cannot reopen ticket")

def assert_can_cancel(user, ticket):
    """
    Check if user can cancel a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: allowed if ticket.created_by.role rank is lower
    - TECHNICIAN: allowed only if ticket.created_by == user
    - VIEWER: never allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Raises:
        AuthorizationError: If user cannot cancel the ticket
    """
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return
    
    # IT_ADMIN can cancel if created_by has lower role rank
    if user.role == _ROLE_IT_ADMIN:
        if has_strictly_higher_role(user.role, ticket.created_by.role):
            return
    
    # TECHNICIAN can only cancel their own created tickets
    if user.role == _ROLE_TECHNICIAN:
        if ticket.created_by_id == user.id:
            return
    
    # VIEWER cannot cancel
    raise AuthorizationError("Cannot cancel ticket")


# Aliases with _ticket suffix for frontend compatibility
assert_can_update_ticket = assert_can_update
assert_can_delete_ticket = assert_can_delete
assert_can_assign_ticket = assert_can_assign
assert_can_close_ticket = assert_can_close
assert_can_resolve_ticket = assert_can_resolve
assert_can_reopen_ticket = assert_can_reopen
assert_can_cancel_ticket = assert_can_cancel




