"""
Mixins for TicketDetailView.

TicketDetailLoggingMixin — extracted from TicketDetailView to separate
the activity-logging concern (~300 LOC) from the view/action logic.

These methods rely on self.request being set by the host view (Django CBV).
"""

from apps.tickets.models import Ticket
from apps.logs.models import ActivityLog


class TicketDetailLoggingMixin:
    """
    Activity-logging helpers for the ticket detail view.
    Writes directly to ActivityLog — not routed through ActivityService
    so that view-layer logging never breaks the request cycle.
    """

    def _get_client_ip(self, request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')

    def _log_ticket_view(self, actor, ticket: Ticket) -> None:
        from django.utils import timezone
        from datetime import timedelta

        already_logged = ActivityLog.objects.filter(
            event_type='TICKET_VIEWED',
            actor_id=str(actor.id),
            entity_id=ticket.id,
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).exists()
        if already_logged:
            return

        ActivityLog.objects.create(
            event_type='TICKET_VIEWED',
            action='VIEW',
            level='INFO',
            severity='INFO',
            intent='access',
            entity_type='ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket viewed by {actor.username}',
            description='User viewed ticket details',
            model_name='ticket',
            object_id=ticket.id,
            object_repr=str(ticket.title),
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'ticket_id': str(ticket.ticket_id),
                'ticket_title': ticket.title,
            },
        )

    def _log_assignment(self, actor, ticket: Ticket, old_assignee, new_assignee) -> None:
        if old_assignee is None:
            description = f"Assigned ticket to {new_assignee.get_full_name() or new_assignee.username}"
        else:
            description = (
                f"Reassigned ticket from {old_assignee.get_full_name() or old_assignee.username} "
                f"to {new_assignee.get_full_name() or new_assignee.username}"
            )

        ActivityLog.objects.create(
            event_type='TICKET_ASSIGNED',
            action='UPDATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket assigned to {new_assignee.username}',
            description=description,
            model_name='ticket',
            object_id=ticket.id,
            object_repr=f'{ticket.title} (assigned to {new_assignee.username})',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'assigned_to': new_assignee.username,
                'assigned_to_id': new_assignee.id,
                'old_assignee': old_assignee.username if old_assignee else None,
                'old_assignee_id': old_assignee.id if old_assignee else None,
                'ticket_id': str(ticket.ticket_id),
            },
        )

    def _log_status_change(self, actor, ticket: Ticket, old_status: str, new_status: str) -> None:
        old_display = dict(Ticket.STATUS_CHOICES)[old_status]
        new_display = dict(Ticket.STATUS_CHOICES)[new_status]

        ActivityLog.objects.create(
            event_type='TICKET_STATUS_CHANGED',
            action='UPDATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket status changed to {new_display}',
            description=f'Changed ticket status from {old_display} to {new_display}',
            model_name='Ticket',
            object_id=ticket.id,
            object_repr=f'{ticket.title} ({new_display})',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'old_status': old_status,
                'old_status_display': old_display,
                'new_status': new_status,
                'new_status_display': new_display,
                'ticket_id': str(ticket.ticket_id),
            },
        )

    def _log_priority_change(self, actor, ticket: Ticket, old_priority: str, new_priority: str) -> None:
        old_display = dict(Ticket.PRIORITY_CHOICES)[old_priority]
        new_display = dict(Ticket.PRIORITY_CHOICES)[new_priority]

        ActivityLog.objects.create(
            event_type='TICKET_PRIORITY_CHANGED',
            action='UPDATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket priority changed to {new_display}',
            description=f'Changed ticket priority from {old_display} to {new_display}',
            model_name='Ticket',
            object_id=ticket.id,
            object_repr=f'{ticket.title} (priority: {new_display})',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'old_priority': old_priority,
                'old_priority_display': old_display,
                'new_priority': new_priority,
                'new_priority_display': new_display,
                'ticket_id': str(ticket.ticket_id),
            },
        )

    def _log_note_creation(self, actor, ticket: Ticket, note, note_type: str = 'INTERNAL') -> None:
        note_summary = note.text[:100] + ('...' if len(note.text) > 100 else '')

        ActivityLog.objects.create(
            event_type='TICKET_NOTE_ADDED',
            action='CREATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title='Internal note added to ticket',
            description=f'Added internal note to ticket (summary: {note_summary})',
            model_name='TicketNote',
            object_id=note.id,
            object_repr=f'Note by {actor.username} on {ticket.ticket_id}',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'note_id': str(note.id),
                'ticket_id': str(ticket.ticket_id),
                'note_type': note_type,
                'note_length': len(note.text),
                'author_username': actor.username,
                'author_role': actor.role,
            },
        )

    def _log_review_submission(self, actor, ticket: Ticket, review) -> None:
        ActivityLog.objects.create(
            event_type='TICKET_REVIEW_SUBMITTED',
            action='CREATE',
            level='INFO',
            severity='INFO',
            intent='feedback',
            entity_type='ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role='CLIENT',
            title='Client review submitted',
            description=f'Client submitted review for ticket (rating: {review.rating if review.rating else "N/A"})',
            model_name='TicketReview',
            object_id=review.id,
            object_repr=f'Review by {actor.username} on {ticket.ticket_id}',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'review_id': str(review.id),
                'ticket_id': str(ticket.ticket_id),
                'rating': review.rating,
                'comment_length': len(review.comment) if review.comment else 0,
                'author_username': actor.username,
            },
        )
