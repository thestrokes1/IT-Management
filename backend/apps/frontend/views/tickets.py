"""
Ticket views for IT Management Platform.
Contains all ticket-related views (list, create, edit, delete).

STRICT RBAC ENFORCEMENT:
- All permission checks use domain authority layer (ticket_authority)
- NO role checks in views - all permissions delegated to authority
- CQRS commands handle business logic with authority validation
- Views translate domain permissions to UI flags via permissions_mapper
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from apps.tickets.models import Ticket
from apps.tickets.domain.services.ticket_authority import (
    get_permissions as get_ticket_permissions,
    can_view as can_view_ticket,
    can_edit as can_edit_ticket,
    can_delete as can_delete_ticket,
    can_assign as can_assign_ticket,
    can_unassign as can_unassign_ticket,
    can_assign_to_self as can_assign_to_self_ticket,
    can_unassign_self as can_unassign_self_ticket,
    can_close as can_close_ticket,
    can_reopen as can_reopen_ticket,
    can_cancel as can_cancel_ticket,
    can_resolve as can_resolve_ticket,
)
from apps.core.domain.authorization import AuthorizationError
from apps.tickets.application.update_ticket import UpdateTicket
from apps.tickets.application.delete_ticket import DeleteTicket
from apps.tickets.application.assign_ticket_to_self import AssignTicketToSelf
from apps.frontend.permissions_mapper import (
    build_ticket_ui_permissions,
    build_tickets_permissions_map,
    get_list_permissions,
)


class TicketsView(LoginRequiredMixin, View):
    """
    List all tickets with proper RBAC enforcement.
    
    Passes permissions_by_ticket mapping to template for UI permission flags.
    Uses permissions_mapper to translate domain authority to UI flags.
    
    UI Permission Flags Contract:
    {
        "can_view": bool,
        "can_update": bool,
        "can_delete": bool,
        "can_assign": bool,
        "can_unassign": bool,
        "can_self_assign": bool,
        "assigned_to_me": bool,
    }
    """
    def get(self, request):
        tickets = Ticket.objects.all().order_by('-created_at')
        
        # Build permissions map using authority via permissions_mapper
        permissions_by_ticket = build_tickets_permissions_map(request.user, tickets)
        
        # Get list-level permissions
        list_permissions = get_list_permissions(request.user)
        
        # Get page-specific actions using the new template tag
        from apps.frontend.templatetags.page_actions import get_page_actions
        page_key = 'tickets'
        if request.resolver_match:
            # Determine page key from URL name
            url_name = request.resolver_match.url_name
            if 'detail' in url_name:
                page_key = 'ticket_detail'
            elif 'create' in url_name:
                page_key = 'create-ticket'
            elif 'edit' in url_name:
                page_key = 'edit-ticket'
        
        allowed_actions = get_page_actions(page_key, request.user)
        
        return render(request, "frontend/tickets.html", {
            "tickets": tickets,
            "permissions_by_ticket": permissions_by_ticket,
            "permissions": list_permissions,
            "allowed_actions": allowed_actions,
            "page_key": page_key,
        })


class TicketDetailView(LoginRequiredMixin, View):
    """
    Ticket detail view with permission flags for template.
    
    Uses domain authority to compute all permission flags via permissions_mapper.
    """
    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Check view permission using authority
        if not can_view_ticket(request.user, ticket):
            raise PermissionDenied("You don't have permission to view this ticket.")
        
        # Build UI permission flags using permissions_mapper
        permissions = build_ticket_ui_permissions(request.user, ticket)
        
        # Add additional context flags for template
        permissions['is_assigned'] = ticket.assigned_to_id is not None
        
        # Get list of assignable users based on role
        from apps.users.models import User
        user = request.user
        
        if user.role in ['SUPERADMIN', 'MANAGER', 'IT_ADMIN']:
            # Show all technicians for assignment
            assignable_users = User.objects.filter(role='TECHNICIAN', is_active=True).order_by('username')
        elif user.role == 'TECHNICIAN':
            # Technician can only see themselves for self-assignment
            assignable_users = User.objects.filter(id=user.id)
        else:
            assignable_users = User.objects.none()
        
        # Get activity timeline for this ticket
        from apps.logs.models import ActivityLog
        from apps.logs.services.activity_service import ActivityService
        
        activities = []
        try:
            # Fetch activities related to this ticket
            activities = ActivityLog.objects.filter(
                Q(model_name='ticket') & Q(object_id=ticket.id)
            ).select_related('user').order_by('-timestamp')[:50]
            
            # Format activities for template using ActivityService
            service = ActivityService()
            activities = [
                {
                    'actor_username': activity.user.username if activity.user else 'System',
                    'actor_role': activity.user.role if activity.user else 'SYSTEM',
                    'action': activity.action,
                    'action_label': service._get_action_label(activity.action),
                    'description': activity.description,
                    'created_at': activity.timestamp,
                    'metadata': activity.extra_data or {},
                }
                for activity in activities
            ]
        except Exception:
            activities = []
        
        return render(request, "frontend/ticket_detail.html", {
            "ticket": ticket,
            "permissions": permissions,
            "assignable_users": assignable_users,
            "activities": activities,
        })


class CreateTicketView(LoginRequiredMixin, View):
    """Create a new ticket."""
    def get(self, request):
        # Get categories and ticket types for the form
        from apps.tickets.models import TicketCategory, TicketType
        from apps.users.models import User
        
        categories = TicketCategory.objects.filter(is_active=True).order_by('name')
        ticket_types = TicketType.objects.filter(is_active=True).order_by('name')
        
        # Get list permissions for create check
        list_perms = get_list_permissions(request.user)
        
        return render(request, "frontend/create-ticket.html", {
            "permissions": list_perms,
            "categories": categories,
            "ticket_types": ticket_types,
            "available_users": User.objects.filter(is_active=True).order_by('username'),
            "assign_config": {
                "visible": True,
                "readonly": False,
                "default_user_id": None,
            },
        })

    def post(self, request):
        from apps.tickets.models import Ticket, TicketCategory, TicketType
        from apps.tickets.application.create_ticket import CreateTicket
        from django.utils import timezone
        from datetime import datetime
        from apps.users.models import User
        
        # Get form data
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        category_id = request.POST.get("category", "")
        ticket_type_id = request.POST.get("ticket_type", "")
        priority = request.POST.get("priority", "MEDIUM")
        impact = request.POST.get("impact", "MEDIUM")
        urgency = request.POST.get("urgency", "MEDIUM")
        assigned_to_id = request.POST.get("assigned_to", "")
        due_date_str = request.POST.get("due_date", "")
        
        # Validate required fields
        errors = []
        if not title:
            errors.append("Title is required")
        if not description:
            errors.append("Description is required")
        if not category_id:
            errors.append("Category is required")
        if not priority:
            errors.append("Priority is required")
        
        if errors:
            for error in errors:
                messages.error(request, error)
            # Re-render form with entered data
            categories = TicketCategory.objects.filter(is_active=True).order_by('name')
            ticket_types = TicketType.objects.filter(is_active=True).order_by('name')
            return render(request, "frontend/create-ticket.html", {
                "permissions": {"can_create": True},
                "categories": categories,
                "ticket_types": ticket_types,
                "available_users": User.objects.filter(is_active=True).order_by('username'),
                "form": {
                    "title": {"value": title},
                    "description": {"value": description},
                    "priority": {"value": priority},
                    "impact": {"value": impact},
                    "urgency": {"value": urgency},
                    "category": {"value": category_id},
                    "ticket_type": {"value": ticket_type_id},
                    "assigned_to": {"value": assigned_to_id},
                    "due_date": {"value": due_date_str},
                },
                "assign_config": {
                    "visible": True,
                    "readonly": False,
                    "default_user_id": None,
                },
            })
        
        # Use CQRS command for ticket creation (includes activity logging)
        create_use_case = CreateTicket()
        try:
            result = create_use_case.execute(
                actor=request.user,
                ticket_data={
                    'title': title,
                    'description': description,
                    'category_id': category_id,
                    'ticket_type_id': ticket_type_id if ticket_type_id else None,
                    'priority': priority,
                    'impact': impact,
                    'urgency': urgency,
                }
            )
            
            if result.success:
                messages.success(request, f"Ticket '{title}' created successfully!")
                return redirect("frontend:tickets")
            else:
                messages.error(request, result.error)
        except Exception as e:
            messages.error(request, f"Error creating ticket: {str(e)}")
        
        # If we get here, re-render form with errors
        categories = TicketCategory.objects.filter(is_active=True).order_by('name')
        ticket_types = TicketType.objects.filter(is_active=True).order_by('name')
        return render(request, "frontend/create-ticket.html", {
            "permissions": {"can_create": True},
            "categories": categories,
            "ticket_types": ticket_types,
            "available_users": User.objects.filter(is_active=True).order_by('username'),
            "form": {
                "title": {"value": title},
                "description": {"value": description},
                "priority": {"value": priority},
                "impact": {"value": impact},
                "urgency": {"value": urgency},
                "category": {"value": category_id},
                "ticket_type": {"value": ticket_type_id},
                "assigned_to": {"value": assigned_to_id},
                "due_date": {"value": due_date_str},
            },
            "assign_config": {
                "visible": True,
                "readonly": False,
                "default_user_id": None,
            },
        })


class EditTicketView(LoginRequiredMixin, View):
    """
    Edit ticket view with authority-based access control.
    Uses domain authority to check edit permission.
    """
    def get(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Check edit permission using authority
        if not can_edit_ticket(request.user, ticket):
            messages.error(request, "You don't have permission to edit this ticket.")
            return redirect("frontend:ticket-detail", ticket_id=pk)
        
        # Build UI permission flags for template consistency
        permissions = build_ticket_ui_permissions(request.user, ticket)
        
        return render(request, "frontend/edit-ticket.html", {
            "ticket": ticket,
            "permissions": permissions,
        })

    def post(self, request, pk):
        ticket = get_object_or_404(Ticket, pk=pk)
        
        # Use CQRS command with authority check
        update_use_case = UpdateTicket()
        result = update_use_case.execute(
            user=request.user,
            ticket_id=str(ticket.ticket_id),
            ticket_data={
                'title': request.POST.get("title", ticket.title),
                'description': request.POST.get("description", ticket.description),
            }
        )
        
        if result.success:
            messages.success(request, "Ticket updated successfully.")
            return redirect("frontend:ticket-detail", ticket_id=pk)
        else:
            messages.error(request, result.error)
            return render(request, "frontend/edit-ticket.html", {
                "ticket": ticket
            })


# Function-based views for URLs
def tickets(request):
    """List all tickets."""
    view = TicketsView.as_view()
    return view(request)


def ticket_detail(request, ticket_id):
    """Show ticket detail."""
    view = TicketDetailView.as_view()
    return view(request, pk=ticket_id)


def create_ticket(request):
    """Create a new ticket."""
    view = CreateTicketView.as_view()
    return view(request)


def edit_ticket(request, ticket_id):
    """Edit a ticket."""
    view = EditTicketView.as_view()
    return view(request, pk=ticket_id)


@login_required
@require_http_methods(["POST"])
def cancel_ticket(request, ticket_id):
    """
    Cancel a ticket.
    Uses domain authority for permission check.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check permission using domain authority
    if not can_cancel_ticket(request.user, ticket):
        messages.error(request, "You do not have permission to cancel this ticket.")
        return redirect("frontend:ticket-detail", ticket_id=ticket_id)
    
    # Only open or new tickets can be cancelled
    if ticket.status not in ['NEW', 'OPEN']:
        messages.error(request, "Only new or open tickets can be cancelled.")
        return redirect("frontend:ticket-detail", ticket_id=ticket_id)
    
    ticket.status = 'CANCELLED'
    ticket.save()
    messages.success(request, f"Ticket #{ticket.id} has been cancelled.")
    return redirect("frontend:tickets")


@login_required
@require_http_methods(["POST"])
def delete_ticket(request, ticket_id):
    """
    Delete a ticket.
    Uses TicketService with raw SQL to bypass signal issues.
    """
    from django.db import connection
    from apps.tickets.models import Ticket
    from apps.tickets.domain.services.ticket_authority import can_delete as can_delete_ticket
    
    # Get ticket for authorization check
    try:
        ticket = Ticket.objects.get(id=ticket_id)
    except Ticket.DoesNotExist:
        error_msg = f"Ticket with id {ticket_id} not found."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=404)
        messages.error(request, error_msg)
        return redirect("frontend:tickets")
    
    # Check permission using domain authority
    if not can_delete_ticket(request.user, ticket):
        error_msg = "You do not have permission to delete this ticket."
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=403)
        messages.error(request, error_msg)
        return redirect("frontend:tickets")
    
    ticket_db_id = ticket.id
    
    # Use raw SQL to avoid signal interference
    try:
        with connection.cursor() as cursor:
            # Delete related records first
            cursor.execute("DELETE FROM ticket_attachments WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_comments WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_history WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_escalations WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_satisfaction WHERE ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM ticket_status_history WHERE ticket_id = %s", [ticket_db_id])
            
            # Clear related tickets (many-to-many)
            cursor.execute("DELETE FROM tickets_related_tickets WHERE from_ticket_id = %s", [ticket_db_id])
            cursor.execute("DELETE FROM tickets_related_tickets WHERE to_ticket_id = %s", [ticket_db_id])
            
            # Update child tickets
            cursor.execute("UPDATE tickets SET parent_ticket_id = NULL WHERE parent_ticket_id = %s", [ticket_db_id])
            
            # Finally delete the ticket itself
            cursor.execute("DELETE FROM tickets WHERE id = %s", [ticket_db_id])
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f'Error deleting ticket: {str(e)}'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': error_msg}, status=500)
        messages.error(request, error_msg)
        return redirect("frontend:tickets")
    
    success_msg = f"Ticket #{ticket_id} has been deleted."
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'message': success_msg})
    messages.success(request, success_msg)
    return redirect("frontend:tickets")


@login_required
@require_http_methods(["POST"])
def reopen_ticket(request, ticket_id):
    """
    Reopen a closed or cancelled ticket.
    Uses domain authority for permission check.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check permission using domain authority
    if not can_reopen_ticket(request.user, ticket):
        messages.error(request, "You do not have permission to reopen this ticket.")
        return redirect("frontend:ticket-detail", ticket_id=ticket_id)
    
    # Only closed or cancelled tickets can be reopened
    if ticket.status not in ['CLOSED', 'CANCELLED', 'RESOLVED']:
        messages.error(request, "Only closed, cancelled, or resolved tickets can be reopened.")
        return redirect("frontend:ticket-detail", ticket_id=ticket_id)
    
    ticket.status = 'OPEN'
    ticket.closed_at = None
    ticket.save()
    messages.success(request, f"Ticket #{ticket.id} has been reopened.")
    return redirect("frontend:ticket-detail", ticket_id=ticket_id)


@login_required
@require_http_methods(["POST"])
def ticket_assign_self(request, ticket_id):
    """
    Assign ticket to self using CQRS command.
    Uses domain authority for permission check.
    """
    if not request.user.is_authenticated:
        return HttpResponseForbidden()
    
    ticket = get_object_or_404(Ticket, pk=ticket_id)
    
    # Check permission using domain authority
    if not can_assign_to_self_ticket(request.user, ticket):
        messages.error(request, "You cannot assign this ticket to yourself.")
        return redirect("frontend:ticket-detail", ticket_id=ticket_id)
    
    # Use CQRS command
    use_case = AssignTicketToSelf()
    result = use_case.execute(
        user=request.user,
        ticket_id=str(ticket.ticket_id)
    )
    
    if result.success:
        messages.success(request, result.data.get('message', 'Ticket assigned to you successfully!'))
    else:
        messages.error(request, result.error)
    
    return redirect("frontend:ticket-detail", ticket_id=ticket_id)


@login_required
@require_http_methods(["POST"])
def ticket_assign_to_user(request, ticket_id, user_id):
    """
    Assign a ticket to a specific user.
    For IT_ADMIN, MANAGER, SUPERADMIN to assign to any user.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Get target user
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Check permission using domain authority
    from apps.tickets.domain.services.ticket_authority import can_assign as can_assign_ticket
    if not can_assign_ticket(request.user, ticket, target_user):
        messages.error(request, 'You do not have permission to assign this ticket.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Store old assignee for logging
    old_assignee = ticket.assigned_to
    old_assignee_name = old_assignee.username if old_assignee else None
    
    # Perform the assignment directly
    ticket.assigned_to = target_user
    ticket.assignment_status = 'ASSIGNED'
    ticket.updated_by = request.user
    ticket.save()
    
    # Emit domain event for activity logging
    from apps.tickets.domain.events import emit_ticket_assigned
    emit_ticket_assigned(
        ticket_id=ticket.id,
        ticket_title=ticket.title,
        actor=request.user,
        assignee_id=target_user.id,
        assignee_username=target_user.username,
        previous_assignee_id=old_assignee.id if old_assignee else None,
        previous_assignee_username=old_assignee_name,
    )
    
    messages.success(request, f'Ticket assigned to {target_user.username} successfully!')
    return redirect('frontend:ticket-detail', ticket_id=ticket_id)


@login_required
@require_http_methods(["POST"])
def ticket_unassign_self(request, ticket_id):
    """
    Unassign ticket from self.
    
    Uses domain authority for permission check.
    Only the assigned user or admin roles can unassign.
    """
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from apps.tickets.models import Ticket
    from apps.tickets.domain.services.ticket_authority import (
        can_unassign_self as can_unassign_self_ticket,
    )
    
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Check if user has permission (only assigned user or admin)
    if not can_unassign_self_ticket(request.user, ticket):
        messages.error(request, 'You do not have permission to unassign this ticket.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Store old assignee for event
    old_assignee = ticket.assigned_to
    old_assignee_name = old_assignee.username if old_assignee else "Unassigned"
    
    # Perform unassignment
    ticket.assigned_to = None
    ticket.assignment_status = 'UNASSIGNED'
    ticket.updated_by = request.user
    ticket.save()
    
    # Emit domain event
    from apps.tickets.domain.events import emit_ticket_unassigned
    emit_ticket_unassigned(
        ticket_id=ticket.id,
        ticket_title=ticket.title,
        actor=request.user,
        unassigned_user_id=old_assignee.id if old_assignee else None,
        unassigned_username=old_assignee_name,
    )
    
    messages.success(request, f'Ticket unassigned from {old_assignee_name}.')
    return redirect('frontend:ticket-detail', ticket_id=ticket_id)


def ticket_crud(request):
    """Ticket CRUD endpoint for API compatibility."""
    return JsonResponse({"status": "ok"})

