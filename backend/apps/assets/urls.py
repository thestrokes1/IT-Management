"""
URL configuration for assets app.
API and web endpoints for asset management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.assets.views import (
    AssetCategoryViewSet, AssetViewSet, HardwareAssetViewSet,
    SoftwareAssetViewSet, AssetAssignmentViewSet, AssetMaintenanceViewSet,
    AssetAuditLogViewSet, AssetSearchView
)

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', AssetCategoryViewSet, basename='assetcategory')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'hardware', HardwareAssetViewSet, basename='hardwareasset')
router.register(r'software', SoftwareAssetViewSet, basename='softwareasset')
router.register(r'assignments', AssetAssignmentViewSet, basename='assetassignment')
router.register(r'maintenance', AssetMaintenanceViewSet, basename='assetmaintenance')
router.register(r'audit-logs', AssetAuditLogViewSet, basename='assetauditlog')

urlpatterns = [
    # API endpoints
    path('search/', AssetSearchView.as_view(), name='asset-search'),
    
    # API router URLs
    path('', include(router.urls)),
]

# Web URLs for Django templates
web_urlpatterns = [
    # Web interface URLs
    path('assets/', lambda request: None, name='web-asset-list'),  # Placeholder
    path('assets/create/', lambda request: None, name='web-asset-create'),  # Placeholder
    path('assets/<int:pk>/', lambda request: None, name='web-asset-detail'),  # Placeholder
    path('assets/<int:pk>/edit/', lambda request: None, name='web-asset-edit'),  # Placeholder
    path('assets/<int:pk>/assign/', lambda request: None, name='web-asset-assign'),  # Placeholder
    path('assets/<int:pk>/maintenance/', lambda request: None, name='web-asset-maintenance'),  # Placeholder
    path('assets/hardware/', lambda request: None, name='web-hardware-list'),  # Placeholder
    path('assets/software/', lambda request: None, name='web-software-list'),  # Placeholder
    path('assets/assigned/', lambda request: None, name='web-assigned-assets'),  # Placeholder
    path('assets/unassigned/', lambda request: None, name='web-unassigned-assets'),  # Placeholder
    path('assets/warranty-expiring/', lambda request: None, name='web-warranty-expiring'),  # Placeholder
    path('assets/search/', lambda request: None, name='web-asset-search'),  # Placeholder
]

# This will be imported as web_urls in config/urls.py
web_urls = web_urlpatterns
