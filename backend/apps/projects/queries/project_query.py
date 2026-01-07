# Project query class for read-only database operations.
# This class follows CQRS principles - only reads data, never mutates state.
# Returns immutable DTOs (View Models) instead of ORM instances.

from django.db.models import QuerySet
from typing import List, Dict, Any, Optional
from ..dtos.project_dto import (
    ProjectDTO, ProjectDetailDTO, ProjectListDTO,
    ProjectCategoryDTO, ProjectMemberDTO
)


class ProjectQuery:
    """
    Query class for Project model.
    All methods are read-only - they NEVER mutate state.
    Returns immutable DTOs, never ORM instances or HttpResponse.
    """
    
    @staticmethod
    def get_all() -> QuerySet:
        """
        Get all projects as ORM queryset (for internal use).
        Returns: QuerySet of Project ORM objects
        """
        from apps.projects.models import Project
        return Project.objects.select_related(
            'created_by', 'owner'
        ).prefetch_related('members').order_by('-created_at')[:50]
    
    @staticmethod
    def get_all_dto() -> List[ProjectDTO]:
        """
        Get all projects as DTOs.
        Returns: List of ProjectDTO objects
        """
        from apps.projects.models import Project
        projects = Project.objects.select_related(
            'created_by', 'owner'
        ).prefetch_related('members').order_by('-created_at')[:50]
        return [ProjectDTO.from_orm(p) for p in projects]
    
    @staticmethod
    def get_list_dto(page: int = 1, page_size: int = 50) -> ProjectListDTO:
        """
        Get paginated list of projects as DTO.
        Returns: ProjectListDTO with pagination info
        """
        from apps.projects.models import Project
        queryset = Project.objects.select_related(
            'created_by', 'owner'
        ).prefetch_related('members').order_by('-created_at')
        return ProjectListDTO.from_queryset(queryset, page, page_size)
    
    @staticmethod
    def get_by_id(project_id: int) -> Optional[ProjectDTO]:
        """
        Get a single project by ID as DTO.
        Args:
            project_id: The ID of the project to retrieve
        Returns: ProjectDTO object or None
        """
        from apps.projects.models import Project
        try:
            project = Project.objects.select_related(
                'created_by', 'owner'
            ).prefetch_related('members').get(id=project_id)
            return ProjectDTO.from_orm(project)
        except (Project.DoesNotExist, ValueError):
            return None
    
    @staticmethod
    def get_with_details(project_id: int) -> Optional[ProjectDetailDTO]:
        """
        Get a project with all details as DTO.
        Args:
            project_id: The ID of the project to retrieve
        Returns: ProjectDetailDTO object or None
        """
        from apps.projects.models import Project
        try:
            project = Project.objects.prefetch_related(
                'members__user', 'category', 'owner', 'created_by'
            ).get(id=project_id)
            return ProjectDetailDTO.from_orm(project)
        except (Project.DoesNotExist, ValueError):
            return None
    
    @staticmethod
    def get_categories() -> List[ProjectCategoryDTO]:
        """
        Get all active project categories as DTOs.
        Returns: List of ProjectCategoryDTO objects
        """
        from apps.projects.models import ProjectCategory
        categories = ProjectCategory.objects.filter(is_active=True)
        return [ProjectCategoryDTO.from_orm(c) for c in categories]
    
    @staticmethod
    def get_status_choices() -> List[tuple]:
        """
        Get project status choices.
        Returns: List of (value, display_name) tuples
        """
        from apps.projects.models import Project
        return Project.STATUS_CHOICES
    
    @staticmethod
    def get_priority_choices() -> List[tuple]:
        """
        Get project priority choices.
        Returns: List of (value, display_name) tuples
        """
        from apps.projects.models import Project
        return Project.PRIORITY_CHOICES
    
    @staticmethod
    def get_active_users() -> List[Dict[str, Any]]:
        """
        Get all active users (for team member selection).
        Returns: List of user dictionaries with id, username, full_name
        """
        from apps.users.models import User
        users = User.objects.filter(is_active=True)
        return [
            {
                'id': u.id,
                'username': u.username,
                'full_name': f"{u.first_name} {u.last_name}".strip() or u.username
            }
            for u in users
        ]
    
    @staticmethod
    def get_for_dashboard() -> Dict[str, Any]:
        """
        Get project statistics for dashboard.
        Returns: Dictionary with project counts by status
        """
        from apps.projects.models import Project
        return {
            'total': Project.objects.count(),
            'planning': Project.objects.filter(status='PLANNING').count(),
            'in_progress': Project.objects.filter(status='IN_PROGRESS').count(),
            'completed': Project.objects.filter(status='COMPLETED').count(),
        }

