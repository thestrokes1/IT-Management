"""
DRF permission classes for Tickets.

Only the 13 classes actually imported by views are kept here.
Dead code (22 unused classes) was removed.
Authorization logic lives in ticket_authority — these classes are thin wrappers.
"""

from rest_framework import permissions
from apps.core.permissions import ListPermission, ObjectPermission, ViewPermission
import apps.tickets.domain.services.ticket_authority as auth


class CanViewTickets(ViewPermission):
    list_fn   = staticmethod(auth.can_view_list)
    object_fn = staticmethod(auth.can_view)


class CanCreateTickets(ListPermission):
    list_fn = staticmethod(auth.can_create)


class CanEditTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_edit)


class CanDeleteTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_delete)


class CanAssignTicket(permissions.BasePermission):
    """
    Assign permission has a fallback for list views where no object is available.
    can_assign only checks user.role so None ticket is safe.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return auth.can_assign(request.user, None, None)

    def has_object_permission(self, request, view, obj):
        return auth.can_assign(request.user, obj, None)


class CanUnassignTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_unassign)


class CanSelfAssignTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_self_assign)


class CanCloseTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_close)


class CanResolveTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_resolve)


class CanReopenTicket(ObjectPermission):
    object_fn = staticmethod(auth.can_reopen)


class CanAddTicketComment(ObjectPermission):
    object_fn = staticmethod(auth.can_add_comment)


class CanViewTicketComment(permissions.BasePermission):
    """Special case: can_view_comment takes (user, ticket, comment) — 3 args."""
    def has_object_permission(self, request, view, obj):
        return auth.can_view_comment(request.user, obj.ticket, obj)


class CanAddTicketAttachment(ObjectPermission):
    object_fn = staticmethod(auth.can_add_attachment)
