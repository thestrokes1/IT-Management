"""
Use case for assigning an asset to another user.

Authorization is enforced via domain service with strict RBAC.
Only users with can_assign permission can assign assets to others.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.assets.domain.services.asset_authority import (
    can_assign,
    assert_can_assign,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class AssignAssetResult:
    """Result of asset assignment use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'AssignAssetResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'AssignAssetResult':
        return cls(success=False, error=error)


class AssignAsset:
    """
    Use case for assigning an asset to another user.
    
    Business Rules:
    - Only users with can_assign permission can assign assets
    - SUPERADMIN, MANAGER, IT_ADMIN can assign any asset
    - TECHNICIAN cannot assign assets to others
    - Assignee can be any active user
    
    Input (via execute):
        command: AssetAssignmentCommand with actor, asset_id, assignee_id
        
    Output:
        AssignAssetResult with assignment confirmation or error
        
    Usage:
        from apps.assets.application.commands import AssetAssignmentCommand
        
        command = AssetAssignmentCommand(
            actor=request.user,
            asset_id=asset_uuid,
            assignee_id=target_user.id
        )
        result = AssignAsset().execute(command)
        
        if result.success:
            print(f"Assigned asset: {result.data['name']}")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        command,
    ) -> AssignAssetResult:
        """
        Execute asset assignment use case.

        Args:
            command: AssetAssignmentCommand containing actor, asset_id, and assignee_id

        Returns:
            AssignAssetResult with assignment confirmation or error
        """
        from apps.assets.models import Asset
        from apps.users.models import User
        from django.utils import timezone
        
        user = command.actor
        asset_id = str(command.asset_id)
        assignee_id = command.assignee_id
        
        # Get asset
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return AssignAssetResult.fail("Asset not found")

        # Get assignee
        try:
            assignee = User.objects.get(id=assignee_id)
        except User.DoesNotExist:
            return AssignAssetResult.fail("Assignee not found")

        # Authorization check - raises AuthorizationError if not authorized
        try:
            assert_can_assign(user, asset, assignee)
        except AuthorizationError as e:
            return AssignAssetResult.fail(str(e))

        # Store old assignee for event
        old_assignee = asset.assigned_to
        old_assignment_status = asset.assignment_status
        
        # Perform assignment
        asset.assigned_to = assignee
        asset.assigned_date = timezone.now()
        asset.assignment_status = 'ASSIGNED'
        asset.updated_by = user
        asset.save()

        # Emit domain event
        from apps.assets.domain.events import emit_asset_assigned
        emit_asset_assigned(
            asset_id=asset.id,
            asset_name=asset.name,
            actor=user,
            assignee_id=assignee.id,
            assignee_username=assignee.username,
            assigner_id=user.id,
            assigner_username=user.username,
        )

        old_assignee_name = old_assignee.username if old_assignee else "Unassigned"

        return AssignAssetResult.ok(
            data={
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'previous_assignee': old_assignee_name,
                'new_assignee': assignee.username,
                'new_assignee_id': assignee.id,
                'previous_assignment_status': old_assignment_status,
                'new_assignment_status': asset.assignment_status,
                'message': f"Asset assigned from {old_assignee_name} to {assignee.username}",
            }
        )


class UnassignAsset:
    """
    Use case for unassigning an asset.
    
    Business Rules:
    - Only users with can_unassign permission can unassign assets
    - SUPERADMIN, MANAGER, IT_ADMIN can unassign any asset
    - TECHNICIAN cannot unassign assets
    
    Input (via execute):
        user: User - User performing the unassignment
        asset_id: UUID - ID of asset to unassign
        
    Output:
        AssignAssetResult with unassignment confirmation or error
    """

    def execute(
        self,
        user: Any,
        asset_id: str,
    ) -> AssignAssetResult:
        """
        Execute asset unassignment use case.

        Args:
            user: User performing the unassignment
            asset_id: UUID string of asset to unassign

        Returns:
            AssignAssetResult with unassignment confirmation or error
        """
        from apps.assets.models import Asset
        from django.utils import timezone
        
        # Get asset
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return AssignAssetResult.fail("Asset not found")

        # Check if asset is already unassigned
        if asset.assigned_to is None:
            return AssignAssetResult.fail("Asset is already unassigned")

        # Authorization check
        from apps.assets.domain.services.asset_authority import (
            assert_can_unassign,
        )
        try:
            assert_can_unassign(user, asset)
        except AuthorizationError as e:
            return AssignAssetResult.fail(str(e))

        # Store old assignee for event
        old_assignee = asset.assigned_to
        old_assignee_name = old_assignee.username if old_assignee else "Unassigned"
        
        # Perform unassignment
        asset.assigned_to = None
        asset.assigned_date = None
        asset.assignment_status = 'UNASSIGNED'
        asset.updated_by = user
        asset.save()

        # Emit domain event
        from apps.assets.domain.events import emit_asset_unassigned
        emit_asset_unassigned(
            asset_id=asset.id,
            asset_name=asset.name,
            actor=user,
            previous_assignee_id=old_assignee.id if old_assignee else None,
            previous_assignee_username=old_assignee_name,
            unassigner_id=user.id,
            unassigner_username=user.username,
        )

        return AssignAssetResult.ok(
            data={
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'unassigned_from': old_assignee_name,
                'new_assignment_status': asset.assignment_status,
                'message': f"Asset unassigned from {old_assignee_name}",
            }
        )


class CanAssignAsset:
    """
    Simple check if user can assign an asset.
    
    Returns:
        bool: True if user can assign the asset
    """
    
    def check(self, user: Any, asset_id: str, assignee_id: int = None) -> bool:
        """
        Check if user can assign the asset.
        
        Args:
            user: User attempting to assign
            asset_id: UUID of asset to assign
            assignee_id: Optional assignee user ID
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.assets.models import Asset
        from apps.users.models import User
        
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return False
        
        assignee = None
        if assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                return False
        
        return can_assign(user, asset, assignee)


class CanUnassignAsset:
    """
    Simple check if user can unassign an asset.
    
    Returns:
        bool: True if user can unassign the asset
    """
    
    def check(self, user: Any, asset_id: str) -> bool:
        """
        Check if user can unassign the asset.
        
        Args:
            user: User attempting to unassign
            asset_id: UUID of asset to unassign
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.assets.models import Asset
        
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return False
        
        from apps.assets.domain.services.asset_authority import can_unassign
        return can_unassign(user, asset)

