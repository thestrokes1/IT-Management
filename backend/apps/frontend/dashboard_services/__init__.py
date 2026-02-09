"""
Frontend dashboard services package.

This package contains dashboard metrics services.
Import from this package for DashboardMetricsService.

For other services (TicketService, AssetService), import from:
- from apps.frontend.services import TicketService, AssetService
"""

from apps.frontend.dashboard_services.dashboard_metrics_service import (
    DashboardMetricsService,
    DashboardMetrics,
    MetricResult,
    get_dashboard_metrics,
    get_metrics_for_role,
)

__all__ = [
    'DashboardMetricsService',
    'DashboardMetrics',
    'MetricResult',
    'get_dashboard_metrics',
    'get_metrics_for_role',
]
