"""
Base DRF permission classes for IT Management Platform.

Three patterns cover almost every domain permission:

  ListPermission    — has_permission only (list-level check, no object)
  ObjectPermission  — has_object_permission only (object-level check)
  ViewPermission    — both list + object (most common for read access)

Usage in domain permission files:
    from apps.core.permissions import ListPermission, ObjectPermission, ViewPermission
    import apps.tickets.domain.services.ticket_authority as auth

    class CanViewTickets(ViewPermission):
        list_fn   = staticmethod(auth.can_view_list)
        object_fn = staticmethod(auth.can_view)

    class CanCreateTickets(ListPermission):
        list_fn = staticmethod(auth.can_create)

    class CanEditTicket(ObjectPermission):
        object_fn = staticmethod(auth.can_edit)
"""

from rest_framework import permissions


def _authenticated(request) -> bool:
    return bool(request.user and request.user.is_authenticated)


class ListPermission(permissions.BasePermission):
    """Permission requiring only a list-level check (no object needed)."""
    list_fn = None  # staticmethod(fn(user) -> bool)

    def has_permission(self, request, view):
        return _authenticated(request) and self.list_fn(request.user)


class ObjectPermission(permissions.BasePermission):
    """Permission requiring only an object-level check."""
    object_fn = None  # staticmethod(fn(user, obj) -> bool)

    def has_object_permission(self, request, view, obj):
        return self.object_fn(request.user, obj)


class ViewPermission(permissions.BasePermission):
    """Permission that checks both list-level access and object-level access."""
    list_fn = None    # staticmethod(fn(user) -> bool)
    object_fn = None  # staticmethod(fn(user, obj) -> bool)

    def has_permission(self, request, view):
        return _authenticated(request) and self.list_fn(request.user)

    def has_object_permission(self, request, view, obj):
        return self.object_fn(request.user, obj)
