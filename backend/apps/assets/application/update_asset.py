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
from apps.core.services.change_detection import get_changed_fields, format_field_value, get_display_field_name


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
        
        # Store original values for change detection BEFORE any modifications
        original_values = {}
        allowed_fields = {
            'name', 'description', 'status', 'category_id',
            'location', 'serial_number', 'model', 'manufacturer',
            'purchase_date', 'purchase_cost', 'warranty_expiry',
            'end_of_life', 'contact_type', 'contact_email', 
            'contact_phone', 'assigned_to_id', 'assigned_to',
        }
        
        for field in allowed_fields:
            if hasattr(asset, field):
                original_values[field] = getattr(asset, field)
        
        # Detect changes before applying updates
        changes = get_changed_fields(asset, asset_data)
        
        # Apply updates to asset
        for field, value in asset_data.items():
            if field in allowed_fields:
                if field == 'assigned_to_id' and value:
                    # Handle assigned_to foreign key
                    from apps.users.models import User
                    try:
                        assigned_user = User.objects.get(id=value)
                        asset.assigned_to = assigned_user
                    except User.DoesNotExist:
                        pass
                elif field.endswith('_id') and field != 'assigned_to_id':
                    # Handle other foreign key fields
                    setattr(asset, field, value)
                else:
                    setattr(asset, field, value)
        
        asset.updated_by = user
        asset.save()
        
        # Activity logging - runs after transaction commits, never breaks command
        # Log each changed field individually
        transaction.on_commit(lambda: self._log_asset_changes(asset, user, changes))
        
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
    
    def _log_asset_changes(self, asset, user, changes):
        """
        Log asset update activity with field-level changes.
        
        Creates one ActivityLog entry per changed field to show
        exactly what was changed (old value → new value).
        """
        try:
            from apps.logs.services.activity_service import ActivityService
            from django.utils import timezone
            
            service = ActivityService()
            
            if not changes:
                # No actual changes, log a generic update
                service.log_asset_action(
                    action='UPDATE',
                    asset=asset,
                    actor=user,
                    request=None,
                    description=f"Updated asset: {asset.name}"
                )
                return
            
            # Log each changed field individually
            for change in changes:
                field_name = change['field']
                old_value = change['old']
                new_value = change['new']
                
                # Format values for display
                old_display = format_field_value(old_value)
                new_display = format_field_value(new_value)
                
                # Get human-readable field name
                display_name = get_display_field_name(field_name)
                
                # Build description showing the change
                description = f"Changed {display_name}: {old_display} → {new_display}"
                
                # Create activity log with change details in extra_data
                service.log_asset_action(
                    action='UPDATED',
                    asset=asset,
                    actor=user,
                    metadata={
                        'field_name': field_name,
                        'field_display': display_name,
                        'old_value': old_value,
                        'new_value': new_value,
                        'old_display': old_display,
                        'new_display': new_display,
                    },
                    request=None,
                    description=description
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

