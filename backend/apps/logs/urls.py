"""
URL configuration for logs app.
API and web endpoints for logging and audit trail management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.logs.views import (
    LogCategoryViewSet, ActivityLogViewSet, AuditLogViewSet,
    SystemLogViewSet, SecurityEventViewSet, LogAlertViewSet,
    LogAlertTriggerViewSet, LogReportViewSet, LogRetentionViewSet,
    LogStatisticsViewSet, LogSearchView, LogExportView, LogDashboardView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', LogCategoryViewSet, basename='logcategory')
router.register(r'activity', ActivityLogViewSet, basename='activitylog')
router.register(r'audit', AuditLogViewSet, basename='auditlog')
router.register(r'system', SystemLogViewSet, basename='systemlog')
router.register(r'security', SecurityEventViewSet, basename='securityevent')
router.register(r'alerts', LogAlertViewSet, basename='logalert')
router.register(r'alert-triggers', LogAlertTriggerViewSet, basename='logalerttrigger')
router.register(r'reports', LogReportViewSet, basename='logreport')
router.register(r'retention', LogRetentionViewSet, basename='logretention')
router.register(r'statistics', LogStatisticsViewSet, basename='logstatistics')

urlpatterns = [
    # API endpoints
    path('search/', LogSearchView.as_view(), name='log-search'),
    path('export/', LogExportView.as_view(), name='log-export'),
    path('dashboard/', LogDashboardView.as_view(), name='log-dashboard'),
    
    # API router URLs
    path('', include(router.urls)),
]

# Web URLs for Django templates
web_urlpatterns = [
    # Web interface URLs
    path('logs/', lambda request: None, name='web-log-list'),  # Placeholder
    path('logs/activity/', lambda request: None, name='web-activity-log-list'),  # Placeholder
    path('logs/audit/', lambda request: None, name='web-audit-log-list'),  # Placeholder
    path('logs/security/', lambda request: None, name='web-security-event-list'),  # Placeholder
    path('logs/system/', lambda request: None, name='web-system-log-list'),  # Placeholder
    path('logs/dashboard/', lambda request: None, name='web-log-dashboard'),  # Placeholder
    path('logs/alerts/', lambda request: None, name='web-log-alert-list'),  # Placeholder
    path('logs/reports/', lambda request: None, name='web-log-report-list'),  # Placeholder
    path('logs/export/', lambda request: None, name='web-log-export'),  # Placeholder
]

# This will be imported as web_urls in config/urls.py
web_urls = web_urlpatterns
