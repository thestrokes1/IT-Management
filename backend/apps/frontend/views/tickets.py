"""
Ticket views for IT Management Platform.
Contains all ticket-related views (list, create, edit, delete, API).
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import datetime
import json

try:
    from apps.users.models import User
    from apps.tickets.models import Ticket, TicketComment, TicketCategory, TicketType
except ImportError:
    User = None
    Ticket = None


class TicketsView(LoginRequiredMixin, TemplateView):
    """
    Tickets management web interface.
    """
    template_name = 'frontend/tickets.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            tickets = Ticket.objects.select_related('created_by', 'assigned_to', 'category', 'ticket_type').order_by('-created_at')[:50]
            status_choices = Ticket.STATUS_CHOICES
            priority_choices = Ticket.PRIORITY_CHOICES
        except:
            tickets = []
            status_choices = []
            priority_choices = []
        context.update({
            'tickets': tickets,
            'status_choices': status_choices,
            'priority_choices': priority_choices
        })
        return context


class CreateTicketView(LoginRequiredMixin, TemplateView):
    """
    Create new support ticket web interface.
    """
    template_name = 'frontend/create-ticket.html'
    login_url = 'frontend:login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            categories = TicketCategory.objects.filter(is_active=True)
            ticket_types = TicketType.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
        except:
            categories = []
            ticket_types = []
            available_users = []
        context.update({
            'categories': categories,
            'ticket_types': ticket_types,
            'available_users': available_users,
            'form': {}
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle ticket creation."""
        try:
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category', '')
            ticket_type_id = request.POST.get('ticket_type', '')
            priority = request.POST.get('priority', 'MEDIUM')
            impact = request.POST.get('impact', 'MEDIUM')
            urgency = request.POST.get('urgency', 'MEDIUM')
            assigned_to_id = request.POST.get('assigned_to', '')
            due_date = request.POST.get('due_date', '')
            
            # Validation
            errors = {}
            if not title:
                errors['title'] = 'Title is required'
            if not description:
                errors['description'] = 'Description is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not priority:
                errors['priority'] = 'Priority is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Create ticket
            category = TicketCategory.objects.get(id=category_id)
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else None
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            # Parse due_date and convert to sla_due_at
            sla_due_at = None
            if due_date:
                try:
                    due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                    sla_due_at = timezone.make_aware(
                        timezone.datetime.combine(due_date_obj, timezone.datetime.min.time())
                    )
                except ValueError:
                    pass
            
            ticket = Ticket.objects.create(
                title=title,
                description=description,
                category=category,
                ticket_type=ticket_type,
                priority=priority,
                impact=impact,
                urgency=urgency,
                assigned_to=assigned_to,
                sla_due_at=sla_due_at,
                requester=request.user,
                created_by=request.user,
                status='NEW'
            )
            
            messages.success(request, f'Ticket #{ticket.id} created successfully!')
            return redirect('frontend:tickets')
        
        except Exception as e:
            messages.error(request, f'Error creating ticket: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


class EditTicketView(LoginRequiredMixin, TemplateView):
    """
    Edit ticket web interface.
    """
    template_name = 'frontend/edit-ticket.html'
    login_url = 'frontend:login'
    
    def dispatch(self, request, ticket_id, *args, **kwargs):
        """Check if user can manage tickets."""
        if not hasattr(request.user, 'can_manage_tickets') or not request.user.can_manage_tickets:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'You do not have permission to edit tickets.'}, status=403)
            messages.error(request, 'You do not have permission to edit tickets.')
            return redirect('frontend:tickets')
        self.ticket_id = ticket_id
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            ticket = Ticket.objects.select_related('category', 'ticket_type', 'assigned_to', 'created_by').get(id=self.ticket_id)
            categories = TicketCategory.objects.filter(is_active=True)
            ticket_types = TicketType.objects.filter(is_active=True)
            available_users = User.objects.filter(is_active=True)
            context.update({
                'ticket': ticket,
                'categories': categories,
                'ticket_types': ticket_types,
                'available_users': available_users,
                'form': {}
            })
        except Ticket.DoesNotExist:
            messages.error(self.request, 'Ticket not found.')
            return redirect('frontend:tickets')
        except Exception as e:
            messages.error(self.request, f'Error loading ticket: {str(e)}')
            return redirect('frontend:tickets')
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle ticket edit."""
        try:
            ticket = Ticket.objects.select_related('category', 'ticket_type', 'assigned_to').get(id=self.ticket_id)
            
            title = request.POST.get('title', '')
            description = request.POST.get('description', '')
            category_id = request.POST.get('category', '')
            ticket_type_id = request.POST.get('ticket_type', '')
            status = request.POST.get('status', 'NEW')
            priority = request.POST.get('priority', 'MEDIUM')
            impact = request.POST.get('impact', 'MEDIUM')
            urgency = request.POST.get('urgency', 'MEDIUM')
            assigned_to_id = request.POST.get('assigned_to', '')
            assigned_team = request.POST.get('assigned_team', '')
            location = request.POST.get('location', '')
            contact_phone = request.POST.get('contact_phone', '')
            contact_email = request.POST.get('contact_email', '')
            sla_due_at_str = request.POST.get('sla_due_at', '')
            resolution_summary = request.POST.get('resolution_summary', '')
            
            # Validation
            errors = {}
            if not title:
                errors['title'] = 'Title is required'
            if not description:
                errors['description'] = 'Description is required'
            if not category_id:
                errors['category'] = 'Category is required'
            if not priority:
                errors['priority'] = 'Priority is required'
            
            if errors:
                context = self.get_context_data()
                context['errors'] = errors
                context['form'] = request.POST
                return render(request, self.template_name, context)
            
            # Update ticket
            category = TicketCategory.objects.get(id=category_id)
            ticket_type = TicketType.objects.get(id=ticket_type_id) if ticket_type_id else None
            assigned_to = User.objects.get(id=assigned_to_id) if assigned_to_id else None
            
            # Parse sla_due_at
            sla_due_at = None
            if sla_due_at_str:
                try:
                    sla_due_at = timezone.make_aware(
                        datetime.fromisoformat(sla_due_at_str.replace('Z', '+00:00'))
                    )
                except (ValueError, TypeError):
                    pass
            
            ticket.title = title
            ticket.description = description
            ticket.category = category
            ticket.ticket_type = ticket_type
            ticket.status = status
            ticket.priority = priority
            ticket.impact = impact
            ticket.urgency = urgency
            ticket.assigned_to = assigned_to
            ticket.assigned_team = assigned_team
            ticket.location = location
            ticket.contact_phone = contact_phone
            ticket.contact_email = contact_email
            ticket.sla_due_at = sla_due_at
            ticket.resolution_summary = resolution_summary
            ticket.updated_by = request.user
            ticket.save()
            
            messages.success(request, f'Ticket #{ticket.id} updated successfully!')
            return redirect('frontend:tickets')
        
        except Ticket.DoesNotExist:
            messages.error(request, 'Ticket not found.')
            return redirect('frontend:tickets')
        except Exception as e:
            messages.error(request, f'Error updating ticket: {str(e)}')
            context = self.get_context_data()
            context['form'] = request.POST
            return render(request, self.template_name, context)


@login_required(login_url='frontend:login')
@require_http_methods(["DELETE", "PATCH"])
def ticket_crud(request, ticket_id):
    """Handle ticket CRUD operations (DELETE and PATCH)."""
    # Check permissions
    if not hasattr(request.user, 'role') or request.user.role not in ['ADMIN', 'SUPERADMIN']:
        return JsonResponse({'error': 'You do not have permission to manage tickets.'}, status=403)
    
    try:
        from apps.tickets.models import TicketComment, TicketAttachment, TicketHistory, TicketEscalation, TicketSatisfaction
        
        ticket = Ticket.objects.get(id=ticket_id)
        
        if request.method == 'DELETE':
            # Properly handle cascade deletion
            from django.db import transaction
            
            with transaction.atomic():
                ticket_title = ticket.title
                
                # Delete related TicketComment records
                TicketComment.objects.filter(ticket=ticket).delete()
                
                # Delete related TicketAttachment records
                TicketAttachment.objects.filter(ticket=ticket).delete()
                
                # Delete related TicketHistory records
                TicketHistory.objects.filter(ticket=ticket).delete()
                
                # Delete related TicketEscalation records
                TicketEscalation.objects.filter(ticket=ticket).delete()
                
                # Delete related TicketSatisfaction record (OneToOne)
                TicketSatisfaction.objects.filter(ticket=ticket).delete()
                
                # Clear related_tickets M2M relationship
                ticket.related_tickets.clear()
                
                # Delete child tickets (tickets that have this ticket as parent)
                Ticket.objects.filter(parent_ticket=ticket).delete()
                
                # Delete the ticket
                ticket.delete()
                
            return JsonResponse({'success': True, 'message': f'Ticket "{ticket_title}" deleted successfully.'})
        
        elif request.method == 'PATCH':
            # Update ticket
            data = json.loads(request.body)
            
            if 'title' in data and data['title'].strip():
                ticket.title = data['title']
            if 'description' in data:
                ticket.description = data['description']
            
            ticket.save()
            
            return JsonResponse({'success': True, 'message': f'Ticket "{ticket.title}" updated successfully.'})
    
    except Ticket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found.'}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Error: {str(e)}'}, status=500)

