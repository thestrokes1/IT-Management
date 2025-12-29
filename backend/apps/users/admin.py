"""
Django admin configuration for users app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, UserProfile, UserSession, LoginAttempt

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile model.
    """
    list_display = ['user', 'language', 'timezone', 'two_factor_enabled', 'created_at']
    list_filter = ['language', 'timezone', 'theme_preference', 'two_factor_enabled', 'created_at']
    search_fields = ['user__username', 'user__email', 'city', 'state', 'country']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSession model.
    """
    list_display = ['user', 'ip_address', 'is_active', 'created_at', 'last_activity']
    list_filter = ['is_active', 'created_at', 'last_activity']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['created_at', 'last_activity']

@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    """
    Admin interface for LoginAttempt model.
    """
    list_display = ['username', 'ip_address', 'successful', 'failure_reason', 'timestamp']
    list_filter = ['successful', 'timestamp']
    search_fields = ['username', 'ip_address', 'failure_reason']
    readonly_fields = ['timestamp']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for User model.
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'status', 'is_active', 'is_staff', 'created_at']
    list_filter = ['role', 'status', 'is_active', 'is_staff', 'is_superuser', 'created_at', 'last_login']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined', 'password_changed_at']
    filter_horizontal = ['groups', 'user_permissions']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'employee_id')
        }),
        ('Role & Status', {
            'fields': ('role', 'status', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Work Information', {
            'fields': ('department', 'job_title')
        }),
        ('Security', {
            'fields': ('failed_login_attempts', 'locked_until', 'last_login_ip', 'password_changed_at')
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at', 'last_active')}),
    )
    
    def get_queryset(self, request):
        """
        Customize queryset to include related fields.
        """
        qs = super().get_queryset(request)
        return qs.select_related()
    
    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of superusers.
        """
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

