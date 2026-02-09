"""
Services package for Activity Logging.

Provides high-level service operations for activity logging,
security event management, and access control.

Modules:
    - activity_service: Activity logging operations
    - security_service: Security event management
    - security_event_service: Structured security events with hash chaining
    - access_policy: Role-based log access control
    - log_query_service: Query-first log filtering
    - event_adapter: Event normalization and adaptation

Usage:
    from apps.logs.services import ActivityService, SecurityEventService
    
    # Activity logging
    activity_svc = ActivityService()
    activity_svc.log_ticket_created(ticket, request.user, request)
    
    # Security events with hash chaining
    from apps.logs.services.security_event_service import log_security_event
    log_security_event('LOGIN_FAILURE', 'MEDIUM', request=request)
    
    # Access control
    from apps.logs.services.access_policy import LogAccessPolicyService
    policy = LogAccessPolicyService(user=request.user)
    logs = policy.filter_queryset(queryset)
"""

from apps.logs.services.activity_service import ActivityService
from apps.logs.services.security_service import SecurityEventService
from apps.logs.services.security_event_service import (
    SecurityEventService as NewSecurityEventService,
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
from apps.logs.services.event_adapter import EventAdapter, adapt_log, adapt_logs

__all__ = [
    # Original services
    'ActivityService',
    'SecurityEventService',
    
    # New security event service
    'NewSecurityEventService',
    'SecurityEvent',
    'SecurityEventType',
    'SecuritySeverity',
    'log_security_event',
    'verify_log_integrity',
    'detect_tampering',
    'HashChainManager',
    'IntegrityVerifier',
    
    # Access policy
    'LogAccessPolicyService',
    'LogImmutabilityService',
    'ReadOnlyAdminMixin',
    'LogCategory',
    'AccessLevel',
    'AccessPolicy',
    'get_log_access_policy',
    'can_user_view_logs',
    'filter_logs_by_access',
    
    # Query service
    'LogQueryService',
    
    # Event adapter
    'EventAdapter',
    'adapt_log',
    'adapt_logs',
]
