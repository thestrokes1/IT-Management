"""
Use case for creating a project.

Authorization is enforced via domain service with strict RBAC.
Activity logging is handled via transaction.on_commit to ensure logging
never breaks the business operation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List
from django.db import transaction

from apps.projects.domain.services.project_authority import (
    can_create,
    assert_can_create,
)
from apps.core.domain.authorization import AuthorizationError


@dataclass
class CreateProjectResult:
    """Result of project creation use case."""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None

    @classmethod
    def ok(cls, data: Dict) -> 'CreateProjectResult':
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, error: str) -> 'CreateProjectResult':
        return cls(success=False, error=error)


class CreateProject:
    """
    Use case for creating a project.
    
    Business Rules:
    - Only users with can_create permission can create projects
    - MANAGER and above can create projects
    
    Input (via execute):
        user: User - User performing the creation
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
        CreateProjectResult with creation confirmation or error
    """

    @transaction.atomic
    def execute(
        self,
        user: Any,
        name: str,
        description: str = '',
        category_id: Optional[int] = None,
        status: str = 'PLANNING',
        priority: str = 'MEDIUM',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        budget: float = 0.0,
        owner_id: Optional[int] = None,
        team_members: Optional[List[int]] = None,
    ) -> CreateProjectResult:
        """
        Execute project creation use case.

        Args:
            user: User performing the creation
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
            CreateProjectResult with creation confirmation or error
        """
        from apps.projects.models import Project, ProjectCategory, ProjectMember
        from apps.users.models import User
        from datetime import datetime
        
        # Authorization check
        try:
            assert_can_create(user)
        except AuthorizationError as e:
            return CreateProjectResult.fail(str(e))

        # Validate required fields
        if not name or not name.strip():
            return CreateProjectResult.fail("Project name is required")

        # Get category
        category = None
        if category_id:
            try:
                category = ProjectCategory.objects.get(id=category_id)
            except ProjectCategory.DoesNotExist:
                return CreateProjectResult.fail(f"Category with ID {category_id} not found")

        # Get owner
        owner = None
        if owner_id:
            try:
                owner = User.objects.get(id=owner_id)
            except User.DoesNotExist:
                return CreateProjectResult.fail(f"Owner with ID {owner_id} not found")
        else:
            # Auto-assign current user if they are MANAGER or SUPERADMIN
            if user.role in ['MANAGER', 'SUPERADMIN']:
                owner = user
            else:
                return CreateProjectResult.fail("A project manager must be selected")

        # Parse dates
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        end_date_obj = None
        if end_date:
            try:
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                pass

        # Create project
        project = Project.objects.create(
            name=name.strip(),
            description=description.strip(),
            category=category,
            status=status,
            priority=priority,
            start_date=start_date_obj,
            end_date=end_date_obj,
            budget=budget,
            project_manager=owner,
            created_by=user
        )

        # Add team members
        if team_members:
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

        # Activity logging - runs after transaction commits, never breaks command
        transaction.on_commit(lambda: self._log_project_created(project, user))

        return CreateProjectResult.ok(
            data={
                'project_id': project.id,
                'name': project.name,
                'status': project.status,
                'priority': project.priority,
                'budget': project.budget,
                'message': f"Project '{project.name}' created successfully",
            }
        )

    def _log_project_created(self, project, user):
        """Log project creation activity."""
        try:
            from apps.logs.services.activity_service import ActivityService
            ActivityService().log_project_created(project, user, None)
        except Exception:
            pass  # Logging must never break the command
