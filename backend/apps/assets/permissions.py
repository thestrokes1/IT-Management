"""
DRF permission classes for Assets.

Only the 10 classes actually imported by views are kept here.
Dead code (11 unused classes) was removed.
Authorization logic lives in asset_authority — these are thin wrappers.
"""

from rest_framework import permissions
from apps.core.permissions import ListPermission, ObjectPermission, ViewPermission
import apps.assets.domain.services.asset_authority as auth


class CanViewAssets(ViewPermission):
    list_fn   = staticmethod(auth.can_view_list)
    object_fn = staticmethod(auth.can_view)


class CanCreateAssets(ListPermission):
    list_fn = staticmethod(auth.can_create)


class CanEditAsset(ObjectPermission):
    object_fn = staticmethod(auth.can_edit)


class CanDeleteAsset(ObjectPermission):
    object_fn = staticmethod(auth.can_delete)


class CanAssignAsset(permissions.BasePermission):
    """can_assign only checks user.role so None asset is safe for list views."""
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return auth.can_assign(request.user, None, None)

    def has_object_permission(self, request, view, obj):
        return auth.can_assign(request.user, obj, None)


class CanUnassignAsset(ObjectPermission):
    object_fn = staticmethod(auth.can_unassign)


class CanSelfAssignAsset(ObjectPermission):
    object_fn = staticmethod(auth.can_self_assign)


class CanViewAssetLogs(ObjectPermission):
    object_fn = staticmethod(auth.can_view_logs)


class CanAddAssetMaintenance(ObjectPermission):
    object_fn = staticmethod(auth.can_add_maintenance)


class CanViewAssetMaintenance(ObjectPermission):
    object_fn = staticmethod(auth.can_view_maintenance)
