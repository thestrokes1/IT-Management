"""
URL configuration for projects app.
API and web endpoints for project and task management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.projects.views import (
    ProjectCategoryViewSet, ProjectViewSet, TaskViewSet,
    TaskCommentViewSet, TaskAttachmentViewSet, ProjectTemplateViewSet,
    ProjectAuditLogViewSet, ProjectSearchView, TaskSearchView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', ProjectCategoryViewSet, basename='projectcategory')
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'comments', TaskCommentViewSet, basename='taskcomment')
router.register(r'attachments', TaskAttachmentViewSet, basename='taskattachment')
router.register(r'templates', ProjectTemplateViewSet, basename='projecttemplate')
router.register(r'audit-logs', ProjectAuditLogViewSet, basename='projectauditlog')

urlpatterns = [
    # API endpoints
    path('search/projects/', ProjectSearchView.as_view(), name='project-search'),
    path('search/tasks/', TaskSearchView.as_view(), name='task-search'),
    
    # API router URLs
    path('', include(router.urls)),
]

# Web URLs for Django templates
web_urlpatterns = [
    # Web interface URLs
    path('projects/', lambda request: None, name='web-project-list'),  # Placeholder
    path('projects/create/', lambda request: None, name='web-project-create'),  # Placeholder
    path('projects/<int:pk>/', lambda request: None, name='web-project-detail'),  # Placeholder
    path('projects/<int:pk>/edit/', lambda request: None, name='web-project-edit'),  # Placeholder
    path('projects/<int:pk>/members/', lambda request: None, name='web-project-members'),  # Placeholder
    path('projects/<int:pk>/tasks/', lambda request: None, name='web-project-tasks'),  # Placeholder
    path('projects/<int:pk>/reports/', lambda request: None, name='web-project-reports'),  # Placeholder
    path('projects/<int:pk>/audit-logs/', lambda request: None, name='web-project-audit-logs'),  # Placeholder
    path('tasks/', lambda request: None, name='web-task-list'),  # Placeholder
    path('tasks/create/', lambda request: None, name='web-task-create'),  # Placeholder
    path('tasks/<int:pk>/', lambda request: None, name='web-task-detail'),  # Placeholder
    path('tasks/<int:pk>/edit/', lambda request: None, name='web-task-edit'),  # Placeholder
    path('tasks/<int:pk>/comments/', lambda request: None, name='web-task-comments'),  # Placeholder
    path('tasks/<int:pk>/attachments/', lambda request: None, name='web-task-attachments'),  # Placeholder
    path('templates/', lambda request: None, name='web-project-template-list'),  # Placeholder
    path('templates/create/', lambda request: None, name='web-project-template-create'),  # Placeholder
]

# This will be imported as web_urls in config/urls.py
web_urls = web_urlpatterns
