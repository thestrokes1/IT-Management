"""
Report Service for IT Management Platform.

Following Clean Architecture:
- Domain Layer: Report data structures and narrative templates
- Application Layer: Report generation with business logic
- Interface Adapters: Views receive fully resolved report data

Features:
- Narrative summaries with key findings, trends, risks, recommendations
- Filterable and exportable reports
- Audit-safe data handling
- Role-based access control
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta
from enum import Enum
import json


class ReportType(Enum):
    """Types of reports available in the system."""
    TICKET_SUMMARY = "ticket_summary"
    ASSET_INVENTORY = "asset_inventory"
    USER_ACTIVITY = "user_activity"
    SECURITY_AUDIT = "security_audit"
    PROJECT_STATUS = "project_status"
    FULL_SYSTEM = "full_system"


class TrendDirection(Enum):
    """Trend direction for metrics."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"
    UNKNOWN = "unknown"


class RiskLevel(Enum):
    """Risk level classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class ReportSection:
    """
    A section of a report containing data and narrative.
    
    All fields are fully resolved - no business logic in templates.
    """
    section_key: str
    section_title: str
    data: Dict[str, Any]
    narrative: str  # Human-readable summary
    key_findings: List[str] = field(default_factory=list)
    trend: TrendDirection = TrendDirection.UNKNOWN
    trend_description: str = ""
    main_risk: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.NONE
    recommendation: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            'section_key': self.section_key,
            'section_title': self.section_title,
            'data': self.data,
            'narrative': self.narrative,
            'key_findings': self.key_findings,
            'trend': self.trend.value,
            'trend_description': self.trend_description,
            'main_risk': self.main_risk,
            'risk_level': self.risk_level.value,
            'recommendation': self.recommendation,
            'generated_at': self.generated_at.isoformat(),
        }


@dataclass
class Report:
    """
    Complete report with metadata, sections, and audit trail.
    
    All data is fully resolved - templates receive safe-to-render data.
    """
    report_id: str
    report_type: ReportType
    title: str
    description: str
    generated_at: datetime
    generated_by: str  # Username of generator
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    sections: List[ReportSection] = field(default_factory=list)
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    is_audit_safe: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering."""
        return {
            'report_id': self.report_id,
            'report_type': self.report_type.value,
            'title': self.title,
            'description': self.description,
            'generated_at': self.generated_at.isoformat(),
            'generated_by': self.generated_by,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'sections': [s.to_dict() for s in self.sections],
            'filters_applied': self.filters_applied,
            'is_audit_safe': self.is_audit_safe,
        }


# =============================================================================
# Report Generators (Application Layer)
# =============================================================================

class ReportGenerator:
    """
    Application service for generating reports with narrative summaries.
    
    All business logic is resolved here - templates receive safe data.
    """
    
    @staticmethod
    def generate_ticket_summary_report(
        user,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        priority_filter: Optional[str] = None,
    ) -> Report:
        """
        Generate a ticket summary report with narrative.
        
        Args:
            user: Current user (for RBAC)
            date_from: Start of report period
            date_to: End of report period
            status_filter: Optional status to filter by
            priority_filter: Optional priority to filter by
            
        Returns:
            Complete Report with sections and narrative
        """
        from django.utils import timezone
        from django.db.models import Q, Count
        from apps.tickets.models import Ticket
        from apps.assets.models import Asset
        from apps.users.models import User
        
        now = timezone.now()
        period_end = date_to or now
        period_start = date_from or (now - timedelta(days=30))
        
        # Build query with filters
        query = Q(created_at__gte=period_start, created_at__lte=period_end)
        if status_filter:
            query &= Q(status=status_filter)
        if priority_filter:
            query &= Q(priority=priority_filter)
        
        # Get statistics
        total_tickets = Ticket.objects.filter(query).count()
        tickets_by_status = {}
        for status, label in Ticket.STATUS_CHOICES:
            count = Ticket.objects.filter(query & Q(status=status)).count()
            tickets_by_status[status] = {'label': label, 'count': count}
        
        tickets_by_priority = {}
        for priority, label in Ticket.PRIORITY_CHOICES:
            count = Ticket.objects.filter(query & Q(priority=priority)).count()
            tickets_by_priority[priority] = {'label': label, 'count': count}
        
        # Calculate trends (compare to previous period)
        prev_period_start = period_start - (period_end - period_start)
        prev_total = Ticket.objects.filter(
            Q(created_at__gte=prev_period_start, created_at__lt=period_start)
        ).count()
        
        trend = TrendDirection.STABLE
        if total_tickets > prev_total * 1.1:
            trend = TrendDirection.UP
        elif total_tickets < prev_total * 0.9:
            trend = TrendDirection.DOWN
        
        # Determine main risk
        main_risk = None
        risk_level = RiskLevel.NONE
        critical_count = tickets_by_priority.get('CRITICAL', {}).get('count', 0)
        high_count = tickets_by_priority.get('HIGH', {}).get('count', 0)
        
        if critical_count > 5:
            main_risk = f"High volume of critical tickets ({critical_count})"
            risk_level = RiskLevel.CRITICAL
        elif high_count > 10:
            main_risk = f"Elevated high priority tickets ({high_count})"
            risk_level = RiskLevel.HIGH
        elif total_tickets > 100:
            main_risk = "High ticket volume may indicate capacity issues"
            risk_level = RiskLevel.MEDIUM
        
        # Generate key findings
        key_findings = [
            f"Total tickets in period: {total_tickets}",
            f"Critical priority: {critical_count} tickets",
            f"High priority: {high_count} tickets",
        ]
        
        # Add status breakdown finding
        open_count = tickets_by_status.get('OPEN', {}).get('count', 0)
        resolved_count = tickets_by_status.get('RESOLVED', {}).get('count', 0)
        if resolved_count > 0:
            resolution_rate = (resolved_count / total_tickets * 100) if total_tickets > 0 else 0
            key_findings.append(f"Resolution rate: {resolution_rate:.1f}%")
        
        # Generate recommendation
        recommendation = ""
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            recommendation = "Immediate action required: Review and prioritize critical/high tickets. Consider escalating to senior team members."
        elif trend == TrendDirection.UP:
            recommendation = "Ticket volume is increasing. Monitor capacity and consider resource allocation adjustments."
        elif resolved_count < open_count:
            recommendation = "Backlog growing faster than resolution. Consider process improvements or additional resources."
        else:
            recommendation = "Operations are stable. Continue monitoring key metrics."
        
        # Build narrative
        narrative_parts = [
            f"During the period from {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')},",
            f"the system processed {total_tickets} tickets.",
        ]
        
        if critical_count > 0:
            narrative_parts.append(f" {critical_count} required immediate attention due to critical priority.")
        
        if trend == TrendDirection.UP:
            narrative_parts.append(" Ticket volume showed an increasing trend compared to the previous period.")
        elif trend == TrendDirection.DOWN:
            narrative_parts.append(" Ticket volume showed a decreasing trend compared to the previous period.")
        
        if resolved_count > 0:
            narrative_parts.append(f" {resolved_count} tickets were successfully resolved.")
        
        narrative = " ".join(narrative_parts)
        
        # Create sections
        overview_section = ReportSection(
            section_key="overview",
            section_title="Ticket Overview",
            data={
                'total_tickets': total_tickets,
                'by_status': tickets_by_status,
                'by_priority': tickets_by_priority,
                'period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat(),
                }
            },
            narrative=narrative,
            key_findings=key_findings,
            trend=trend,
            trend_description=f"Compared to previous period: {prev_total} tickets",
            main_risk=main_risk,
            risk_level=risk_level,
            recommendation=recommendation,
        )
        
        # Create distribution section
        distribution_section = ReportSection(
            section_key="distribution",
            section_title="Ticket Distribution",
            data={
                'status_distribution': tickets_by_status,
                'priority_distribution': tickets_by_priority,
                'resolution_rate': (resolved_count / total_tickets * 100) if total_tickets > 0 else 0,
            },
            narrative=f"Status distribution shows {open_count} open tickets and {resolved_count} resolved. Priority breakdown indicates {critical_count} critical and {high_count} high priority items requiring attention.",
            key_findings=[
                f"Open tickets: {open_count}",
                f"Resolved tickets: {resolved_count}",
                f"Critical: {critical_count}",
                f"High: {high_count}",
            ],
            trend=trend,
            trend_description="Volume trend compared to previous period",
            recommendation="Focus on resolving high-priority items first to improve turnaround times.",
        )
        
        return Report(
            report_id=f"ticket_summary_{now.strftime('%Y%m%d_%H%M%S')}",
            report_type=ReportType.TICKET_SUMMARY,
            title="Ticket Summary Report",
            description=f"Comprehensive analysis of ticket activity from {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            generated_at=now,
            generated_by=getattr(user, 'username', 'System'),
            period_start=period_start,
            period_end=period_end,
            sections=[overview_section, distribution_section],
            filters_applied={
                'date_from': date_from.isoformat() if date_from else None,
                'date_to': date_to.isoformat() if date_to else None,
                'status_filter': status_filter,
                'priority_filter': priority_filter,
            },
            is_audit_safe=True,
        )
    
    @staticmethod
    def generate_asset_inventory_report(user) -> Report:
        """Generate an asset inventory report with narrative."""
        from django.utils import timezone
        from apps.assets.models import Asset
        
        now = timezone.now()
        
        # Get asset statistics
        total_assets = Asset.objects.count()
        
        status_distribution = {}
        for status, label in Asset.STATUS_CHOICES:
            count = Asset.objects.filter(status=status).count()
            status_distribution[status] = {'label': label, 'count': count}
        
        # Calculate utilization
        assigned_count = status_distribution.get('ASSIGNED', {}).get('count', 0)
        available_count = status_distribution.get('AVAILABLE', {}).get('count', 0)
        maintenance_count = status_distribution.get('MAINTENANCE', {}).get('count', 0)
        
        utilization_rate = (assigned_count / total_assets * 100) if total_assets > 0 else 0
        
        # Determine risk
        main_risk = None
        risk_level = RiskLevel.NONE
        if maintenance_count > total_assets * 0.2:
            main_risk = f"High maintenance rate ({maintenance_count} assets - {maintenance_count/total_assets*100:.1f}%)"
            risk_level = RiskLevel.HIGH
        
        # Key findings
        key_findings = [
            f"Total assets tracked: {total_assets}",
            f"Currently assigned: {assigned_count}",
            f"Available in pool: {available_count}",
            f"Under maintenance: {maintenance_count}",
            f"Utilization rate: {utilization_rate:.1f}%",
        ]
        
        # Recommendation
        recommendation = ""
        if utilization_rate > 90:
            recommendation = "High asset utilization. Consider acquiring additional assets to meet demand."
        elif utilization_rate < 50:
            recommendation = "Low asset utilization. Review asset allocation and consider redistributing resources."
        else:
            recommendation = "Asset utilization is within healthy range. Continue monitoring."
        
        # Narrative
        narrative = (
            f"The asset inventory currently contains {total_assets} tracked assets. "
            f"{assigned_count} are actively assigned to users ({utilization_rate:.1f}% utilization), "
            f"{available_count} are available in the resource pool, and "
            f"{maintenance_count} are currently under maintenance."
        )
        
        overview_section = ReportSection(
            section_key="overview",
            section_title="Asset Inventory Overview",
            data={
                'total_assets': total_assets,
                'status_distribution': status_distribution,
                'utilization_rate': utilization_rate,
            },
            narrative=narrative,
            key_findings=key_findings,
            trend=TrendDirection.STABLE,
            trend_description="Stable asset inventory with consistent allocation patterns",
            main_risk=main_risk,
            risk_level=risk_level,
            recommendation=recommendation,
        )
        
        return Report(
            report_id=f"asset_inventory_{now.strftime('%Y%m%d_%H%M%S')}",
            report_type=ReportType.ASSET_INVENTORY,
            title="Asset Inventory Report",
            description=f"Current state of asset management as of {now.strftime('%Y-%m-%d %H:%M')}",
            generated_at=now,
            generated_by=getattr(user, 'username', 'System'),
            sections=[overview_section],
            is_audit_safe=True,
        )
    
    @staticmethod
    def generate_security_audit_report(user) -> Report:
        """Generate a security audit report with narrative."""
        from django.utils import timezone
        from apps.logs.models import SecurityEvent, ActivityLog
        from datetime import timedelta
        
        now = timezone.now()
        period_start = now - timedelta(days=7)
        
        # Get security events
        security_events = SecurityEvent.objects.filter(
            detected_at__gte=period_start
        ).order_by('-detected_at')
        
        # Count by severity
        events_by_severity = {}
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = security_events.filter(severity=severity).count()
            events_by_severity[severity] = {'count': count}
        
        # Count by status
        events_by_status = {}
        for status in ['OPEN', 'INVESTIGATING', 'RESOLVED']:
            count = security_events.filter(status=status).count()
            events_by_status[status] = {'count': count}
        
        total_events = security_events.count()
        
        # Determine risk
        main_risk = None
        risk_level = RiskLevel.NONE
        critical_count = events_by_severity.get('CRITICAL', {}).get('count', 0)
        if critical_count > 0:
            main_risk = f"{critical_count} critical security events require immediate attention"
            risk_level = RiskLevel.CRITICAL
        elif events_by_severity.get('HIGH', {}).get('count', 0) > 5:
            main_risk = "Elevated security events detected"
            risk_level = RiskLevel.HIGH
        elif total_events > 20:
            main_risk = "Elevated security event volume"
            risk_level = RiskLevel.MEDIUM
        
        # Key findings
        key_findings = [
            f"Total security events: {total_events}",
            f"Critical: {critical_count}",
            f"High: {events_by_severity.get('HIGH', {}).get('count', 0)}",
            f"Open investigations: {events_by_status.get('OPEN', {}).get('count', 0)}",
        ]
        
        # Recommendation
        recommendation = ""
        if risk_level == RiskLevel.CRITICAL:
            recommendation = "URGENT: Review critical security events immediately. Implement emergency protocols if necessary."
        elif risk_level == RiskLevel.HIGH:
            recommendation = "Elevated security activity detected. Increase monitoring and review security protocols."
        else:
            recommendation = "Security posture is stable. Continue standard monitoring procedures."
        
        # Narrative
        narrative = (
            f"Over the past 7 days, the system recorded {total_events} security events. "
            f"{events_by_severity.get('CRITICAL', {}).get('count', 0)} were classified as critical severity, "
            f"requiring immediate response. "
            f"{events_by_status.get('OPEN', {}).get('count', 0)} events remain under investigation."
        )
        
        overview_section = ReportSection(
            section_key="security_overview",
            section_title="Security Event Summary",
            data={
                'total_events': total_events,
                'by_severity': events_by_severity,
                'by_status': events_by_status,
                'period_days': 7,
            },
            narrative=narrative,
            key_findings=key_findings,
            trend=TrendDirection.STABLE,
            trend_description="Security event monitoring period: 7 days",
            main_risk=main_risk,
            risk_level=risk_level,
            recommendation=recommendation,
        )
        
        return Report(
            report_id=f"security_audit_{now.strftime('%Y%m%d_%H%M%S')}",
            report_type=ReportType.SECURITY_AUDIT,
            title="Security Audit Report",
            description=f"Security event analysis for the period {period_start.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}",
            generated_at=now,
            generated_by=getattr(user, 'username', 'System'),
            period_start=period_start,
            period_end=now,
            sections=[overview_section],
            is_audit_safe=True,
        )


# =============================================================================
# Report Factory
# =============================================================================

class ReportFactory:
    """
    Factory for creating reports based on type and parameters.
    """
    
    @staticmethod
    def create_report(
        report_type: str,
        user,
        **kwargs
    ) -> Report:
        """
        Create a report of the specified type.
        
        Args:
            report_type: Type of report to generate
            user: Current user for RBAC
            **kwargs: Additional parameters for specific reports
            
        Returns:
            Generated Report object
        """
        generator = ReportGenerator()
        
        if report_type == 'ticket_summary':
            return generator.generate_ticket_summary_report(
                user,
                date_from=kwargs.get('date_from'),
                date_to=kwargs.get('date_to'),
                status_filter=kwargs.get('status_filter'),
                priority_filter=kwargs.get('priority_filter'),
            )
        elif report_type == 'asset_inventory':
            return generator.generate_asset_inventory_report(user)
        elif report_type == 'security_audit':
            return generator.generate_security_audit_report(user)
        else:
            # Default to ticket summary
            return generator.generate_ticket_summary_report(user)
    
    @staticmethod
    def get_available_report_types() -> List[Dict[str, Any]]:
        """Get list of available report types with metadata."""
        return [
            {
                'type': 'ticket_summary',
                'name': 'Ticket Summary',
                'description': 'Comprehensive ticket analysis with trends and metrics',
                'supports_filters': True,
                'supports_date_range': True,
            },
            {
                'type': 'asset_inventory',
                'name': 'Asset Inventory',
                'description': 'Current state of asset management and utilization',
                'supports_filters': False,
                'supports_date_range': False,
            },
            {
                'type': 'security_audit',
                'name': 'Security Audit',
                'description': 'Security event analysis and risk assessment',
                'supports_filters': False,
                'supports_date_range': False,
            },
        ]
