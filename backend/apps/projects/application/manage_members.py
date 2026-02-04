"""
Use case for managing project members.

Authorization is enforced via domain service with strict RBAC.
Activity logging is handled via transaction.on_commit to ensure logging
never breaks the business operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from django.db import transaction

from apps.projects.domain.services.project_authority import (
    can_assign,
    assert_can_assign,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class AddProjectMemberResult:
    """Result of adding project member use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'AddProjectMemberResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'AddProjectMemberResult':
        return cls(success=False, error=error)


class AddProjectMember:
    """
    Use case for adding a member to a project.
    
    Business Rules:
    - Only users with can_assign permission can add members
    - SUPERADMIN, MANAGER, IT_ADMIN can add members
    
    Input (via execute):
        user: User - User performing the action
        project_id: int - Project ID
        member_id: int - User ID to add
        role: str - Member role (default: MEMBER)
        
    Output:
        AddProjectMemberResult with confirmation or error
    """

    def execute(
        self,
        user: Any,
        project_id: int,
        member_id: int,
        role: str = 'MEMBER',
    ) -> AddProjectMemberResult:
        """
        Execute add project member use case.

        Args:
            user: User performing the action
            project_id: Project ID
            member_id: User ID to add
            role: Member role

        Returns:
            AddProjectMemberResult with confirmation or error
        """
        from apps.projects.models import Project, ProjectMember
        from apps.users.models import User
        from datetime import datetime
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return AddProjectMemberResult.fail(f"Project with ID {project_id} not found")

        # Get member
        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return AddProjectMemberResult.fail(f"User with ID {member_id} not found")

        # Authorization check
        try:
            assert_can_assign(user, project, member)
        except AuthorizationError as e:
            return AddProjectMemberResult.fail(str(e))

        # Check if already a member
        existing = ProjectMember.objects.filter(project=project, user=member).first()
        if existing:
            return AddProjectMemberResult.fail(
                f"User '{member.username}' is already a member of this project"
            )

        # Add member
        project_member = ProjectMember.objects.create(
            project=project,
            user=member,
            role=role,
            joined_date=datetime.now().date()
        )

        # Activity logging
        transaction.on_commit(lambda: self._log_member_added(project, member, user))

        return AddProjectMemberResult.ok(
            data={
                'project_id': project.id,
                'member_id': member.id,
                'member_username': member.username,
                'role': role,
                'message': f"Added '{member.username}' to project '{project.name}'",
            }
        )

    def _log_member_added(self, project, member, user):
        """Log member addition activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_project_action(
                action='PROJECT_MEMBER_ADDED',
                project=project,
                actor=user,
                metadata={
                    'member_id': member.id,
                    'member_username': member.username,
                },
                request=None,
            )
        except Exception:
            pass


@dataclass
class RemoveProjectMemberResult:
    """Result of removing project member use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'RemoveProjectMemberResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'RemoveProjectMemberResult':
        return cls(success=False, error=error)


class RemoveProjectMember:
    """
    Use case for removing a member from a project.
    
    Business Rules:
    - Only users with can_unassign permission can remove members
    - SUPERADMIN, MANAGER, IT_ADMIN can remove members
    
    Input (via execute):
        user: User - User performing the action
        project_id: int - Project ID
        member_id: int - User ID to remove
        
    Output:
        RemoveProjectMemberResult with confirmation or error
    """

    def execute(
        self,
        user: Any,
        project_id: int,
        member_id: int,
    ) -> RemoveProjectMemberResult:
        """
        Execute remove project member use case.

        Args:
            user: User performing the action
            project_id: Project ID
            member_id: User ID to remove

        Returns:
            RemoveProjectMemberResult with confirmation or error
        """
        from apps.projects.models import Project, ProjectMember
        from apps.users.models import User
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return RemoveProjectMemberResult.fail(f"Project with ID {project_id} not found")

        # Get member
        try:
            member = User.objects.get(id=member_id)
        except User.DoesNotExist:
            return RemoveProjectMemberResult.fail(f"User with ID {member_id} not found")

        # Authorization check
        from apps.projects.domain.services.project_authority import (
            assert_can_unassign,
        )
        try:
            assert_can_unassign(user, project)
        except AuthorizationError as e:
            return RemoveProjectMemberResult.fail(str(e))

        # Get membership
        try:
            project_member = ProjectMember.objects.get(project=project, user=member)
        except ProjectMember.DoesNotExist:
            return RemoveProjectMemberResult.fail(
                f"User '{member.username}' is not a member of this project"
            )

        # Store for logging
        member_username = member.username
        project_name = project.name

        # Remove member
        project_member.delete()

        # Activity logging
        transaction.on_commit(
            lambda: self._log_member_removed(project_id, project_name, member_username, user)
        )

        return RemoveProjectMemberResult.ok(
            data={
                'project_id': project.id,
                'member_id': member.id,
                'member_username': member_username,
                'message': f"Removed '{member_username}' from project '{project_name}'",
            }
        )

    def _log_member_removed(self, project_id, project_name, member_username, user):
        """Log member removal activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            # Create a minimal object for logging since project may be deleted
            class TempProject:
                def __init__(self, pid, pname):
                    self.id = pid
                    self.name = pname
                def __str__(self):
                    return self.name
            temp_project = TempProject(project_id, project_name)
            ActivityService().log_project_action(
                action='PROJECT_MEMBER_REMOVED',
                project=temp_project,
                actor=user,
                metadata={
                    'member_username': member_username,
                },
                request=None,
            )
        except Exception:
            pass
