"""
Command DTOs for asset operations.

These are immutable data containers with no business logic.
They are passed to handlers/resolvers which route to the appropriate use case.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class AssetAssignmentCommand:
    """
    Command for assigning an asset to a user.
    
    This is an immutable DTO with no business logic.
    
    Fields:
        actor: The user performing the assignment
        asset_id: UUID of the asset to assign
        assignee_id: Optional user ID to assign to (None for self-assignment)
    """
    actor: any
    asset_id: UUID
    assignee_id: Optional[int] = None

