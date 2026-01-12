"""
URL Configuration for IT Management Platform frontend.
Imports views from the apps.frontend.views package.
"""

from django.urls import path
from apps.frontend import views
from apps.frontend.views import users as user_views


app_name = 'frontend'

urlpatterns = [
    # Authentication
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard_alt'),
    path('dashboard/api/', views.dashboard_api, name='dashboard_api'),
    path('search/', views.search_api, name='search_api'),
    path('notifications/', views.notifications_api, name='notifications_api'),
    path('quick-actions/', views.quick_actions, name='quick_actions'),
    
    # Tickets
    path('tickets/', views.TicketsView.as_view(), name='tickets'),
    path('tickets/create/', views.CreateTicketView.as_view(), name='create-ticket'),
    path('tickets/<int:ticket_id>/edit/', views.EditTicketView.as_view(), name='edit-ticket'),
    path('tickets/<int:ticket_id>/', views.EditTicketView.as_view(), name='ticket-detail'),
    path('tickets/api/<int:ticket_id>/', views.ticket_crud, name='ticket_crud'),
    
    # Projects
    path('projects/', views.ProjectsView.as_view(), name='projects'),
    path('projects/create/', views.CreateProjectView.as_view(), name='create-project'),
    path('projects/<int:project_id>/edit/', views.EditProjectView.as_view(), name='edit-project'),
    path('projects/<int:project_id>/', views.EditProjectView.as_view(), name='project-detail'),
    path('projects/api/<int:project_id>/', views.project_crud, name='project_crud'),
    
    # Assets
    path('assets/', views.AssetsView.as_view(), name='assets'),
    path('assets/create/', views.CreateAssetView.as_view(), name='create-asset'),
    path('assets/<int:asset_id>/edit/', views.EditAssetView.as_view(), name='edit-asset'),
    path('assets/<int:asset_id>/', views.EditAssetView.as_view(), name='asset-detail'),
    path('assets/api/<int:asset_id>/', views.asset_crud, name='asset_crud'),
    
    # Users
    
    path('users/', user_views.UsersView.as_view(), name='users'),
    path('users/create/', user_views.CreateUserView.as_view(), name='create-user'),
    path('users/<int:user_id>/edit/', user_views.EditUserView.as_view(), name='edit-user'),
    path('users/<int:user_id>/delete/', user_views.delete_user, name='delete_user'),
    path('users/<int:user_id>/change-role/', user_views.change_user_role, name='change-user-role'),

    # Profile and settings
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('logs/', views.LogsView.as_view(), name='logs'),
    path('reports/', views.ReportsView.as_view(), name='reports'),
    
    # Error pages
    path('error/404/', views.Error404View.as_view(), name='error404'),
    path('error/500/', views.Error500View.as_view(), name='error500'),
    path('maintenance/', views.MaintenanceView.as_view(), name='maintenance'),
]

