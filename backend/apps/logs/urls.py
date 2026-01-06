"""
URL configuration for logs app.
API and web endpoints for logging and audit trail management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.logs.views import (
    LogCategoryViewSet,
    ActivityLogViewSet,
    AuditLogViewSet,
    SystemLogViewSet,
    SecurityEventViewSet,
    LogAlertViewSet,
    LogAlertTriggerViewSet,
    LogReportViewSet,
    LogRetentionViewSet,
    LogStatisticsViewSet,
    LogSearchView,
    LogExportView,
    LogDashboardView,
)

router = DefaultRouter()
router.register(r'categories', LogCategoryViewSet)
router.register(r'activity', ActivityLogViewSet)
router.register(r'audit', AuditLogViewSet)
router.register(r'system', SystemLogViewSet)
router.register(r'security', SecurityEventViewSet)
router.register(r'alerts', LogAlertViewSet)
router.register(r'alert-triggers', LogAlertTriggerViewSet)
router.register(r'reports', LogReportViewSet)
router.register(r'retention', LogRetentionViewSet)
router.register(r'statistics', LogStatisticsViewSet)

urlpatterns = [
    path('search/', LogSearchView.as_view(), name='log-search'),
    path('export/', LogExportView.as_view(), name='log-export'),
    path('dashboard/', LogDashboardView.as_view(), name='log-dashboard'),
    path('', include(router.urls)),
]

