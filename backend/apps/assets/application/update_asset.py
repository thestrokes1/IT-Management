"""
Asset update use case.

Application layer for updating assets.
Handles authorization and transaction boundaries.
Authorization is enforced via domain service with strict RBAC.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from django.db import transaction

from apps.core.domain.authorization import AuthorizationError
from apps.assets.domain.services.asset_authority import (
    assert_can_edit,
    can_edit,
)


@dataclass
class UpdateAssetResult:
    """Result of asset update use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    
    @classmethod
    def ok(cls, data: Dict) -> 'UpdateAssetResult':
        return cls(success=True, data=data)
    
    @classmethod
    def fail(cls, error: str) -> 'UpdateAssetResult':
        return cls(success=False, error=error)


class UpdateAsset:
    """
    Use case for updating an existing asset.
    
    Business Rules:
    - Authorization check via domain service
    - Supports partial updates
    - Technician can only edit assets assigned to them
    
    Input (via execute):
        user: User - User performing the update
        asset_id: UUID - ID of asset to update
        asset_data: Dict - Fields to update
        idempotency_key: Optional[str] - Key to prevent duplicate updates
    
    Output:
        UpdateAssetResult with updated asset details or error
    
    Usage:
        result = UpdateAsset().execute(
            user=request.user,
            asset_id=asset_uuid,
            asset_data={'status': 'IN_ACTIVE'},
            idempotency_key="update-asset-123"
        )
        
        if result.success:
            print(f"Updated asset {result.data['asset_id']}")
        else:
            print(f"Error: {result.error}")
    """
    
    @transaction.atomic
    def execute(
        self,
        user: Any,
        asset_id: str,
        asset_data: Dict,
        idempotency_key: Optional[str] = None,
    ) -> UpdateAssetResult:
        """
        Execute asset update use case.
        
        Args:
            user: User performing the update
            asset_id: UUID string of asset to update
            asset_data: Dictionary with fields to update
            idempotency_key: Optional key to prevent duplicate updates
            
        Returns:
            UpdateAssetResult with updated asset details or error
        """
        from apps.assets.models import Asset
        from django.utils import timezone
        
        # Get asset
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return UpdateAssetResult.fail("Asset not found")
        
        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_edit(user, asset)
        except AuthorizationError as e:
            return UpdateAssetResult.fail(str(e))
        
        # Track changes for event
        changes = {}
        allowed_fields = {
            'name', 'description', 'status', 'category_id',
            'location_id', 'serial_number', 'asset_tag',
            'purchase_date', 'purchase_price', 'warranty_expiry',
            'notes',
        }
        
        for field, value in asset_data.items():
            if field in allowed_fields:
                old_value = getattr(asset, field, None)
                if field.endswith('_id'):
                    # Handle foreign key fields
                    setattr(asset, field, value)
                else:
                    setattr(asset, field, value)
                changes[field] = (old_value, value)
        
        asset.updated_by = user
        asset.save()
        
        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: self._log_asset_updated(asset, user))
        
        # Emit domain event
        from apps.assets.domain.events import emit_asset_updated
        emit_asset_updated(
            asset_id=asset.id,
            asset_name=asset.name,
            actor=user,
            changes=changes,
        )
        
        return UpdateAssetResult.ok(
            data={
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'status': asset.status,
                'updated_at': asset.updated_at.isoformat() if asset.updated_at else None,
            }
        )
    
    def _log_asset_updated(self, asset, user):
        """Log asset update activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_asset_action(
                action='UPDATE',
                asset=asset,
                actor=user,
                request=None,
                description=f"Updated asset: {asset.name}"
            )
        except Exception:
            pass  # Logging must never break the command


class CanEditAsset:
    """
    Simple check if user can edit an asset.
    
    Returns:
        bool: True if user can edit the asset
    """
    
    def check(self, user: Any, asset_id: str) -> bool:
        """
        Check if user can edit the asset.
        
        Args:
            user: User attempting to edit
            asset_id: UUID of asset to edit
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.assets.models import Asset
        
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return False
        
        return can_edit(user, asset)

