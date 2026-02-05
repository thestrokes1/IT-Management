"""
Handlers/Resolvers for asset commands.

These handlers receive Command DTOs and delegate to the appropriate use case.
Views should import handlers, not use cases directly.
"""

from apps.assets.application.commands import AssetAssignmentCommand
from apps.assets.application.assign_asset import AssignAsset
from apps.assets.application.assign_asset_to_self import AssignAssetToSelf


class AssetAssignmentHandler:
    """
    Handler for asset assignment commands.
    
    This handler:
    1. Receives an AssetAssignmentCommand
    2. Routes to the appropriate use case based on assignee_id
    3. Executes the use case with the command as the single argument
    
    Usage:
        handler = AssetAssignmentHandler()
        command = AssetAssignmentCommand(
            actor=request.user,
            asset_id=asset_uuid,
            assignee_id=None  # None = self-assignment
        )
        result = handler.handle(command)
    """
    
    def __init__(self):
        self._assign_asset = AssignAsset()
        self._assign_to_self = AssignAssetToSelf()
    
    def handle(self, command: AssetAssignmentCommand):
        """
        Handle an asset assignment command.
        
        Args:
            command: AssetAssignmentCommand with actor, asset_id, and optional assignee_id
            
        Returns:
            Result from the appropriate use case
        """
        # Route based on whether this is self-assignment or assignment to another
        if command.assignee_id is None:
            # Self-assignment
            return self._assign_to_self.execute(command)
        else:
            # Assignment to another user
            return self._assign_asset.execute(command)


def assign_asset(command: AssetAssignmentCommand):
    """
    Convenience function for asset assignment.
    
    This is the preferred entry point for asset assignment.
    
    Args:
        command: AssetAssignmentCommand with actor, asset_id, and optional assignee_id
        
    Returns:
        Result from the appropriate use case
    """
    handler = AssetAssignmentHandler()
    return handler.handle(command)

