"""
Permissions classes for Tickets Management.
Role-based access control for ticket and support operations.
"""

from rest_framework import permissions
from apps.tickets.models import Ticket, TicketComment, TicketAttachment

class CanManageTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_tickets

class IsTicketRequesterOrAssigned(permissions.BasePermission):
    """
    Custom permission to only allow ticket requester or assigned users to edit.
    Read access for authenticated users.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for all authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions for ticket requester, assigned user, or admin
        if request.user.is_admin:
            return True
        
        if hasattr(obj, 'requester'):
            # For tickets
            return (obj.requester == request.user or 
                    obj.assigned_to == request.user or
                    request.user.can_manage_tickets)
        else:
            # For comments and attachments
            ticket = obj.ticket
            return (ticket.requester == request.user or 
                    ticket.assigned_to == request.user or
                    obj.user == request.user or
                    request.user.can_manage_tickets)

class IsTicketCreator(permissions.BasePermission):
    """
    Custom permission to only allow ticket creators to modify their tickets.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can modify all
        if request.user.is_admin:
            return True
        
        if hasattr(obj, 'requester'):
            # For tickets
            return obj.requester == request.user or request.user.can_manage_tickets
        else:
            # For comments and attachments
            return obj.user == request.user or request.user.can_manage_tickets

class CanCreateTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can create tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

class CanViewTicketDetails(permissions.BasePermission):
    """
    Custom permission to check if user can view ticket details.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.is_admin:
            return True
        
        # Ticket requester can view their tickets
        if obj.requester == request.user:
            return True
        
        # Assigned user can view assigned tickets
        if obj.assigned_to == request.user:
            return True
        
        # Users with ticket management rights can view all tickets
        if request.user.can_manage_tickets:
            return True
        
        return False

class CanManageTicketCategories(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket categories.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_tickets
        )

class CanAssignTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can assign tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanResolveTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can resolve tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanCloseTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can close tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanEscalateTickets(permissions.BasePermission):
    """
    Custom permission to only allow users who can escalate tickets.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanViewTicketComments(permissions.BasePermission):
    """
    Custom permission to check if user can view ticket comments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.is_admin:
            return True
        
        ticket = obj.ticket
        
        # Ticket requester can view all comments
        if ticket.requester == request.user:
            # Check if user can view internal comments
            if hasattr(obj, 'is_internal') and obj.is_internal:
                return request.user.can_manage_tickets
            return True
        
        # Assigned user can view all comments
        if ticket.assigned_to == request.user:
            return True
        
        # Users with ticket management rights can view all comments
        if request.user.can_manage_tickets:
            return True
        
        return False

class CanCreateTicketComments(permissions.BasePermission):
    """
    Custom permission to check if user can create ticket comments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can create comments
        if request.user.is_admin:
            return True
        
        ticket = obj.ticket
        
        # Ticket requester can create comments
        if ticket.requester == request.user:
            return True
        
        # Assigned user can create comments
        if ticket.assigned_to == request.user:
            return True
        
        # Users with ticket management rights can create comments
        if request.user.can_manage_tickets:
            return True
        
        return False

class CanManageTicketAttachments(permissions.BasePermission):
    """
    Custom permission to check if user can manage ticket attachments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can manage all attachments
        if request.user.is_admin:
            return True
        
        ticket = obj.ticket
        
        # Ticket requester can manage attachments
        if ticket.requester == request.user:
            return True
        
        # Assigned user can manage attachments
        if ticket.assigned_to == request.user:
            return True
        
        # Attachment creator can manage their attachments
        if obj.user == request.user:
            return True
        
        # Users with ticket management rights can manage attachments
        if request.user.can_manage_tickets:
            return True
        
        return False

class CanViewTicketHistory(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket history.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_admin
        )

class CanViewTicketTemplates(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket templates.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanManageTicketTemplates(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket templates.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_tickets
        )

class CanViewSLAs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view SLAs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_admin
        )

class CanManageSLAs(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage SLAs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_tickets
        )

class CanViewTicketReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_manager
        )

class CanGenerateTicketReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can generate ticket reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_manager
        )

class CanRateTicketSatisfaction(permissions.BasePermission):
    """
    Custom permission to only allow ticket requesters to rate satisfaction.
    """
    
    def has_object_permission(self, request, view, obj):
        # Only the ticket requester can rate satisfaction
        return hasattr(obj, 'ticket') and obj.ticket.requester == request.user

class CanViewTicketEscalations(permissions.BasePermission):
    """
    Custom permission to only allow users who can view ticket escalations.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanManageTicketEscalations(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket escalations.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_technician
        )

class CanAccessTicketStatistics(permissions.BasePermission):
    """
    Custom permission to only allow users who can access ticket statistics.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_tickets or request.user.is_manager
        )

class CanManageTicketWorkflows(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage ticket workflows.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin
