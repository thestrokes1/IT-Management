"""
Ticket authorization domain service.

Pure domain logic for ticket permissions based on strict role hierarchy.
Uses role utilities and ownership checks - no status or workflow logic.

IMPORTANT: For TECHNICIAN role, ownership is determined by assigned_to,
NOT created_by. Technicians can only edit/delete tickets assigned to them.

Role Hierarchy (highest to lowest):
    - SUPERADMIN (rank 4) - Full access, no restrictions
    - MANAGER (rank 4) - Same as SUPERADMIN
    - IT_ADMIN (rank 3) - Full ticket access, cannot manage projects/users
    - TECHNICIAN (rank 2) - Can only manage tickets/assets assigned to them
    - VIEWER (rank 1) - Read-only, no ticket access
"""

from apps.core.domain.roles import (
    ROLE_RANKS,
    has_higher_role,
    has_strictly_higher_role,
    is_superadmin_or_manager,
    is_admin_role,
)
from apps.core.domain.authorization import AuthorizationError


# Role constants
_ROLE_SUPERADMIN = 'SUPERADMIN'
_ROLE_MANAGER = 'MANAGER'
_ROLE_IT_ADMIN = 'IT_ADMIN'
_ROLE_TECHNICIAN = 'TECHNICIAN'
_ROLE_VIEWER = 'VIEWER'


# =============================================================================
# VIEW PERMISSIONS
# =============================================================================

def can_view(user, ticket) -> bool:
    """
    Check if user can view a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed (full access)
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: always allowed (can view any ticket)
    - VIEWER: NOT allowed - VIEWER has no ticket access
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can view the ticket
    """
    # VIEWER has no ticket access
    if user.role == _ROLE_VIEWER:
        return False
    
    # All other roles can view tickets
    return True


def can_view_list(user) -> bool:
    """
    Check if user can view the ticket list.
    
    Rules:
    - VIEWER: NOT allowed
    - All other authenticated roles: allowed
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user can view ticket list
    """
    return user.role != _ROLE_VIEWER


def can_view_details(user, ticket) -> bool:
    """
    Check if user can view ticket details.
    
    Same as can_view - returns HTTP 403 for VIEWER.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can view ticket details
    """
    return can_view(user, ticket)


# =============================================================================
# CREATE PERMISSIONS
# =============================================================================

def can_create(user) -> bool:
    """
    Check if user can create tickets.
    
    Rules:
    - VIEWER: NOT allowed
    - All other roles: allowed
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user can create tickets
    """
    return user.role != _ROLE_VIEWER


# =============================================================================
# EDIT PERMISSIONS
# =============================================================================

def can_edit(user, ticket) -> bool:
    """
    Check if user can edit a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
    - VIEWER: NOT allowed
    
    IMPORTANT: Technician ownership is determined by assigned_to,
    NOT created_by.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can edit the ticket
    """
    # VIEWER cannot edit
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full ticket access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only edit if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id == user.id
    
    return False


def can_update(user, ticket) -> bool:
    """
    Alias for can_edit - check if user can update a ticket.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can update the ticket
    """
    return can_edit(user, ticket)


def can_modify(user, ticket) -> bool:
    """
    Alias for can_edit - check if user can modify a ticket.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can modify the ticket
    """
    return can_edit(user, ticket)


# =============================================================================
# DELETE PERMISSIONS
# =============================================================================

def can_delete(user, ticket) -> bool:
    """
    Check if user can delete a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
    - VIEWER: NOT allowed
    
    IMPORTANT: Technician ownership is determined by assigned_to,
    NOT created_by.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can delete the ticket
    """
    # VIEWER cannot delete
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full ticket access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only delete if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id == user.id
    
    return False


# =============================================================================
# ASSIGN / UNASSIGN PERMISSIONS
# =============================================================================

def can_assign(user, ticket, assignee) -> bool:
    """
    Check if user can assign a ticket to another user.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: NEVER allowed (cannot assign to others)
    - VIEWER: NOT allowed
    
    Args:
        user: User instance attempting to assign
        ticket: Ticket instance being assigned
        assignee: User instance to assign the ticket to
        
    Returns:
        bool: True if user can assign the ticket
    """
    # VIEWER cannot assign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full ticket access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: NEVER can assign to others
    return False


def can_unassign(user, ticket) -> bool:
    """
    Check if user can unassign a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
    - VIEWER: NOT allowed
    
    Args:
        user: User instance attempting to unassign
        ticket: Ticket instance
        
    Returns:
        bool: True if user can unassign the ticket
    """
    # VIEWER cannot unassign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER have full access
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN has full ticket access
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only unassign if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id == user.id
    
    return False


def can_self_assign(user, ticket) -> bool:
    """
    Check if user can self-assign to a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
      (technician can claim unassigned ticket)
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can self-assign the ticket
    """
    # VIEWER cannot self-assign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER can always self-assign
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can always self-assign
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only self-assign if unassigned
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id is None
    
    return False


def can_unassign_self(user, ticket) -> bool:
    """
    Check if user can unassign themselves from a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can unassign themselves from the ticket
    """
    # VIEWER cannot unassign
    if user.role == _ROLE_VIEWER:
        return False
    
    # SUPERADMIN and MANAGER can always unassign
    if is_superadmin_or_manager(user.role):
        return True
    
    # IT_ADMIN can always unassign
    if user.role == _ROLE_IT_ADMIN:
        return True
    
    # TECHNICIAN: can only unassign if assigned to them
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id == user.id
    
    return False


def can_assign_to_self(user, ticket) -> bool:
    """
    Check if user can assign the ticket to themselves.
    
    Used by the UI self-assign action. Delegates to can_self_assign
    for consistent authorization logic.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket is unassigned
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can self-assign the ticket
    """
    return can_self_assign(user, ticket)


def can_reassign(user, ticket) -> bool:
    """
    Check if user can reassign a ticket to another user.
    
    Same as can_assign - TECHNICIAN cannot reassign.
    
    Args:
        user: User instance attempting to reassign
        ticket: Ticket instance
        
    Returns:
        bool: True if user can reassign the ticket
    """
    # TECHNICIAN cannot reassign
    if user.role == _ROLE_TECHNICIAN:
        return False
    
    # Other roles can reassign (checked by can_assign)
    return can_assign(user, ticket, None)


# =============================================================================
# STATUS CHANGE PERMISSIONS
# =============================================================================

def can_close(user, ticket) -> bool:
    """
    Check if user can close a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can close the ticket
    """
    return can_edit(user, ticket)


def can_resolve(user, ticket) -> bool:
    """
    Check if user can resolve a ticket.
    
    Same as can_edit.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can resolve the ticket
    """
    return can_edit(user, ticket)


def can_reopen(user, ticket) -> bool:
    """
    Check if user can reopen a ticket.
    
    Rules:
    - Ticket must be in RESOLVED status (enforced by caller)
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed (full ticket access)
    - TECHNICIAN: allowed ONLY if ticket.assigned_to == user
    - VIEWER: NOT allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can reopen the ticket
    """
    return can_edit(user, ticket)


def can_cancel(user, ticket) -> bool:
    """
    Check if user can cancel a ticket.
    
    Same as can_edit.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can cancel the ticket
    """
    return can_edit(user, ticket)


# =============================================================================
# COMMENT / ATTACHMENT PERMISSIONS
# =============================================================================

def can_add_comment(user, ticket) -> bool:
    """
    Check if user can add a comment to a ticket.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if ticket.assigned_to == user
    - All other roles: allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can add comments
    """
    # VIEWER cannot comment
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN: can only comment if assigned
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id == user.id
    
    # Other roles can comment
    return True


def can_view_comment(user, ticket, comment) -> bool:
    """
    Check if user can view a specific comment.
    
    Rules:
    - VIEWER: cannot view internal comments
    - TECHNICIAN: only if ticket.assigned_to == user
    - All other roles: allowed
    
    Args:
        user: User instance
        ticket: Ticket instance
        comment: TicketComment instance
        
    Returns:
        bool: True if user can view the comment
    """
    # VIEWER cannot view internal comments
    if user.role == _ROLE_VIEWER:
        return False
    
    # TECHNICIAN: can only view if assigned
    if user.role == _ROLE_TECHNICIAN:
        return ticket.assigned_to_id == user.id
    
    return True


def can_add_attachment(user, ticket) -> bool:
    """
    Check if user can add an attachment to a ticket.
    
    Same as can_add_comment.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        bool: True if user can add attachments
    """
    return can_add_comment(user, ticket)


# =============================================================================
# PERMISSION AGGREGATION
# =============================================================================

def get_permissions(user, ticket) -> dict:
    """
    Get all permissions for a user on a specific ticket.
    
    Returns a dictionary with all permission checks for UI rendering.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_view': can_view(user, ticket),
        'can_edit': can_edit(user, ticket),
        'can_delete': can_delete(user, ticket),
        'can_assign': can_assign(user, ticket, None),
        'can_unassign': can_unassign(user, ticket),
        'can_self_assign': can_self_assign(user, ticket),
        'can_unassign_self': can_unassign_self(user, ticket),
        'can_close': can_close(user, ticket),
        'can_resolve': can_resolve(user, ticket),
        'can_reopen': can_reopen(user, ticket),
        'can_cancel': can_cancel(user, ticket),
        'can_add_comment': can_add_comment(user, ticket),
        'can_add_attachment': can_add_attachment(user, ticket),
    }


def get_list_permissions(user) -> dict:
    """
    Get all list-level permissions for a user.
    
    Args:
        user: User instance
        
    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_view_list': can_view_list(user),
        'can_create': can_create(user),
    }


# =============================================================================
# ASSERTION HELPERS (Raise AuthorizationError)
# =============================================================================

def assert_can_view(user, ticket) -> None:
    """
    Assert that user can view the ticket.
    
    Raises:
        AuthorizationError: If user cannot view the ticket
    """
    if not can_view(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to view ticket"
        )


def assert_can_create(user) -> None:
    """
    Assert that user can create tickets.
    
    Raises:
        AuthorizationError: If user cannot create tickets
    """
    if not can_create(user):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to create tickets"
        )


def assert_can_edit(user, ticket) -> None:
    """
    Assert that user can edit the ticket.
    
    Raises:
        AuthorizationError: If user cannot edit the ticket
    """
    if not can_edit(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to edit ticket"
        )


def assert_can_delete(user, ticket) -> None:
    """
    Assert that user can delete the ticket.
    
    Raises:
        AuthorizationError: If user cannot delete the ticket
    """
    if not can_delete(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to delete ticket"
        )


def assert_can_assign(user, ticket, assignee) -> None:
    """
    Assert that user can assign the ticket.
    
    Raises:
        AuthorizationError: If user cannot assign the ticket
    """
    if not can_assign(user, ticket, assignee):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to assign ticket"
        )


def assert_can_unassign(user, ticket) -> None:
    """
    Assert that user can unassign the ticket.
    
    Raises:
        AuthorizationError: If user cannot unassign the ticket
    """
    if not can_unassign(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to unassign ticket"
        )


def assert_can_self_assign(user, ticket) -> None:
    """
    Assert that user can self-assign the ticket.
    
    Raises:
        AuthorizationError: If user cannot self-assign the ticket
    """
    if not can_self_assign(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to self-assign ticket"
        )


def assert_can_close(user, ticket) -> None:
    """
    Assert that user can close the ticket.
    
    Raises:
        AuthorizationError: If user cannot close the ticket
    """
    if not can_close(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to close ticket"
        )


def assert_can_resolve(user, ticket) -> None:
    """
    Assert that user can resolve the ticket.
    
    Raises:
        AuthorizationError: If user cannot resolve the ticket
    """
    if not can_resolve(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to resolve ticket"
        )


def assert_can_reopen(user, ticket) -> None:
    """
    Assert that user can reopen the ticket.
    
    Raises:
        AuthorizationError: If user cannot reopen the ticket
    """
    if not can_reopen(user, ticket):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to reopen ticket"
        )


# =============================================================================
# LEGACY ALIASES (for backward compatibility)
# =============================================================================

def can_read_ticket(user, ticket) -> bool:
    """Alias for can_view."""
    return can_view(user, ticket)


def can_create_ticket(user) -> bool:
    """Alias for can_create."""
    return can_create(user)


def can_update_ticket(user, ticket) -> bool:
    """Alias for can_edit."""
    return can_edit(user, ticket)


def can_delete_ticket(user, ticket) -> bool:
    """Alias for can_delete."""
    return can_delete(user, ticket)


def can_assign_ticket(user, ticket, assignee) -> bool:
    """Alias for can_assign."""
    return can_assign(user, ticket, assignee)


def can_close_ticket(user, ticket) -> bool:
    """Alias for can_close."""
    return can_close(user, ticket)


def can_resolve_ticket(user, ticket) -> bool:
    """Alias for can_resolve."""
    return can_resolve(user, ticket)


def can_reopen_ticket(user, ticket) -> bool:
    """Alias for can_reopen."""
    return can_reopen(user, ticket)


def can_self_assign_ticket(user, ticket) -> bool:
    """Alias for can_self_assign."""
    return can_self_assign(user, ticket)


def can_reassign_ticket(user, ticket) -> bool:
    """Alias for can_reassign."""
    return can_reassign(user, ticket)


def can_unassign_ticket(user, ticket) -> bool:
    """Alias for can_unassign."""
    return can_unassign(user, ticket)


def get_ticket_permissions(user, ticket) -> dict:
    """Alias for get_permissions."""
    return get_permissions(user, ticket)


# Legacy assertion aliases
def assert_can_update(user, ticket):
    return assert_can_edit(user, ticket)


def assert_can_delete(user, ticket):
    return assert_can_delete(user, ticket)


def assert_can_assign(user, ticket):
    return assert_can_assign(user, ticket, None)


def assert_can_close(user, ticket):
    return assert_can_close(user, ticket)


def assert_can_resolve(user, ticket):
    return assert_can_resolve(user, ticket)


def assert_can_reopen(user, ticket):
    return assert_can_reopen(user, ticket)


def assert_can_cancel(user, ticket):
    if not can_cancel(user, ticket):
        raise AuthorizationError("Cannot cancel ticket")


# Legacy assertion aliases with _ticket suffix
assert_can_update_ticket = assert_can_update
assert_can_delete_ticket = assert_can_delete
assert_can_assign_ticket = assert_can_assign
assert_can_close_ticket = assert_can_close
assert_can_resolve_ticket = assert_can_resolve
assert_can_reopen_ticket = assert_can_reopen
assert_can_cancel_ticket = assert_can_cancel


# =============================================================================
# TICKET AUTHORITY CLASS - Wrapper for domain service functions
# =============================================================================

class TicketAuthority:
    """
    Wrapper class for ticket authorization functions.
    Allows using OOP-style access to authorization rules.
    
    Example:
        authority = TicketAuthority()
        if authority.can_view(user, ticket):
            # proceed
    """
    
    def can_view(self, user, ticket) -> bool:
        """Check if user can view this ticket."""
        return can_view(user, ticket)
    
    def can_view_list(self, user) -> bool:
        """Check if user can view ticket list."""
        return can_view_list(user)
    
    def can_view_details(self, user, ticket) -> bool:
        """Check if user can view ticket details."""
        return can_view_details(user, ticket)
    
    def can_create(self, user) -> bool:
        """Check if user can create tickets."""
        return can_create(user)
    
    def can_edit(self, user, ticket) -> bool:
        """Check if user can edit this ticket."""
        return can_edit(user, ticket)
    
    def can_update(self, user, ticket) -> bool:
        """Check if user can update this ticket."""
        return can_update(user, ticket)
    
    def can_modify(self, user, ticket) -> bool:
        """Check if user can modify this ticket."""
        return can_modify(user, ticket)
    
    def can_delete(self, user, ticket) -> bool:
        """Check if user can delete this ticket."""
        return can_delete(user, ticket)
    
    def can_assign(self, user, ticket, assignee) -> bool:
        """Check if user can assign this ticket."""
        return can_assign(user, ticket, assignee)
    
    def can_unassign(self, user, ticket) -> bool:
        """Check if user can unassign this ticket."""
        return can_unassign(user, ticket)
    
    def can_self_assign(self, user, ticket) -> bool:
        """Check if user can self-assign this ticket."""
        return can_self_assign(user, ticket)
    
    def can_unassign_self(self, user, ticket) -> bool:
        """Check if user can unassign themselves from this ticket."""
        return can_unassign_self(user, ticket)
    
    def can_assign_to_self(self, user, ticket) -> bool:
        """Check if user can assign ticket to themselves."""
        return can_assign_to_self(user, ticket)
    
    def can_reassign(self, user, ticket) -> bool:
        """Check if user can reassign this ticket."""
        return can_reassign(user, ticket)
    
    def can_close(self, user, ticket) -> bool:
        """Check if user can close this ticket."""
        return can_close(user, ticket)
    
    def can_resolve(self, user, ticket) -> bool:
        """Check if user can mark ticket as resolved."""
        return can_resolve(user, ticket)
    
    def can_reopen(self, user, ticket) -> bool:
        """Check if user can reopen this ticket."""
        return can_reopen(user, ticket)
    
    def can_cancel(self, user, ticket) -> bool:
        """Check if user can cancel this ticket."""
        return can_cancel(user, ticket)
    
    def can_add_comment(self, user, ticket) -> bool:
        """Check if user can add comments to this ticket."""
        return can_add_comment(user, ticket)
    
    def can_view_comment(self, user, ticket, comment) -> bool:
        """Check if user can view a comment on this ticket."""
        return can_view_comment(user, ticket, comment)
    
    def can_add_attachment(self, user, ticket) -> bool:
        """Check if user can add attachments to this ticket."""
        return can_add_attachment(user, ticket)
