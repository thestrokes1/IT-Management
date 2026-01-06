# Project DTOs - Immutable Read DTOs (View Models) for Project data.
# These DTOs contain no business logic - they are pure data containers.
# Used by queries to return structured read-only data to views.

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, date


@dataclass(frozen=True)
class ProjectDTO:
    """
    Immutable DTO for basic project information.
    Used for list views where full details are not needed.
    """
    id: int
    name: str
    description: str
    status: str
    priority: str
    created_at: Optional[datetime]
    owner_name: Optional[str]
    
    @classmethod
    def from_orm(cls, obj) -> 'ProjectDTO':
        """Create DTO from ORM model instance."""
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            status=obj.status,
            priority=obj.priority,
            created_at=obj.created_at,
            owner_name=obj.owner.username if obj.owner else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary for template rendering."""
        return asdict(self)


@dataclass(frozen=True)
class ProjectMemberDTO:
    """
    Immutable DTO for project member information.
    """
    user_id: int
    username: str
    full_name: str
    role: str
    joined_at: Optional[datetime]
    
    @classmethod
    def from_orm(cls, obj) -> 'ProjectMemberDTO':
        """Create DTO from ORM model instance."""
        return cls(
            user_id=obj.user.id,
            username=obj.user.username,
            full_name=f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username,
            role=obj.role,
            joined_at=obj.joined_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class ProjectCategoryDTO:
    """
    Immutable DTO for project category information.
    """
    id: int
    name: str
    description: Optional[str]
    
    @classmethod
    def from_orm(cls, obj) -> 'ProjectCategoryDTO':
        """Create DTO from ORM model instance."""
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class ProjectDetailDTO:
    """
    Immutable DTO for detailed project information.
    Used for detail/edit views where full project data is needed.
    """
    id: int
    name: str
    description: str
    status: str
    priority: str
    start_date: Optional[date]
    end_date: Optional[date]
    budget: float
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Related data
    category: Optional[ProjectCategoryDTO]
    owner_id: Optional[int]
    owner_name: Optional[str]
    created_by_id: Optional[int]
    created_by_name: Optional[str]
    members: List[ProjectMemberDTO]
    
    @classmethod
    def from_orm(cls, obj) -> 'ProjectDetailDTO':
        """Create DTO from ORM model instance."""
        # Build category DTO
        category_dto = None
        if obj.category:
            category_dto = ProjectCategoryDTO(
                id=obj.category.id,
                name=obj.category.name,
                description=obj.category.description
            )
        
        # Build member DTOs
        members_dto = []
        if hasattr(obj, 'members'):
            for member in obj.members.all():
                members_dto.append(ProjectMemberDTO.from_orm(member))
        
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            status=obj.status,
            priority=obj.priority,
            start_date=obj.start_date,
            end_date=obj.end_date,
            budget=obj.budget,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            category=category_dto,
            owner_id=obj.owner.id if obj.owner else None,
            owner_name=obj.owner.username if obj.owner else None,
            created_by_id=obj.created_by.id if obj.created_by else None,
            created_by_name=obj.created_by.username if obj.created_by else None,
            members=members_dto
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary for template rendering."""
        result = asdict(self)
        # Convert category to dict if present
        if self.category:
            result['category'] = self.category.to_dict()
        # Convert members to dicts
        result['members'] = [m.to_dict() for m in self.members]
        return result


@dataclass(frozen=True)
class ProjectListDTO:
    """
    Immutable DTO for project list with pagination info.
    """
    projects: List[ProjectDTO]
    total_count: int
    page: int
    page_size: int
    
    @classmethod
    def from_queryset(cls, queryset, page: int = 1, page_size: int = 50) -> 'ProjectListDTO':
        """
        Create DTO list from queryset.
        Args:
            queryset: Django ORM queryset
            page: Page number (1-indexed)
            page_size: Number of items per page
        """
        total_count = queryset.count()
        offset = (page - 1) * page_size
        items = queryset[offset:offset + page_size]
        
        projects = [ProjectDTO.from_orm(obj) for obj in items]
        
        return cls(
            projects=projects,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert to list of dictionaries for template rendering."""
        return [p.to_dict() for p in self.projects]

