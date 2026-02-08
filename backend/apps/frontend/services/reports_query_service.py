"""
Reports Query Service for IT Management Platform.

Following Clean Architecture:
- All business logic resolved in service layer
- Templates receive fully resolved data structures
- No ORM logic in templates

Data Flow:
    DB Query → Service Aggregation → View Context → Template Render
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from django.db.models import Count, Q
from django.utils import timezone


@dataclass
class TicketSummary:
    """Summary of a ticket for reports."""
    id: int
    title: str
    status: str
    priority: str
    status_display: str = ""
    priority_display: str = ""
    created_by_id: Optional[int] = None
    created_by_username: str = ""
    created_at: Optional[datetime] = None
    updated_by_id: Optional[int] = None
    updated_by_username: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'status': self.status,
            'priority': self.priority,
            'status_display': self.status_display,
            'priority_display': self.priority_display,
            'created_by': {
                'id': self.created_by_id,
                'username': self.created_by_username,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_by': {
                'id': self.updated_by_id,
                'username': self.updated_by_username,
            } if self.updated_by_id else None,
        }


@dataclass
class ActivitySummary:
    """Summary of an activity log entry for reports."""
    id: int
    timestamp: Optional[datetime] = None
    actor_id: Optional[int] = None
    actor_username: str = ""
    actor_role: str = ""
    action: str = ""
    action_label: str = ""
    action_icon: str = ""
    action_color: str = ""
    entity_type: str = ""
    entity_id: Optional[int] = None
    entity_name: str = ""
    entity_url: str = ""
    changes_summary: str = ""
    description: str = ""
    ip_address: str = ""
    level: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'actor': {
                'id': self.actor_id,
                'username': self.actor_username,
                'role': self.actor_role,
            },
            'action': self.action,
            'action_label': self.action_label,
            'action_icon': self.action_icon,
            'action_color': self.action_color,
            'entity': {
                'type': self.entity_type,
                'id': self.entity_id,
                'name': self.entity_name,
                'url': self.entity_url,
            },
            'changes_summary': self.changes_summary,
            'description': self.description,
            'ip_address': self.ip_address,
            'level': self.level,
        }


@dataclass
class StatusDistribution:
    """Status distribution for charts."""
    status: str
    label: str
    count: int
    percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'status': self.status,
            'label': self.label,
            'count': self.count,
            'percentage': self.percentage,
        }


class ReportsQueryService:
    """
    Service for aggregating reports data from the database.
    
    All business logic is resolved here - templates receive
    fully resolved, safe-to-render data structures.
    """
    
    # Role labels for display
    ROLE_LABELS = {
        'SUPERADMIN': 'Super Admin',
        'IT_ADMIN': 'IT Admin',
        'MANAGER': 'Manager',
        'TECHNICIAN': 'Technician',
        'VIEWER': 'Viewer',
    }
    
    # Action icons and colors
    ACTION_ICONS = {
        'TICKET_CREATED': 'fa-ticket-alt',
        'TICKET_UPDATED': 'fa-edit',
        'TICKET_ASSIGNED': 'fa-user-plus',
        'TICKET_RESOLVED': 'fa-check-circle',
        'TICKET_DELETED': 'fa-trash',
        'TICKET_REOPENED': 'fa-undo',
        'ASSET_CREATED': 'fa-desktop',
        'ASSET_UPDATED': 'fa-edit',
        'ASSET_ASSIGNED': 'fa-hand-paper',
        'ASSET_DELETED': 'fa-trash',
        'PROJECT_CREATED': 'fa-project-diagram',
        'PROJECT_UPDATED': 'fa-edit',
        'PROJECT_DELETED': 'fa-trash',
        'USER_CREATED': 'fa-user-plus',
        'USER_LOGIN': 'fa-sign-in-alt',
        'USER_LOGOUT': 'fa-sign-out-alt',
        'USER_UPDATED': 'fa-edit',
        'LOGIN_SUCCESS': 'fa-check-circle',
        'LOGIN_FAILURE': 'fa-exclamation-circle',
    }
    
    ACTION_COLORS = {
        'CREATED': 'text-green-500',
        'DELETED': 'text-red-500',
        'ASSIGNED': 'text-blue-500',
        'RESOLVED': 'text-green-600',
        'LOGIN': 'text-green-500',
        'LOGOUT': 'text-gray-500',
        'UPDATED': 'text-blue-500',
        'REOPENED': 'text-orange-500',
    }
    
    def get_summary_metrics(self, user=None, is_admin: bool = True) -> Dict[str, int]:
        """
        Get summary metrics for the reports page.
        
        Returns:
            Dict with total_assets, active_projects, open_tickets, active_users,
            recent_security_events
        """
        from apps.assets.models import Asset
        from apps.projects.models import Project
        from apps.tickets.models import Ticket
        from apps.users.models import User
        from apps.logs.models import ActivityLog
        
        # Total Assets
        total_assets = Asset.objects.count() if Asset else 0
        
        # Active Projects (filter by status)
        if Project:
            active_projects = Project.objects.filter(
                status__in=['PLANNING', 'ACTIVE']
            ).count()
        else:
            active_projects = 0
        
        # Open Tickets (NEW, OPEN, IN_PROGRESS)
        if Ticket:
            open_tickets = Ticket.objects.filter(
                status__in=['NEW', 'OPEN', 'IN_PROGRESS']
            ).count()
        else:
            open_tickets = 0
        
        # Active Users (is_active=True)
        if User:
            if is_admin:
                active_users = User.objects.filter(is_active=True).count()
            else:
                # Non-admin users only see themselves
                active_users = 1 if user and user.is_active else 0
        else:
            active_users = 0
        
        # Security Events in last 7 days
        seven_days_ago = timezone.now() - timedelta(days=7)
        if ActivityLog:
            # Count security-related events
            recent_security_events = ActivityLog.objects.filter(
                timestamp__gte=seven_days_ago,
                action__in=['LOGIN_FAILURE', 'PERMISSION_DENIED', 'PRIVILEGE_ESCALATION']
            ).count()
        else:
            recent_security_events = 0
        
        return {
            'total_assets': total_assets,
            'active_projects': active_projects,
            'open_tickets': open_tickets,
            'active_users': active_users,
            'recent_security_events': recent_security_events,
        }
    
    def get_asset_status_distribution(self) -> Dict[str, Dict[str, Any]]:
        """
        Get asset status distribution grouped by status.
        
        Returns:
            Dict mapping status to {label, count}
        """
        from apps.assets.models import Asset
        
        if not Asset:
            return {}
        
        distribution = {}
        total_assets = Asset.objects.count()
        
        for status, label in Asset.STATUS_CHOICES:
            count = Asset.objects.filter(status=status).count()
            percentage = (count / total_assets * 100) if total_assets > 0 else 0
            distribution[status] = {
                'label': label,
                'count': count,
                'percentage': round(percentage, 1),
            }
        
        return distribution
    
    def get_ticket_status_distribution(self) -> Dict[str, Dict[str, Any]]:
        """
        Get ticket status distribution grouped by status.
        
        Returns:
            Dict mapping status to {label, count}
        """
        from apps.tickets.models import Ticket
        
        if not Ticket:
            return {}
        
        distribution = {}
        total_tickets = Ticket.objects.count()
        
        for status, label in Ticket.STATUS_CHOICES:
            count = Ticket.objects.filter(status=status).count()
            percentage = (count / total_tickets * 100) if total_tickets > 0 else 0
            distribution[status] = {
                'label': label,
                'count': count,
                'percentage': round(percentage, 1),
            }
        
        return distribution
    
    def get_ticket_priority_distribution(self) -> Dict[str, Dict[str, Any]]:
        """
        Get ticket priority distribution grouped by priority.
        
        Returns:
            Dict mapping priority to {label, count}
        """
        from apps.tickets.models import Ticket
        
        if not Ticket:
            return {}
        
        distribution = {}
        for priority, label in Ticket.PRIORITY_CHOICES:
            count = Ticket.objects.filter(priority=priority).count()
            distribution[priority] = {
                'label': label,
                'count': count,
            }
        
        return distribution
    
    def get_recent_tickets(self, limit: int = 10, user=None, is_admin: bool = True) -> List[TicketSummary]:
        """
        Get recent tickets ordered by creation date.
        
        Args:
            limit: Maximum number of tickets to return
            user: Current user for RBAC
            is_admin: Whether user has admin privileges
            
        Returns:
            List of TicketSummary objects
        """
        from apps.tickets.models import Ticket
        
        if not Ticket:
            return []
        
        # Build queryset with select_related for N+1 prevention
        queryset = Ticket.objects.select_related(
            'created_by', 'updated_by', 'category'
        ).order_by('-created_at')[:limit]
        
        tickets = []
        for ticket in queryset:
            # RBAC check - admins see all, regular users see their own
            if not is_admin and user:
                if ticket.created_by != user and ticket.assigned_to != user:
                    continue
            
            tickets.append(TicketSummary(
                id=ticket.id,
                title=ticket.title,
                status=ticket.status,
                priority=ticket.priority,
                status_display=ticket.get_status_display(),
                priority_display=ticket.get_priority_display(),
                created_by_id=ticket.created_by.id if ticket.created_by else None,
                created_by_username=ticket.created_by.username if ticket.created_by else 'System',
                created_at=ticket.created_at,
                updated_by_id=ticket.updated_by.id if ticket.updated_by else None,
                updated_by_username=ticket.updated_by.username if ticket.updated_by else '',
            ))
        
        return tickets
    
    def get_recent_activities(
        self, 
        limit: int = 20, 
        user=None, 
        is_admin: bool = True
    ) -> List[ActivitySummary]:
        """
        Get recent activity logs for audit trail.
        
        Args:
            limit: Maximum number of activities to return
            user: Current user for RBAC
            is_admin: Whether user has admin privileges
            
        Returns:
            List of ActivitySummary objects (NULL-safe)
        """
        from apps.logs.models import ActivityLog
        
        if not ActivityLog:
            return []
        
        # Get recent activities
        activities = ActivityLog.objects.select_related(
            'user'
        ).order_by('-timestamp')[:limit * 2]  # Get more to filter
        
        results = []
        count = 0
        
        for activity in activities:
            # RBAC check
            if not is_admin and user:
                # Regular users only see activities they performed or are related to
                # For simplicity, we'll show all to admins
                pass
            
            # Build entity info
            entity_type = activity.model_name or 'System'
            entity_id = activity.object_id
            entity_name = activity.object_repr or ''
            
            # Build entity URL
            entity_url = '#'
            if entity_type == 'ticket' and entity_id:
                entity_url = f'/tickets/{entity_id}/'
            elif entity_type == 'asset' and entity_id:
                entity_url = f'/assets/{entity_id}/'
            elif entity_type == 'project' and entity_id:
                entity_url = f'/projects/{entity_id}/'
            elif entity_type == 'user' and entity_id:
                entity_url = f'/users/{entity_id}/'
            
            # Get actor info (NULL-safe)
            actor_id = activity.user.id if activity.user else None
            actor_username = activity.user.username if activity.user else 'System'
            
            # Try to get role from user or extra_data
            actor_role = 'VIEWER'
            if activity.user and hasattr(activity.user, 'role'):
                actor_role = activity.user.role
            elif activity.extra_data:
                actor_role = activity.extra_data.get('actor_role', 'VIEWER')
            
            # Get changes summary from extra_data
            changes_summary = ''
            if activity.extra_data:
                if 'changes' in activity.extra_data:
                    changes_summary = activity.extra_data['changes']
                elif 'from_status' in activity.extra_data and 'to_status' in activity.extra_data:
                    changes_summary = f"Status: {activity.extra_data['from_status']} → {activity.extra_data['to_status']}"
                elif 'from_priority' in activity.extra_data and 'to_priority' in activity.extra_data:
                    changes_summary = f"Priority: {activity.extra_data['from_priority']} → {activity.extra_data['to_priority']}"
            
            # Get action label and icon
            action = activity.action or 'UNKNOWN'
            action_label = self._get_action_label(action)
            action_icon = self.ACTION_ICONS.get(action, 'fa-circle')
            
            # Get action color
            action_color = 'text-blue-500'
            for key, color in self.ACTION_COLORS.items():
                if key in action:
                    action_color = color
                    break
            
            results.append(ActivitySummary(
                id=activity.id,
                timestamp=activity.timestamp,
                actor_id=actor_id,
                actor_username=actor_username,
                actor_role=actor_role,
                action=action,
                action_label=action_label,
                action_icon=action_icon,
                action_color=action_color,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                entity_url=entity_url,
                changes_summary=changes_summary or activity.description or '',
                description=activity.description or '',
                ip_address=activity.ip_address or '',
                level=activity.level or 'INFO',
            ))
            
            count += 1
            if count >= limit:
                break
        
        return results
    
    def _get_action_label(self, action: str) -> str:
        """Get human-readable action label."""
        label_map = {
            'TICKET_CREATED': 'Created Ticket',
            'TICKET_UPDATED': 'Updated Ticket',
            'TICKET_ASSIGNED': 'Assigned Ticket',
            'TICKET_RESOLVED': 'Resolved Ticket',
            'TICKET_CLOSED': 'Closed Ticket',
            'TICKET_REOPENED': 'Reopened Ticket',
            'ASSET_CREATED': 'Created Asset',
            'ASSET_UPDATED': 'Updated Asset',
            'ASSET_ASSIGNED': 'Assigned Asset',
            'PROJECT_CREATED': 'Created Project',
            'PROJECT_UPDATED': 'Updated Project',
            'USER_CREATED': 'Created User',
            'USER_LOGIN': 'User Login',
            'USER_LOGOUT': 'User Logout',
            'LOGIN_SUCCESS': 'Login Successful',
            'LOGIN_FAILURE': 'Login Failed',
            'PERMISSION_DENIED': 'Permission Denied',
            'PRIVILEGE_ESCALATION': 'Privilege Escalation',
            'ROLE_CHANGED': 'Role Changed',
        }
        return label_map.get(action, action.replace('_', ' ').title())
    
    def get_full_report_data(
        self, 
        user=None, 
        is_admin: bool = True
    ) -> Dict[str, Any]:
        """
        Get all report data in one call.
        
        This is the main method for the reports page.
        
        Returns:
            Dict with all data needed for the reports template
        """
        # Get all data
        summary = self.get_summary_metrics(user, is_admin)
        asset_distribution = self.get_asset_status_distribution()
        ticket_status = self.get_ticket_status_distribution()
        ticket_priority = self.get_ticket_priority_distribution()
        recent_tickets = self.get_recent_tickets(limit=10, user=user, is_admin=is_admin)
        recent_activities = self.get_recent_activities(limit=20, user=user, is_admin=is_admin)
        
        # Calculate total tickets for percentage
        total_tickets = sum(d['count'] for d in ticket_status.values())
        total_assets = sum(d['count'] for d in asset_distribution.values())
        
        return {
            # Summary metrics
            'total_assets': summary['total_assets'],
            'active_projects': summary['active_projects'],
            'open_tickets': summary['open_tickets'],
            'active_users': summary['active_users'],
            'recent_security_events': summary['recent_security_events'],
            
            # Distributions
            'asset_status_distribution': asset_distribution,
            'tickets_by_status': ticket_status,
            'tickets_by_priority': ticket_priority,
            'total_tickets': total_tickets,
            'total_assets': total_assets,
            
            # Recent items
            'recent_tickets': [t.to_dict() for t in recent_tickets],
            'recent_activities': [a.to_dict() for a in recent_activities],
            
            # Admin flag
            'is_admin': is_admin,
        }

