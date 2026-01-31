"""
Permissions classes for Tickets Management.

Role-based access control for ticket and support operations.
All permission checks are enforced server-side using domain authority services.

IMPORTANT: All permission checks MUST use the domain authority services
to ensure consistent enforcement across all entry points (API, views, etc.).
"""

from rest_framework import permissions
from apps.tickets.models import Ticket, TicketComment, TicketAttachment


class CanViewTickets(permissions.BasePermission):
    """
    Check if user can view tickets.
    
    Rules:
    - VIEWER: NOT allowed
    - All other roles: allowed
    """
    
    def has_permission(self, request, view):
        from apps.tickets.domain.services.ticket_authority import can_view_list
        return (
            request.user 
            and request.user.is_authenticated 
            and can_view_list(request.user)
        )
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_view
        return can_view(request.user, obj)


class CanCreateTickets(permissions.BasePermission):
    """
    Check if user can create tickets.
    
    Rules:
    - VIEWER: NOT allowed
    - All other roles: allowed
    """
    
    def has_permission(self, request, view):
        from apps.tickets.domain.services.ticket_authority import can_create
        return (
            request.user 
            and request.user.is_authenticated 
            and can_create(request.user)
        )


class CanEditTicket(permissions.BasePermission):
    """
    Check if user can edit a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_edit
        return can_edit(request.user, obj)


class CanDeleteTicket(permissions.BasePermission):
    """
    Check if user can delete a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_delete
        return can_delete(request.user, obj)


class CanAssignTicket(permissions.BasePermission):
    """
    Check if user can assign a ticket to another user.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: NEVER allowed
    - VIEWER: NOT allowed
    """
    
    def has_permission(self, request, view):
        from apps.tickets.domain.services.ticket_authority import can_assign
        ticket = getattr(view, 'get_object', lambda: None)()
        if ticket is None:
            # For list views, check general assign permission
            return request.user.is_authenticated and request.user.role in (
                'SUPERADMIN', 'MANAGER', 'IT_ADMIN'
            )
        return can_assign(request.user, ticket, None)
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_assign
        return can_assign(request.user, obj, None)


class CanUnassignTicket(permissions.BasePermission):
    """
    Check if user can unassign a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: NEVER allowed
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_unassign
        return can_unassign(request.user, obj)


class CanSelfAssignTicket(permissions.BasePermission):
    """
    Check if user can self-assign to a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if unassigned
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_self_assign
        return can_self_assign(request.user, obj)


class CanCloseTicket(permissions.BasePermission):
    """
    Check if user can close a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_close
        return can_close(request.user, obj)


class CanResolveTicket(permissions.BasePermission):
    """
    Check if user can resolve a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_resolve
        return can_resolve(request.user, obj)


class CanReopenTicket(permissions.BasePermission):
    """
    Check if user can reopen a ticket.
    
    Rules:
    - SUPERADMIN, MANAGER: always allowed
    - IT_ADMIN: always allowed
    - TECHNICIAN: only if assigned_to == user
    - VIEWER: NOT allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_reopen
        return can_reopen(request.user, obj)


class CanAddTicketComment(permissions.BasePermission):
    """
    Check if user can add a comment to a ticket.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if assigned_to == user
    - All other roles: allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_add_comment
        return can_add_comment(request.user, obj)


class CanViewTicketComment(permissions.BasePermission):
    """
    Check if user can view a ticket comment.
    
    Rules:
    - VIEWER: cannot view internal comments
    - TECHNICIAN: only if assigned_to == user
    - All other roles: allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_view_comment
        return can_view_comment(request.user, obj.ticket, obj)


class CanAddTicketAttachment(permissions.BasePermission):
    """
    Check if user can add an attachment to a ticket.
    
    Rules:
    - VIEWER: NOT allowed
    - TECHNICIAN: only if assigned_to == user
    - All other roles: allowed
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_add_attachment
        return can_add_attachment(request.user, obj)


class IsTicketRequesterOrAssigned(permissions.BasePermission):
    """
    Custom permission to only allow ticket requester or assigned users to edit.
    Read access for authenticated users.
    
    This is kept for backward compatibility - prefer using CanEditTicket.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users (except VIEWER)
        if request.method in permissions.SAFE_METHODS:
            from apps.tickets.domain.services.ticket_authority import can_view
            return can_view(request.user, obj)
        
        # Write permissions
        from apps.tickets.domain.services.ticket_authority import can_edit
        return can_edit(request.user, obj)


class IsTicketCreator(permissions.BasePermission):
    """
    Custom permission to only allow ticket creators to modify their tickets.
    
    This is kept for backward compatibility - prefer using CanEditTicket.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_edit
        return can_edit(request.user, obj)


# =============================================================================
# Legacy permissions (for backward compatibility)
# =============================================================================

class CanManageTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage tickets.
    """
    
    def has_permission(self, request, view):
        from apps.tickets.domain.services.ticket_authority import can_create
        return (
            request.user 
            and request.user.is_authenticated 
            and can_create(request.user)
        )


class CanViewTicketDetails(permissions.BasePermission):
    """
    Custom permission to check if user can view ticket details.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_view
        return can_view(request.user, obj)


class CanManageTicketCategories(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket categories.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanViewTicketComments(permissions.BasePermission):
    """
    Custom permission to check if user can view ticket comments.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_view_comment
        return can_view_comment(request.user, obj.ticket, obj)


class CanCreateTicketComments(permissions.BasePermission):
    """
    Custom permission to check if user can create ticket comments.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_add_comment
        return can_add_comment(request.user, obj.ticket)


class CanManageTicketAttachments(permissions.BasePermission):
    """
    Custom permission to check if user can manage ticket attachments.
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_add_attachment
        return can_add_attachment(request.user, obj.ticket)


class CanViewTicketHistory(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket history.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanViewTicketTemplates(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket templates.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role != 'VIEWER'
        )


class CanManageTicketTemplates(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket templates.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanViewSLAs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view SLAs.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanManageSLAs(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage SLAs.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanViewTicketReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket reports.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanGenerateTicketReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can generate ticket reports.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanRateTicketSatisfaction(permissions.BasePermission):
    """
    Custom permission to only allow ticket requesters to rate satisfaction.
    """
    
    def has_object_permission(self, request, view, obj):
        return hasattr(obj, 'ticket') and obj.ticket.requester == request.user


class CanViewTicketEscalations(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket escalations.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role != 'VIEWER'
        )


class CanManageTicketEscalations(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket escalations.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanAccessTicketStatistics(permissions.BasePermission):
    """
    Custom permission to only allow users who can access ticket statistics.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class CanManageTicketWorkflows(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket workflows.
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.role in ('SUPERADMIN', 'MANAGER', 'IT_ADMIN')
        )


class IsAssignedTechnician(permissions.BasePermission):
    """
    Custom permission to check if user is the assigned technician.
    
    Rules:
    - User must be the assigned technician
    - ADMIN roles always have access
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_edit
        return can_edit(request.user, obj)


class CanReassignTicket(permissions.BasePermission):
    """
    Custom permission to check if user can reassign a ticket.
    
    Rules:
    - MANAGER / IT_ADMIN / SUPERADMIN: can always reassign
    - TECHNICIAN: CANNOT reassign tickets (even their own)
    """
    
    def has_object_permission(self, request, view, obj):
        from apps.tickets.domain.services.ticket_authority import can_reassign
        return can_reassign(request.user, obj)

