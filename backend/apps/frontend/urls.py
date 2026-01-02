"""
URL configuration for frontend app.
Web interface URLs for IT Management Platform.
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'frontend'

urlpatterns = [
    # Authentication URLs
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='frontend/auth/password_reset.html'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='frontend/auth/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='frontend/auth/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='frontend/auth/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Main application URLs
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Module URLs
    path('assets/', views.AssetsView.as_view(), name='assets'),
    path('assets/create/', views.CreateAssetView.as_view(), name='create_asset'),
    path('assets/<int:asset_id>/edit/', views.EditAssetView.as_view(), name='edit_asset'),
    path('projects/', views.ProjectsView.as_view(), name='projects'),
    path('projects/create/', views.CreateProjectView.as_view(), name='create_project'),
    path('projects/<int:project_id>/edit/', views.EditProjectView.as_view(), name='edit_project'),
    path('tickets/', views.TicketsView.as_view(), name='tickets'),
    path('tickets/create/', views.CreateTicketView.as_view(), name='create_ticket'),
    path('tickets/<int:ticket_id>/edit/', views.EditTicketView.as_view(), name='edit_ticket'),
    path('users/', views.UsersView.as_view(), name='users'),
    path('users/create/', views.CreateUserView.as_view(), name='create_user'),
    path('users/<int:user_id>/edit/', views.EditUserView.as_view(), name='edit_user'),
    path('logs/', views.LogsView.as_view(), name='logs'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    
    # API endpoints for frontend
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    path('api/quick-actions/', views.quick_actions, name='quick_actions'),
    path('api/users/<int:user_id>/', views.delete_user, name='delete_user'),
    path('api/projects/<int:project_id>/', views.project_crud, name='project_crud'),
    path('api/tickets/<int:ticket_id>/', views.ticket_crud, name='ticket_crud'),
    path('api/assets/<int:asset_id>/', views.asset_crud, name='asset_crud'),
    
    # Error pages
    path('404/', views.Error404View.as_view(), name='error_404'),
    path('500/', views.Error500View.as_view(), name='error_500'),
    path('maintenance/', views.MaintenanceView.as_view(), name='maintenance'),
    
    # Additional frontend pages
    path('help/', lambda request: None, name='help'),  # Placeholder
    path('settings/', lambda request: None, name='settings'),  # Placeholder
    path('about/', lambda request: None, name='about'),  # Placeholder
    path('contact/', lambda request: None, name='contact'),  # Placeholder
]

