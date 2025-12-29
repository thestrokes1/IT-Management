"""
Security app URL patterns for IT Management Platform.
Defines API endpoints for security-related operations.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'security-events', views.SecurityEventViewSet, basename='securityevent')
router.register(r'audit-logs', views.AuditLogViewSet, basename='auditlog')
router.register(r'security-policies', views.SecurityPolicyViewSet, basename='securitypolicy')
router.register(r'security-thresholds', views.SecurityThresholdViewSet, basename='securitythreshold')
router.register(r'security-incidents', views.SecurityIncidentViewSet, basename='securityincident')
router.register(r'security-dashboards', views.SecurityDashboardViewSet, basename='securitydashboard')
router.register(r'security-configuration', views.SecurityConfigurationViewSet, basename='securityconfiguration')
router.register(r'security-health', views.SecurityHealthCheckViewSet, basename='securityhealth')

app_name = 'security'

urlpatterns = [
    # API endpoints (using ViewSets with router)
    path('', include(router.urls)),
]

