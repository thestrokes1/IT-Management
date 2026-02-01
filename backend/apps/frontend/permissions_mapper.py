"""
Permission Mapper Layer for IT Management Platform.

Translates domain authority permissions to UI flags for templates.
Keeps authority layer pure while providing consistent UI permission structure.

UI Permission Flags Contract (Authoritative):
{
    "can_view": bool,           # authority.can_view(user, obj)
    "can_update": bool,         # authority.can_edit(user, obj) - UI alias
    "can_delete": bool,         # authority.can_delete(user, obj)
    "can_assign": bool,         # authority.can_assign(user, obj)
    "can_unassign": bool,       # authority.can_unassign(user, obj)
    "can_self_assign": bool,    # authority.can_assign_to_self(user, obj) - UI alias
    "assigned_to_me": bool,     # obj.assigned_to_id == user.id
}
"""

from apps.tickets.domain.services.ticket_authority import (
    can_view as ticket_can_view,
    can_edit as ticket_can_edit,
    can_delete as ticket_can_delete,
    can_assign as ticket_can_assign,
    can_unassign as ticket_can_unassign,
    can_assign_to_self as ticket_can_assign_to_self,
)
from apps.assets.domain.services.asset_authority import (
    can_view as asset_can_view,
    can_edit as asset_can_edit,
    can_delete as asset_can_delete,
    can_assign as asset_can_assign,
    can_unassign as asset_can_unassign,
    can_assign_to_self as asset_can_assign_to_self,
)
from apps.projects.domain.services.project_authority import (
    can_view as project_can_view,
    can_edit as project_can_edit,
    can_delete as project_can_delete,
    can_assign as project_can_assign,
    can_unassign as project_can_unassign,
    can_assign_to_self as project_can_assign_to_self,
)
from apps.users.domain.services.user_authority import (
    can_view as user_can_view,
    can_edit as user_can_edit,
    can_delete as user_can_delete,
    can_change_role as user_can_change_role,
    can_deactivate as user_can_deactivate,
)


# =============================================================================
# Ticket Permission Mapper
# =============================================================================

def build_ticket_ui_permissions(user, ticket) -> dict:
    """
    Build UI permission flags for a ticket.
    
    Translates domain authority permissions to template-consumable flags.
    
    Args:
        user: User instance
        ticket: Ticket instance
        
    Returns:
        dict: UI permission flags
    """
    return {
        'can_view': ticket_can_view(user, ticket),
        'can_update': ticket_can_edit(user, ticket),
        'can_delete': ticket_can_delete(user, ticket),
        'can_assign': ticket_can_assign(user, ticket, None),
        'can_unassign': ticket_can_unassign(user, ticket),
        'can_self_assign': ticket_can_assign_to_self(user, ticket),
        'assigned_to_me': ticket.assigned_to_id == user.id if ticket else False,
    }


def build_tickets_permissions_map(user, tickets) -> dict:
    """
    Build permissions map for a list of tickets.
    
    Args:
        user: User instance
        tickets: QuerySet of Ticket instances
        
    Returns:
        dict: Mapping of ticket.id -> permission flags
    """
    return {
        ticket.id: build_ticket_ui_permissions(user, ticket)
        for ticket in tickets
    }


# =============================================================================
# Asset Permission Mapper
# =============================================================================

def build_asset_ui_permissions(user, asset) -> dict:
    """
    Build UI permission flags for an asset.
    
    Translates domain authority permissions to template-consumable flags.
    
    Args:
        user: User instance
        asset: Asset instance
        
    Returns:
        dict: UI permission flags
    """
    return {
        'can_view': asset_can_view(user, asset),
        'can_update': asset_can_edit(user, asset),
        'can_delete': asset_can_delete(user, asset),
        'can_assign': asset_can_assign(user, asset, None),
        'can_unassign': asset_can_unassign(user, asset),
        'can_self_assign': asset_can_assign_to_self(user, asset),
        'assigned_to_me': asset.assigned_to_id == user.id if asset else False,
    }


def build_assets_permissions_map(user, assets) -> dict:
    """
    Build permissions map for a list of assets.
    
    Args:
        user: User instance
        assets: QuerySet of Asset instances
        
    Returns:
        dict: Mapping of asset.id -> permission flags
    """
    return {
        asset.id: build_asset_ui_permissions(user, asset)
        for asset in assets
    }


# =============================================================================
# Project Permission Mapper
# =============================================================================

def build_project_ui_permissions(user, project) -> dict:
    """
    Build UI permission flags for a project.
    
    Translates domain authority permissions to template-consumable flags.
    
    Args:
        user: User instance
        project: Project instance (or dict with project data)
        
    Returns:
        dict: UI permission flags
    """
    # Handle both Project model and dict representations
    if isinstance(project, dict):
        project_id = project.get('id')
        assigned_to_id = project.get('assigned_to_id')
    else:
        project_id = project.id
        assigned_to_id = getattr(project, 'assigned_to_id', None)
    
    return {
        'can_view': project_can_view(user, project),
        'can_update': project_can_edit(user, project),
        'can_delete': project_can_delete(user, project),
        'can_assign': project_can_assign(user, project, None),
        'can_unassign': project_can_unassign(user, project),
        'can_self_assign': project_can_assign_to_self(user, project),
        'assigned_to_me': assigned_to_id == user.id if assigned_to_id else False,
    }


def build_projects_permissions_map(user, projects) -> dict:
    """
    Build permissions map for a list of projects.
    
    Args:
        user: User instance
        projects: List of Project instances or dicts
        
    Returns:
        dict: Mapping of project.id -> permission flags
    """
    return {
        project.id if hasattr(project, 'id') else project['id']: 
            build_project_ui_permissions(user, project)
        for project in projects
    }


# =============================================================================
# User Permission Mapper
# =============================================================================

def build_user_ui_permissions(actor, target) -> dict:
    """
    Build UI permission flags for a user.
    
    Translates domain authority permissions to template-consumable flags.
    
    Args:
        actor: User instance attempting the action
        target: User instance being accessed
        
    Returns:
        dict: UI permission flags
    """
    return {
        'can_view': user_can_view(actor, target),
        'can_update': user_can_edit(actor, target),
        'can_delete': user_can_delete(actor, target),
        'can_change_role': user_can_change_role(actor, target, target.role),
        'can_deactivate': user_can_deactivate(actor, target),
        'can_assign': False,  # User assignment not applicable
        'can_unassign': False,  # User assignment not applicable
        'can_self_assign': False,  # User assignment not applicable
        'assigned_to_me': actor.id == target.id,
    }


def build_users_permissions_map(actor, users) -> dict:
    """
    Build permissions map for a list of users.
    
    Args:
        actor: User instance attempting the actions
        users: QuerySet of User instances
        
    Returns:
        dict: Mapping of user.id -> permission flags
    """
    return {
        user.id: build_user_ui_permissions(actor, user)
        for user in users
    }


# =============================================================================
# List-Level Permissions
# =============================================================================

def get_list_permissions(user) -> dict:
    """
    Get list-level permissions for the current user.
    
    Args:
        user: User instance
        
    Returns:
        dict: List-level permission flags
    """
    return {
        'can_view_list': True,  # Already filtered by view mixin
        'can_create': user.is_authenticated,
    }

