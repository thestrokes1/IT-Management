"""
Security Event Service

Provides structured security event logging for:
- Login success/failure
- Permission denials
- Role changes
- Privilege escalations
- Data exports

Usage:
    from apps.logs.services.security_event_service import log_security_event
    
    # Log a security event
    log_security_event(
        event_type='LOGIN_FAILURE',
        severity='HIGH',
        actor=request.user,
        details={'reason': 'invalid_password', 'ip': request.ip},
        request=request
    )
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger(__name__)

User = get_user_model()


# =============================================================================
# Security Event Types
# =============================================================================

class SecurityEventType(Enum):
    """Types of security events to log."""
    LOGIN_SUCCESS = 'LOGIN_SUCCESS'
    LOGIN_FAILURE = 'LOGIN_FAILURE'
    LOGOUT = 'LOGOUT'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    ROLE_CHANGED = 'ROLE_CHANGED'
    PRIVILEGE_ESCALATION = 'PRIVILEGE_ESCALATION'
    DATA_EXPORT = 'DATA_EXPORT'
    BULK_DELETE = 'BULK_DELETE'
    SETTINGS_CHANGE = 'SETTINGS_CHANGE'
    API_ACCESS = 'API_ACCESS'
    SUSPICIOUS_ACTIVITY = 'SUSPICIOUS_ACTIVITY'
    PASSWORD_CHANGE = 'PASSWORD_CHANGE'
    PASSWORD_RESET = 'PASSWORD_RESET'
    ACCOUNT_LOCKED = 'ACCOUNT_LOCKED'
    ACCOUNT_UNLOCKED = 'ACCOUNT_UNLOCKED'


class SecuritySeverity(Enum):
    """Severity levels for security events."""
    LOW = 'LOW'
    MEDIUM = 'MEDIUM'
    HIGH = 'HIGH'
    CRITICAL = 'CRITICAL'


# =============================================================================
# Security Event Model (if needed)
# =============================================================================

class SecurityEventMixin:
    """Mixin for models that can be security event sources."""
    
    @property
    def security_event_type(self) -> str:
        raise NotImplementedError
    
    @property
    def security_event_details(self) -> Dict[str, Any]:
        return {}


# =============================================================================
# Security Event DTO
# =============================================================================

@dataclass
class SecurityEvent:
    """
    Represents a security event for logging.
    """
    event_type: str
    severity: str
    timestamp: datetime = field(default_factory=timezone.now)
    actor_id: Optional[int] = None
    actor_username: Optional[str] = None
    actor_role: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    hash_chain: Optional[str] = None
    previous_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'severity': self.severity,
            'timestamp': self.timestamp.isoformat(),
            'actor_id': self.actor_id,
            'actor_username': self.actor_username,
            'actor_role': self.actor_role,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'details': self.details,
            'target_type': self.target_type,
            'target_id': self.target_id,
            'hash_chain': self.hash_chain,
        }


# =============================================================================
# Hash Chain Management
# =============================================================================

class HashChainManager:
    """
    Manages hash chaining for tamper-evident logging.
    
    Each log entry contains:
    - previous_hash: Hash of the previous entry
    - current_hash: Hash of this entry + previous hash
    
    This creates a chain where any modification breaks the hash chain.
    """
    
    CACHE_KEY_LAST_HASH = 'security_event_last_hash'
    
    def __init__(self):
        self._last_hash = None
    
    def get_last_hash(self) -> str:
        """
        Get the hash of the last logged event.
        Uses cache for performance.
        """
        from django.core.cache import cache
        
        cached = cache.get(self.CACHE_KEY_LAST_HASH)
        if cached:
            return cached
        return ''
    
    def set_last_hash(self, hash_value: str):
        """Store the hash of the most recent event."""
        from django.core.cache import cache
        
        cache.set(self.CACHE_KEY_LAST_HASH, hash_value, timeout=None)
        self._last_hash = hash_value
    
    def compute_hash(self, event: SecurityEvent, previous_hash: str) -> str:
        """
        Compute hash for an event including previous hash.
        
        Creates: SHA256(previous_hash + event_data)
        """
        # Serialize event data
        event_data = {
            'event_type': event.event_type,
            'severity': event.severity,
            'timestamp': event.timestamp.isoformat(),
            'actor_id': event.actor_id,
            'actor_username': event.actor_username,
            'details': event.details,
            'target_type': event.target_type,
            'target_id': event.target_id,
        }
        
        # Create hash input
        hash_input = previous_hash + json.dumps(event_data, sort_keys=True)
        
        # Compute SHA256 hash
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def create_event_with_chain(self, event: SecurityEvent) -> SecurityEvent:
        """
        Add hash chain information to an event.
        """
        previous_hash = self.get_last_hash()
        current_hash = self.compute_hash(event, previous_hash)
        
        event.previous_hash = previous_hash
        event.hash_chain = current_hash
        
        # Update last hash
        self.set_last_hash(current_hash)
        
        return event


# =============================================================================
# Integrity Verification
# =============================================================================

class IntegrityVerifier:
    """
    Utility for verifying log integrity.
    
    Can verify:
    - Individual log integrity
    - Chain integrity (hash chain)
    - Complete audit trail
    """
    
    @staticmethod
    def verify_event_hash(event: SecurityEvent, previous_hash: str) -> bool:
        """
        Verify that an event's hash is correct.
        """
        # Recreate hash input
        event_data = {
            'event_type': event.event_type,
            'severity': event.severity,
            'timestamp': event.timestamp.isoformat(),
            'actor_id': event.actor_id,
            'actor_username': event.actor_username,
            'details': event.details,
            'target_type': event.target_type,
            'target_id': event.target_id,
        }
        
        hash_input = previous_hash + json.dumps(event_data, sort_keys=True)
        expected_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        return event.hash_chain == expected_hash
    
    @staticmethod
    def verify_chain(events: List[SecurityEvent]) -> Dict[str, Any]:
        """
        Verify the integrity of a chain of events.
        
        Returns dict with:
        - is_valid: bool
        - broken_at: index of first broken link, or None
        - verified_count: number of events verified
        """
        if not events:
            return {'is_valid': True, 'broken_at': None, 'verified_count': 0}
        
        previous_hash = ''
        verified_count = 0
        
        for i, event in enumerate(events):
            # Verify this event
            if not IntegrityVerifier.verify_event_hash(event, previous_hash):
                return {
                    'is_valid': False,
                    'broken_at': i,
                    'verified_count': verified_count,
                    'event_id': getattr(event, 'id', None),
                }
            
            previous_hash = event.hash_chain or ''
            verified_count += 1
        
        return {
            'is_valid': True,
            'broken_at': None,
            'verified_count': verified_count,
        }
    
    @staticmethod
    def detect_tampering(events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """
        Detect any tampering in a list of events.
        
        Returns list of tampering incidents found.
        """
        incidents = []
        chain_result = IntegrityVerifier.verify_chain(events)
        
        if not chain_result['is_valid']:
            broken_at = chain_result['broken_at']
            incidents.append({
                'type': 'CHAIN_BROKEN',
                'location': broken_at,
                'message': f'Hash chain broken at event {broken_at}',
                'severity': 'CRITICAL',
            })
        
        # Check for time anomalies
        for i in range(1, len(events)):
            prev_time = events[i-1].timestamp
            curr_time = events[i].timestamp
            
            # Events shouldn't go backwards in time
            if curr_time < prev_time:
                incidents.append({
                    'type': 'TIMESTAMP_REGRESSION',
                    'location': i,
                    'message': f'Timestamp regression at event {i}',
                    'severity': 'HIGH',
                })
        
        return incidents


# =============================================================================
# Security Event Service
# =============================================================================

class SecurityEventService:
    """
    Service for logging and managing security events.
    
    Features:
    - Structured security event logging
    - Hash chaining for tamper evidence
    - Automatic severity inference
    - IP and user agent capture
    """
    
    _hash_chain_manager = HashChainManager()
    
    @classmethod
    def log_event(
        cls,
        event_type: str,
        severity: str,
        actor=None,
        request=None,
        details: Optional[Dict[str, Any]] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
    ) -> SecurityEvent:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event (see SecurityEventType)
            severity: Severity level (see SecuritySeverity)
            actor: User performing the action
            request: HTTP request for metadata
            details: Additional event details
            target_type: Type of target entity
            target_id: ID of target entity
        
        Returns:
            SecurityEvent that was logged
        """
        # Build event
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            actor_id=actor.id if actor else None,
            actor_username=actor.username if actor else 'anonymous',
            actor_role=getattr(actor, 'role', None) if actor else None,
            ip_address=cls._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '') if request else '',
            details=details or {},
            target_type=target_type,
            target_id=target_id,
        )
        
        # Add hash chain
        event = cls._hash_chain_manager.create_event_with_chain(event)
        
        # Log to Django logger
        log_level = cls._get_log_level(severity)
        logger.log(
            log_level,
            f"SECURITY EVENT: {event_type} - {actor.username if actor else 'anonymous'}",
            extra={
                'event_data': event.to_dict(),
                'security_event': True,
            }
        )
        
        # Optionally save to database
        cls._save_event(event)
        
        return event
    
    @classmethod
    def log_login_success(cls, user, request=None, details: Optional[Dict] = None):
        """Log successful login."""
        return cls.log_event(
            event_type=SecurityEventType.LOGIN_SUCCESS.value,
            severity=SecuritySeverity.LOW.value,
            actor=user,
            request=request,
            details=details or {},
        )
    
    @classmethod
    def log_login_failure(cls, username, request=None, reason='unknown', details: Optional[Dict] = None):
        """Log failed login attempt."""
        return cls.log_event(
            event_type=SecurityEventType.LOGIN_FAILURE.value,
            severity=SecuritySeverity.MEDIUM.value,
            actor=None,  # No user for failed login
            request=request,
            details=details or {
                'attempted_username': username,
                'failure_reason': reason,
            },
        )
    
    @classmethod
    def log_permission_denied(cls, user, resource, action, request=None):
        """Log permission denial."""
        return cls.log_event(
            event_type=SecurityEventType.PERMISSION_DENIED.value,
            severity=SecuritySeverity.HIGH.value,
            actor=user,
            request=request,
            details={
                'resource': resource,
                'action': action,
            },
        )
    
    @classmethod
    def log_role_change(cls, admin_user, target_user, old_role, new_role, request=None):
        """Log role change for a user."""
        return cls.log_event(
            event_type=SecurityEventType.ROLE_CHANGED.value,
            severity=SecuritySeverity.HIGH.value,
            actor=admin_user,
            request=request,
            details={
                'target_user_id': target_user.id,
                'target_username': target_user.username,
                'old_role': old_role,
                'new_role': new_role,
            },
            target_type='user',
            target_id=target_user.id,
        )
    
    @classmethod
    def log_privilege_escalation(cls, user, attempted_action, request=None):
        """Log privilege escalation attempt."""
        return cls.log_event(
            event_type=SecurityEventType.PRIVILEGE_ESCALATION.value,
            severity=SecuritySeverity.CRITICAL.value,
            actor=user,
            request=request,
            details={
                'attempted_action': attempted_action,
            },
        )
    
    @classmethod
    def log_data_export(cls, user, export_type, record_count, filters, request=None):
        """Log data export action."""
        return cls.log_event(
            event_type=SecurityEventType.DATA_EXPORT.value,
            severity=SecuritySeverity.MEDIUM.value,
            actor=user,
            request=request,
            details={
                'export_type': export_type,
                'record_count': record_count,
                'filters_applied': filters,
            },
        )
    
    @classmethod
    def log_bulk_operation(cls, user, operation_type, affected_count, request=None):
        """Log bulk delete or update operation."""
        return cls.log_event(
            event_type=SecurityEventType.BULK_DELETE.value,
            severity=SecuritySeverity.HIGH.value,
            actor=user,
            request=request,
            details={
                'operation_type': operation_type,
                'affected_count': affected_count,
            },
        )
    
    @classmethod
    def log_settings_change(cls, user, setting_name, old_value, new_value, request=None):
        """Log system settings change."""
        return cls.log_event(
            event_type=SecurityEventType.SETTINGS_CHANGE.value,
            severity=SecuritySeverity.HIGH.value,
            actor=user,
            request=request,
            details={
                'setting_name': setting_name,
                'old_value': '***',  # Don't log actual values for security
                'new_value': '***',
            },
        )
    
    @classmethod
    def log_suspicious_activity(cls, user, activity_type, evidence, request=None):
        """Log suspicious activity for investigation."""
        return cls.log_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY.value,
            severity=SecuritySeverity.CRITICAL.value,
            actor=user,
            request=request,
            details={
                'activity_type': activity_type,
                'evidence': evidence,
            },
        )
    
    @classmethod
    def get_recent_events(cls, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent security events from the activity log.
        
        Args:
            limit: Maximum number of events to return (default: 10)
        
        Returns:
            List of dictionaries containing security event information
        """
        try:
            from apps.logs.models import ActivityLog
            
            # Query for security events, ordered by timestamp descending
            security_logs = ActivityLog.objects.filter(
                action='SECURITY_EVENT'
            ).order_by('-timestamp')[:limit]
            
            # Convert to dictionaries for template rendering
            events = []
            for log in security_logs:
                events.append({
                    'log_id': str(log.log_id),
                    'timestamp': log.timestamp,
                    'actor_name': log.actor_name,
                    'actor_role': log.actor_role,
                    'action': log.action,
                    'level': log.level,
                    'description': log.description,
                    'event_type': log.event_type or log.action,
                    'entity_type': log.entity_type,
                    'entity_id': log.entity_id,
                    'severity': log.severity or log.level,
                    'is_security_event': True,
                })
            
            return events
        except Exception as e:
            logger.error(f"Error fetching recent security events: {e}")
            return []
    
    # =========================================================================
    # Private Methods
    # =========================================================================
    
    @staticmethod
    def _get_client_ip(request) -> str:
        """Extract client IP from request."""
        if not request:
            return ''
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
    
    @staticmethod
    def _get_log_level(severity: str) -> int:
        """Map severity to log level."""
        level_map = {
            SecuritySeverity.LOW.value: logging.INFO,
            SecuritySeverity.MEDIUM.value: logging.WARNING,
            SecuritySeverity.HIGH.value: logging.ERROR,
            SecuritySeverity.CRITICAL.value: logging.CRITICAL,
        }
        return level_map.get(severity, logging.INFO)
    
    @staticmethod
    def _save_event(event: SecurityEvent):
        """
        Save event to database if ActivityLog model supports it.
        
        This is optional - events are always logged to Django logger.
        """
        try:
            from apps.logs.models import ActivityLog
            
            # Create ActivityLog entry
            ActivityLog.objects.create(
                action=event.event_type,
                level=event.severity,
                actor_id=event.actor_id,
                actor_name=event.actor_username,
                actor_role=event.actor_role,
                ip_address=event.ip_address,
                description=json.dumps(event.details),
                extra_data={
                    **event.details,
                    'security_event': True,
                    'hash_chain': event.hash_chain,
                },
            )
        except Exception as e:
            # Don't fail if database save fails
            logger.error(f"Failed to save security event to database: {e}")


# =============================================================================
# Convenience Functions
# =============================================================================

def log_security_event(
    event_type: str,
    severity: str,
    actor=None,
    request=None,
    details: Optional[Dict] = None,
):
    """
    Convenience function to log a security event.
    
    Usage:
        from apps.logs.services.security_event_service import log_security_event
        
        log_security_event(
            event_type='LOGIN_FAILURE',
            severity='MEDIUM',
            actor=request.user,
            request=request,
            details={'reason': 'invalid_password'}
        )
    """
    return SecurityEventService.log_event(
        event_type=event_type,
        severity=severity,
        actor=actor,
        request=request,
        details=details,
    )


def verify_log_integrity(events: List[SecurityEvent]) -> Dict[str, Any]:
    """
    Verify integrity of a list of security events.
    """
    return IntegrityVerifier.verify_chain(events)


def detect_tampering(events: List[SecurityEvent]) -> List[Dict[str, Any]]:
    """
    Detect tampering in security events.
    """
    return IntegrityVerifier.detect_tampering(events)
