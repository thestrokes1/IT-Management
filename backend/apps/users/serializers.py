"""
User serializers for IT Management Platform.
Handles serialization and validation for user-related operations.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from apps.users.models import User, UserProfile, UserSession, LoginAttempt
from django.contrib.auth.password_validation import validate_password

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number', 'role',
            'department', 'job_title', 'employee_id'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password and password confirmation don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            if user.status != 'ACTIVE':
                raise serializers.ValidationError('User account is not active')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 'address', 'city', 'state', 'country', 'postal_code',
            'hire_date', 'manager', 'language', 'timezone', 'theme_preference',
            'two_factor_enabled', 'created_at', 'updated_at'
        ]

class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for user list view.
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'user_id', 'username', 'email', 'first_name', 'last_name',
            'role', 'status', 'department', 'job_title', 'employee_id',
            'is_active', 'last_login', 'created_at', 'last_active', 'profile'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'last_login', 'last_active']

class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for user detail view.
    """
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'user_id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'role', 'status', 'department', 'job_title', 'employee_id',
            'is_active', 'is_staff', 'last_login', 'date_joined', 'created_at',
            'updated_at', 'last_active', 'profile'
        ]
        read_only_fields = [
            'id', 'user_id', 'is_staff', 'date_joined', 'created_at', 'last_login'
        ]

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information.
    """
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone_number', 'role',
            'department', 'job_title', 'employee_id', 'status', 'profile'
        ]
    
    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile if provided
        if profile_data:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing password.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New password and confirmation don't match")
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

class UserSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for user sessions.
    """
    class Meta:
        model = UserSession
        fields = [
            'id', 'session_key', 'ip_address', 'user_agent',
            'is_active', 'created_at', 'last_activity', 'expires_at'
        ]
        read_only_fields = ['id', 'session_key', 'created_at', 'expires_at']

class LoginAttemptSerializer(serializers.ModelSerializer):
    """
    Serializer for login attempts.
    """
    class Meta:
        model = LoginAttempt
        fields = [
            'id', 'username', 'ip_address', 'successful', 'failure_reason', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class UserRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for user role information.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_active']
        read_only_fields = ['id', 'username', 'is_active']

class UserStatisticsSerializer(serializers.Serializer):
    """
    Serializer for user statistics.
    """
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    users_by_role = serializers.DictField()
    users_by_department = serializers.DictField()
    recent_logins = UserListSerializer(many=True)
