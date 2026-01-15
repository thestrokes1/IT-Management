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


def get_ticket_permissions(user, ticket) -> dict:
    """
    Get all permissions for a user on a specific ticket.
    
    Returns a dictionary with all permission checks.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_create': can_create_ticket(user),
        'can_read': can_read_ticket(user, ticket),
        'can_update': can_update_ticket(user, ticket),
        'can_delete': can_delete_ticket(user, ticket),
        'can_assign': can_assign_ticket(user, ticket, ticket.assigned_to),
        'can_close': can_close_ticket(user, ticket),
    }


def assert_can_update_ticket(user, ticket) -> None:
    """
    Assert that user can update the ticket.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_update_ticket(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to update ticket"
        )


def assert_can_delete_ticket(user, ticket) -> None:
    """
    Assert that user can delete the ticket.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_delete_ticket(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to delete ticket"
        )


def assert_can_assign_ticket(user, ticket, assignee) -> None:
    """
    Assert that user can assign the ticket.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_assign_ticket(user, ticket, assignee):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to assign ticket"
        )


def assert_can_close_ticket(user, ticket) -> None:
    """
    Assert that user can close the ticket.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_close_ticket(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to close ticket"
        )


