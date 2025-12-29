"""
Ticket views for IT Management Platform.
API endpoints for IT support ticket management with role-based access control.
"""

from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime, timedelta

from apps.tickets.models import (
    TicketCategory, TicketType, Ticket, TicketComment, TicketAttachment,
    TicketHistory, TicketTemplate, SLA, TicketEscalation, TicketSatisfaction,
    TicketReport
)
from apps.tickets.serializers import (
    TicketCategorySerializer, TicketTypeSerializer, TicketListSerializer,
    TicketDetailSerializer, TicketCreateSerializer, TicketUpdateSerializer,
    TicketCommentSerializer, TicketAttachmentSerializer, TicketHistorySerializer,
    TicketTemplateSerializer, SLASerializer, TicketEscalationSerializer,
    TicketSatisfactionSerializer, TicketReportSerializer, TicketStatisticsSerializer,
    TicketSearchSerializer, TicketActionSerializer, TicketTemplateUseSerializer
)
from apps.tickets.permissions import (
    CanManageTickets, IsTicketRequesterOrAssigned, IsTicketCreator,
    CanCreateTickets, CanViewTicketDetails, CanManageTicketCategories,
    CanAssignTickets, CanResolveTickets, CanCloseTickets, CanEscalateTickets,
    CanViewTicketComments, CanCreateTicketComments, CanManageTicketAttachments,
    CanViewTicketHistory, CanViewTicketTemplates, CanManageTicketTemplates,
    CanViewSLAs, CanManageSLAs, CanViewTicketReports, CanGenerateTicketReports,
    CanRateTicketSatisfaction, CanViewTicketEscalations, CanManageTicketEscalations,
    CanAccessTicketStatistics
)
from apps.users.models import User

class TicketCategoryViewSet(viewsets.ModelViewSet):
    """
    Ticket category management viewset.
    """
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [CanManageTicketCategories]
    
    def get_queryset(self):
        queryset = TicketCategory.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')

class TicketTypeViewSet(viewsets.ModelViewSet):
    """
    Ticket type management viewset.
    """
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    permission_classes = [CanManageTicketCategories]
    
    def get_queryset(self):
        queryset = TicketType.objects.select_related('category')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('category__name', 'name')

class TicketViewSet(viewsets.ModelViewSet):
    """
    Ticket management viewset with comprehensive filtering and actions.
    """
    permission_classes = [CanManageTickets, IsTicketRequesterOrAssigned, IsTicketCreator, CanCreateTickets]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        elif self.action == 'retrieve':
            return TicketDetailSerializer
        elif self.action == 'create':
            return TicketCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return TicketUpdateSerializer
        return TicketDetailSerializer
    
    def get_queryset(self):
        queryset = Ticket.objects.select_related(
            'category', 'ticket_type', 'requester', 'assigned_to', 'parent_ticket',
            'created_by', 'updated_by'
        ).prefetch_related('related_tickets', 'comments', 'attachments')
        
        # Filter by requester
        requester = self.request.query_params.get('requester')
        if requester:
            queryset = queryset.filter(requester_id=requester)
        
        # Filter by assigned user
        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by ticket type
        ticket_type = self.request.query_params.get('ticket_type')
        if ticket_type:
            queryset = queryset.filter(ticket_type_id=ticket_type)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by impact
        impact = self.request.query_params.get('impact')
        if impact:
            queryset = queryset.filter(impact=impact)
        
        # Filter by urgency
        urgency = self.request.query_params.get('urgency')
        if urgency:
            queryset = queryset.filter(urgency=urgency)
        
        # Filter by overdue tickets
        overdue = self.request.query_params.get('overdue')
        if overdue and overdue.lower() == 'true':
            queryset = queryset.filter(
                sla_due_at__isnull=False,
                sla_due_at__lt=timezone.now(),
                status__in=['NEW', 'OPEN', 'IN_PROGRESS', 'PENDING']
            )
        
        # Filter by assigned team
        team = self.request.query_params.get('team')
        if team:
            queryset = queryset.filter(assigned_team=team)
        
        # Date range filtering
        created_from = self.request.query_params.get('created_from')
        created_to = self.request.query_params.get('created_to')
        
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(ticket_id__icontains=search)
            )
        
        # For non-admin users, only show tickets they are involved with
        if not self.request.user.is_admin and not self.request.user.can_manage_tickets:
            queryset = queryset.filter(
                Q(requester=self.request.user) |
                Q(assigned_to=self.request.user)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign ticket to a user."""
        ticket = self.get_object()
        assignee_id = request.data.get('assignee_id')
        team = request.data.get('team')
        
        if not assignee_id and not team:
            return Response({'error': 'Either assignee_id or team is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if assignee_id:
            try:
                assignee = User.objects.get(id=assignee_id)
                ticket.assign_to(assignee, request.user)
                message = f"Ticket assigned to {assignee.username}"
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        elif team:
            ticket.assigned_team = team
            ticket.assigned_to = None
            ticket.updated_by = request.user
            ticket.save()
            message = f"Ticket assigned to team: {team}"
        
        return Response({'message': message})
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve ticket."""
        ticket = self.get_object()
        resolution_summary = request.data.get('resolution_summary', '')
        
        ticket.mark_resolved(resolution_summary, request.user)
        
        return Response({'message': 'Ticket resolved successfully'})
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Close ticket."""
        ticket = self.get_object()
        ticket.mark_closed(request.user)
        
        return Response({'message': 'Ticket closed successfully'})
    
    @action(detail=True, methods=['post'])
    def reopen(self, request, pk=None):
        """Reopen ticket."""
        ticket = self.get_object()
        ticket.status = 'OPEN'
        ticket.updated_by = request.user
        ticket.save()
        
        return Response({'message': 'Ticket reopened successfully'})
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate ticket."""
        ticket = self.get_object()
        escalation_level = request.data.get('escalation_level')
        escalated_to_id = request.data.get('escalated_to_id')
        reason = request.data.get('reason', '')
        
        if not escalation_level or not escalated_to_id:
            return Response({'error': 'escalation_level and escalated_to_id are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            escalated_to = User.objects.get(id=escalated_to_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Create escalation record
        escalation = TicketEscalation.objects.create(
            ticket=ticket,
            escalated_by=request.user,
            escalated_to=escalated_to,
            escalation_level=escalation_level,
            reason=reason
        )
        
        # Update ticket status to indicate escalation
        ticket.status = 'PENDING'
        ticket.updated_by = request.user
        ticket.save()
        
        return Response({'message': f'Ticket escalated to {escalation_level}'})
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update ticket status."""
        ticket = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = ticket.status
        ticket.status = new_status
        ticket.updated_by = request.user
        
        # Handle status-specific logic
        if new_status == 'RESOLVED':
            ticket.resolved_at = timezone.now()
        elif new_status == 'CLOSED':
            ticket.closed_at = timezone.now()
        
        ticket.save()
        
        return Response({'message': f'Status changed from {old_status} to {new_status}'})
    
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """Get ticket comments."""
        ticket = self.get_object()
        comments = ticket.comments.select_related('user').all()
        serializer = TicketCommentSerializer(comments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attachments(self, request, pk=None):
        """Get ticket attachments."""
        ticket = self.get_object()
        attachments = ticket.attachments.select_related('user').all()
        serializer = TicketAttachmentSerializer(attachments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get ticket history."""
        ticket = self.get_object()
        history = ticket.history.select_related('user').all()
        serializer = TicketHistorySerializer(history, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def escalations(self, request, pk=None):
        """Get ticket escalations."""
        ticket = self.get_object()
        escalations = ticket.escalations.select_related('escalated_by', 'escalated_to').all()
        serializer = TicketEscalationSerializer(escalations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def satisfaction(self, request, pk=None):
        """Get ticket satisfaction rating."""
        ticket = self.get_object()
        try:
            satisfaction = ticket.satisfaction
            serializer = TicketSatisfactionSerializer(satisfaction)
            return Response(serializer.data)
        except TicketSatisfaction.DoesNotExist:
            return Response({'message': 'No satisfaction rating found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def rate_satisfaction(self, request, pk=None):
        """Rate ticket satisfaction."""
        ticket = self.get_object()
        rating = request.data.get('rating')
        feedback = request.data.get('feedback', '')
        
        if not rating:
            return Response({'error': 'Rating is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Only ticket requester can rate
        if ticket.requester != request.user:
            return Response({'error': 'Only the ticket requester can rate satisfaction'}, status=status.HTTP_403_FORBIDDEN)
        
        # Create or update satisfaction rating
        satisfaction, created = TicketSatisfaction.objects.update_or_create(
            ticket=ticket,
            defaults={
                'rating': rating,
                'feedback': feedback,
                'rated_by': request.user
            }
        )
        
        message = 'Satisfaction rating created' if created else 'Satisfaction rating updated'
        return Response({'message': message})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get ticket statistics."""
        # Cache statistics for 5 minutes
        cache_key = f'ticket_statistics_{request.user.id}'
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        total_tickets = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status__in=['NEW', 'OPEN']).count()
        in_progress_tickets = Ticket.objects.filter(status='IN_PROGRESS').count()
        resolved_tickets = Ticket.objects.filter(status='RESOLVED').count()
        closed_tickets = Ticket.objects.filter(status='CLOSED').count()
        overdue_tickets = Ticket.objects.filter(
            sla_due_at__isnull=False,
            sla_due_at__lt=timezone.now(),
            status__in=['NEW', 'OPEN', 'IN_PROGRESS', 'PENDING']
        ).count()
        
        tickets_by_status = dict(
            Ticket.objects.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )
        
        tickets_by_priority = dict(
            Ticket.objects.values('priority').annotate(count=Count('id')).values_list('priority', 'count')
        )
        
        tickets_by_category = dict(
            Ticket.objects.values('category__name').annotate(count=Count('id')).values_list('category__name', 'count')
        )
        
        # Calculate SLA compliance rate
        resolved_tickets_with_sla = Ticket.objects.filter(
            status__in=['RESOLVED', 'CLOSED'],
            sla_due_at__isnull=False
        )
        total_resolved = resolved_tickets_with_sla.count()
        compliant_resolved = resolved_tickets_with_sla.filter(
            resolved_at__lte=F('sla_due_at')
        ).count()
        sla_compliance_rate = (compliant_resolved / total_resolved * 100) if total_resolved > 0 else 0
        
        # Calculate average resolution time
        avg_resolution_time = Ticket.objects.filter(
            status__in=['RESOLVED', 'CLOSED'],
            resolved_at__isnull=False
        ).aggregate(
            avg_time=Avg('resolution_time')
        )['avg_time']
        
        avg_resolution_hours = avg_resolution_time.total_seconds() / 3600 if avg_resolution_time else 0
        
        recent_activities = TicketHistory.objects.select_related('ticket', 'user')[:10]
        
        upcoming_sla_breaches = Ticket.objects.filter(
            sla_due_at__isnull=False,
            sla_due_at__lte=timezone.now() + timedelta(hours=24),
            sla_due_at__gt=timezone.now(),
            status__in=['NEW', 'OPEN', 'IN_PROGRESS', 'PENDING']
        ).select_related('category', 'requester', 'assigned_to')[:10]
        
        stats = {
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'in_progress_tickets': in_progress_tickets,
            'resolved_tickets': resolved_tickets,
            'closed_tickets': closed_tickets,
            'overdue_tickets': overdue_tickets,
            'tickets_by_status': tickets_by_status,
            'tickets_by_priority': tickets_by_priority,
            'tickets_by_category': tickets_by_category,
            'sla_compliance_rate': round(sla_compliance_rate, 2),
            'average_resolution_time': round(avg_resolution_hours, 2),
            'recent_activities': TicketHistorySerializer(recent_activities, many=True).data,
            'upcoming_sla_breaches': TicketListSerializer(upcoming_sla_breaches, many=True).data
        }
        
        cache.set(cache_key, stats, 300)  # Cache for 5 minutes
        return Response(stats)

class TicketCommentViewSet(viewsets.ModelViewSet):
    """
    Ticket comment management viewset.
    """
    serializer_class = TicketCommentSerializer
    permission_classes = [CanViewTicketComments, CanCreateTicketComments]
    
    def get_queryset(self):
        queryset = TicketComment.objects.select_related('ticket', 'user')
        
        # Filter by ticket
        ticket = self.request.query_params.get('ticket')
        if ticket:
            queryset = queryset.filter(ticket_id=ticket)
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        return queryset.order_by('created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TicketAttachmentViewSet(viewsets.ModelViewSet):
    """
    Ticket attachment management viewset.
    """
    serializer_class = TicketAttachmentSerializer
    permission_classes = [CanManageTicketAttachments]
    
    def get_queryset(self):
        queryset = TicketAttachment.objects.select_related('ticket', 'user')
        
        # Filter by ticket
        ticket = self.request.query_params.get('ticket')
        if ticket:
            queryset = queryset.filter(ticket_id=ticket)
        
        # Filter by user
        user = self.request.query_params.get('user')
        if user:
            queryset = queryset.filter(user_id=user)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class TicketTemplateViewSet(viewsets.ModelViewSet):
    """
    Ticket template management viewset.
    """
    serializer_class = TicketTemplateSerializer
    permission_classes = [CanViewTicketTemplates, CanManageTicketTemplates]
    
    def get_queryset(self):
        queryset = TicketTemplate.objects.select_related('category', 'ticket_type', 'created_by')
        
        # Only show public templates or templates created by current user
        if not self.request.user.is_admin:
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=self.request.user)
            )
        
        return queryset.order_by('-usage_count', 'name')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def use_template(self, request, pk=None):
        """Use template to create a new ticket."""
        template = self.get_object()
        serializer = TicketTemplateUseSerializer(data=request.data)
        
        if serializer.is_valid():
            # Increment usage count
            template.usage_count += 1
            template.save()
            
            # Create ticket from template
            ticket_data = {
                'title': serializer.validated_data.get('title', template.template_title),
                'description': serializer.validated_data.get('description', template.template_description),
                'category': template.category,
                'ticket_type': template.ticket_type,
                'priority': template.default_priority,
                'impact': template.default_impact,
                'urgency': template.default_urgency,
                'location': serializer.validated_data.get('location', ''),
                'contact_phone': serializer.validated_data.get('contact_phone', ''),
                'contact_email': serializer.validated_data.get('contact_email', ''),
                'tags': template.default_tags,
                'requester': request.user,
                'created_by': request.user
            }
            
            ticket = Ticket.objects.create(**ticket_data)
            ticket.update_sla_due()
            
            return Response({'message': 'Ticket created from template', 'ticket_id': ticket.ticket_id})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SLAViewSet(viewsets.ModelViewSet):
    """
    SLA management viewset.
    """
    serializer_class = SLASerializer
    permission_classes = [CanViewSLAs, CanManageSLAs]
    
    def get_queryset(self):
        queryset = SLA.objects.select_related('category', 'ticket_type')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('name')

class TicketEscalationViewSet(viewsets.ModelViewSet):
    """
    Ticket escalation management viewset.
    """
    serializer_class = TicketEscalationSerializer
    permission_classes = [CanViewTicketEscalations, CanManageTicketEscalations]
    
    def get_queryset(self):
        queryset = TicketEscalation.objects.select_related('ticket', 'escalated_by', 'escalated_to')
        
        # Filter by ticket
        ticket = self.request.query_params.get('ticket')
        if ticket:
            queryset = queryset.filter(ticket_id=ticket)
        
        # Filter by escalated to
        escalated_to = self.request.query_params.get('escalated_to')
        if escalated_to:
            queryset = queryset.filter(escalated_to_id=escalated_to)
        
        # Filter by escalated by
        escalated_by = self.request.query_params.get('escalated_by')
        if escalated_by:
            queryset = queryset.filter(escalated_by_id=escalated_by)
        
        return queryset.order_by('-escalated_at')

class TicketSearchView(APIView):
    """
    Advanced ticket search endpoint.
    """
    permission_classes = [CanManageTickets]
    
    def post(self, request):
        serializer = TicketSearchSerializer(data=request.data)
        
        if serializer.is_valid():
            queryset = Ticket.objects.select_related('category', 'ticket_type', 'requester', 'assigned_to')
            
            # Apply filters
            search = serializer.validated_data.get('search')
            status = serializer.validated_data.get('status')
            priority = serializer.validated_data.get('priority')
            category = serializer.validated_data.get('category')
            ticket_type = serializer.validated_data.get('ticket_type')
            requester = serializer.validated_data.get('requester')
            assigned_to = serializer.validated_data.get('assigned_to')
            overdue = serializer.validated_data.get('overdue')
            created_from = serializer.validated_data.get('created_from')
            created_to = serializer.validated_data.get('created_to')
            
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(description__icontains=search) |
                    Q(ticket_id__icontains=search)
                )
            
            if status:
                queryset = queryset.filter(status=status)
            
            if priority:
                queryset = queryset.filter(priority=priority)
            
            if category:
                queryset = queryset.filter(category_id=category)
            
            if ticket_type:
                queryset = queryset.filter(ticket_type_id=ticket_type)
            
            if requester:
                queryset = queryset.filter(requester_id=requester)
            
            if assigned_to:
                queryset = queryset.filter(assigned_to_id=assigned_to)
            
            if overdue:
                queryset = queryset.filter(
                    sla_due_at__isnull=False,
                    sla_due_at__lt=timezone.now(),
                    status__in=['NEW', 'OPEN', 'IN_PROGRESS', 'PENDING']
                )
            
            if created_from:
                queryset = queryset.filter(created_at__date__gte=created_from)
            if created_to:
                queryset = queryset.filter(created_at__date__lte=created_to)
            
            # Paginate results
            page = int(request.query_params.get('page', 1))
            page_size = int(request.query_params.get('page_size', 20))
            start = (page - 1) * page_size
            end = start + page_size
            
            results = queryset.order_by('-created_at')[start:end]
            total_count = queryset.count()
            
            response_data = {
                'results': TicketListSerializer(results, many=True).data,
                'total_count': total_count,
                'page': page,
                'page_size': page_size,
                'total_pages': (total_count + page_size - 1) // page_size
            }
            
            return Response(response_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
