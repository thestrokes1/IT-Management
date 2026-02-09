"""
Use case for changing project status.

Authorization is enforced via domain service with strict RBAC.
Activity logging is handled via transaction.on_commit to ensure logging
never breaks the business operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from django.db import transaction

from apps.projects.domain.services.project_authority import (
    can_edit,
    assert_can_edit,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class ChangeProjectStatusResult:
    """Result of project status change use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'ChangeProjectStatusResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'ChangeProjectStatusResult':
        return cls(success=False, error=error)


class ChangeProjectStatus:
    """
    Use case for changing a project's status.
    
    Business Rules:
    - Only users with can_edit permission can change status
    - SUPERADMIN, MANAGER, IT_ADMIN can change status
    
    Input (via execute):
        user: User - User performing the action
        project_id: int - Project ID
        new_status: str - New status
        
    Output:
        ChangeProjectStatusResult with confirmation or error
    """

    def execute(
        self,
        user: Any,
        project_id: int,
        new_status: str,
    ) -> ChangeProjectStatusResult:
        """
        Execute project status change use case.

        Args:
            user: User performing the action
            project_id: Project ID
            new_status: New status value

        Returns:
            ChangeProjectStatusResult with confirmation or error
        """
        from apps.projects.models import Project
        
        # Valid statuses
        valid_statuses = ['PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED']
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return ChangeProjectStatusResult.fail(f"Project with ID {project_id} not found")

        # Validate status
        if new_status not in valid_statuses:
            return ChangeProjectStatusResult.fail(
                f"Invalid status '{new_status}'. Valid statuses: {', '.join(valid_statuses)}"
            )

        # Store old status
        old_status = project.status

        # Authorization check
        try:
            assert_can_edit(user, project)
        except AuthorizationError as e:
            return ChangeProjectStatusResult.fail(str(e))

        # Change status
        project.status = new_status
        project.updated_by = user
        project.save()

        # Activity logging
        transaction.on_commit(
            lambda: self._log_status_changed(project, user, old_status, new_status)
        )

        return ChangeProjectStatusResult.ok(
            data={
                'project_id': project.id,
                'name': project.name,
                'old_status': old_status,
                'new_status': new_status,
                'message': f"Project '{project.name}' status changed from '{old_status}' to '{new_status}'",
            }
        )

    def _log_status_changed(self, project, user, old_status, new_status):
        """Log status change activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_project_action(
                action='PROJECT_STATUS_CHANGED',
                project=project,
                actor=user,
                metadata={
                    'old_status': old_status,
                    'new_status': new_status,
                },
                request=None,
            )
        except Exception:
            pass
