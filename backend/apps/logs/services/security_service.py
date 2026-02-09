"""
Security Event Service Layer for IT Management Platform.

Provides high-level operations for security event management,
including creation, tracking, resolution, and dashboard integration.

Usage:
    from apps.logs.services.security_service import SecurityEventService
    
    service = SecurityEventService()
    service.create_security_event(
        event_type='FAILED_LOGIN',
        severity='HIGH',
        title='Multiple failed login attempts',
        description='User attempted to login 5 times with invalid password',
        source_ip='192.168.1.100',
        affected_user=user_instance
    )
"""

import logging
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, timedelta
from uuid import UUID

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Count, Q
from django.conf import settings

from apps.logs.models import SecurityEvent
from apps.logs.dto import (
    SecurityEventDetailDTO,
    SecurityEventSummaryDTO,
    SecurityEventCreateDTO,
    SecurityEventUpdateDTO,
    TimelineEntryDTO,
    TimelineDTO,
)
from apps.logs.enums import SecuritySeverity, SecurityStatus, SecurityEventType

User = get_user_model()

# Named logger for this service
logger = logging.getLogger("logs.service")


def _is_debug_enabled() -> bool:
    """Check if debug logging is enabled.
    
    Returns True only when:
    - DEBUG=True in settings
    - LOGS_DEBUG=True in settings
    """
    return getattr(settings, 'DEBUG', False) and getattr(settings, 'LOGS_DEBUG', False)


# =============================================================================
# Security Event Service
# =============================================================================

class SecurityEventService:
    """
    Service layer for security event operations.
    
    Provides high-level operations for security event
    management and display.
    """
    
    def __init__(self, user: Optional[Any] = None):
        """
        Initialize the security event service.
        
        Args:
            user: Optional user context for the service
        """
        self._user = user
    
    def _get_client_ip(self, request: Optional[Any] = None) -> Optional[str]:
        """Extract client IP from request."""
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    # -------------------------------------------------------------------------
    # Create Methods
    # -------------------------------------------------------------------------
    
    @transaction.atomic
    def create_security_event(
        self,
        event_type: str,
        severity: str,
        title: str,
        description: str,
        source_ip: Optional[str] = None,
        affected_user: Optional[Any] = None,
        request: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SecurityEvent:
        """
        Create a new security event.
        
        Args:
            event_type: Type of security event
            severity: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
            title: Event title
            description: Detailed description
            source_ip: IP address of the source
            affected_user: User affected by the event
            request: Django request for additional context
            metadata: Additional event data
        
        Returns:
            SecurityEvent: The created event
        """
        return SecurityEvent.objects.create(
            event_type=event_type,
            severity=severity,
            status='OPEN',
            title=title,
            description=description,
            affected_user=affected_user,
            source_ip=source_ip or self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500] if request else '',
            request_path=request.path if request else '',
            request_method=request.method if request else '',
            extra_data=metadata or {},
        )
    
    def log_failed_login(
        self,
        username: str,
        source_ip: Optional[str] = None,
        request: Optional[Any] = None,
        attempt_count: int = 1,
    ) -> SecurityEvent:
        """
        Log a failed login attempt.
        
        Args:
            username: Username that failed to login
            source_ip: IP address of the attempt
            request: Django request
            attempt_count: Number of failed attempts
        
        Returns:
            SecurityEvent: The created event
        """
        # Determine severity based on attempt count
        if attempt_count >= 5:
            severity = 'CRITICAL'
        elif attempt_count >= 3:
            severity = 'HIGH'
        else:
            severity = 'MEDIUM'
        
        return self.create_security_event(
            event_type='FAILED_LOGIN',
            severity=severity,
            title=f'Failed login attempt for "{username}"',
            description=f'User "{username}" failed to login. Attempt #{attempt_count}.',
            source_ip=source_ip,
            request=request,
            metadata={'attempted_username': username, 'attempt_count': attempt_count},
        )
    
    def log_brute_force(
        self,
        source_ip: str,
        request: Optional[Any] = None,
        attempt_count: int = 10,
    ) -> SecurityEvent:
        """
        Log a brute force attack detection.
        
        Args:
            source_ip: IP address of the attacker
            request: Django request
            attempt_count: Number of attempts detected
        
        Returns:
            SecurityEvent: The created event
        """
        return self.create_security_event(
            event_type='BRUTE_FORCE',
            severity='CRITICAL',
            title=f'Brute force attack detected from {source_ip}',
            description=f'Multiple failed login attempts ({attempt_count}) detected from IP {source_ip}. This may indicate a brute force attack.',
            source_ip=source_ip,
            request=request,
            metadata={'attempt_count': attempt_count, 'source_ip': source_ip},
        )
    
    def log_unauthorized_access(
        self,
        resource: str,
        source_ip: Optional[str] = None,
        request: Optional[Any] = None,
        user: Optional[Any] = None,
    ) -> SecurityEvent:
        """
        Log an unauthorized access attempt.
        
        Args:
            resource: Resource that was accessed
            source_ip: IP address of the attempt
            request: Django request
            user: User who attempted access
        
        Returns:
            SecurityEvent: The created event
        """
        return self.create_security_event(
            event_type='UNAUTHORIZED_ACCESS',
            severity='HIGH',
            title=f'Unauthorized access attempt on {resource}',
            description=f'User attempted to access {resource} without proper authorization.',
            source_ip=source_ip,
            affected_user=user,
            request=request,
            metadata={'resource': resource},
        )
    
    def log_policy_violation(
        self,
        violation_type: str,
        description: str,
        user: Optional[Any] = None,
        source_ip: Optional[str] = None,
        request: Optional[Any] = None,
    ) -> SecurityEvent:
        """
        Log a policy violation.
        
        Args:
            violation_type: Type of policy violation
            description: Detailed description
            user: User who violated the policy
            source_ip: IP address
            request: Django request
        
        Returns:
            SecurityEvent: The created event
        """
        return self.create_security_event(
            event_type='POLICY_VIOLATION',
            severity='MEDIUM',
            title=f'Policy violation: {violation_type}',
            description=description,
            source_ip=source_ip,
            affected_user=user,
            request=request,
            metadata={'violation_type': violation_type},
        )
    
    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------
    
    def get_open_events(
        self,
        user: Any,
        limit: int = 50,
    ) -> QuerySet:
        """
        Get all open security events.
        
        Args:
            user: User context for permissions
            limit: Maximum number of events
        
        Returns:
            QuerySet: SecurityEvent queryset
        """
        return SecurityEvent.objects.filter(
            status__in=['OPEN', 'INVESTIGATING']
        ).select_related('affected_user', 'assigned_to').order_by('-detected_at')[:limit]
    
    def get_critical_events(
        self,
        user: Any,
        limit: int = 10,
    ) -> QuerySet:
        """
        Get critical security events.
        
        Args:
            user: User context for permissions
            limit: Maximum number of events
        
        Returns:
            QuerySet: SecurityEvent queryset
        """
        return SecurityEvent.objects.filter(
            severity='CRITICAL',
            status__in=['OPEN', 'INVESTIGATING']
        ).select_related('affected_user', 'assigned_to').order_by('-detected_at')[:limit]
    
    def get_events_for_dashboard(
        self,
        user: Any,
        limit: int = 5,
    ) -> List[SecurityEventDetailDTO]:
        """
        Get security events formatted for dashboard display.
        
        Args:
            user: User context for permissions
            limit: Maximum number of events
        
        Returns:
            List[SecurityEventDetailDTO]: List of event DTOs
        """
        events = SecurityEvent.objects.filter(
            status__in=['OPEN', 'INVESTIGATING']
        ).select_related('affected_user', 'assigned_to').order_by('-detected_at')[:limit]
        
        result = []
        for event in events:
            result.append(SecurityEventDetailDTO(
                event_id=event.event_id,
                detected_at=event.detected_at,
                event_type=event.event_type,
                event_type_label=SecurityEventType.get_label(event.event_type),
                severity=event.severity,
                status=event.status,
                title=event.title,
                description=event.description,
                affected_user=event.affected_user.username if event.affected_user else None,
                source_ip=event.source_ip,
                assigned_to=event.assigned_to.username if event.assigned_to else None,
                resolution_notes=event.resolution_notes,
            ))
        
        return result
    
    def get_security_summary(
        self,
        user: Any,
    ) -> SecurityEventSummaryDTO:
        """
        Get security events summary for dashboard.
        
        Args:
            user: User context for permissions
        
        Returns:
            SecurityEventSummaryDTO: Security summary
        """
        # Count by status
        open_count = SecurityEvent.objects.filter(status='OPEN').count()
        investigating_count = SecurityEvent.objects.filter(status='INVESTIGATING').count()
        resolved_count = SecurityEvent.objects.filter(status='RESOLVED').count()
        
        # Count by severity
        critical_count = SecurityEvent.objects.filter(
            severity='CRITICAL',
            status__in=['OPEN', 'INVESTIGATING']
        ).count()
        high_count = SecurityEvent.objects.filter(
            severity='HIGH',
            status__in=['OPEN', 'INVESTIGATING']
        ).count()
        
        # Get recent critical events
        critical_events = self.get_critical_events(user, limit=5)
        
        return SecurityEventSummaryDTO(
            total_open=open_count,
            total_investigating=investigating_count,
            total_resolved=resolved_count,
            total_critical=critical_count,
            total_high=high_count,
            recent_critical=[
                SecurityEventDetailDTO(
                    event_id=e.event_id,
                    detected_at=e.detected_at,
                    event_type=e.event_type,
                    event_type_label=SecurityEventType.get_label(e.event_type),
                    severity=e.severity,
                    status=e.status,
                    title=e.title,
                    description=e.description,
                    affected_user=e.affected_user.username if e.affected_user else None,
                    source_ip=e.source_ip,
                    assigned_to=e.assigned_to.username if e.assigned_to else None,
                    resolution_notes=e.resolution_notes,
                )
                for e in critical_events
            ],
        )
    
    def get_events_by_type(
        self,
        user: Any,
        event_type: str,
        limit: int = 50,
    ) -> QuerySet:
        """
        Get security events by type.
        
        Args:
            user: User context for permissions
            event_type: Type of security event
            limit: Maximum number of events
        
        Returns:
            QuerySet: SecurityEvent queryset
        """
        return SecurityEvent.objects.filter(
            event_type=event_type
        ).select_related('affected_user', 'assigned_to').order_by('-detected_at')[:limit]
    
    def get_events_timeline(
        self,
        user: Any,
        days: int = 30,
        limit: int = 100,
    ) -> TimelineDTO:
        """
        Get security events timeline for charts.
        
        Args:
            user: User context for permissions
            days: Number of days to include
            limit: Maximum number of entries
        
        Returns:
            TimelineDTO: Timeline data
        """
        now = timezone.now()
        start_date = now - timedelta(days=days)
        
        events = SecurityEvent.objects.filter(
            detected_at__gte=start_date
        ).select_related('affected_user', 'assigned_to').order_by('-detected_at')[:limit]
        
        timeline = TimelineDTO()
        
        for event in events:
            entry = TimelineEntryDTO(
                timestamp=event.detected_at,
                entry_type='security',
                title=SecurityEventType.get_label(event.event_type),
                description=event.title,
                icon=self._get_icon_for_event_type(event.event_type),
                icon_color=self._get_icon_color_for_severity(event.severity),
                badge=event.severity,
                badge_color=self._get_badge_color_for_severity(event.severity),
                metadata={
                    'event_id': str(event.event_id),
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'status': event.status,
                    'affected_user': event.affected_user.username if event.affected_user else None,
                },
            )
            timeline.add_entry(entry)
        
        return timeline
    
    # -------------------------------------------------------------------------
    # Update Methods
    # -------------------------------------------------------------------------
    
    @transaction.atomic
    def resolve_event(
        self,
        event_id: UUID,
        resolver: Any,
        notes: str,
    ) -> bool:
        """
        Resolve a security event.
        
        Args:
            event_id: ID of the event to resolve
            resolver: User resolving the event
            notes: Resolution notes
        
        Returns:
            bool: True if successful
        """
        try:
            event = SecurityEvent.objects.get(event_id=event_id)
            event.status = 'RESOLVED'
            event.resolution_notes = notes
            event.resolved_at = timezone.now()
            event.assigned_to = resolver
            event.save()
            return True
        except SecurityEvent.DoesNotExist:
            return False
    
    @transaction.atomic
    def mark_as_false_positive(
        self,
        event_id: UUID,
        marker: Any,
        reason: str,
    ) -> bool:
        """
        Mark a security event as false positive.
        
        Args:
            event_id: ID of the event
            marker: User marking as false positive
            reason: Reason for marking as false positive
        
        Returns:
            bool: True if successful
        """
        try:
            event = SecurityEvent.objects.get(event_id=event_id)
            event.status = 'FALSE_POSITIVE'
            event.false_positive_reason = reason
            event.assigned_to = marker
            event.resolved_at = timezone.now()
            event.save()
            return True
        except SecurityEvent.DoesNotExist:
            return False
    
    @transaction.atomic
    def assign_event(
        self,
        event_id: UUID,
        assignee: Any,
        assigner: Any,
    ) -> bool:
        """
        Assign a security event to a user.
        
        Args:
            event_id: ID of the event
            assignee: User to assign the event to
            assigner: User making the assignment
        
        Returns:
            bool: True if successful
        """
        try:
            event = SecurityEvent.objects.get(event_id=event_id)
            event.assigned_to = assignee
            if event.status == 'OPEN':
                event.status = 'INVESTIGATING'
            event.save()
            return True
        except SecurityEvent.DoesNotExist:
            return False
    
    @transaction.atomic
    def escalate_event(
        self,
        event_id: UUID,
        escalator: Any,
        reason: str,
        assignee: Optional[Any] = None,
    ) -> bool:
        """
        Escalate a security event.
        
        Args:
            event_id: ID of the event
            escalator: User escalating the event
            reason: Reason for escalation
            assignee: Optional user to assign the escalated event to
        
        Returns:
            bool: True if successful
        """
        try:
            event = SecurityEvent.objects.get(event_id=event_id)
            
            # Escalate severity
            if event.severity == 'LOW':
                event.severity = 'MEDIUM'
            elif event.severity == 'MEDIUM':
                event.severity = 'HIGH'
            elif event.severity == 'HIGH':
                event.severity = 'CRITICAL'
            
            event.status = 'INVESTIGATING'
            event.assigned_to = assignee
            event.extra_data = event.extra_data or {}
            event.extra_data['escalation'] = {
                'escalated_by': escalator.username,
                'escalated_at': timezone.now().isoformat(),
                'reason': reason,
            }
            event.save()
            return True
        except SecurityEvent.DoesNotExist:
            return False
    
    # -------------------------------------------------------------------------
    # Internal Methods
    # -------------------------------------------------------------------------
    
    def _get_icon_for_event_type(self, event_type: str) -> str:
        """Get icon class for an event type."""
        icons = {
            'FAILED_LOGIN': 'fa-exclamation-triangle',
            'BRUTE_FORCE': 'fa-skull-crossbones',
            'UNAUTHORIZED_ACCESS': 'fa-ban',
            'PRIVILEGE_ESCALATION': 'fa-level-up-alt',
            'DATA_BREACH': 'fa-database',
            'MALWARE_DETECTION': 'fa-virus',
            'SUSPICIOUS_ACTIVITY': 'fa-eye',
            'POLICY_VIOLATION': 'fa-exclamation-circle',
            'UNAUTHORIZED_API_CALL': 'fa-code',
            'SESSION_HIJACKING': 'fa-user-secret',
            'SQL_INJECTION': 'fa-database',
            'XSS_ATTEMPT': 'fa-code',
            'CSRF_VIOLATION': 'fa-shield-alt',
            'FILE_UPLOAD_ABUSE': 'fa-file-upload',
            'OTHER': 'fa-exclamation',
        }
        return icons.get(event_type, 'fa-shield-alt')
    
    def _get_icon_color_for_severity(self, severity: str) -> str:
        """Get icon color for severity level."""
        colors = {
            'LOW': 'text-blue-500',
            'MEDIUM': 'text-yellow-500',
            'HIGH': 'text-orange-500',
            'CRITICAL': 'text-red-600',
        }
        return colors.get(severity, 'text-gray-500')
    
    def _get_badge_color_for_severity(self, severity: str) -> str:
        """Get badge color class for severity level."""
        colors = {
            'LOW': 'bg-blue-100 text-blue-800',
            'MEDIUM': 'bg-yellow-100 text-yellow-800',
            'HIGH': 'bg-orange-100 text-orange-800',
            'CRITICAL': 'bg-red-100 text-red-800',
        }
        return colors.get(severity, 'bg-gray-100 text-gray-800')
