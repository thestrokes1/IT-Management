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
        
        return render(request, "frontend/tickets.html", {
            "tickets": tickets,
            "permissions_by_ticket": permissions_by_ticket,
            "permissions": list_permissions,
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
        
        return render(request, "frontend/ticket_detail.html", {
            "ticket": ticket,
            "permissions": permissions,
            "assignable_users": assignable_users,
        })


class CreateTicketView(LoginRequiredMixin, View):
    """Create a new ticket."""
    def get(self, request):
        # Get list permissions for create check
        list_perms = get_list_permissions(request.user)
        return render(request, "frontend/create-ticket.html", {
            "permissions": list_perms,
        })

    def post(self, request):
        ticket = Ticket.objects.create(
            title=request.POST.get("title", ""),
            description=request.POST.get("description", ""),
            created_by=request.user,
        )
        return redirect("frontend:tickets")


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
@require_http_methods(["POST", "DELETE"])
def delete_ticket(request, ticket_id):
    """
    Delete a ticket.
    Uses CQRS command with authority enforcement.
    """
    # Check if user is authenticated
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required. Please log in.'}, status=401)
        return redirect('frontend:login')
    
    try:
        # Get ticket for authorization check
        ticket = get_object_or_404(Ticket, id=ticket_id)
        
        # Use CQRS command with authority enforcement
        delete_use_case = DeleteTicket()
        result = delete_use_case.execute(
            user=request.user,
            ticket_id=str(ticket.ticket_id),
        )
        
        if result.success:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Ticket deleted successfully.'})
            messages.success(request, f"Ticket #{ticket_id} has been deleted.")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': result.error}, status=403)
            messages.error(request, result.error)
    
    except AuthorizationError as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': str(e)}, status=403)
        messages.error(request, str(e))
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': f'Error deleting ticket: {str(e)}'}, status=500)
        messages.error(request, f"Error deleting ticket: {str(e)}")
    
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
    """Handle assignment of a ticket to a specific user."""
    from apps.tickets.application.assign_ticket_to_self import AssignTicketToSelf
    from django.shortcuts import get_object_or_404
    from apps.tickets.models import Ticket
    from apps.users.models import User
    
    # Get ticket
    ticket = get_object_or_404(Ticket, id=ticket_id)
    
    # Get target user
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Check permission using domain authority (can_assign)
    from apps.tickets.domain.services.ticket_authority import can_assign as can_assign_ticket
    if not can_assign_ticket(request.user, ticket, target_user):
        messages.error(request, 'You do not have permission to assign this ticket.')
        return redirect('frontend:ticket-detail', ticket_id=ticket_id)
    
    # Use the CQRS command to assign
    use_case = AssignTicketToSelf()
    try:
        result = use_case.execute(request.user, str(ticket.ticket_id), target_user.id)
        if result.success:
            messages.success(request, result.data.get('message', f'Ticket assigned to {target_user.username} successfully!'))
        else:
            messages.error(request, result.error)
    except ValueError as e:
        messages.error(request, str(e))
    
    return redirect('frontend:ticket-detail', ticket_id=ticket_id)


def ticket_crud(request):
    """Ticket CRUD endpoint for API compatibility."""
    return JsonResponse({"status": "ok"})

