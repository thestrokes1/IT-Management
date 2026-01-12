"""
Permissions classes for Assets Management.
Role-based access control for asset operations.

遵循 RBAC 规则:
- 所有权限检查必须使用 user.can_* 属性
- 永远不要直接检查 user.role 字符串或用户组
- User 模型是权限判断的唯一真实来源
"""

from rest_framework import permissions
from apps.assets.models import Asset


class CanManageAssets(permissions.BasePermission):
    """
    资产管理的完整权限（创建、编辑、删除、分配等）。
    
    授权规则:
    - MANAGER 及以上角色拥有此权限
    - 对应 User.can_manage_assets 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_manage_assets
        )


class CanViewAssets(permissions.BasePermission):
    """
    查看资产列表的权限。
    
    授权规则:
    - 所有已认证用户均可查看资产列表
    - 对应 User.can_access_assets 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_access_assets
        )


class IsAssetOwnerOrReadOnly(permissions.BasePermission):
    """
    资产对象级权限：允许资产所有者或具有管理权限的用户操作。
    
    读取权限: 所有可以访问资产的用户
    写入权限: 资产管理者或资产分配的用户
    """
    
    def has_object_permission(self, request, view, obj):
        # 读取权限：所有已认证用户（已通过 has_permission 预检查）
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写入权限：资产管理者
        if request.user.can_manage_assets:
            return True
        
        # 资产所有者可以更新分配给自己的资产
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        # 资产创建者可以更新自己创建的资产
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False


class CanViewAssetDetails(permissions.BasePermission):
    """
    查看资产详情的权限。
    
    授权规则:
    - 资产管理者可以查看所有资产
    - 用户可以查看分配给自己的资产
    - 用户可以查看自己创建的资产
    """
    
    def has_object_permission(self, request, view, obj):
        # 资产管理者可以查看所有
        if request.user.can_manage_assets:
            return True
        
        # 用户可以查看分配给自己的资产
        if hasattr(obj, 'assigned_to') and obj.assigned_to == request.user:
            return True
        
        # 用户可以查看自己创建的资产
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        return False


class CanAssignAssets(permissions.BasePermission):
    """
    分配资产的权限。
    
    授权规则:
    - 具有资产分配权限的用户
    - 对应 User.can_manage_assets（资产管理者可以分配）
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_manage_assets
        )


class CanViewMaintenanceRecords(permissions.BasePermission):
    """
    查看维护记录的权限。
    
    授权规则:
    - 资产管理者可以查看所有维护记录
    - 用户可以查看分配给自己资产的维护记录
    """
    
    def has_object_permission(self, request, view, obj):
        # 资产管理者可以查看所有
        if request.user.can_manage_assets:
            return True
        
        # 用户可以查看分配给自己资产的维护记录
        if hasattr(obj, 'asset') and hasattr(obj.asset, 'assigned_to'):
            if obj.asset.assigned_to == request.user:
                return True
        
        return False


class CanManageMaintenance(permissions.BasePermission):
    """
    管理维护记录的权限。
    
    授权规则:
    - 技术人员及以上角色
    - 使用 User.is_technician 属性（TECHNICIAN 或更高角色）
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.is_technician
        )


class CanViewAssetAuditLogs(permissions.BasePermission):
    """
    查看资产审计日志的权限。
    
    授权规则:
    - 具有查看日志权限的用户
    - 对应 User.can_view_logs 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_view_logs
        )


class CanGenerateAssetReports(permissions.BasePermission):
    """
    生成资产报告的权限。
    
    授权规则:
    - 具有创建报告权限的用户
    - 对应 User.can_create_reports 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_create_reports
        )


class CanManageAssetCategories(permissions.BasePermission):
    """
    管理资产类别的权限。
    
    授权规则:
    - IT_ADMIN 或 SUPERADMIN 角色
    - 使用 User.can_manage_settings 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_manage_settings
        )


class CanApproveAssetRetirement(permissions.BasePermission):
    """
    批准资产报废的权限。
    
    授权规则:
    - IT_ADMIN 或 SUPERADMIN 角色
    - 使用 User.can_manage_settings 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_manage_settings
        )


class CanExportAssets(permissions.BasePermission):
    """
    导出资产数据的权限。
    
    授权规则:
    - 具有导出数据权限的用户
    - 对应 User.can_export_data 属性
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_export_data
        )


class CanImportAssets(permissions.BasePermission):
    """
    导入资产数据的权限。
    
    授权规则:
    - 与导出权限相同，需要 MANAGER 或更高角色
    - 对应 User.can_export_data 属性（导入需要管理权限）
    """
    
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.can_export_data
        )
