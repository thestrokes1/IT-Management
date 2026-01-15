"""
Project authorization domain service.

Pure domain layer authorization for project management.
No Django dependencies.
"""

from apps.core.domain.roles import has_higher_role, has_strictly_higher_role
from apps.core.domain.authorization import AuthorizationError


# Role constants
_ROLE_MANAGER = 'MANAGER'
_ROLE_SUPERADMIN = 'SUPERADMIN'


def can_create_project(user) -> bool:
    """
    Check if user can create projects.

    Rules:
    - MANAGER and above can create projects

    Args:
        user: User instance

    Returns:
        bool: True if user can create projects
    """
    return has_higher_role(user.role, _ROLE_MANAGER)


def can_read_project(user, project) -> bool:
    """
    Check if user can read/view a project.

    Rules:
    - All roles can read projects

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user can view the project
    """
    return True


def can_update_project(user, project) -> bool:
    """
    Check if user can update a project.

    Rules:
    - MANAGER and above can update projects
    - Ownership does NOT affect permissions

    Args:
        user: User instance attempting the action
        project: Project instance

    Returns:
        bool: True if user can update the project
    """
    return has_higher_role(user.role, _ROLE_MANAGER)


def can_delete_project(user, project) -> bool:
    """
    Check if user can delete a project.

    Rules:
    - SUPERADMIN only can delete projects
    - Ownership does NOT affect permissions

    Args:
        user: User instance attempting the action
        project: Project instance

    Returns:
        bool: True if user can delete the project
    """
    # Only SUPERADMIN can delete projects
    return user.role == _ROLE_SUPERADMIN


def can_assign_project_members(user, project) -> bool:
    """
    Check if user can assign project members.

    Rules:
    - MANAGER and above can assign project members
    - Ownership does NOT affect permissions

    Args:
        user: User instance attempting the action
        project: Project instance

    Returns:
        bool: True if user can assign project members
    """
    return has_higher_role(user.role, _ROLE_MANAGER)


def can_view_project_logs(user, project) -> bool:
    """
    Check if user can view project logs/history.

    Rules:
    - MANAGER and above can view project logs
    - Ownership does NOT affect permissions

    Args:
        user: User instance
        project: Project instance

    Returns:
        bool: True if user can view project logs
    """
    return has_higher_role(user.role, _ROLE_MANAGER)


def get_project_permissions(user, project) -> dict:
    """
    Get all permissions for a user on a specific project.

    Args:
        user: User instance
        project: Project instance

    Returns:
        dict: Dictionary with permission keys and boolean values
    """
    return {
        'can_create': can_create_project(user),
        'can_read': can_read_project(user, project),
        'can_update': can_update_project(user, project),
        'can_delete': can_delete_project(user, project),
        'can_assign': can_assign_project_members(user, project),
        'can_view_logs': can_view_project_logs(user, project),
    }


def assert_can_update_project(user, project) -> None:
    """
    Assert that user can update the project.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_update_project(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to update project"
        )


def assert_can_delete_project(user, project) -> None:
    """
    Assert that user can delete the project.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_delete_project(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to delete project"
        )


def assert_can_assign_project_members(user, project) -> None:
    """
    Assert that user can assign project members.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_assign_project_members(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to assign project members"
        )


def assert_can_create_project(user) -> None:
    """
    Assert that user can create projects.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_create_project(user):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to create projects"
        )


def assert_can_read_project(user, project) -> None:
    """
    Assert that user can read/view a project.

    Raises:
        AuthorizationError: If user is not authorized
    """
    if not can_read_project(user, project):
        raise AuthorizationError(
            f"User '{user.username}' is not authorized to view project"
        )

