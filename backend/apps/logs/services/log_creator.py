"""
Centralized Log Creation Service for IT Management Platform.

Provides a clean, transaction-safe API for creating activity logs.
All actor information is captured at log creation time, ensuring logs
remain readable even if users are deleted.

Architectural Principles:
- Clean Architecture: Service in application layer, uses domain models
- Immutable Data: Actor info captured once, never dereferenced from FK
- Transaction Safe: Can be used inside on_commit callbacks
- Type Safe: Enforces severity and intent enums

Usage:
    from apps.logs.services.log_creator import LogCreator, LogSeverity, LogIntent
    
    # User action
    LogCreator.log(
        actor=request.user,
        action='TICKET_CREATED',
        target_type='ticket',
        target_id=ticket.id,
        target_name=str(ticket),
        description='Created ticket',
        severity=LogSeverity.INFO,
        intent=LogIntent.WORKFLOW,
        extra_data={'priority': 'HIGH'},
    )
    
    # System action (no user)
    LogCreator.log(
        actor=None,
        action='BATCH_PROCESS_COMPLETED',
        target_type='batch_job',
        target_id=job.id,
        target_name='Nightly Batch Job',
        description='Nightly data sync completed',
        severity=LogSeverity.INFO,
        intent=LogIntent.SYSTEM,
    )
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, Type

from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.http import HttpRequest

from apps.logs.models import ActivityLog, LogCategory

User = get_user_model()
logger = logging.getLogger("logs.creator")


class LogSeverity(str, Enum):
    """Severity levels for activity logs."""
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    SECURITY = 'SECURITY'


class LogIntent(str, Enum):
    """Intent/purpose of the logged action."""
    WORKFLOW = 'workflow'
    SLA_RISK = 'sla_risk'
    SECURITY = 'security'
    SYSTEM = 'system'


class LogAction(str, Enum):
    """Common log actions for consistency."""
    # Ticket actions
    TICKET_CREATED = 'TICKET_CREATED'
    TICKET_UPDATED = 'TICKET_UPDATED'
    TICKET_ASSIGNED = 'TICKET_ASSIGNED'
    TICKET_RESOLVED = 'TICKET_RESOLVED'
    TICKET_REOPENED = 'TICKET_REOPENED'
    TICKET_CLOSED = 'TICKET_CLOSED'
    
    # Asset actions
    ASSET_CREATED = 'ASSET_CREATED'
    ASSET_UPDATED = 'ASSET_UPDATED'
    ASSET_ASSIGNED = 'ASSET_ASSIGNED'
    ASSET_RETURNED = 'ASSET_RETURNED'
    
    # Project actions
    PROJECT_CREATED = 'PROJECT_CREATED'
    PROJECT_UPDATED = 'PROJECT_UPDATED'
    PROJECT_COMPLETED = 'PROJECT_COMPLETED'
    
    # User actions
    USER_CREATED = 'USER_CREATED'
    USER_LOGIN = 'USER_LOGIN'
    USER_LOGOUT = 'USER_LOGOUT'
    USER_ROLE_CHANGED = 'USER_ROLE_CHANGED'
    
    # System actions
    SYSTEM_STARTUP = 'SYSTEM_STARTUP'
    SYSTEM_SHUTDOWN = 'SYSTEM_SHUTDOWN'
    BATCH_PROCESS_STARTED = 'BATCH_PROCESS_STARTED'
    BATCH_PROCESS_COMPLETED = 'BATCH_PROCESS_COMPLETED'
    DATA_IMPORT = 'DATA_IMPORT'
    DATA_EXPORT = 'DATA_EXPORT'
    
    # Security actions
    SECURITY_ALERT = 'SECURITY_ALERT'
    FAILED_LOGIN = 'FAILED_LOGIN'
    UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS'


@dataclass
class LogContext:
    """Optional request context for log enrichment."""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    session_key: Optional[str] = None
    
    @classmethod
    def from_request(cls, request: Optional[HttpRequest]) -> 'LogContext':
        """Create context from Django request object."""
        if not request:
            return cls()
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip_address = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
        
        return cls(
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT'),
            request_path=request.path,
            request_method=request.method,
            session_key=request.session.session_key if hasattr(request, 'session') else None,
        )


class LogCreator:
    """
    Centralized service for creating activity logs.
    
    Key Features:
    - Captures actor info at creation time (immutable)
    - Supports system-generated logs (actor=None)
    - Enforces severity and intent enums
    - Transaction-safe (can be used in on_commit)
    - Rich metadata support via extra_data
    """
    
    # Default category for logs (lazy loaded)
    _default_category: Optional[LogCategory] = None
    
    @classmethod
    def log(
        cls,
        *,
        actor: Optional[User],
        action: str,
        target_type: str,
        target_id: Optional[int],
        target_name: str,
        description: str,
        severity: LogSeverity = LogSeverity.INFO,
        intent: LogIntent = LogIntent.WORKFLOW,
        extra_data: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None,
        level: str = 'INFO',
    ) -> ActivityLog:
        """
        Create an activity log entry.
        
        This is the primary method for creating logs. All actor information
        is captured at creation time, making logs immune to user deletion.
        
        Args:
            actor: The user performing the action (None for system events)
            action: The action performed (e.g., 'TICKET_CREATED')
            target_type: Type of affected entity ('ticket', 'asset', 'user', etc.)
            target_id: ID of the affected entity (None if no specific entity)
            target_name: Human-readable name of the target
            description: Human-readable description of the action
            severity: Severity level (INFO, WARNING, ERROR, SECURITY)
            intent: Intent/purpose (workflow, sla_risk, security, system)
            extra_data: Additional metadata as key-value pairs
            context: Request context for enrichment (IP, user agent, etc.)
            level: Legacy log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            
        Returns:
            ActivityLog: The created log entry
            
        Example:
            # User creates a ticket
            LogCreator.log(
                actor=request.user,
                action='TICKET_CREATED',
                target_type='ticket',
                target_id=ticket.id,
                target_name=f"Ticket #{ticket.id}: {ticket.title}",
                description='Created new support ticket',
                severity=LogSeverity.INFO,
                intent=LogIntent.WORKFLOW,
                extra_data={'priority': ticket.priority, 'category': str(ticket.category)},
                context=LogContext.from_request(request),
            )
            
            # System event (no user)
            LogCreator.log(
                actor=None,
                action='BATCH_PROCESS_COMPLETED',
                target_type='batch_job',
                target_id=job.id,
                target_name='Nightly Data Sync',
                description='Automated data synchronization completed',
                severity=LogSeverity.INFO,
                intent=LogIntent.SYSTEM,
                extra_data={'records_processed': 1500, 'duration_seconds': 45},
            )
        """
        # Resolve actor information at creation time
        actor_type, actor_id, actor_name, actor_role = cls._resolve_actor(actor)
        
        # Build metadata with actor info embedded
        metadata = cls._build_metadata(actor_id, actor_name, actor_role, extra_data)
        
        # Get request context
        ctx = context or LogContext()
        
        # Get or create default category
        category = cls._get_default_category()
        
        try:
            log = ActivityLog.objects.create(
                # Actor information - IMMUTABLE, captured at creation time
                actor_type=actor_type,
                actor_id=actor_id,
                actor_name=actor_name,
                actor_role=actor_role,
                
                # Event information
                event_type=action,
                severity=severity.value,
                intent=intent.value,
                
                # Entity information
                entity_type=target_type,
                entity_id=target_id,
                
                # Legacy FK (deprecated but kept for compatibility)
                user=actor,
                
                # Log content
                action=action,
                level=level,
                title=description,
                description=description,
                model_name=target_type,
                object_id=target_id,
                object_repr=target_name,
                
                # Request context
                ip_address=ctx.ip_address,
                user_agent=ctx.user_agent,
                request_path=ctx.request_path,
                request_method=ctx.request_method,
                session_key=ctx.session_key,
                
                # Additional data
                category=category,
                extra_data=metadata,
            )
            
            return log
            
        except Exception as e:
            logger.error(
                f"Failed to create activity log: action={action}, "
                f"target_type={target_type}, target_id={target_id}"
            )
            logger.exception(e)
            raise
    
    @classmethod
    def log_user_action(
        cls,
        actor: User,
        action: str,
        target_user: User,
        description: str,
        severity: LogSeverity = LogSeverity.INFO,
        intent: LogIntent = LogIntent.WORKFLOW,
        extra_data: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None,
    ) -> ActivityLog:
        """
        Convenience method for logging user-related actions.
        
        Example:
            LogCreator.log_user_action(
                actor=admin_user,
                action='USER_ROLE_CHANGED',
                target_user=target_user,
                description='Changed user role from TECHNICIAN to MANAGER',
                extra_data={'old_role': 'TECHNICIAN', 'new_role': 'MANAGER'},
            )
        """
        return cls.log(
            actor=actor,
            action=action,
            target_type='user',
            target_id=target_user.id,
            target_name=target_user.username,
            description=description,
            severity=severity,
            intent=intent,
            extra_data=extra_data,
            context=context,
        )
    
    @classmethod
    def log_ticket_action(
        cls,
        actor: Optional[User],
        action: str,
        ticket_id: int,
        ticket_title: str,
        description: str,
        severity: LogSeverity = LogSeverity.INFO,
        intent: LogIntent = LogIntent.WORKFLOW,
        extra_data: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None,
    ) -> ActivityLog:
        """
        Convenience method for logging ticket-related actions.
        
        Example:
            LogCreator.log_ticket_action(
                actor=request.user,
                action='TICKET_ASSIGNED',
                ticket_id=ticket.id,
                ticket_title=ticket.title,
                description='Assigned ticket to technician',
                extra_data={'assignee_id': technician.id, 'assignee_name': technician.username},
            )
        """
        return cls.log(
            actor=actor,
            action=action,
            target_type='ticket',
            target_id=ticket_id,
            target_name=f"Ticket #{ticket_id}: {ticket_title}",
            description=description,
            severity=severity,
            intent=intent,
            extra_data=extra_data,
            context=context,
        )
    
    @classmethod
    def log_asset_action(
        cls,
        actor: Optional[User],
        action: str,
        asset_id: int,
        asset_name: str,
        description: str,
        severity: LogSeverity = LogSeverity.INFO,
        intent: LogIntent = LogIntent.WORKFLOW,
        extra_data: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None,
    ) -> ActivityLog:
        """
        Convenience method for logging asset-related actions.
        """
        return cls.log(
            actor=actor,
            action=action,
            target_type='asset',
            target_id=asset_id,
            target_name=f"Asset #{asset_id}: {asset_name}",
            description=description,
            severity=severity,
            intent=intent,
            extra_data=extra_data,
            context=context,
        )
    
    @classmethod
    def log_system_event(
        cls,
        action: str,
        target_type: str,
        target_id: Optional[int],
        target_name: str,
        description: str,
        severity: LogSeverity = LogSeverity.INFO,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> ActivityLog:
        """
        Convenience method for logging system-generated events.
        
        System events have actor=None and actor_role='SYSTEM'.
        
        Example:
            LogCreator.log_system_event(
                action='BATCH_PROCESS_COMPLETED',
                target_type='batch_job',
                target_id=job.id,
                target_name='Nightly Backup',
                description='Automated backup completed successfully',
                severity=LogSeverity.INFO,
                extra_data={'files_backed_up': 150, 'total_size_gb': 5.2},
            )
        """
        return cls.log(
            actor=None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            description=description,
            severity=severity,
            intent=LogIntent.SYSTEM,
            extra_data=extra_data,
        )
    
    @classmethod
    def log_security_event(
        cls,
        actor: Optional[User],
        action: str,
        target_type: str,
        target_id: Optional[int],
        target_name: str,
        description: str,
        severity: LogSeverity = LogSeverity.SECURITY,
        extra_data: Optional[Dict[str, Any]] = None,
        context: Optional[LogContext] = None,
    ) -> ActivityLog:
        """
        Convenience method for logging security-related events.
        
        Security events automatically use severity=SECURITY.
        
        Example:
            LogCreator.log_security_event(
                actor=None,  # Unknown user
                action='FAILED_LOGIN',
                target_type='user',
                target_id=user.id if user else None,
                target_name=username,
                description='Failed login attempt - invalid password',
                extra_data={'ip_address': '192.168.1.100', 'attempts': 3},
            )
        """
        return cls.log(
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            description=description,
            severity=LogSeverity.SECURITY,
            intent=LogIntent.SECURITY,
            extra_data=extra_data,
            context=context,
        )
    
    # =========================================================================
    # Internal helper methods
    # =========================================================================
    
    @classmethod
    def _resolve_actor(cls, actor: Optional[User]) -> tuple:
        """
        Resolve actor information at log creation time.
        
        Returns:
            tuple: (actor_type, actor_id, actor_name, actor_role)
        """
        if actor is None:
            # System-generated event
            return ('system', None, 'System', 'SYSTEM')
        
        # User-generated event
        actor_id = str(actor.id)
        actor_name = getattr(actor, 'username', None) or 'Unknown'
        actor_role = getattr(actor, 'role', 'VIEWER') or 'VIEWER'
        
        # Determine actor type
        if getattr(actor, 'is_authenticated', False):
            actor_type = 'user'
        else:
            actor_type = 'system'
        
        return (actor_type, actor_id, actor_name, actor_role)
    
    @classmethod
    def _build_metadata(
        cls,
        actor_id: Optional[str],
        actor_name: str,
        actor_role: str,
        extra_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build metadata dictionary with actor info embedded.
        
        Actor information is embedded in extra_data for backward
        compatibility with existing queries.
        """
        metadata = {
            'actor_id': actor_id,
            'actor_username': actor_name,
            'actor_role': actor_role,
        }
        
        if extra_data:
            metadata.update(extra_data)
        
        return metadata
    
    @classmethod
    def _get_default_category(cls) -> Optional[LogCategory]:
        """Get or create the default log category."""
        if cls._default_category is not None:
            return cls._default_category
        
        cls._default_category, _ = LogCategory.objects.get_or_create(
            name='General',
            defaults={
                'description': 'General activity logs',
                'color': '#3B82F6',
            }
        )
        
        return cls._default_category


# =============================================================================
# Example Usage from Application Layer (Use Cases)
# =============================================================================

"""
Example 1: Ticket Creation Use Case
====================================

from apps.logs.services.log_creator import LogCreator, LogSeverity, LogIntent

class CreateTicketUseCase:
    def execute(self, request, title, description, priority, category):
        # Create the ticket
        ticket = Ticket.objects.create(
            title=title,
            description=description,
            priority=priority,
            category=category,
            created_by=request.user,
        )
        
        # Log the activity (transaction-safe, actor info captured)
        LogCreator.log_ticket_action(
            actor=request.user,
            action='TICKET_CREATED',
            ticket_id=ticket.id,
            ticket_title=ticket.title,
            description=f"Created ticket: {ticket.title}",
            severity=LogSeverity.INFO,
            intent=LogIntent.WORKFLOW,
            extra_data={
                'priority': priority,
                'category': str(category),
            },
            context=LogContext.from_request(request),
        )
        
        return ticket


Example 2: System Batch Job (No User)
======================================

from apps.logs.services.log_creator import LogCreator, LogSeverity, LogIntent

class NightlyBatchJob:
    def run(self):
        start_time = timezone.now()
        
        try:
            # Process data
            records_processed = self._sync_data()
            
            # Log successful completion
            LogCreator.log_system_event(
                action='BATCH_PROCESS_COMPLETED',
                target_type='batch_job',
                target_id=self.job_id,
                target_name='Nightly Data Sync',
                description=f'Successfully processed {records_processed} records',
                severity=LogSeverity.INFO,
                extra_data={
                    'records_processed': records_processed,
                    'duration_seconds': (timezone.now() - start_time).total_seconds(),
                    'job_type': 'data_sync',
                },
            )
            
        except Exception as e:
            # Log failure
            LogCreator.log_system_event(
                action='BATCH_PROCESS_FAILED',
                target_type='batch_job',
                target_id=self.job_id,
                target_name='Nightly Data Sync',
                description=f'Batch job failed: {str(e)}',
                severity=LogSeverity.ERROR,
                extra_data={
                    'error_type': type(e).__name__,
                    'duration_seconds': (timezone.now() - start_time).total_seconds(),
                },
            )
            raise


Example 3: Security Event (Failed Login)
==========================================

from apps.logs.services.log_creator import LogCreator, LogSeverity, LogIntent

def login_view(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    user = authenticate(request, username=username, password=password)
    
    if user is None:
        # Log failed login attempt
        LogCreator.log_security_event(
            actor=None,  # Unknown user
            action='FAILED_LOGIN',
            target_type='user',
            target_id=None,
            target_name=username,
            description=f'Failed login attempt for username: {username}',
            severity=LogSeverity.SECURITY,
            extra_data={
                'ip_address': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'attempted_username': username,
            },
            context=LogContext.from_request(request),
        )
        
        messages.error(request, 'Invalid credentials')
        return render(request, 'login.html')
    
    # Log successful login
    LogCreator.log_user_action(
        actor=user,
        action='USER_LOGIN',
        target_user=user,
        description=f'User logged in successfully',
        severity=LogSeverity.INFO,
        intent=LogIntent.SECURITY,
        context=LogContext.from_request(request),
    )
    
    login(request, user)
    return redirect('dashboard')
"""
