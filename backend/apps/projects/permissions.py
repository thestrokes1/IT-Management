"""
Permissions classes for Projects Management.
Role-based access control for project and task operations.
"""

from rest_framework import permissions
from apps.projects.models import Project, Task

class CanManageProjects(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage projects.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_manage_projects

class IsProjectManagerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow project managers and above to edit.
    Read access for project members (including IT_ADMIN) and authenticated users.
    IT_ADMIN users allowed read-only access via project membership.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for project members and authenticated users
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'project'):
                # For tasks, check if user is member of the project
                return request.user.is_authenticated and (
                    request.user in obj.project.team_members.all() or
                    obj.project.project_manager == request.user or
                    request.user.is_admin
                )
            else:
                # For projects - allow read access for team members and ITADMINs
                is_project_member = (
                    request.user in obj.team_members.all() or
                    obj.project_manager == request.user
                )
                # Check ProjectMember for IT_ADMIN assignments
                if not is_project_member and hasattr(obj, 'memberships'):
                    try:
                        from apps.projects.models import ProjectMember
                        is_project_member = ProjectMember.objects.filter(
                            project=obj,
                            user=request.user,
                            is_active=True
                        ).exists()
                    except:
                        pass
                
                return request.user.is_authenticated and (is_project_member or request.user.is_admin)
        
        # Write permissions for project managers and admins only (IT_ADMIN denied write)
        if request.user.is_admin and request.user.role != 'IT_ADMIN':
            return True
        
        if hasattr(obj, 'project'):
            # For tasks
            return request.user == obj.project.project_manager or request.user.can_manage_projects
        else:
            # For projects - IT_ADMIN users cannot write
            from apps.users.models import UserRole
            if hasattr(request.user, 'role') and request.user.role == UserRole.IT_ADMIN:
                return False
            return request.user == obj.project_manager or request.user.can_manage_projects

class IsProjectMember(permissions.BasePermission):
    """
    Custom permission to check if user is a member of the project.
    """
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'project'):
            # For tasks
            project = obj.project
        else:
            # For projects
            project = obj
        
        return request.user and request.user.is_authenticated and (
            request.user == project.project_manager or
            request.user in project.team_members.all() or
            request.user.is_admin
        )

class CanCreateProjects(permissions.BasePermission):
    """
    Custom permission to only allow users who can create projects.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_projects or request.user.is_manager
        )

class CanManageProjectMembers(permissions.BasePermission):
    """
    Custom permission to only allow project managers to manage members.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_manager or request.user.can_manage_projects
        )

class CanViewProjectDetails(permissions.BasePermission):
    """
    Custom permission to check if user can view project details.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.is_admin:
            return True
        
        # Project managers can view all
        if request.user.can_manage_projects:
            return True
        
        # Project members can view their projects
        if hasattr(obj, 'project'):
            # For tasks
            return request.user in obj.project.team_members.all() or obj.project.project_manager == request.user
        else:
            # For projects
            return request.user in obj.team_members.all() or obj.project_manager == request.user

class CanManageTasks(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage tasks.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_projects or request.user.is_technician
        )

class IsTaskAssigneeOrCreator(permissions.BasePermission):
    """
    Custom permission to only allow task assignee, creator, or project managers.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.is_admin:
            return True
        
        # Task assignee can update their tasks
        if obj.assigned_to == request.user:
            return True
        
        # Task creator can update their tasks
        if obj.created_by == request.user:
            return True
        
        # Project managers can manage all tasks in their projects
        if obj.project.project_manager == request.user:
            return True
        
        # Users with project management rights can manage tasks
        if request.user.can_manage_projects:
            return True
        
        return False

class CanViewTaskComments(permissions.BasePermission):
    """
    Custom permission to check if user can view task comments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can view all
        if request.user.is_admin:
            return True
        
        # Project managers can view all comments in their projects
        if obj.project.project_manager == request.user:
            return True
        
        # Project members can view comments
        if request.user in obj.project.team_members.all():
            # Check if user can view internal comments
            if hasattr(obj, 'is_internal') and obj.is_internal:
                return request.user.can_manage_projects
            return True
        
        # Users with project management rights can view all comments
        if request.user.can_manage_projects:
            return True
        
        return False

class CanCreateTaskComments(permissions.BasePermission):
    """
    Custom permission to check if user can create task comments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can create comments
        if request.user.is_admin:
            return True
        
        # Project managers can create comments
        if obj.project.project_manager == request.user:
            return True
        
        # Project members can create comments
        if request.user in obj.project.team_members.all():
            return True
        
        # Users with project management rights can create comments
        if request.user.can_manage_projects:
            return True
        
        return False

class CanManageTaskAttachments(permissions.BasePermission):
    """
    Custom permission to check if user can manage task attachments.
    """
    
    def has_object_permission(self, request, view, obj):
        # Admin can manage all attachments
        if request.user.is_admin:
            return True
        
        # Task creator can manage attachments
        if obj.created_by == request.user:
            return True
        
        # Task assignee can manage attachments
        if obj.assigned_to == request.user:
            return True
        
        # Project managers can manage all attachments
        if obj.project.project_manager == request.user:
            return True
        
        # Users with project management rights can manage attachments
        if request.user.can_manage_projects:
            return True
        
        return False

class CanViewProjectReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can view project reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_projects or request.user.is_manager
        )

class CanGenerateProjectReports(permissions.BasePermission):
    """
    Custom permission to only allow users who can generate project reports.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_projects or request.user.is_manager
        )

class CanManageProjectTemplates(permissions.BasePermission):
    """
    Custom permission to only allow users who can manage project templates.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_admin or request.user.can_manage_projects
        )

class CanUseProjectTemplates(permissions.BasePermission):
    """
    Custom permission to check if user can use project templates.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.can_manage_projects or request.user.is_manager
        )

class CanViewProjectAuditLogs(permissions.BasePermission):
    """
    Custom permission to only allow users who can view project audit logs.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.can_view_logs
