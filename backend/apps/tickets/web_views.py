"""
Web views for tickets app - template-based (HTML) views.
Separate from API viewsets - these render HTML pages for authenticated users.
"""

from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.contrib.auth import get_user_model

from apps.tickets.models import Ticket, TicketCategory, TicketType
from apps.logs.models import ActivityLog
from apps.tickets.domain.services.ticket_authority import TicketAuthority
from apps.users.models import UserRole

User = get_user_model()


class TicketDetailView(LoginRequiredMixin, DetailView):
    """
    READ-ONLY ticket detail page for internal staff.
    
    Displays:
    - Ticket metadata (number, title, status, priority, etc.)
    - Full description
    - Activity timeline (from ActivityLog model)
    - Sidebar widgets (SLA, timeline, assignee, related items)
    
    Permission checks:
    - VIEWER role: Denied (should use public view instead)
    - TECHNICIAN: Can view all tickets (RBAC enforced by ticket_authority)
    - MANAGER/SUPERADMIN/IT_ADMIN: Can view all tickets
    
    No forms, no mutations, no internal notes editing.
    """
    
    model = Ticket
    template_name = 'frontend/ticket_detail.html'
    context_object_name = 'ticket'
    pk_url_kwarg = 'ticket_id'  # URL parameter name
    
    def get_object(self, queryset=None):
        """
        Get ticket by UUID (ticket_id).
        
        Optimized with select_related for FK relationships:
        - category (for category name, color, SLA info)
        - ticket_type (for ticket type info)
        - assigned_to (for assignee info)
        - requester (for who created the ticket)
        
        NOT using prefetch_related for ActivityLog here - handled separately
        in get_context_data with pagination.
        """
        if queryset is None:
            queryset = self.get_queryset()
        
        # Get ticket ID from URL
        ticket_id = self.kwargs.get('ticket_id')
        
        # Query with optimizations for this view's needs
        ticket = get_object_or_404(
            queryset.select_related(
                'category',
                'ticket_type',
                'assigned_to',
                'requester'
            ),
            ticket_id=ticket_id
        )
        
        return ticket
    
    def get_queryset(self):
        """Base queryset - further optimized in get_object"""
        return Ticket.objects.filter(
            # Start with all active tickets - permission checks in dispatch
        )
    
    def dispatch(self, request, *args, **kwargs):
        """
        Check RBAC before allowing access.
        
        Uses ticket_authority.can_view() to enforce:
        - VIEWER: Denied (HTTP 403)
        - Others: Allowed
        """
        # Get the ticket first
        ticket = self.get_object()
        
        # Check permissions via domain service
        authority = TicketAuthority()
        if not authority.can_view(request.user, ticket):
            # User doesn't have permission to view this ticket
            raise PermissionDenied(
                "You do not have permission to view this ticket."
            )
        
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST requests for mutations (assignment, status change, priority change, notes, reviews, etc.).
        
        Supports:
        - action=assign: Assign ticket to technician (Phase 2A)
        - action=change_status: Change ticket status (Phase 2B)
        - action=change_priority: Change ticket priority (Phase 2C)
        - action=add_note: Add internal note to ticket (Phase 3A/3B)
        - action=submit_review: Submit client/requester review (Phase 3C)
        
        Returns:
        - GET request with success/error message
        - Redirects back to GET view (PRG pattern)
        """
        ticket = self.get_object()
        action = request.POST.get('action', '')
        
        if action == 'assign':
            return self._handle_assignment(request, ticket)
        elif action == 'change_status':
            return self._handle_status_change(request, ticket)
        elif action == 'change_priority':
            return self._handle_priority_change(request, ticket)
        elif action == 'add_note':
            return self._handle_note_creation(request, ticket)
        elif action == 'submit_review':
            return self._handle_review_submission(request, ticket)
        
        # Default: redirect back to GET view
        return redirect(request.path)
    
    def _handle_assignment(self, request, ticket: Ticket) -> HttpResponse:
        """
        Handle ticket assignment.
        
        Permissions:
        - Admin/Manager/IT_Admin: Can assign to any technician
        - Technician: Can only assign to self (if unassigned)
        - VIEWER: Denied (should not reach here due to dispatch check)
        
        Args:
            request: The HTTP request
            ticket: The Ticket instance
            
        Returns:
            HttpResponse: Redirect back to GET view
        """
        authority = TicketAuthority()
        assignee_id = request.POST.get('assigned_to', '').strip()
        
        # Validate assignee_id was provided
        if not assignee_id:
            return self._redirect_with_message(
                request, ticket, 'error', 'Assignee ID is required.'
            )
        
        try:
            assignee = User.objects.get(id=int(assignee_id))
        except (User.DoesNotExist, ValueError):
            return self._redirect_with_message(
                request, ticket, 'error', 'Invalid assignee selected.'
            )
        
        # Check if user can assign to this person
        # For now, just check if user can assign (general permission)
        if not authority.can_assign(request.user, ticket, assignee):
            return self._redirect_with_message(
                request, ticket, 'error', 'You do not have permission to assign this ticket.'
            )
        
        # Save old assignee for logging
        old_assignee = ticket.assigned_to
        
        # Update ticket
        ticket.assigned_to = assignee
        ticket.assignment_status = 'ASSIGNED'
        ticket.updated_at = timezone.now()
        ticket.save()
        
        # Log the assignment in ActivityLog
        self._log_assignment(request.user, ticket, old_assignee, assignee)
        
        return self._redirect_with_message(
            request, ticket, 'success', f'Ticket assigned to {assignee.get_full_name() or assignee.username}.'
        )
    
    def _log_assignment(self, actor, ticket: Ticket, old_assignee, new_assignee) -> None:
        """
        Log assignment event in ActivityLog.
        
        Args:
            actor: User who performed the assignment
            ticket: Ticket being assigned
            old_assignee: Previous assignee (User or None)
            new_assignee: New assignee (User)
        """
        # Determine description based on old assignee
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
            entity_type='Ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket assigned to {new_assignee.username}',
            description=description,
            model_name='Ticket',
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
            }
        )
    
    def _handle_status_change(self, request, ticket: Ticket) -> HttpResponse:
        """
        Handle ticket status change.
        
        Enforces valid state transitions and permissions:
        - Admin/Manager/IT_Admin: Can transition to most statuses
        - Technician: Limited transitions (no CLOSED/CANCELLED)
        
        Args:
            request: The HTTP request
            ticket: The Ticket instance
            
        Returns:
            HttpResponse: Redirect back to GET view
        """
        authority = TicketAuthority()
        new_status = request.POST.get('new_status', '').strip().upper()
        
        # Validate new_status was provided
        if not new_status:
            return self._redirect_with_message(
                request, ticket, 'error', 'Status is required.'
            )
        
        # Validate new_status is valid choice
        valid_statuses = dict(Ticket.STATUS_CHOICES)
        if new_status not in valid_statuses:
            return self._redirect_with_message(
                request, ticket, 'error', f'Invalid status: {new_status}.'
            )
        
        # Cannot transition to same status
        if new_status == ticket.status:
            return self._redirect_with_message(
                request, ticket, 'warning', f'Ticket is already {ticket.get_status_display().lower()}.'
            )
        
        # Check if user can edit this ticket
        if not authority.can_edit(request.user, ticket):
            return self._redirect_with_message(
                request, ticket, 'error', 'You do not have permission to change this ticket status.'
            )
        
        # Check if the transition is allowed based on user role
        allowed_transitions = self._get_allowed_transitions(request.user, ticket)
        if new_status not in allowed_transitions:
            return self._redirect_with_message(
                request, ticket, 'error', 
                f'Cannot transition from {ticket.get_status_display()} to {valid_statuses[new_status]}.'
            )
        
        # Save old status for logging
        old_status = ticket.status
        
        # Update ticket status and timestamps based on new status
        ticket.status = new_status
        ticket.updated_at = timezone.now()
        
        # Set resolved_at timestamp when changing to RESOLVED
        if new_status == 'RESOLVED' and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        # Clear resolved_at if reverting to earlier status
        elif new_status != 'RESOLVED' and old_status == 'RESOLVED':
            ticket.resolved_at = None
        
        # Set closed_at timestamp when changing to CLOSED
        if new_status == 'CLOSED' and not ticket.closed_at:
            ticket.closed_at = timezone.now()
        # Clear closed_at if reverting to earlier status
        elif new_status != 'CLOSED' and old_status == 'CLOSED':
            ticket.closed_at = None
        
        # Save the ticket
        ticket.save()
        
        # Log the status change in ActivityLog
        self._log_status_change(request.user, ticket, old_status, new_status)
        
        old_status_display = dict(Ticket.STATUS_CHOICES)[old_status]
        return self._redirect_with_message(
            request, ticket, 'success', 
            f'Ticket status changed from {old_status_display} to {valid_statuses[new_status]}.'
        )
    
    def _get_allowed_transitions(self, user, ticket) -> list:
        """
        Get list of allowed status transitions for current user.
        
        Admins can transition to most statuses.
        Technicians have limited transitions.
        
        Args:
            user: Current user
            ticket: Ticket instance
            
        Returns:
            list: List of allowed status codes
        """
        current_status = ticket.status
        
        # Define base transitions available from each status
        # All users can do these
        base_transitions = {
            'NEW': ['OPEN', 'CANCELLED'],
            'OPEN': ['IN_PROGRESS', 'PENDING', 'CANCELLED'],
            'IN_PROGRESS': ['PENDING', 'RESOLVED', 'CANCELLED'],
            'PENDING': ['IN_PROGRESS', 'CANCELLED'],
            'RESOLVED': ['CLOSED', 'OPEN'],  # Can reopen from resolved
            'CLOSED': [],  # Cannot transition from closed
            'CANCELLED': [],  # Cannot transition from cancelled
        }
        
        allowed = base_transitions.get(current_status, [])
        
        # Technicians have additional restrictions
        if user.role == 'TECHNICIAN':
            # Technicians cannot close or revert from closed
            allowed = [s for s in allowed if s not in ['CLOSED', 'CANCELLED']]
        
        # Admins can also directly change to certain statuses
        if user.role in ['SUPERADMIN', 'MANAGER', 'IT_ADMIN']:
            # Admins can transition to CLOSED from RESOLVED
            if current_status == 'RESOLVED' and 'CLOSED' not in allowed:
                allowed.append('CLOSED')
        
        return allowed
    
    def _log_status_change(self, actor, ticket: Ticket, old_status: str, new_status: str) -> None:
        """
        Log status change event in ActivityLog.
        
        Args:
            actor: User who performed the status change
            ticket: Ticket being changed
            old_status: Previous status code
            new_status: New status code
        """
        old_status_display = dict(Ticket.STATUS_CHOICES)[old_status]
        new_status_display = dict(Ticket.STATUS_CHOICES)[new_status]
        
        description = f"Changed ticket status from {old_status_display} to {new_status_display}"
        
        ActivityLog.objects.create(
            event_type='TICKET_STATUS_CHANGED',
            action='UPDATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='Ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket status changed to {new_status_display}',
            description=description,
            model_name='Ticket',
            object_id=ticket.id,
            object_repr=f'{ticket.title} ({new_status_display})',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'old_status': old_status,
                'old_status_display': old_status_display,
                'new_status': new_status,
                'new_status_display': new_status_display,
                'ticket_id': str(ticket.ticket_id),
            }
        )
    
    def _handle_priority_change(self, request, ticket: Ticket) -> HttpResponse:
        """
        Handle ticket priority change.
        
        Permissions:
        - Admin/Manager/IT_Admin: Can change priority
        - Technician: Cannot change priority (read-only)
        - VIEWER: Cannot change priority
        
        Args:
            request: The HTTP request
            ticket: The Ticket instance
            
        Returns:
            HttpResponse: Redirect back to GET view
        """
        new_priority = request.POST.get('new_priority', '').strip().upper()
        
        # Validate new_priority was provided
        if not new_priority:
            return self._redirect_with_message(
                request, ticket, 'error', 'Priority is required.'
            )
        
        # Validate new_priority is valid choice
        valid_priorities = dict(Ticket.PRIORITY_CHOICES)
        if new_priority not in valid_priorities:
            return self._redirect_with_message(
                request, ticket, 'error', f'Invalid priority: {new_priority}.'
            )
        
        # Cannot change to same priority
        if new_priority == ticket.priority:
            return self._redirect_with_message(
                request, ticket, 'warning', 
                f'Ticket priority is already {ticket.get_priority_display().lower()}.'
            )
        
        # Check if user can change priority (admin/manager/it_admin only)
        if not self._can_change_priority(request.user):
            return self._redirect_with_message(
                request, ticket, 'error', 
                'You do not have permission to change ticket priority.'
            )
        
        # Save old priority for logging
        old_priority = ticket.priority
        
        # Update ticket priority
        ticket.priority = new_priority
        ticket.updated_at = timezone.now()
        ticket.save()
        
        # Log the priority change in ActivityLog
        self._log_priority_change(request.user, ticket, old_priority, new_priority)
        
        return self._redirect_with_message(
            request, ticket, 'success', 
            f'Ticket priority changed to {valid_priorities[new_priority]}.'
        )
    
    def _can_change_priority(self, user) -> bool:
        """
        Check if user can change ticket priority.
        
        Rules:
        - SUPERADMIN, MANAGER: allowed
        - IT_ADMIN: allowed
        - TECHNICIAN: NOT allowed (read-only)
        - VIEWER: NOT allowed
        
        Args:
            user: User instance
            
        Returns:
            bool: True if user can change priority
        """
        return user.role in ['SUPERADMIN', 'MANAGER', 'IT_ADMIN']
    
    def _log_priority_change(self, actor, ticket: Ticket, old_priority: str, new_priority: str) -> None:
        """
        Log priority change event in ActivityLog.
        
        Args:
            actor: User who performed the priority change
            ticket: Ticket being changed
            old_priority: Previous priority code
            new_priority: New priority code
        """
        old_priority_display = dict(Ticket.PRIORITY_CHOICES)[old_priority]
        new_priority_display = dict(Ticket.PRIORITY_CHOICES)[new_priority]
        
        description = f"Changed ticket priority from {old_priority_display} to {new_priority_display}"
        
        ActivityLog.objects.create(
            event_type='TICKET_PRIORITY_CHANGED',
            action='UPDATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='Ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Ticket priority changed to {new_priority_display}',
            description=description,
            model_name='Ticket',
            object_id=ticket.id,
            object_repr=f'{ticket.title} (priority: {new_priority_display})',
            ip_address=self._get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', ''),
            request_path=self.request.path,
            request_method=self.request.method,
            extra_data={
                'old_priority': old_priority,
                'old_priority_display': old_priority_display,
                'new_priority': new_priority,
                'new_priority_display': new_priority_display,
                'ticket_id': str(ticket.ticket_id),
            }
        )
    
    # =========================================================================
    # PHASE 3A: INTERNAL STAFF-ONLY TICKET NOTES
    # =========================================================================
    
    def _handle_note_creation(self, request, ticket: Ticket) -> HttpResponse:
        """
        Handle internal note creation on a ticket (Phase 3A/3B).
        
        Permissions:
        - Admin/Manager/IT_Admin: Always allowed
        - Technician: Only if assigned to ticket
        - VIEWER: Denied
        
        Phase 3B enhancement: Accepts optional note_type parameter.
        
        Validates note text, checks permissions, creates TicketNote, logs to ActivityLog.
        Returns redirect with success/error message.
        """
        user = request.user
        note_text = request.POST.get('note_text', '').strip()
        note_type = request.POST.get('note_type', 'INTERNAL').strip().upper()
        
        if not note_text:
            return self._redirect_with_message(request, ticket, 'error', 'Note text is required.')
        
        if len(note_text) > 5000:
            return self._redirect_with_message(request, ticket, 'error', 'Note must be 5000 characters or less.')
        
        if not self._can_add_note(user, ticket):
            return self._redirect_with_message(request, ticket, 'error', 'You do not have permission to add notes to this ticket.')
        
        # Validate note_type (Phase 3B) - fallback to INTERNAL if invalid
        allowed_note_types = ['INTERNAL', 'OBSERVATION', 'DIAGNOSIS', 'WORK_DONE', 'ESCALATION']
        if note_type not in allowed_note_types:
            note_type = 'INTERNAL'
        
        # Create the note (append-only, no edits)
        from apps.tickets.models import TicketNote
        note = TicketNote.objects.create(
            ticket=ticket,
            author=user,
            text=note_text
        )
        
        # Log the note creation with note_type (Phase 3B enhancement)
        self._log_note_creation(user, ticket, note, note_type)
        
        # Success message
        return self._redirect_with_message(request, ticket, 'success', f'Note added successfully.')
    
    def _can_add_note(self, user, ticket: Ticket) -> bool:
        """
        Check if user can add internal notes to this ticket.
        
        Rules:
        - Admin/Manager/IT_Admin: Always allowed
        - Technician: Only if assigned to this ticket
        - VIEWER/Others: Denied
        
        Returns boolean permission flag.
        """
        # Admin roles can always add notes
        if user.role in ['SUPERADMIN', 'MANAGER', 'IT_ADMIN']:
            return True
        
        # Technician can add notes only if assigned
        if user.role == 'TECHNICIAN':
            return ticket.assigned_to == user
        
        # All others are denied
        return False
    
    def _get_note_types_from_log(self, ticket: Ticket, notes) -> dict:
        """
        Get note_type for each note from ActivityLog (Phase 3B).
        
        Returns a dictionary mapping note.id -> note_type string.
        Defaults to 'INTERNAL' if note_type not found in ActivityLog.
        
        Args:
            ticket: The ticket being viewed
            notes: QuerySet of TicketNote objects
            
        Returns:
            dict: Mapping of note.id -> note_type
        """
        from apps.logs.models import ActivityLog
        
        note_types = {}
        note_ids = [note.id for note in notes]
        
        if not note_ids:
            return note_types
        
        # Query ActivityLog for all TICKET_NOTE_ADDED events for these notes
        log_entries = ActivityLog.objects.filter(
            event_type='TICKET_NOTE_ADDED',
            entity_type='Ticket',
            entity_id=ticket.id
        ).values('object_id', 'extra_data')
        
        # Build mapping from extra_data which contains note_id and note_type
        for log_entry in log_entries:
            extra_data = log_entry.get('extra_data', {})
            note_id = extra_data.get('note_id')
            note_type = extra_data.get('note_type', 'INTERNAL')
            if note_id:
                try:
                    note_types[int(note_id)] = note_type
                except (ValueError, TypeError):
                    note_types[note_id] = note_type
        
        return note_types
    
    def _log_note_creation(self, actor, ticket: Ticket, note, note_type: str = 'INTERNAL') -> None:
        """
        Log internal note creation to ActivityLog.
        
        Event: TICKET_NOTE_ADDED
        Records: ticket, author, summary of note (first 100 chars)
        Does NOT store full note text (security/privacy)
        Includes: immutable actor info, timestamp, extra metadata, note_type (Phase 3B)
        
        Args:
            actor: User who created the note
            ticket: The ticket being noted
            note: The TicketNote object created
            note_type: Classification of note (INTERNAL, OBSERVATION, DIAGNOSIS, WORK_DONE, ESCALATION)
        """
        from apps.logs.models import ActivityLog
        
        # Get note summary (first 100 chars + ellipsis if longer)
        note_summary = note.text[:100]
        if len(note.text) > 100:
            note_summary += '...'
        
        description = f"Added internal note to ticket (summary: {note_summary})"
        
        ActivityLog.objects.create(
            event_type='TICKET_NOTE_ADDED',
            action='CREATE',
            level='INFO',
            severity='INFO',
            intent='workflow',
            entity_type='Ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role=actor.role,
            title=f'Internal note added to ticket',
            description=description,
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
                'note_type': note_type,  # Phase 3B: Include note classification
                'note_length': len(note.text),
                'author_username': actor.username,
                'author_role': actor.role,
            }
        )
    
    # =========================================================================
    # PHASE 3C: CLIENT / REQUESTER TICKET REVIEWS
    # =========================================================================
    
    def _handle_review_submission(self, request, ticket: Ticket) -> HttpResponse:
        """
        Handle client/requester review submission on a resolved ticket.
        
        Permissions:
        - Only requester (ticket.requester) can submit
        - Only if ticket is RESOLVED or CLOSED
        - Only one review per ticket (unique constraint)
        
        Validates review data, checks permissions, creates TicketReview, logs to ActivityLog.
        Returns redirect with success/error message.
        """
        user = request.user
        
        # Check if user is the ticket requester
        if user != ticket.requester:
            return self._redirect_with_message(request, ticket, 'error', 'Only the ticket requester can submit a review.')
        
        # Check ticket status - must be RESOLVED or CLOSED
        if ticket.status not in ['RESOLVED', 'CLOSED']:
            return self._redirect_with_message(request, ticket, 'error', 'Reviews can only be submitted for resolved or closed tickets.')
        
        # Check if review already exists
        if hasattr(ticket, 'client_review') and ticket.client_review:
            return self._redirect_with_message(request, ticket, 'warning', 'You have already submitted a review for this ticket.')
        
        # Get and validate rating (optional)
        rating_str = request.POST.get('rating', '').strip()
        rating = None
        if rating_str:
            try:
                rating = int(rating_str)
                if rating < 1 or rating > 5:
                    return self._redirect_with_message(request, ticket, 'error', 'Rating must be between 1 and 5.')
            except (ValueError, TypeError):
                return self._redirect_with_message(request, ticket, 'error', 'Invalid rating format.')
        
        # Get and validate comment (optional but recommended)
        comment = request.POST.get('comment', '').strip()
        if len(comment) > 2000:
            return self._redirect_with_message(request, ticket, 'error', 'Comment must be 2000 characters or less.')
        
        # At least rating or comment should be provided
        if not rating and not comment:
            return self._redirect_with_message(request, ticket, 'error', 'Please provide a rating or comment.')
        
        # Create the review (append-only, one-per-ticket)
        from apps.tickets.models import TicketReview
        try:
            review = TicketReview.objects.create(
                ticket=ticket,
                author=user,
                rating=rating,
                comment=comment
            )
        except Exception as e:
            # Handle unique constraint or other DB errors gracefully
            return self._redirect_with_message(request, ticket, 'error', 'A review for this ticket already exists.')
        
        # Log the review submission (metadata only, not full comment)
        self._log_review_submission(user, ticket, review)
        
        # Success message
        return self._redirect_with_message(request, ticket, 'success', 'Thank you for your feedback.')
    
    def _log_review_submission(self, actor, ticket: Ticket, review) -> None:
        """
        Log ticket review submission to ActivityLog.
        
        Event: TICKET_REVIEW_SUBMITTED
        Records: ticket, author, rating (if provided)
        Does NOT store full comment text (privacy)
        Includes: immutable actor info, timestamp, extra metadata
        """
        from apps.logs.models import ActivityLog
        
        description = f"Client submitted review for ticket (rating: {review.rating if review.rating else 'N/A'})"
        
        ActivityLog.objects.create(
            event_type='TICKET_REVIEW_SUBMITTED',
            action='CREATE',
            level='INFO',
            severity='INFO',
            intent='feedback',
            entity_type='Ticket',
            entity_id=ticket.id,
            actor_type='user',
            actor_id=str(actor.id),
            actor_name=actor.username,
            actor_role='CLIENT',  # Always CLIENT for reviews
            title=f'Client review submitted',
            description=description,
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
            }
        )
    
    def _redirect_with_message(self, request, ticket: Ticket, message_type: str, message: str) -> HttpResponse:
        """
        Redirect back to ticket detail with a flash message.
        
        Args:
            request: The HTTP request
            ticket: The Ticket instance
            message_type: 'success', 'error', 'warning', or 'info'
            message: The message text
            
        Returns:
            HttpResponse: Redirect response
        """
        # Use Django's messages framework
        from django.contrib import messages
        
        if message_type == 'success':
            messages.success(request, message)
        elif message_type == 'error':
            messages.error(request, message)
        elif message_type == 'warning':
            messages.warning(request, message)
        else:
            messages.info(request, message)
        
        return redirect('frontend:ticket_detail', ticket_id=ticket.ticket_id)
    
    def _get_client_ip(self, request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: The HTTP request
            
        Returns:
            str: Client IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_context_data(self, **kwargs):
        """
        Build context with:
        - Ticket data (already in object)
        - Activity log entries (paginated from ActivityLog)
        - Assignment control data (for template form)
        - Permission flags
        """
        context = super().get_context_data(**kwargs)
        ticket = self.object
        user = self.request.user
        
        # =====================================================================
        # ACTIVITY LOG - Source of truth for all ticket events
        # =====================================================================
        # Query ActivityLog filtered by this ticket
        activity_entries = ActivityLog.objects.filter(
            entity_type='Ticket',
            entity_id=ticket.id
        ).select_related(
            'user'  # Optional: if you have user FK for legacy data
        ).order_by('-timestamp')  # Newest first
        
        # Paginate activity log (10 entries per page)
        paginator = Paginator(activity_entries, per_page=10)
        page_number = self.request.GET.get('activity_page', 1)
        activities_page = paginator.get_page(page_number)
        
        context['activities'] = activities_page
        context['activities_count'] = activity_entries.count()
        
        # =====================================================================
        # METADATA FOR DISPLAY
        # =====================================================================
        context['ticket_status_display'] = ticket.get_status_display()
        context['ticket_priority_display'] = ticket.get_priority_display()
        context['ticket_impact_display'] = ticket.get_impact_display()
        context['ticket_urgency_display'] = ticket.get_urgency_display()
        
        # =====================================================================
        # ASSIGNMENT CONTROLS - for Phase 2A mutation
        # =====================================================================
        authority = TicketAuthority()
        context['can_assign_other'] = authority.can_assign(user, ticket, None)
        context['can_self_assign'] = authority.can_self_assign(user, ticket)
        context['can_assign'] = context['can_assign_other'] or context['can_self_assign']
        
        # Get available technicians for dropdown (only if user can assign)
        if context['can_assign']:
            context['available_technicians'] = self._get_available_technicians(user)
        else:
            context['available_technicians'] = []
        
        # =====================================================================
        # STATUS CHANGE CONTROLS - for Phase 2B mutation
        # =====================================================================
        context['can_change_status'] = authority.can_edit(user, ticket)
        
        # Get available status transitions for dropdown (only if user can edit)
        if context['can_change_status']:
            allowed_transitions = self._get_allowed_transitions(user, ticket)
            context['available_status_transitions'] = [
                (status_code, dict(Ticket.STATUS_CHOICES)[status_code])
                for status_code in allowed_transitions
            ]
        else:
            context['available_status_transitions'] = []
        
        # =====================================================================
        # PRIORITY CHANGE CONTROLS - for Phase 2C mutation
        # =====================================================================
        context['can_change_priority'] = self._can_change_priority(user)
        
        # Get available priorities (all priorities can be set, no transitions) 
        if context['can_change_priority']:
            context['available_priorities'] = [
                (priority_code, dict(Ticket.PRIORITY_CHOICES)[priority_code])
                for priority_code in [code for code, _ in Ticket.PRIORITY_CHOICES]
            ]
        else:
            context['available_priorities'] = []
        
        # =====================================================================
        # INTERNAL NOTES CONTROLS - for Phase 3A/3B feature
        # =====================================================================
        context['can_add_note'] = self._can_add_note(user, ticket)
        
        # Get internal notes for display (chronological, staff-only)
        from apps.tickets.models import TicketNote
        internal_notes = TicketNote.objects.filter(ticket=ticket).select_related('author').order_by('created_at')
        context['internal_notes'] = internal_notes
        context['internal_notes_count'] = internal_notes.count()
        
        # Phase 3B: Get note type mapping from ActivityLog for badge display
        context['note_types'] = self._get_note_types_from_log(ticket, internal_notes)
        
        # Phase 3B: Get last internal note for sidebar widget (if exists)
        context['last_internal_note'] = internal_notes.last() if internal_notes.exists() else None
        if context['last_internal_note']:
            context['last_internal_note_type'] = context['note_types'].get(
                context['last_internal_note'].id, 'INTERNAL'
            )
        
        # =====================================================================
        # CLIENT REVIEW - for Phase 3C feature
        # =====================================================================
        # Check if review can be submitted by requester
        has_existing_review = hasattr(ticket, 'client_review') and ticket.client_review is not None
        context['can_submit_review'] = (
            user == ticket.requester and 
            ticket.status in ['RESOLVED', 'CLOSED'] and
            not has_existing_review
        )
        
        # Get existing review if present (for display)
        context['client_review'] = getattr(ticket, 'client_review', None)
        context['has_review'] = context['client_review'] is not None
        
        # =====================================================================
        # PERMISSION FLAGS (for template rendering)
        # Only used to determine what sections to show
        # =====================================================================
        context['can_view'] = authority.can_view(user, ticket)
        
        # Can current user see internal notes? (staff only)
        context['is_staff'] = user.role in [
            'SUPERADMIN', 'MANAGER', 'IT_ADMIN', 'TECHNICIAN'
        ]
        
        # =====================================================================
        # EMPTY STATE HANDLING
        # =====================================================================
        # If no activities, provide helpful message based on context
        if not context['activities_count']:
            context['no_activities_reason'] = (
                "No activity recorded yet. Ticket created at {}".format(
                    ticket.created_at.strftime('%b %d, %Y %H:%M')
                )
            )
        
        return context
    
    def _get_available_technicians(self, current_user) -> list:
        """
        Get list of available technicians for assignment.
        
        Rules:
        - Admin/Manager/IT_Admin: All active technicians
        - Technician: Only self
        
        Args:
            current_user: Current user
            
        Returns:
            list: List of (user_id, user_name) tuples
        """
        if current_user.role in ['SUPERADMIN', 'MANAGER', 'IT_ADMIN']:
            # Admins can assign to any active technician
            technicians = User.objects.filter(
                role='TECHNICIAN',
                is_active=True
            ).values_list('id', 'username').order_by('username')
        elif current_user.role == 'TECHNICIAN':
            # Technician can only assign to self
            technicians = User.objects.filter(
                id=current_user.id,
                is_active=True
            ).values_list('id', 'username')
        else:
            technicians = []
        
        return list(technicians)
