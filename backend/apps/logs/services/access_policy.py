"""
Log Access Policy Service

Defines who can see what logs based on role:
- SUPERADMIN: all logs
- IT_ADMIN: security + activity
- MANAGER: activity only
- TECHNICIAN: own actions
- VIEWER: none or summary only

Also provides immutability enforcement for logs.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from django.db import models


# =============================================================================
# Log Categories for Access Control
# =============================================================================

class LogCategory(Enum):
    """Categories of logs for access control."""
    SECURITY = 'SECURITY'
    ACTIVITY = 'ACTIVITY'
    SYSTEM = 'SYSTEM'
    AUDIT = 'AUDIT'
    ERROR = 'ERROR'


# =============================================================================
# Access Levels
# =============================================================================

class AccessLevel(Enum):
    """Access levels for log viewing."""
    NONE = 'none'          # Cannot view any logs
    SUMMARY = 'summary'    # Can only see aggregated summaries
    OWN = 'own'            # Can only see own actions
    CATEGORY = 'category'  # Can see specific categories
    ALL = 'all'            # Can see all logs


# =============================================================================
# Role Access Policy Configuration
# =============================================================================

ROLE_ACCESS_POLICY = {
    'SUPERADMIN': {
        'access_level': AccessLevel.ALL,
        'categories': list(LogCategory),  # All categories
        'can_export': True,
        'can_delete': False,  # Even admins can't delete logs
        'can_view_sensitive': True,
        'can_verify_integrity': True,
    },
    'IT_ADMIN': {
        'access_level': AccessLevel.CATEGORY,
        'categories': [LogCategory.SECURITY, LogCategory.ACTIVITY, LogCategory.AUDIT],
        'can_export': True,
        'can_delete': False,
        'can_view_sensitive': True,
        'can_verify_integrity': True,
    },
    'MANAGER': {
        'access_level': AccessLevel.CATEGORY,
        'categories': [LogCategory.ACTIVITY, LogCategory.AUDIT],
        'can_export': False,
        'can_delete': False,
        'can_view_sensitive': False,
        'can_verify_integrity': False,
    },
    'TECHNICIAN': {
        'access_level': AccessLevel.OWN,
        'categories': [LogCategory.ACTIVITY],
        'can_export': False,
        'can_delete': False,
        'can_view_sensitive': False,
        'can_verify_integrity': False,
    },
    'VIEWER': {
        'access_level': AccessLevel.NONE,
        'categories': [],
        'can_export': False,
        'can_delete': False,
        'can_view_sensitive': False,
        'can_verify_integrity': False,
    },
}


# =============================================================================
# Access Policy Result
# =============================================================================

@dataclass
class AccessPolicy:
    """Result of an access policy check."""
    allowed: bool
    access_level: AccessLevel
    allowed_categories: List[LogCategory]
    can_export: bool
    can_delete: bool
    can_view_sensitive: bool
    can_verify_integrity: bool
    reason: str = ''


@dataclass
class FilteredQuery:
    """Result of filtering a query by access policy."""
    queryset: models.QuerySet
    applied_filters: Dict[str, Any]
    access_policy: AccessPolicy


# =============================================================================
# Log Access Policy Service
# =============================================================================

class LogAccessPolicyService:
    """
    Service for enforcing log access policies based on user role.
    
    Usage:
        service = LogAccessPolicyService(user=request.user, role='IT_ADMIN')
        policy = service.get_access_policy()
        
        if policy.allowed:
            logs = service.filter_queryset(queryset)
    """
    
    def __init__(self, user=None, role: str = None):
        """
        Initialize access policy service.
        
        Args:
            user: Django user instance
            role: Role string (extracted from user if not provided)
        """
        self._user = user
        self._role = getattr(user, 'role', role) if user else role
        self._role = self._role or 'VIEWER'
        self._policy = self._get_policy()
    
    def get_access_policy(self) -> AccessPolicy:
        """Get the access policy for this user/role."""
        return self._policy
    
    def can_view_logs(self) -> bool:
        """Check if user can view any logs."""
        return self._policy.access_level != AccessLevel.NONE
    
    def can_view_category(self, category: LogCategory) -> bool:
        """Check if user can view a specific log category."""
        return category in self._policy.allowed_categories
    
    def can_view_log(self, log) -> bool:
        """
        Check if user can view a specific log entry.
        
        Args:
            log: ActivityLog instance
        
        Returns:
            bool indicating if viewing is allowed
        """
        if not self.can_view_logs():
            return False
        
        # Check category
        log_category = self._get_log_category(log)
        if log_category not in self._policy.allowed_categories:
            return False
        
        # For OWN access level, check if user owns the log
        if self._policy.access_level == AccessLevel.OWN:
            if hasattr(log, 'actor_id') and self._user:
                return log.actor_id == self._user.id
            if hasattr(log, 'actor_name') and self._user:
                return log.actor_name == self._user.username
        
        return True
    
    def filter_queryset(self, queryset) -> FilteredQuery:
        """
        Filter a queryset based on access policy.
        
        Args:
            queryset: ActivityLog queryset
        
        Returns:
            FilteredQuery with filtered queryset and policy info
        """
        applied_filters = {}
        
        if self._policy.access_level == AccessLevel.NONE:
            # Return empty queryset
            return FilteredQuery(
                queryset=queryset.none(),
                applied_filters=applied_filters,
                access_policy=self._policy,
            )
        
        if self._policy.access_level == AccessLevel.OWN and self._user:
            # Filter to user's own actions
            queryset = queryset.filter(
                models.Q(actor_id=self._user.id) |
                models.Q(actor_name=self._user.username)
            )
            applied_filters['actor'] = self._user.username
        
        if self._policy.access_level in [AccessLevel.CATEGORY, AccessLevel.ALL]:
            # Filter by allowed categories
            allowed_category_values = [c.value for c in self._policy.allowed_categories]
            queryset = queryset.filter(category__in=allowed_category_values)
            applied_filters['categories'] = allowed_category_values
        
        return FilteredQuery(
            queryset=queryset,
            applied_filters=applied_filters,
            access_policy=self._policy,
        )
    
    def get_allowed_categories(self) -> List[LogCategory]:
        """Get list of categories user can access."""
        return self._policy.allowed_categories
    
    def get_summary_data(self) -> Dict[str, int]:
        """
        Get summary data for users with SUMMARY access.
        
        Returns:
            Dict with aggregated counts by category
        """
        from apps.logs.models import ActivityLog
        
        queryset = ActivityLog.objects.all()
        filtered = self.filter_queryset(queryset)
        
        result = {}
        for category in LogCategory:
            count = filtered.queryset.filter(
                category=category.value
            ).count()
            result[category.value] = count
        
        return result
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    def _get_policy(self) -> AccessPolicy:
        """Get the access policy for the user's role."""
        config = ROLE_ACCESS_POLICY.get(
            self._role,
            ROLE_ACCESS_POLICY['VIEWER']
        )
        
        return AccessPolicy(
            allowed=config['access_level'] != AccessLevel.NONE,
            access_level=config['access_level'],
            allowed_categories=config['categories'],
            can_export=config.get('can_export', False),
            can_delete=config.get('can_delete', False),
            can_view_sensitive=config.get('can_view_sensitive', False),
            can_verify_integrity=config.get('can_verify_integrity', False),
            reason=f"Role '{self._role}' has {config['access_level'].value} access",
        )
    
    def _get_log_category(self, log) -> LogCategory:
        """Determine the category of a log entry."""
        # Try to get from category field
        if hasattr(log, 'category') and log.category:
            try:
                return LogCategory(log.category.value)
            except ValueError:
                pass
        
        # Infer from action or level
        action = getattr(log, 'action', '') or ''
        level = getattr(log, 'level', '') or ''
        
        if 'SECURITY' in action or 'LOGIN' in action or 'LOGOUT' in action:
            return LogCategory.SECURITY
        if 'ERROR' in level or 'EXCEPTION' in action:
            return LogCategory.ERROR
        if 'SYSTEM' in action or 'MAINTENANCE' in action:
            return LogCategory.SYSTEM
        if 'AUDIT' in action or 'EXPORT' in action:
            return LogCategory.AUDIT
        
        return LogCategory.ACTIVITY


# =============================================================================
# Immutability Enforcement
# =============================================================================

class LogImmutabilityService:
    """
    Service for enforcing log immutability.
    
    Ensures logs cannot be edited or deleted through ORM operations.
    """
    
    @staticmethod
    def prevent_delete(queryset) -> bool:
        """
        Check and prevent deletion of logs.
        
        Raises:
            PermissionDenied: If deletion is attempted
        
        Returns:
            True if operation would be allowed (for testing)
        """
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied(
            "Logs are immutable and cannot be deleted. "
            "Contact administrator if you need to archive logs."
        )
    
    @staticmethod
    def prevent_update(queryset, **kwargs) -> bool:
        """
        Check and prevent update of logs.
        
        Raises:
            PermissionDenied: If update is attempted
        
        Returns:
            True if operation would be allowed (for testing)
        """
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied(
            "Logs are immutable and cannot be modified. "
            "Contact administrator if you need to add annotations."
        )
    
    @staticmethod
    def check_immutable(model_class) -> bool:
        """
        Check if a model is marked as immutable.
        
        Args:
            model_class: The model class to check
        
        Returns:
            True if model is immutable
        """
        # Check for immutable marker
        if hasattr(model_class, '_is_immutable') and model_class._is_immutable:
            return True
        
        # Check if model is ActivityLog or related
        model_name = model_class.__name__
        immutable_models = [
            'ActivityLog',
            'SecurityEvent', 
            'AuditLog',
            'SystemLog',
        ]
        
        return model_name in immutable_models


# =============================================================================
# Model-Level Immutability (Django Signals)
# =============================================================================

def prevent_log_modification(sender, **kwargs):
    """
    Django pre_save signal to prevent log modifications.
    
    Connect this signal in apps.py:
        from django.db.models.signals import pre_save
        from apps.logs.models import ActivityLog
        from apps.logs.services.access_policy import prevent_log_modification
        
        pre_save.connect(prevent_log_modification, sender=ActivityLog)
    """
    instance = kwargs.get('instance')
    
    if not instance:
        return
    
    # Check if this is an existing record (has pk)
    if instance.pk:
        # Get original from database
        try:
            original = sender.objects.get(pk=instance.pk)
            
            # Check for any field modifications
            immutable_fields = [
                'action', 'level', 'actor_id', 'actor_name', 'actor_role',
                'ip_address', 'description', 'timestamp', 'extra_data',
            ]
            
            for field in immutable_fields:
                original_value = getattr(original, field, None)
                new_value = getattr(instance, field, None)
                
                if str(original_value) != str(new_value):
                    from django.core.exceptions import PermissionDenied
                    raise PermissionDenied(
                        f"Cannot modify immutable field '{field}' on log entry."
                    )
        except sender.DoesNotExist:
            pass  # New record, allow creation


def prevent_log_deletion(sender, **kwargs):
    """
    Django pre_delete signal to prevent log deletions.
    
    Connect this signal in apps.py:
        from django.db.models.signals import pre_delete
        from apps.logs.models import ActivityLog
        from apps.logs.services.access_policy import prevent_log_deletion
        
        pre_delete.connect(prevent_log_deletion, sender=ActivityLog)
    """
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied("Logs are immutable and cannot be deleted.")


# =============================================================================
# Admin Read-Only Enforcement
# =============================================================================

class ReadOnlyAdminMixin:
    """
    Mixin for Django admin classes to enforce read-only access to logs.
    
    Usage:
        class ActivityLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
            def has_add_permission(self, request):
                return False  # Or check role
            
            def has_change_permission(self, request, obj=None):
                return False
            
            def has_delete_permission(self, request, obj=None):
                return False
            
            def get_actions(self, request):
                # Remove delete action from admin actions
                actions = super().get_actions(request)
                if 'delete_selected' in actions:
                    del actions['delete_selected']
                return actions
    """
    
    def has_add_permission(self, request):
        """Check if user can add logs (usually no one)."""
        # Logs are created by the system, not through admin
        return False
    
    def has_change_permission(self, request, obj=None):
        """Check if user can change logs (always no - immutable)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Check if user can delete logs (always no - immutable)."""
        return False
    
    def get_actions(self, request):
        """Remove destructive actions from admin."""
        actions = super().get_actions(request)
        
        # Remove delete action
        if 'delete_selected' in actions:
            del actions['delete_selected']
        
        return actions
    
    def delete_model(self, request, obj):
        """Prevent model deletion."""
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Logs cannot be deleted.")
    
    def delete_queryset(self, request, queryset):
        """Prevent queryset deletion."""
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Logs cannot be deleted.")


# =============================================================================
# Convenience Functions
# =============================================================================

def get_log_access_policy(user=None, role: str = None) -> AccessPolicy:
    """
    Convenience function to get log access policy.
    
    Args:
        user: Django user instance
        role: Role string
    
    Returns:
        AccessPolicy instance
    """
    service = LogAccessPolicyService(user=user, role=role)
    return service.get_access_policy()


def can_user_view_logs(user=None, role: str = None) -> bool:
    """
    Check if a user can view logs.
    
    Args:
        user: Django user instance
        role: Role string
    
    Returns:
        True if user can view logs
    """
    service = LogAccessPolicyService(user=user, role=role)
    return service.can_view_logs()


def filter_logs_by_access(queryset, user=None, role: str = None) -> models.QuerySet:
    """
    Filter logs queryset by user access policy.
    
    Args:
        queryset: ActivityLog queryset
        user: Django user instance
        role: Role string
    
    Returns:
        Filtered queryset
    """
    service = LogAccessPolicyService(user=user, role=role)
    return service.filter_queryset(queryset).queryset
