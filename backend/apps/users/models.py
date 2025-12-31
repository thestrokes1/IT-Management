"""
User models for IT Management Platform.
Custom user model with role-based access control.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid

class User(AbstractUser):
    """
    Custom user model with extended fields and role-based access control.
    """
    
    # Role choices
    ROLE_CHOICES = [
        ('SUPERADMIN', 'Super Administrator'),
        ('IT_ADMIN', 'IT Administrator'),
        ('MANAGER', 'Manager'),
        ('TECHNICIAN', 'Technician'),
        ('VIEWER', 'Viewer'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
    ]
    
    # User ID (unique identifier)
    user_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Extended fields
    email = models.EmailField(unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    
    # Role and status
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='VIEWER')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Profile information
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True, unique=True)
    
    # Account management
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    password_changed_at = models.DateTimeField(default=timezone.now)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    # Audit fields
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='users_created')
    updated_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='users_updated')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        """Check if user has admin privileges"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN']
    
    @property
    def is_manager(self):
        """Check if user has manager privileges"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER']
    
    @property
    def is_technician(self):
        """Check if user has technician privileges"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']
    
    @property
    def can_manage_users(self):
        """Check if user can manage other users"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN']
    
    @property
    def can_manage_assets(self):
        """Check if user can manage assets"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']
    
    @property
    def can_manage_projects(self):
        """Check if user can manage projects"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']
    
    @property
    def can_manage_tickets(self):
        """Check if user can manage tickets"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN', 'MANAGER', 'TECHNICIAN']
    
    @property
    def can_view_logs(self):
        """Check if user can view audit logs"""
        return self.role in ['SUPERADMIN', 'IT_ADMIN']
    
    def save(self, *args, **kwargs):
        # Set email from username if not provided
        if not self.email and self.username:
            self.email = f"{self.username}@company.com"
        
        # Auto-generate employee_id if not provided
        if not self.employee_id:
            import random
            import string
            # Generate a unique employee ID
            random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if self.username:
                self.employee_id = f"EMP-{self.username.upper()[:4]}-{random_suffix}"
            else:
                self.employee_id = f"EMP-{random_suffix}"
            
            # Ensure uniqueness
            counter = 1
            original_employee_id = self.employee_id
            while User.objects.filter(employee_id=self.employee_id).exclude(pk=self.pk).exists():
                self.employee_id = f"{original_employee_id}-{counter}"
                counter += 1
        
        # Update password_changed_at when password changes
        if self.pk:
            try:
                old_user = User.objects.get(pk=self.pk)
                if old_user.password != self.password:
                    self.password_changed_at = timezone.now()
            except User.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    def get_user_info(self):
        """Get basic user information for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'status': self.status,
            'department': self.department,
            'job_title': self.job_title,
            'employee_id': self.employee_id,
            'created_at': self.created_at,
            'is_active': self.is_active,
        }

class UserProfile(models.Model):
    """
    Extended user profile information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal information
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Work information
    hire_date = models.DateField(null=True, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='direct_reports')
    
    # Preferences
    language = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    theme_preference = models.CharField(max_length=20, default='light')
    
    # Security preferences
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"Profile for {self.user.username}"

class UserSession(models.Model):
    """
    Track user sessions for security and monitoring.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"

class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring.
    """
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    successful = models.BooleanField()
    failure_reason = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_attempts'
        verbose_name = 'Login Attempt'
        verbose_name_plural = 'Login Attempts'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        status = "SUCCESS" if self.successful else "FAILED"
        return f"{self.username} - {status} - {self.ip_address}"
