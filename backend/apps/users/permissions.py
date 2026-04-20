"""
DRF permission classes for Users.

Only the 8 classes actually imported by views are kept here.
Dead code (12+ unused classes) was removed.
Authorization logic lives in user_authority — these are thin wrappers.
"""

from rest_framework import permissions
from apps.core.permissions import ListPermission, ObjectPermission, ViewPermission
from apps.core.domain.roles import is_admin_role
import apps.users.domain.services.user_authority as auth


class CanViewUsers(ViewPermission):
    list_fn   = staticmethod(auth.can_view_list)
    object_fn = staticmethod(auth.can_view)


class CanCreateUsers(ListPermission):
    list_fn = staticmethod(auth.can_create)


class CanEditUser(ObjectPermission):
    object_fn = staticmethod(auth.can_edit)


class CanChangeUserRole(permissions.BasePermission):
    """
    has_permission: only admin-level roles can change roles at all.
    has_object_permission: delegates to can_change_role (3-arg authority).
    Passing obj.role as new_role is a conservative check — if actor cannot
    even assign the target's current role, they certainly can't change it.
    """
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and is_admin_role(request.user.role)
        )

    def has_object_permission(self, request, view, obj):
        return auth.can_change_role(request.user, obj, obj.role)


class CanDeactivateUser(ObjectPermission):
    object_fn = staticmethod(auth.can_deactivate)


class CanActivateUser(ObjectPermission):
    object_fn = staticmethod(auth.can_activate)


class CanDeleteUser(ObjectPermission):
    object_fn = staticmethod(auth.can_delete)


class IsSelfOrAdmin(permissions.BasePermission):
    """Allow users to act on their own data, or admins to act on anyone."""
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        from apps.users.models import User
        if isinstance(obj, User):
            return auth.can_edit(request.user, obj)
        return False
