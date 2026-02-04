"""
Use case for deleting a project.

Authorization is enforced via domain service with strict RBAC.
Activity logging is handled via transaction.on_commit to ensure logging
never breaks the business operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from django.db import transaction

from apps.projects.domain.services.project_authority import (
    can_delete,
    assert_can_delete,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class DeleteProjectResult:
    """Result of project deletion use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'DeleteProjectResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'DeleteProjectResult':
        return cls(success=False, error=error)


class DeleteProject:
    """
    Use case for deleting a project.
    
    Business Rules:
    - Only SUPERADMIN can delete projects
    
    Input (via execute):
        user: User - User performing the deletion
        project_id: int - Project ID to delete
        
    Output:
        DeleteProjectResult with deletion confirmation or error
    """

    @transaction.atomic
    def execute(
        self,
        user: Any,
        project_id: int,
    ) -> DeleteProjectResult:
        """
        Execute project deletion use case.

        Args:
            user: User performing the deletion
            project_id: Project ID to delete

        Returns:
            DeleteProjectResult with deletion confirmation or error
        """
        from apps.projects.models import Project, Task, ProjectMember
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return DeleteProjectResult.fail(f"Project with ID {project_id} not found")

        # Store project name for logging
        project_name = project.name

        # Authorization check
        try:
            assert_can_delete(user, project)
        except AuthorizationError as e:
            return DeleteProjectResult.fail(str(e))

        # Delete related records
        # Delete related records
        Task.objects.filter(project=project).delete()
        ProjectMember.objects.filter(project=project).delete()
        project.delete()

        # Activity logging
        transaction.on_commit(lambda: self._log_project_deleted(project_id, project_name, user))

        return DeleteProjectResult.ok(
            data={
                'project_id': project_id,
                'name': project_name,
                'message': f"Project '{project_name}' deleted successfully",
            }
        )

    def _log_project_deleted(self, project_id, project_name, user):
        """Log project deletion activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_project_action(
                action='PROJECT_DELETED',
                project=None,  # Project is already deleted
                actor=user,
                metadata={'project_id': project_id, 'project_name': project_name},
                request=None,
            )
        except Exception:
            pass
