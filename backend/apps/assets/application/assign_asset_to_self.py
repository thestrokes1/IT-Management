"""
Use case for self-assigning an asset.

Technician can self-assign to an ACTIVE, unassigned asset.
Authorization is enforced via domain service with strict RBAC.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from apps.assets.domain.services.asset_authority import (
    can_self_assign,
    can_reassign,
    assert_can_self_assign,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class AssignAssetToSelfResult:
    """Result of asset self-assignment use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'AssignAssetToSelfResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'AssignAssetToSelfResult':
        return cls(success=False, error=error)


class AssignAssetToSelf:
    """
    Use case for a technician to self-assign to an asset.
    
    Business Rules:
    - Asset must be ACTIVE
    - Asset must not be already assigned
    - Technician can only self-assign to assets they created
    - Admin roles can always self-assign
    
    Input (via execute):
        command: AssetAssignmentCommand with actor, asset_id, assignee_id=None
        
    Output:
        AssignAssetToSelfResult with assignment confirmation or error
        
    Usage:
        from apps.assets.application.commands import AssetAssignmentCommand
        
        command = AssetAssignmentCommand(
            actor=request.user,
            asset_id=asset_uuid,
            assignee_id=None  # None indicates self-assignment
        )
        result = AssignAssetToSelf().execute(command)
        
        if result.success:
            print(f"Self-assigned to asset: {result.data['name']}")
        else:
            print(f"Error: {result.error}")
    """

    def execute(
        self,
        command,
    ) -> AssignAssetToSelfResult:
        """
        Execute asset self-assignment use case.

        Args:
            command: AssetAssignmentCommand containing actor, asset_id, and assignee_id=None

        Returns:
            AssignAssetToSelfResult with assignment confirmation or error
        """
        from apps.assets.models import Asset
        from django.utils import timezone
        
        user = command.actor
        asset_id = str(command.asset_id)
        
        # Get asset
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return AssignAssetToSelfResult.fail("Asset not found")

        # Authorization check
        try:
            assert_can_self_assign(user, asset)
        except AuthorizationError as e:
            return AssignAssetToSelfResult.fail(str(e))

        # Perform assignment
        old_assignment_status = asset.assignment_status
        
        asset.assigned_to = user
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
            assignee_id=user.id,
            assignee_username=user.username,
            assigner_id=user.id,
            assigner_username=user.username,
        )

        return AssignAssetToSelfResult.ok(
            data={
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'assigned_to': user.username,
                'assigned_to_id': user.id,
                'previous_assignment_status': old_assignment_status,
                'new_assignment_status': asset.assignment_status,
                'message': f"Asset self-assigned to {user.username}",
            }
        )


class ReassignAsset:
    """
    Use case for reassigning an asset to a different user.
    
    Business Rules:
    - Only MANAGER, IT_ADMIN, SUPERADMIN can reassign
    - TECHNICIAN cannot reassign assets
    
    Input (via execute):
        user: User - User performing the reassignment
        asset_id: UUID - ID of asset to reassign
        new_assignee_id: int - User ID to assign the asset to
        
    Output:
        AssignAssetToSelfResult with reassignment confirmation or error
    """

    def execute(
        self,
        user: Any,
        asset_id: str,
        new_assignee_id: int,
    ) -> AssignAssetToSelfResult:
        """
        Execute asset reassignment use case.

        Args:
            user: User performing the reassignment
            asset_id: UUID string of asset to reassign
            new_assignee_id: User ID of new assignee

        Returns:
            AssignAssetToSelfResult with reassignment confirmation or error
        """
        from apps.assets.models import Asset
        from apps.users.models import User
        
        # Get asset
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return AssignAssetToSelfResult.fail("Asset not found")

        # Get new assignee
        try:
            new_assignee = User.objects.get(id=new_assignee_id)
        except User.DoesNotExist:
            return AssignAssetToSelfResult.fail("New assignee not found")

        # Authorization check - TECHNICIAN cannot reassign
        if not can_reassign(user, asset):
            return AssignAssetToSelfResult.fail(
                "You are not authorized to reassign assets. "
                "Only MANAGER, IT_ADMIN, or SUPERADMIN can reassign assets."
            )

        old_assignee = asset.assigned_to
        
        # Perform reassignment
        asset.assigned_to = new_assignee
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
            assignee_id=new_assignee.id,
            assignee_username=new_assignee.username,
            assigner_id=user.id,
            assigner_username=user.username,
        )

        old_assignee_name = old_assignee.username if old_assignee else "Unassigned"

        return AssignAssetToSelfResult.ok(
            data={
                'asset_id': str(asset.asset_id),
                'name': asset.name,
                'previous_assignee': old_assignee_name,
                'new_assignee': new_assignee.username,
                'new_assignee_id': new_assignee.id,
                'assignment_status': asset.assignment_status,
                'message': f"Asset reassigned from {old_assignee_name} to {new_assignee.username}",
            }
        )


class CanSelfAssignAsset:
    """
    Simple check if user can self-assign an asset.
    
    Returns:
        bool: True if user can self-assign the asset
    """
    
    def check(self, user: Any, asset_id: str) -> bool:
        """
        Check if user can self-assign the asset.
        
        Args:
            user: User attempting to self-assign
            asset_id: UUID of asset to self-assign
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.assets.models import Asset
        
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return False
        
        return can_self_assign(user, asset)


class CanReassignAsset:
    """
    Simple check if user can reassign an asset.
    
    Returns:
        bool: True if user can reassign the asset
    """
    
    def check(self, user: Any, asset_id: str) -> bool:
        """
        Check if user can reassign the asset.
        
        Args:
            user: User attempting to reassign
            asset_id: UUID of asset to reassign
            
        Returns:
            bool: True if authorized, False otherwise
        """
        from apps.assets.models import Asset
        
        try:
            asset = Asset.objects.get(asset_id=asset_id)
        except Asset.DoesNotExist:
            return False
        
        return can_reassign(user, asset)

