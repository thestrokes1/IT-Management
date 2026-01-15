# Ticket views for IT Management Platform.
# Contains all ticket-related views (list, create, edit, delete).
# Uses CQRS pattern: Queries for reads, Services for writes.

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
import json

from apps.frontend.mixins import CanManageTicketsMixin
from apps.frontend.services import TicketService
from apps.tickets.queries import TicketQuery
from apps.tickets.domain.services.ticket_authority import (
    get_ticket_permissions, 
    can_create_ticket as ticket_can_create,
    assert_can_delete_ticket,
    assert_can_update_ticket,
)
from apps.core.domain.authorization import AuthorizationError


def get_assign_field_config(user):
    """
    Get assignment field configuration based on user role.
    Used by templates to control assign field visibility and editability.
    """
    role = getattr(user, 'role', None)

    if role == 'VIEWER':
        return {'visible': False, 'readonly': False, 'default_user_id': None}

    if role == 'TECHNICIAN':
        return {
            'visible': True,
            'readonly': True,
            'default_user_id': user.id
        }

    # IT_ADMIN, MANAGER, SUPERADMIN
    return {
        'visible': True,
        'readonly': False,
        'default_user_id': None
    }


class TicketsView(LoginRequiredMixin, TemplateView):
    """
    Tickets management web interface.
    Uses TicketQuery for read operations.
    """
    template_name = 'frontend/tickets.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tickets = TicketQuery.get_all()
        status_choices = TicketQuery.get_status_choices()
        priority_choices = TicketQuery.get_priority_choices()

        # Compute permissions map for each ticket
        permissions_map = {
            ticket.id: get_ticket_permissions(self.request.user, ticket)
            for ticket in tickets
        }

        context.update({
            'tickets': tickets,
            'status_choices': status_choices,
            'priority_choices': priority_choices,
            'permissions_map': permissions_map,
        })
        return context


class CreateTicketView(LoginRequiredMixin, TemplateView):
    """
    Create new support ticket web interface.
    Uses TicketQuery for reads, TicketService for writes.
    """
    template_name = 'frontend/create-ticket.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = TicketQuery.get_categories()
        ticket_types = TicketQuery.get_types()
        available_users = TicketQuery.get_active_users()

        # Assignment field configuration
        assign_config = get_assign_field_config(self.request.user)

        # Pass permissions object for template consistency
        permissions = {
            'can_create': ticket_can_create(self.request.user),
        }

        context.update({
            'categories': categories,
            'ticket_types': ticket_types,
            'available_users': available_users,
            'assign_config': assign_config,
            'form': {},
            'permissions': permissions,
        })
        return context

    def post(self, request, *args, **kwargs):
        """Handle ticket creation using Service."""
        # Check domain permission
        if not ticket_can_create(request.user):
            messages.error(request, 'You do not have permission to create tickets.')
            return redirect('frontend:tickets')
        
        try:
            ticket = TicketService.create_ticket(
                request=request,
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                category_id=request.POST.get('category', ''),
                ticket_type_id=request.POST.get('ticket_type', ''),
                priority=request.POST.get('priority', 'MEDIUM'),
                impact=request.POST.get('impact', 'MEDIUM'),
                urgency=request.POST.get('urgency', 'MEDIUM'),
                assigned_to_id=request.POST.get('assigned_to', ''),
                due_date=request.POST.get('due_date', '')
            )

            messages.success(request, f'Ticket #{ticket.id} created successfully!')
            return redirect('frontend:tickets')

        except Exception as e:
            messages.error(request, f'Error creating ticket: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class EditTicketView(CanManageTicketsMixin, TemplateView):
    """
    Edit ticket web interface.
    Uses TicketQuery for reads, TicketService for writes.
    """
    template_name = 'frontend/edit-ticket.html'
    login_url = 'frontend:login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_id = self.kwargs.get('ticket_id')

        ticket = TicketQuery.get_with_details(ticket_id)

        if ticket is None:
            messages.error(self.request, 'Ticket not found.')
            return redirect('frontend:tickets')

        categories = TicketQuery.get_categories()
        ticket_types = TicketQuery.get_types()
        available_users = TicketQuery.get_active_users()

        # Compute permissions once per request
        ticket_perms = get_ticket_permissions(self.request.user, ticket)

        # Assignment field configuration
        assign_config = get_assign_field_config(self.request.user)

        context.update({
            'ticket': ticket,
            'categories': categories,
            'ticket_types': ticket_types,
            'available_users': available_users,
            'ticket_perms': ticket_perms,
            'assign_config': assign_config,
            'form': {}
        })
        return context

    def post(self, request, *args, **kwargs):
        """Handle ticket edit using Service."""
        try:
            ticket_id = self.kwargs.get('ticket_id')

            ticket = TicketService.update_ticket(
                request=request,
                ticket_id=ticket_id,
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                category_id=request.POST.get('category', ''),
                ticket_type_id=request.POST.get('ticket_type', ''),
                status=request.POST.get('status', 'NEW'),
                priority=request.POST.get('priority', 'MEDIUM'),
                impact=request.POST.get('impact', 'MEDIUM'),
                urgency=request.POST.get('urgency', 'MEDIUM'),
                assigned_to_id=request.POST.get('assigned_to', ''),
                assigned_team=request.POST.get('assigned_team', ''),
                location=request.POST.get('location', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                contact_email=request.POST.get('contact_email', ''),
                sla_due_at_str=request.POST.get('sla_due_at', ''),
                resolution_summary=request.POST.get('resolution_summary', '')
            )

            messages.success(request, f'Ticket #{ticket.id} updated successfully!')
            return redirect('frontend:tickets')

        except Exception as e:
            messages.error(request, f'Error updating ticket: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def ticket_crud(request, ticket_id):
    """
    Handle ticket CRUD operations (DELETE and PATCH).
    Uses TicketService for write operations.
    Uses domain authority for authorization.
    """
    try:
        # Get ticket for authorization check
        ticket = TicketQuery.get_by_id(ticket_id)
        if ticket is None:
            return JsonResponse({'error': f'Ticket with id {ticket_id} not found.'}, status=404)
        
        if request.method == 'DELETE':
            # Check domain permission
            assert_can_delete_ticket(request.user, ticket)
            TicketService.delete_ticket(ticket_id)
            return JsonResponse({'success': True, 'message': 'Ticket deleted successfully.'})

        elif request.method == 'PATCH':
            # Check domain permission
            assert_can_update_ticket(request.user, ticket)
            data = json.loads(request.body)
            ticket = TicketService.partial_update_ticket(ticket_id, data)
            return JsonResponse({'success': True, 'message': f'Ticket "{ticket.title}" updated successfully.'})

    except AuthorizationError as e:
        return JsonResponse({'error': str(e)}, status=403)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

