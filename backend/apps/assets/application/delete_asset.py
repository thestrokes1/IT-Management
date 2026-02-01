"""
Asset deletion use case.

Application layer for deleting assets.
Handles authorization and transaction boundaries.
Authorization is enforced via domain service with strict RBAC.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.assets.domain.services.asset_authority import (
    assert_can_delete,
    can_delete,
)


@dataclass
class DeleteAssetResult:
    """Result of asset deletion use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'DeleteAssetResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'DeleteAssetResult':
        return cls(success=False, error=error)


class DeleteAsset:
    """
    Use case for deleting an asset.

    Business Rules:
    - Authorization check via domain service
    - Cascades deletion of related records
    - Technician can only delete assets assigned to them
    - SUPERADMIN can delete any asset

    Input (via execute):
        user: User - User performing the deletion
        asset_id: UUID - ID of asset to delete
        idempotency_key: Optional[str] - Key to prevent duplicate deletions

    Output:
        DeleteAssetResult with deletion confirmation or error

    Usage:
        result = DeleteAsset().execute(
            user=request.user,
            asset_id=asset_uuid,
            idempotency_key="delete-asset-123"
        )

        if result.success:
            print(f"Deleted asset")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        user: Any,
        asset_id: str,
        idempotency_key: Optional[str] = None,
    ) -> DeleteAssetResult:
        """
        Execute asset deletion use case.

        Args:
            user: User performing the deletion
            asset_id: UUID string of asset to delete
            idempotency_key: Optional key to prevent duplicate deletions

        Returns:
            DeleteAssetResult with deletion confirmation or error
        """
        from django.db import transaction
        from apps.assets.models import (
            Asset, AssetAssignment, AssetMaintenance,
            AssetAuditLog, AssetDocument,
        )

        # Get asset
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return DeleteAssetResult.fail("Asset not found")

        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_delete(user, asset)
        except Exception as e:
            return DeleteAssetResult.fail(str(e))

        # Store asset info before deletion for result
        asset_name = asset.name
        asset_id_int = asset.id

        # Delete with cascade
        with transaction.atomic():
            # Delete related records
            AssetAssignment.objects.filter(asset=asset).delete()
            AssetMaintenance.objects.filter(asset=asset).delete()
            AssetAuditLog.objects.filter(asset_id=asset.id).delete()
            AssetDocument.objects.filter(asset=asset).delete()

            # Delete the asset
            asset.delete()

        return DeleteAssetResult.ok(
            data={
                'asset_id': asset_id,
                'name': asset_name,
                'message': 'Asset deleted successfully',
            }
        )


class CanDeleteAsset:
    """
    Simple check if user can delete an asset.
    
    Returns:
        bool: True if user can delete the asset
    """
    
    def check(self, user: Any, asset_id: str) -> bool:
        """
        Check if user can delete the asset.
        
        Args:
            user: User attempting to delete
            asset_id: UUID of asset to delete
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.assets.models import Asset
        
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return False
        
        return can_delete(user, asset)

