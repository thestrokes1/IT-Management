"""
Activity Log Adapter for IT Management Platform.

Provides a clean interface for converting ActivityLog models to template-safe dicts.
All actor information is resolved in the backend - no FK access in templates.

Usage:
    from apps.logs.services.log_adapter import LogAdapter
    
    adapter = LogAdapter()
    log_entries = adapter.to_template_dicts(activity_logs)
"""

from typing import List, Dict, Any
from django.utils.timesince import timesince


class LogAdapter:
    """
    Adapter for converting ActivityLog models to template-safe dictionaries.
    
    NEVER exposes log.user or user objects to templates.
    All actor information is resolved at adapter time.
    """
    
    # Severity configuration
    SEVERITY_CONFIG = {
        'ERROR': {'label': 'Error', 'icon': 'fa-times-circle', 'color': 'text-red-500 bg-red-100'},
        'WARNING': {'label': 'Warning', 'icon': 'fa-exclamation-triangle', 'color': 'text-yellow-500 bg-yellow-100'},
        'SECURITY': {'label': 'Security', 'icon': 'fa-shield-alt', 'color': 'text-red-700 bg-red-100'},
        'INFO': {'label': 'Info', 'icon': 'fa-info-circle', 'color': 'text-blue-500 bg-blue-100'},
    }
    
    # Intent configuration
    INTENT_CONFIG = {
        'workflow': {'label': 'Workflow', 'color': 'bg-blue-100 text-blue-800'},
        'sla_risk': {'label': 'SLA Risk', 'color': 'bg-orange-100 text-orange-800'},
        'security': {'label': 'Security', 'color': 'bg-red-100 text-red-800'},
        'system': {'label': 'System', 'color': 'bg-gray-100 text-gray-800'},
    }
    
    # Event label mapping
    EVENT_LABELS = {
        'TICKET_CREATED': 'Created ticket',
        'TICKET_UPDATED': 'Updated ticket',
        'TICKET_ASSIGNED': 'Assigned ticket',
        'TICKET_RESOLVED': 'Resolved ticket',
        'TICKET_REOPENED': 'Reopened ticket',
        'TICKET_CLOSED': 'Closed ticket',
        'ASSET_CREATED': 'Created asset',
        'ASSET_UPDATED': 'Updated asset',
        'ASSET_ASSIGNED': 'Assigned asset',
        'ASSET_RETURNED': 'Returned asset',
        'PROJECT_CREATED': 'Created project',
        'PROJECT_UPDATED': 'Updated project',
        'PROJECT_COMPLETED': 'Completed project',
        'USER_CREATED': 'Created user',
        'USER_LOGIN': 'User logged in',
        'USER_LOGOUT': 'User logged out',
        'USER_ROLE_CHANGED': 'Changed user role',
        'SYSTEM_STARTUP': 'System started',
        'SYSTEM_SHUTDOWN': 'System stopped',
        'BATCH_PROCESS_STARTED': 'Batch job started',
        'BATCH_PROCESS_COMPLETED': 'Batch job completed',
        'BATCH_PROCESS_FAILED': 'Batch job failed',
        'SECURITY_ALERT': 'Security alert',
        'FAILED_LOGIN': 'Failed login attempt',
        'UNAUTHORIZED_ACCESS': 'Unauthorized access',
        'CREATE': 'Created',
        'UPDATE': 'Updated',
        'DELETE': 'Deleted',
        'LOGIN': 'Logged in',
        'LOGOUT': 'Logged out',
    }
    
    def to_template_dicts(self, activity_logs: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert ActivityLog models to template-safe dictionaries.
        
        Args:
            activity_logs: List of ActivityLog model instances
            
        Returns:
            List of dictionaries with all fields pre-computed for template rendering.
            No FK access - all data is resolved in the backend.
        """
        return [self._to_dict(log) for log in activity_logs]
    
    def _to_dict(self, log: Any) -> Dict[str, Any]:
        """
        Convert a single ActivityLog to a template-safe dictionary.
        
        Args:
            log: ActivityLog model instance
            
        Returns:
            Dictionary with all template-safe fields.
        """
        extra_data = log.extra_data or {}
        
        # Resolve actor_name safely:
        # 1. Use user.username if user exists
        # 2. Else use extra_data.actor_username
        # 3. Else fallback to "System"
        if log.user is not None:
            actor_name = log.user.username
        elif extra_data.get('actor_username'):
            actor_name = extra_data.get('actor_username')
        else:
            actor_name = 'System'
        
# Resolve actor_role safely:
        # 1. Use extra_data.actor_role first
        # 2. Else use user.role if user exists
        # 3. Else fallback to "VIEWER"
        actor_role = 'VIEWER'  # Default value
        if extra_data.get('actor_role'):
            actor_role = extra_data.get('actor_role')
        elif log.user is not None:
            user_role = getattr(log.user, 'role', None)
            if user_role:
                actor_role = user_role
        
        # Determine severity from level
        level = (log.level or '').upper()
        if level == 'ERROR':
            severity = 'ERROR'
        elif level in ['WARNING', 'WARN']:
            severity = 'WARNING'
        elif log.action and 'SECURITY' in log.action:
            severity = 'SECURITY'
        else:
            severity = 'INFO'
        
        # Get severity config
        severity_config = self.SEVERITY_CONFIG.get(severity, self.SEVERITY_CONFIG['INFO'])
        
        # Determine intent
        intent = log.intent or 'workflow'
        intent_config = self.INTENT_CONFIG.get(intent, self.INTENT_CONFIG['workflow'])
        
        # Get event label
        event_type = log.action or ''
        event_label = self.EVENT_LABELS.get(event_type, event_type.replace('_', ' ').title())
        
        # Build entity display
        entity_type = log.model_name or ''
        entity_id = log.object_id
        entity_name = log.object_repr or ''
        if entity_type and entity_id:
            entity_display = f"{entity_type.capitalize()} #{entity_id}"
        else:
            entity_display = entity_name or entity_type or 'System'
        
        # Format timestamp
        formatted_timestamp = log.timestamp.strftime('%b %d, %Y %H:%M')
        time_ago = timesince(log.timestamp)
        
# Check if has details to show
        has_details = bool(extra_data) and len(extra_data) > 2
        
        # Generate human-readable narrative
        narrative = self._generate_narrative(
            actor_name=actor_name,
            actor_role=actor_role,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_name=entity_name,
        )
        
        return {
            # Core identifiers
            'log_id': str(log.log_id),
            'timestamp': log.timestamp,
            'formatted_timestamp': formatted_timestamp,
            'time_ago': time_ago,
            
            # Actor info (SAFE - no FK access)
            'actor_name': actor_name,
            'actor_role': actor_role,
            'actor_type': log.actor_type or 'user',
            
            # Event info
            'event_type': event_type,
            'event_label': event_label,
            'action': log.action or '',
            'description': log.description or '',
            'narrative': narrative,
            
            # Entity info
            'entity_type': entity_type,
            'entity_id': entity_id,
            'entity_name': entity_name,
            'entity_display': entity_display,
            
            # Classification (pre-computed for template)
            'severity': severity,
            'severity_label': severity_config['label'],
            'severity_icon': severity_config['icon'],
            'severity_color': severity_config['color'],
            
            'intent': intent,
            'intent_label': intent_config['label'],
            'intent_color': intent_config['color'],
            
            # Request context
            'ip_address': log.ip_address,
            
            # Additional data for expandable details
            'extra_data': extra_data,
            'has_details': has_details,
        }
    
    def _generate_narrative(
        self,
        actor_name: str,
        actor_role: str,
        event_type: str,
        entity_type: str,
        entity_id: Optional[int],
        entity_name: str,
    ) -> str:
        """
        Generate a human-readable narrative sentence for a log entry.
        
        Format: "{actor_name} ({actor_role}) {action_verb} {entity}"
        
        Examples:
        - "john_doe (IT_ADMIN) created ticket #123"
        - "jane (MANAGER) updated asset Laptop Pro 15"
        - "System performed SYSTEM_ACTION on project Website Redesign"
        """
        # Determine action verb from event type
        action_verb = self._get_action_verb(event_type)
        
        # Build entity reference
        if entity_type and entity_id:
            entity_ref = f"{entity_type} #{entity_id}"
        elif entity_name:
            entity_ref = entity_name
        elif entity_type:
            entity_ref = f"a {entity_type}"
        else:
            entity_ref = "the system"
        
        # Build and return narrative
        return f"{actor_name} ({actor_role}) {action_verb} {entity_ref}"
    
    def _get_action_verb(self, event_type: str) -> str:
        """
        Get the past tense verb for an action type.
        
        Maps action types to human-readable verbs.
        """
        verb_map = {
            # Ticket actions
            'TICKET_CREATED': 'created',
            'TICKET_VIEWED': 'viewed',
            'TICKET_UPDATED': 'updated',
            'TICKET_DELETED': 'deleted',
            'TICKET_ASSIGNED': 'assigned',
            'TICKET_UNASSIGNED': 'unassigned',
            'TICKET_RESOLVED': 'resolved',
            'TICKET_REOPENED': 'reopened',
            'TICKET_CLOSED': 'closed',
            'TICKET_CANCELLED': 'cancelled',
            'TICKET_ESCALATED': 'escalated',
            'TICKET_COMMENT_ADDED': 'added a comment to',
            'TICKET_ATTACHMENT_ADDED': 'added an attachment to',
            'TICKET_PRIORITY_CHANGED': 'changed priority of',
            'TICKET_STATUS_CHANGED': 'changed status of',
            'TICKET_ASSIGNEE_CHANGED': 'changed assignee of',
            
            # Asset actions
            'ASSET_CREATED': 'created',
            'ASSET_VIEWED': 'viewed',
            'ASSET_UPDATED': 'updated',
            'ASSET_DELETED': 'deleted',
            'ASSET_ASSIGNED': 'assigned',
            'ASSET_RETURNED': 'returned',
            'ASSET_MAINTENANCE_SCHEDULED': 'scheduled maintenance for',
            'ASSET_STATUS_CHANGED': 'changed status of',
            'ASSET_LOCATION_CHANGED': 'changed location of',
            'ASSET_CHECKED_OUT': 'checked out',
            'ASSET_CHECKED_IN': 'checked in',
            
            # Project actions
            'PROJECT_CREATED': 'created',
            'PROJECT_VIEWED': 'viewed',
            'PROJECT_UPDATED': 'updated',
            'PROJECT_DELETED': 'deleted',
            'PROJECT_COMPLETED': 'completed',
            'PROJECT_CANCELLED': 'cancelled',
            'PROJECT_MEMBER_ADDED': 'added member to',
            'PROJECT_MEMBER_REMOVED': 'removed member from',
            'PROJECT_ROLE_CHANGED': 'changed role in',
            'PROJECT_TASK_CREATED': 'created task in',
            'PROJECT_TASK_COMPLETED': 'completed task in',
            
            # User actions
            'USER_CREATED': 'created',
            'USER_LOGIN': 'logged in to',
            'USER_LOGOUT': 'logged out from',
            'USER_PASSWORD_CHANGED': 'changed password for',
            'USER_ROLE_CHANGED': 'changed role of',
            'USER_DEACTIVATED': 'deactivated',
            'USER_REACTIVATED': 'reactivated',
            'USER_PROFILE_UPDATED': 'updated profile for',
            
            # Generic actions
            'CREATE': 'created',
            'UPDATE': 'updated',
            'DELETE': 'deleted',
            'LOGIN': 'logged in to',
            'LOGOUT': 'logged out from',
            'SEARCH': 'searched',
            'DOWNLOAD': 'downloaded',
            'UPLOAD': 'uploaded',
            'EXPORT': 'exported',
            'IMPORT': 'imported',
            'API_CALL': 'made API call to',
            'SYSTEM_ACTION': 'performed system action on',
            'SECURITY_EVENT': 'triggered security event on',
            'ERROR': 'encountered error in',
            'READ': 'read',
        }
        
        return verb_map.get(event_type, f"performed {event_type.lower().replace('_', ' ')} on")


def get_log_adapter() -> LogAdapter:
    """
    Factory function to get a LogAdapter instance.
    
    Returns:
        LogAdapter instance ready to convert logs.
    """
    return LogAdapter()
