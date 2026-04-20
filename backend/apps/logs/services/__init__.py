"""
Services package for Activity Logging.

Modules:
    - activity_service: Activity logging (tickets, assets, projects)
    - security_event_service: SecurityEventService — hash-chained security event logging
    - access_policy: Role-based log access control
    - log_query_service: Query-first log filtering

Usage:
    from apps.logs.services import ActivityService, SecurityEventService

    activity_svc = ActivityService()
    activity_svc.log_ticket_created(ticket, request.user, request)

    from apps.logs.services.security_event_service import log_security_event
    log_security_event('LOGIN_FAILURE', 'MEDIUM', request=request)

    from apps.logs.services.access_policy import LogAccessPolicyService
    policy = LogAccessPolicyService(user=request.user)
    logs = policy.filter_queryset(queryset)
"""

from apps.logs.services.activity_service import ActivityService
from apps.logs.services.security_event_service import (
    SecurityEventService,
    SecurityEvent,
    SecurityEventType,
    SecuritySeverity,
    log_security_event,
    verify_log_integrity,
    detect_tampering,
    HashChainManager,
    IntegrityVerifier,
)
from apps.logs.services.access_policy import (
    LogAccessPolicyService,
    LogImmutabilityService,
    ReadOnlyAdminMixin,
    LogCategory,
    AccessLevel,
    AccessPolicy,
    get_log_access_policy,
    can_user_view_logs,
    filter_logs_by_access,
)
from apps.logs.services.log_query_service import LogQueryService

__all__ = [
    'ActivityService',
    'SecurityEventService',
    'SecurityEvent',
    'SecurityEventType',
    'SecuritySeverity',
    'log_security_event',
    'verify_log_integrity',
    'detect_tampering',
    'HashChainManager',
    'IntegrityVerifier',
    'LogAccessPolicyService',
    'LogImmutabilityService',
    'ReadOnlyAdminMixin',
    'LogCategory',
    'AccessLevel',
    'AccessPolicy',
    'get_log_access_policy',
    'can_user_view_logs',
    'filter_logs_by_access',
    'LogQueryService',
]
