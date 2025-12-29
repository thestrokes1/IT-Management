"""
User views for IT Management Platform.
API endpoints for user management with role-based access control.
"""

from django.contrib.auth import logout
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.utils import timezone
from django.core.cache import cache

from apps.users.models import User, UserProfile, UserSession, LoginAttempt
from apps.users.serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserListSerializer,
    UserDetailSerializer, UserUpdateSerializer, ChangePasswordSerializer,
    UserSessionSerializer, LoginAttemptSerializer, UserStatisticsSerializer
)
from apps.users.permissions import (
    IsAdminOrReadOnly, IsOwnerOrAdmin, CanManageUsers, IsSelfOrAdmin
)

class UserRegistrationView(APIView):
    """
    User registration endpoint.
    """
    permission_classes = [CanManageUsers]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserListSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(TokenObtainPairView):
    """
    Custom login view with session tracking.
    """
    serializer_class = UserLoginSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            # Log failed login attempt
            LoginAttempt.objects.create(
                username=request.data.get('username'),
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                successful=False,
                failure_reason=str(e)
            )
            raise
        
        user = serializer.validated_data['user']
        
        # Log successful login
        LoginAttempt.objects.create(
            username=user.username,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            successful=True
        )
        
        # Update user session data
        user.last_login_ip = self.get_client_ip(request)
        user.last_login = timezone.now()
        user.last_active = timezone.now()
        user.failed_login_attempts = 0
        user.save()
        
        # Create user session
        UserSession.objects.create(
            user=user,
            session_key=request.session.session_key or 'temp_key',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            expires_at=timezone.now() + timezone.timedelta(days=7)
        )
        
        return super().post(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserViewSet(viewsets.ModelViewSet):
    """
    User management viewset with role-based permissions.
    """
    queryset = User.objects.all()
    permission_classes = [CanManageUsers]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return UserUpdateSerializer
        return UserDetailSerializer
    
    def get_queryset(self):
        queryset = User.objects.select_related('profile').all()
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by department
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate user account."""
        user = self.get_object()
        user.status = 'ACTIVE'
        user.is_active = True
        user.save()
        
        return Response({'message': 'User activated successfully'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate user account."""
        user = self.get_object()
        user.status = 'INACTIVE'
        user.is_active = False
        user.save()
        
        return Response({'message': 'User deactivated successfully'})
    
    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile."""
        user = request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update current user profile."""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get user statistics."""
        if not request.user.can_manage_users:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Cache statistics for 5 minutes
        cache_key = f'user_statistics_{request.user.id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        total_users = User.objects.count()
        active_users = User.objects.filter(status='ACTIVE').count()
        
        users_by_role = dict(
            User.objects.values('role').annotate(count=Count('id')).values_list('role', 'count')
        )
        
        users_by_department = dict(
            User.objects.exclude(department='').values('department').annotate(count=Count('id')).values_list('department', 'count')
        )
        
        recent_logins = User.objects.filter(
            last_login__isnull=False
        ).order_by('-last_login')[:10]
        
        stats = {
            'total_users': total_users,
            'active_users': active_users,
            'users_by_role': users_by_role,
            'users_by_department': users_by_department,
            'recent_logins': UserListSerializer(recent_logins, many=True).data
        }
        
        cache.set(cache_key, stats, 300)  # Cache for 5 minutes
        return Response(stats)

class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    User sessions viewset for managing active sessions.
    """
    serializer_class = UserSessionSerializer
    permission_classes = [IsSelfOrAdmin]
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return UserSession.objects.all()
        return UserSession.objects.filter(user=self.request.user)

class LoginAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Login attempts viewset for security monitoring.
    """
    serializer_class = LoginAttemptSerializer
    permission_classes = [CanManageUsers]
    
    def get_queryset(self):
        queryset = LoginAttempt.objects.all()
        
        # Filter by username
        username = self.request.query_params.get('username')
        if username:
            queryset = queryset.filter(username=username)
        
        # Filter by success status
        successful = self.request.query_params.get('successful')
        if successful is not None:
            queryset = queryset.filter(successful=successful.lower() == 'true')
        
        return queryset.order_by('-timestamp')[:100]  # Limit to recent 100 attempts

class LogoutView(APIView):
    """
    User logout view.
    """
    permission_classes = [IsSelfOrAdmin]
    
    def post(self, request):
        try:
            # Invalidate refresh token
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Mark session as inactive
            UserSession.objects.filter(
                user=request.user,
                session_key=request.session.session_key
            ).update(is_active=False)
            
            # Logout user
            logout(request)
            
            return Response({'message': 'Logged out successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
