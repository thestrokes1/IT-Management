"""
Use case for updating a project.

Authorization is enforced via domain service with strict RBAC.
Activity logging is handled via transaction.on_commit to ensure logging
never breaks the business operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from django.db import transaction

from apps.projects.domain.services.project_authority import (
    can_edit,
    assert_can_edit,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class UpdateProjectResult:
    """Result of project update use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'UpdateProjectResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'UpdateProjectResult':
        return cls(success=False, error=error)


class UpdateProject:
    """
    Use case for updating a project.
    
    Business Rules:
    - Only users with can_edit permission can update projects
    - SUPERADMIN, MANAGER, IT_ADMIN can edit projects
    
    Input (via execute):
        user: User - User performing the update
        project_id: int - Project ID
        name: str - Project name
        description: str - Project description
        category_id: int - Category ID
        status: str - Project status
        priority: str - Project priority
        start_date: str - Start date
        end_date: str - End date
        budget: float - Budget
        owner_id: int - Owner user ID
        team_members: List[int] - Team member IDs
        
    Output:
        UpdateProjectResult with update confirmation or error
    """

    @transaction.atomic
    def execute(
        self,
        user: Any,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: Optional[float] = None,
        owner_id: Optional[int] = None,
        team_members: Optional[List[int]] = None,
    ) -> UpdateProjectResult:
        """
        Execute project update use case.

        Args:
            user: User performing the update
            project_id: Project ID
            name: Project name
            description: Project description
            category_id: Category ID
            status: Project status
            priority: Project priority
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            budget: Budget amount
            owner_id: Owner user ID
            team_members: List of team member IDs

        Returns:
            UpdateProjectResult with update confirmation or error
        """
        from apps.projects.models import Project, ProjectCategory, ProjectMember
        from apps.users.models import User
        from datetime import datetime
        
        # Get project
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return UpdateProjectResult.fail(f"Project with ID {project_id} not found")

        # Authorization check
        try:
            assert_can_edit(user, project)
        except AuthorizationError as e:
            return UpdateProjectResult.fail(str(e))

        # Store old values for change tracking
        old_data = {
            'name': project.name,
            'description': project.description,
            'status': project.status,
            'priority': project.priority,
            'budget': project.budget,
        }

        # Update fields if provided
        if name is not None:
            if not name.strip():
                return UpdateProjectResult.fail("Project name cannot be empty")
            project.name = name.strip()

        if description is not None:
            project.description = description.strip()

        if category_id is not None:
            try:
                category = ProjectCategory.objects.get(id=category_id)
                project.category = category
            except ProjectCategory.DoesNotExist:
                return UpdateProjectResult.fail(f"Category with ID {category_id} not found")

        if status is not None:
            project.status = status

        if priority is not None:
            project.priority = priority

        if budget is not None:
            project.budget = budget

        if start_date is not None:
            try:
                project.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        if end_date is not None:
            try:
                project.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        if owner_id is not None:
            try:
                owner = User.objects.get(id=owner_id)
                project.project_manager = owner
            except User.DoesNotExist:
                return UpdateProjectResult.fail(f"Owner with ID {owner_id} not found")

        project.updated_by = user
        project.save()

        # Update team members if provided
        if team_members is not None:
            ProjectMember.objects.filter(project=project).delete()
            for member_id in team_members:
                try:
                    member = User.objects.get(id=member_id)
                    ProjectMember.objects.get_or_create(
                        project=project,
                        user=member,
                        defaults={'role': 'MEMBER', 'joined_date': datetime.now().date()}
                    )
                except (User.DoesNotExist, ValueError):
                    pass

        # Track changes
        changes = {}
        for field in ['name', 'description', 'status', 'priority', 'budget']:
            old_value = old_data.get(field)
            new_value = getattr(project, field, None)
            if str(old_value) != str(new_value):
                changes[field] = {'old': str(old_value), 'new': str(new_value)}

        # Activity logging
        transaction.on_commit(lambda: self._log_project_updated(project, user, changes))

        return UpdateProjectResult.ok(
            data={
                'project_id': project.id,
                'name': project.name,
                'status': project.status,
                'priority': project.priority,
                'changes': changes,
                'message': f"Project '{project.name}' updated successfully",
            }
        )

    def _log_project_updated(self, project, user, changes):
        """Log project update activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_project_action(
                action='PROJECT_UPDATED',
                project=project,
                actor=user,
                metadata={'changes': changes},
                request=None,
            )
        except Exception:
            pass
