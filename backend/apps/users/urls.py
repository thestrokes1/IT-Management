"""
URL configuration for users app.
API and web endpoints for user management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.users.views import (
    UserRegistrationView, UserLoginView, UserViewSet,
    UserSessionViewSet, LoginAttemptViewSet, LogoutView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'sessions', UserSessionViewSet, basename='usersession')
router.register(r'login-attempts', LoginAttemptViewSet, basename='loginattempt')

urlpatterns = [
    # API endpoints
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    # API router URLs
    path('', include(router.urls)),
]

# Web URLs for Django templates
web_urlpatterns = [
    # Web interface URLs
    path('login/', lambda request: None, name='web-user-login'),  # Placeholder
    path('dashboard/', lambda request: None, name='web-user-dashboard'),  # Placeholder
    path('profile/', lambda request: None, name='web-user-profile'),  # Placeholder
    path('users/', lambda request: None, name='web-user-list'),  # Placeholder
    path('users/create/', lambda request: None, name='web-user-create'),  # Placeholder
    path('users/<int:pk>/', lambda request: None, name='web-user-detail'),  # Placeholder
    path('users/<int:pk>/edit/', lambda request: None, name='web-user-edit'),  # Placeholder
]

# This will be imported as web_urls in config/urls.py
web_urls = web_urlpatterns
