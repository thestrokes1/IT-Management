"""
DashboardMetricsService - Log-driven metrics for the dashboard.

Computes dashboard metrics from activity logs using LogQueryService.
Metrics are role-scoped and performance-optimized.

Usage:
    service = DashboardMetricsService(user=request.user, role='IT_ADMIN')
    metrics = service.get_all_metrics()
    
    # Or get specific metric
    tickets_today = service.get_tickets_created_today()
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from django.utils import timezone
from django.core.cache import cache

from apps.logs.services.log_query_service import LogQueryService
from apps.logs.enums import EventCategory


# =============================================================================
# Metric Result DTOs
# =============================================================================

@dataclass
class DashboardMetrics:
    """
    Complete dashboard metrics payload.
    
    All metrics are computed from logs via LogQueryService.
    """
    # Timestamps
    computed_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Ticket Metrics
    tickets_created_today: int
    tickets_created_week: int
    tickets_by_status: Dict[str, int]
    tickets_by_priority: Dict[str, int]
    
    # Asset Metrics
    assets_modified_today: int
    assets_modified_week: int
    assets_by_status: Dict[str, int]
    
    # Security Metrics
    security_incidents_30d: int
    security_by_severity: Dict[str, int]
    security_by_status: Dict[str, int]
    open_critical_count: int
    
    # Activity Metrics
    total_actions_period: int
    actions_by_role: Dict[str, int]
    actions_by_category: Dict[str, int]
    top_actors: List[Dict[str, Any]]
    
    # User Metrics
    active_users_today: int
    active_users_week: int
    user_activity_summary: Dict[str, int]
    
    # Performance metadata
    cache_hit: bool = False
    query_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'computed_at': self.computed_at.isoformat(),
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'tickets': {
                'created_today': self.tickets_created_today,
                'created_week': self.tickets_created_week,
                'by_status': self.tickets_by_status,
                'by_priority': self.tickets_by_priority,
            },
            'assets': {
                'modified_today': self.assets_modified_today,
                'modified_week': self.assets_modified_week,
                'by_status': self.assets_by_status,
            },
            'security': {
                'incidents_30d': self.security_incidents_30d,
                'by_severity': self.security_by_severity,
                'by_status': self.security_by_status,
                'open_critical': self.open_critical_count,
            },
            'activity': {
                'total_actions': self.total_actions_period,
                'by_role': self.actions_by_role,
                'by_category': self.actions_by_category,
                'top_actors': self.top_actors,
            },
            'users': {
                'active_today': self.active_users_today,
                'active_week': self.active_users_week,
                'summary': self.user_activity_summary,
            },
            'performance': {
                'cache_hit': self.cache_hit,
                'query_time_ms': self.query_time_ms,
            },
        }


@dataclass
class MetricResult:
    """Single metric result with metadata."""
    value: Any
    label: str
    description: str
    trend: Optional[str] = None  # 'up', 'down', 'stable'
    trend_value: Optional[float] = None


# =============================================================================
# Role Scoping Configuration
# =============================================================================

ROLE_SCOPE_CONFIG = {
    'SUPERADMIN': {
        'scope': 'global',
        'access_level': 'full',
        'cache_ttl_seconds': 300,  # 5 minutes
        'include_private': True,
    },
    'IT_ADMIN': {
        'scope': 'it_department',
        'access_level': 'full',
        'cache_ttl_seconds': 300,
        'include_private': True,
    },
    'MANAGER': {
        'scope': 'team',
        'access_level': 'team',
        'cache_ttl_seconds': 600,  # 10 minutes
        'include_private': False,
    },
    'TECHNICIAN': {
        'scope': 'own_actions',
        'access_level': 'limited',
        'cache_ttl_seconds': 60,  # 1 minute
        'include_private': False,
    },
    'VIEWER': {
        'scope': 'read_only',
        'access_level': 'read_only',
        'cache_ttl_seconds': 900,  # 15 minutes
        'include_private': False,
    },
}


# =============================================================================
# Dashboard Metrics Service
# =============================================================================

class DashboardMetricsService:
    """
    Service for computing log-driven dashboard metrics.
    
    Design principles:
    - Uses LogQueryService for all queries (no ORM in views)
    - Role-scoped access (SUPERADMIN sees global, TECHNICIAN sees own)
    - Performance optimized (indexed fields, caching)
    - Returns pure data (no HTML)
    """
    
    CACHE_KEY_PREFIX = 'dashboard_metrics'
    CACHE_TIMEOUT_DEFAULT = 300  # 5 minutes
    
    def __init__(self, user=None, role=None):
        """
        Initialize the metrics service.
        
        Args:
            user: Django user instance (optional)
            role: Role string (optional, extracted from user if not provided)
        """
        self._user = user
        self._role = getattr(user, 'role', role) if user else role
        self._role = self._role or 'VIEWER'
        
        # Get scope configuration
        self._scope_config = ROLE_SCOPE_CONFIG.get(
            self._role, 
            ROLE_SCOPE_CONFIG['VIEWER']
        )
        
        # Initialize query service
        self._query_service = LogQueryService(user=user)
        
        # Time boundaries
        now = timezone.now()
        self._today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        self._week_ago = self._today - timedelta(days=7)
        self._month_ago = self._today - timedelta(days=30)
    
    def get_all_metrics(self) -> DashboardMetrics:
        """
        Compute all dashboard metrics.
        
        Returns:
            DashboardMetrics with all computed metrics
        """
        import time
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key('all')
        cached = cache.get(cache_key)
        if cached and self._should_use_cache():
            cached['performance']['cache_hit'] = True
            return self._dict_to_metrics(cached)
        
        # Compute all metrics
        metrics = DashboardMetrics(
            computed_at=timezone.now(),
            period_start=self._week_ago,
            period_end=self._today,
            
            tickets_created_today=self._get_tickets_created('today'),
            tickets_created_week=self._get_tickets_created('week'),
            tickets_by_status=self._get_tickets_by_status(),
            tickets_by_priority=self._get_tickets_by_priority(),
            
            assets_modified_today=self._get_assets_modified('today'),
            assets_modified_week=self._get_assets_modified('week'),
            assets_by_status=self._get_assets_by_status(),
            
            security_incidents_30d=self._get_security_incidents(),
            security_by_severity=self._get_security_by_severity(),
            security_by_status=self._get_security_by_status(),
            open_critical_count=self._get_open_critical_count(),
            
            total_actions_period=self._get_total_actions(),
            actions_by_role=self._get_actions_by_role(),
            actions_by_category=self._get_actions_by_category(),
            top_actors=self._get_top_actors(),
            
            active_users_today=self._get_active_users('today'),
            active_users_week=self._get_active_users('week'),
            user_activity_summary=self._get_user_activity_summary(),
        )
        
        # Calculate query time
        metrics.query_time_ms = int((time.time() - start_time) * 1000)
        metrics.cache_hit = False
        
        # Cache the result
        self._cache_metrics(cache_key, metrics)
        
        return metrics
    
    def get_tickets_created_today(self) -> MetricResult:
        """Get count of tickets created today."""
        count = self._get_tickets_created('today')
        return MetricResult(
            value=count,
            label='Tickets Created Today',
            description='Number of tickets created in the last 24 hours',
            trend='up' if count > 0 else 'stable',
        )
    
    def get_security_summary(self) -> MetricResult:
        """Get security incidents summary."""
        count = self._get_security_incidents()
        critical = self._get_open_critical_count()
        return MetricResult(
            value={
                'total': count,
                'critical': critical,
            },
            label='Security Incidents (30d)',
            description='Security events and critical incidents in the last 30 days',
        )
    
    def get_activity_summary(self) -> MetricResult:
        """Get activity summary by role."""
        by_role = self._get_actions_by_role()
        return MetricResult(
            value=by_role,
            label='Actions by Role',
            description='Activity breakdown by user role',
        )
    
    # =========================================================================
    # Private Methods - Ticket Metrics
    # =========================================================================
    
    def _get_tickets_created(self, period: str) -> int:
        """Get ticket creation count for period."""
        start_date = self._today if period == 'today' else self._week_ago
        
        qs = self._query_service.filter_by_date_range(
            start_date=start_date,
            end_date=self._today
        ).filter_by_action(['CREATE']).filter_by_target('ticket')
        
        return qs.count()
    
    def _get_tickets_by_status(self) -> Dict[str, int]:
        """Get ticket counts by status from logs."""
        # This is inferred from action + entity patterns
        return {
            'created': self._get_tickets_created('week'),
            'updated': self._get_tickets_by_action('week', 'UPDATE'),
            'resolved': self._get_tickets_by_action('week', 'RESOLVE'),
        }
    
    def _get_tickets_by_priority(self) -> Dict[str, int]:
        """Get ticket counts by priority (from metadata)."""
        # Would require parsing extra_data for priority
        return {'unknown': 0}
    
    def _get_tickets_by_action(self, period: str, action: str) -> int:
        """Get tickets by specific action."""
        start_date = self._today if period == 'today' else self._week_ago
        
        qs = self._query_service.filter_by_date_range(
            start_date=start_date,
            end_date=self._today
        ).filter_by_action([action]).filter_by_target('ticket')
        
        return qs.count()
    
    # =========================================================================
    # Private Methods - Asset Metrics
    # =========================================================================
    
    def _get_assets_modified(self, period: str) -> int:
        """Get asset modification count."""
        start_date = self._today if period == 'today' else self._week_ago
        
        qs = self._query_service.filter_by_date_range(
            start_date=start_date,
            end_date=self._today
        ).filter_by_target('asset')
        
        return qs.count()
    
    def _get_assets_by_status(self) -> Dict[str, int]:
        """Get asset counts by status."""
        return {
            'modified_week': self._get_assets_modified('week'),
            'assigned': self._get_assets_by_action('ASSIGNED'),
            'returned': self._get_assets_by_action('RETURNED'),
        }
    
    def _get_assets_by_action(self, action: str) -> int:
        """Get assets by specific action."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._week_ago,
            end_date=self._today
        ).filter_by_action([action]).filter_by_target('asset')
        
        return qs.count()
    
    # =========================================================================
    # Private Methods - Security Metrics
    # =========================================================================
    
    def _get_security_incidents(self) -> int:
        """Get security incidents in last 30 days."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._month_ago,
            end_date=self._today
        ).filter_by_category(EventCategory.SECURITY.value)
        
        return qs.count()
    
    def _get_security_by_severity(self) -> Dict[str, int]:
        """Get security incidents by severity."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._month_ago,
            end_date=self._today
        ).filter_by_category(EventCategory.SECURITY.value)
        
        # Aggregate by severity from the queryset
        result = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'UNKNOWN': 0}
        for log in qs[:1000]:  # Limit for performance
            severity = log.severity if hasattr(log, 'severity') else 'UNKNOWN'
            result[severity] = result.get(severity, 0) + 1
        
        return result
    
    def _get_security_by_status(self) -> Dict[str, int]:
        """Get security incidents by status (open, resolved, etc.)."""
        # Status would be inferred from action patterns
        return {'open': self._get_open_critical_count(), 'resolved': 0}
    
    def _get_open_critical_count(self) -> int:
        """Get count of open critical security events."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._month_ago,
            end_date=self._today
        ).filter_by_category(EventCategory.SECURITY.value)
        
        # Count events marked as critical
        count = 0
        for log in qs[:1000]:
            if hasattr(log, 'severity') and log.severity == 'CRITICAL':
                count += 1
        
        return count
    
    # =========================================================================
    # Private Methods - Activity Metrics
    # =========================================================================
    
    def _get_total_actions(self) -> int:
        """Get total actions in period."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._week_ago,
            end_date=self._today
        )
        
        return qs.count()
    
    def _get_actions_by_role(self) -> Dict[str, int]:
        """Get action counts grouped by actor role."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._week_ago,
            end_date=self._today
        )
        
        # Aggregate by actor_role
        result = {}
        for log in qs[:10000]:  # Limit for performance
            role = getattr(log, 'actor_role', 'UNKNOWN') or 'UNKNOWN'
            result[role] = result.get(role, 0) + 1
        
        return result
    
    def _get_actions_by_category(self) -> Dict[str, int]:
        """Get action counts by event category."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._week_ago,
            end_date=self._today
        )
        
        # Aggregate by inferred category
        result = {}
        for log in qs[:10000]:
            category = EventCategory.from_action(log.action).value
            result[category] = result.get(category, 0) + 1
        
        return result
    
    def _get_top_actors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most active users."""
        qs = self._query_service.filter_by_date_range(
            start_date=self._week_ago,
            end_date=self._today
        )
        
        # Aggregate by actor_name
        actor_counts = {}
        for log in qs[:10000]:
            name = getattr(log, 'actor_name', 'Unknown') or 'Unknown'
            if name not in actor_counts:
                actor_counts[name] = {'name': name, 'count': 0}
            actor_counts[name]['count'] += 1
        
        # Sort and limit
        sorted_actors = sorted(
            actor_counts.values(), 
            key=lambda x: x['count'], 
            reverse=True
        )[:limit]
        
        return sorted_actors
    
    # =========================================================================
    # Private Methods - User Metrics
    # =========================================================================
    
    def _get_active_users(self, period: str) -> int:
        """Get count of active users in period."""
        start_date = self._today if period == 'today' else self._week_ago
        
        qs = self._query_service.filter_by_date_range(
            start_date=start_date,
            end_date=self._today
        )
        
        # Count unique actors
        unique_users = set()
        for log in qs[:10000]:
            name = getattr(log, 'actor_name', None)
            if name:
                unique_users.add(name)
        
        return len(unique_users)
    
    def _get_user_activity_summary(self) -> Dict[str, int]:
        """Get user activity summary."""
        return {
            'total_actions': self._get_total_actions(),
            'unique_actors': self._get_active_users('week'),
            'most_active_role': self._get_most_active_role(),
        }
    
    def _get_most_active_role(self) -> str:
        """Get the most active role."""
        by_role = self._get_actions_by_role()
        if not by_role:
            return 'UNKNOWN'
        return max(by_role, key=by_role.get)
    
    # =========================================================================
    # Private Methods - Caching
    # =========================================================================
    
    def _get_cache_key(self, metric_type: str) -> str:
        """Generate cache key for metric."""
        user_id = self._user.id if self._user else 'anonymous'
        return f"{self.CACHE_KEY_PREFIX}:{user_id}:{metric_type}"
    
    def _should_use_cache(self) -> bool:
        """Check if caching should be used for this role."""
        return self._scope_config.get('cache_ttl_seconds', 0) > 0
    
    def _cache_metrics(self, key: str, metrics: DashboardMetrics):
        """Cache metrics with role-specific TTL."""
        ttl = self._scope_config.get('cache_ttl_seconds', self.CACHE_TIMEOUT_DEFAULT)
        cache.set(key, metrics.to_dict(), ttl)
    
    def _dict_to_metrics(self, data: Dict[str, Any]) -> DashboardMetrics:
        """Convert cached dict back to DashboardMetrics."""
        # This is a simplified conversion
        return DashboardMetrics(
            computed_at=datetime.fromisoformat(data['computed_at']),
            period_start=datetime.fromisoformat(data['period_start']),
            period_end=datetime.fromisoformat(data['period_end']),
            tickets_created_today=data['tickets']['created_today'],
            tickets_created_week=data['tickets']['created_week'],
            tickets_by_status=data['tickets']['by_status'],
            tickets_by_priority=data['tickets']['by_priority'],
            assets_modified_today=data['assets']['modified_today'],
            assets_modified_week=data['assets']['modified_week'],
            assets_by_status=data['assets']['by_status'],
            security_incidents_30d=data['security']['incidents_30d'],
            security_by_severity=data['security']['by_severity'],
            security_by_status=data['security']['by_status'],
            open_critical_count=data['security']['open_critical'],
            total_actions_period=data['activity']['total_actions'],
            actions_by_role=data['activity']['by_role'],
            actions_by_category=data['activity']['by_category'],
            top_actors=data['activity']['top_actors'],
            active_users_today=data['users']['active_today'],
            active_users_week=data['users']['active_week'],
            user_activity_summary=data['users']['summary'],
            cache_hit=data['performance']['cache_hit'],
            query_time_ms=data['performance']['query_time_ms'],
        )
    
    def clear_cache(self):
        """Clear cached metrics for this user."""
        cache.delete(self._get_cache_key('all'))


# =============================================================================
# Convenience Functions
# =============================================================================

def get_dashboard_metrics(user=None, role=None) -> DashboardMetrics:
    """
    Convenience function to get all dashboard metrics.
    
    Args:
        user: Django user instance
        role: Role string (optional)
    
    Returns:
        DashboardMetrics instance
    """
    service = DashboardMetricsService(user=user, role=role)
    return service.get_all_metrics()


def get_metrics_for_role(role: str) -> Dict[str, Any]:
    """
    Get metrics summary for a specific role (no user required).
    
    Args:
        role: Role string (SUPERADMIN, IT_ADMIN, etc.)
    
    Returns:
        Dictionary with role-appropriate metrics
    """
    service = DashboardMetricsService(role=role)
    metrics = service.get_all_metrics()
    return metrics.to_dict()
