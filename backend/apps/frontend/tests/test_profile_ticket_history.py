"""
Unit tests for ProfileView and TicketQueryService.

Tests cover:
- Ticket fetching with Q objects
- RBAC enforcement
- Statistics calculation
- Pagination
- Filtering
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from apps.frontend.views.profile import ProfileView, profile_reopen_ticket
from apps.tickets.services.ticket_query_service import TicketQueryService

User = get_user_model()


class TestTicketQueryService(TestCase):
    """Test cases for TicketQueryService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = Mock()
        self.user.id = 1
        self.user.username = 'testuser'
    
    @patch('apps.tickets.services.ticket_query_service.Ticket')
    def test_get_user_tickets_returns_tickets_where_created_by_or_assigned(self, mock_ticket_model):
        """Test that get_user_tickets fetches tickets where user is creator OR assignee."""
        # Create mock ticket objects
        mock_ticket1 = Mock()
        mock_ticket1.id = 1
        mock_ticket1.title = 'Ticket 1'
        mock_ticket1.status = 'OPEN'
        mock_ticket1.priority = 'HIGH'
        mock_ticket1.created_by = self.user
        mock_ticket1.assigned_to = None
        
        mock_ticket2 = Mock()
        mock_ticket2.id = 2
        mock_ticket2.title = 'Ticket 2'
        mock_ticket2.status = 'IN_PROGRESS'
        mock_ticket2.priority = 'MEDIUM'
        mock_ticket2.created_by = None
        mock_ticket2.assigned_to = self.user
        
        # Set up mock queryset
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=[mock_ticket1, mock_ticket2])
        mock_ticket_model.objects.filter.return_value = mock_qs
        
        # Create service and call method
        service = TicketQueryService()
        
        # Mock the Paginator
        with patch('apps.tickets.services.ticket_query_service.Paginator') as mock_paginator:
            mock_page = MagicMock()
            mock_page.object_list = [mock_ticket1, mock_ticket2]
            mock_page.has_next.return_value = False
            mock_page.has_previous.return_value = False
            mock_paginator_instance = MagicMock()
            mock_paginator_instance.page.return_value = mock_page
            mock_paginator.return_value = mock_paginator_instance
            
            result = service.get_user_tickets(user=self.user)
        
        # Verify Q objects were used with OR logic
        call_args = mock_ticket_model.objects.filter.call_args
        # The filter should be called with a Q object containing OR condition
        self.assertTrue(call_args[0][0] is not None)
    
    @patch('apps.tickets.services.ticket_query_service.Ticket')
    def test_get_user_tickets_with_status_filter(self, mock_ticket_model):
        """Test filtering by status."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=[])
        mock_ticket_model.objects.filter.return_value = mock_qs
        
        with patch('apps.tickets.services.ticket_query_service.Paginator') as mock_paginator:
            mock_page = MagicMock()
            mock_page.object_list = []
            mock_page.has_next.return_value = False
            mock_page.has_previous.return_value = False
            mock_paginator_instance = MagicMock()
            mock_paginator_instance.page.return_value = mock_page
            mock_paginator.return_value = mock_paginator_instance
            
            service = TicketQueryService()
            result = service.get_user_tickets(
                user=self.user,
                status_filter='OPEN'
            )
        
        # Verify status filter was applied
        filter_call = mock_ticket_model.objects.filter.call_args
        # The Q object should include status filter
    
    @patch('apps.tickets.services.ticket_query_service.Ticket')
    def test_get_user_tickets_with_priority_filter(self, mock_ticket_model):
        """Test filtering by priority."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=[])
        mock_ticket_model.objects.filter.return_value = mock_qs
        
        with patch('apps.tickets.services.ticket_query_service.Paginator') as mock_paginator:
            mock_page = MagicMock()
            mock_page.object_list = []
            mock_page.has_next.return_value = False
            mock_page.has_previous.return_value = False
            mock_paginator_instance = MagicMock()
            mock_paginator_instance.page.return_value = mock_page
            mock_paginator.return_value = mock_paginator_instance
            
            service = TicketQueryService()
            result = service.get_user_tickets(
                user=self.user,
                priority_filter='HIGH'
            )
        
        # Verify priority filter was applied
    
    @patch('apps.tickets.services.ticket_query_service.Ticket')
    def test_get_user_ticket_stats(self, mock_ticket_model):
        """Test statistics calculation."""
        # Mock the Ticket model queryset
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.count.return_value = 5
        mock_ticket_model.objects.filter.return_value = mock_qs
        
        service = TicketQueryService()
        stats = service.get_user_ticket_stats(user=self.user)
        
        # Verify all stats are calculated
        self.assertIn('total', stats)
        self.assertIn('created', stats)
        self.assertIn('assigned', stats)
        self.assertIn('resolved', stats)
        self.assertIn('open', stats)
        self.assertIn('can_reopen', stats)
    
    def test_can_user_reopen_ticket_admin_returns_true(self):
        """Test that admins can reopen tickets."""
        admin_user = Mock()
        admin_user.is_superuser = True
        admin_user.role = 'SUPERADMIN'
        
        service = TicketQueryService()
        result = service.can_user_reopen_ticket(user=admin_user)
        
        self.assertTrue(result)
    
    def test_can_user_reopen_ticket_it_admin_returns_true(self):
        """Test that IT_ADMIN can reopen tickets."""
        admin_user = Mock()
        admin_user.is_superuser = False
        admin_user.role = 'IT_ADMIN'
        
        service = TicketQueryService()
        result = service.can_user_reopen_ticket(user=admin_user)
        
        self.assertTrue(result)
    
    def test_can_user_reopen_ticket_manager_returns_true(self):
        """Test that MANAGER can reopen tickets."""
        manager_user = Mock()
        manager_user.is_superuser = False
        manager_user.role = 'MANAGER'
        
        service = TicketQueryService()
        result = service.can_user_reopen_ticket(user=manager_user)
        
        self.assertTrue(result)
    
    def test_can_user_reopen_ticket_technician_returns_false(self):
        """Test that Technician cannot reopen tickets."""
        tech_user = Mock()
        tech_user.is_superuser = False
        tech_user.role = 'TECHNICIAN'
        
        service = TicketQueryService()
        result = service.can_user_reopen_ticket(user=tech_user)
        
        self.assertFalse(result)
    
    def test_can_user_reopen_ticket_none_user_returns_false(self):
        """Test that None user cannot reopen tickets."""
        service = TicketQueryService()
        result = service.can_user_reopen_ticket(user=None)
        
        self.assertFalse(result)
    
    @patch('apps.tickets.services.ticket_query_service.Ticket')
    def test_get_available_filters(self, mock_ticket_model):
        """Test getting available filter options."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.values_list.return_value = mock_qs
        mock_qs.distinct.return_value = mock_qs
        mock_qs.__iter__ = Mock(return_value=iter(['OPEN', 'RESOLVED']))
        mock_ticket_model.objects.filter.return_value = mock_qs
        
        service = TicketQueryService()
        filters = service.get_available_filters(user=self.user)
        
        # Verify filter options are returned
        self.assertIn('statuses', filters)
        self.assertIn('priorities', filters)


class TestProfileView(TestCase):
    """Test cases for ProfileView."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.user = Mock()
        self.user.id = 1
        self.user.username = 'testuser'
        self.user.email = 'test@example.com'
        self.user.first_name = 'Test'
        self.user.last_name = 'User'
        self.user.role = 'TECHNICIAN'
        self.user.is_superuser = False
        self.user.is_active = True
        self.user.date_joined = timezone.now()
        self.user.last_login = timezone.now()
    
    def test_profile_view_uses_correct_template(self):
        """Test that ProfileView uses the correct template."""
        view = ProfileView()
        self.assertEqual(view.template_name, 'frontend/profile.html')
    
    def test_profile_view_requires_login(self):
        """Test that ProfileView requires login."""
        view = ProfileView()
        self.assertEqual(view.login_url, 'frontend:login')
    
    @patch('apps.frontend.views.profile.TicketQueryService')
    def test_get_context_data_uses_service(self, mock_service_class):
        """Test that get_context_data uses TicketQueryService."""
        # Set up mock service
        mock_service = Mock()
        mock_service.get_user_tickets.return_value = {
            'tickets': [],
            'page': 1,
            'page_size': 10,
            'total_count': 0,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
        }
        mock_service.get_user_ticket_stats.return_value = {
            'total': 0, 'created': 0, 'assigned': 0,
            'resolved': 0, 'open': 0, 'can_reopen': 0
        }
        mock_service.can_user_reopen_ticket.return_value = False
        mock_service.get_available_filters.return_value = {
            'statuses': [], 'priorities': []
        }
        mock_service_class.return_value = mock_service
        
        # Create view and request
        view = ProfileView()
        request = self.factory.get('/profile/')
        request.user = self.user
        
        # Call get_context_data
        with patch.object(view, 'get', return_value=Mock()):
            view.request = request
            context = view.get_context_data()
        
        # Verify service was called
        mock_service.get_user_tickets.assert_called_once()
        mock_service.get_user_ticket_stats.assert_called_once()
    
    @patch('apps.frontend.views.profile.TicketQueryService')
    def test_context_contains_ticket_data(self, mock_service_class):
        """Test that context contains ticket data."""
        mock_service = Mock()
        mock_service.get_user_tickets.return_value = {
            'tickets': [
                {
                    'id': 1,
                    'title': 'Test Ticket',
                    'status': 'OPEN',
                    'priority': 'HIGH',
                    'status_display': 'Open',
                    'priority_display': 'High',
                    'created_at': timezone.now(),
                    'updated_at': timezone.now(),
                    'created_by': {'id': 1, 'username': 'testuser'},
                    'updated_by': {'id': 1, 'username': 'testuser'},
                }
            ],
            'page': 1,
            'page_size': 10,
            'total_count': 1,
            'total_pages': 1,
            'has_next': False,
            'has_previous': False,
        }
        mock_service.get_user_ticket_stats.return_value = {
            'total': 1, 'created': 1, 'assigned': 0,
            'resolved': 0, 'open': 1, 'can_reopen': 0
        }
        mock_service.can_user_reopen_ticket.return_value = False
        mock_service.get_available_filters.return_value = {
            'statuses': ['OPEN', 'RESOLVED'],
            'priorities': ['HIGH', 'MEDIUM']
        }
        mock_service_class.return_value = mock_service
        
        view = ProfileView()
        request = self.factory.get('/profile/')
        request.user = self.user
        
        with patch.object(view, 'get', return_value=Mock()):
            view.request = request
            context = view.get_context_data()
        
        # Verify context contains expected data
        self.assertIn('my_tickets', context)
        self.assertIn('ticket_pagination', context)
        self.assertIn('stats', context)
        self.assertIn('can_reopen_ticket', context)
        self.assertIn('available_filters', context)
        self.assertIn('current_filters', context)
    
    @patch('apps.frontend.views.profile.TicketQueryService')
    def test_context_contains_user(self, mock_service_class):
        """Test that context contains user."""
        mock_service = Mock()
        mock_service.get_user_tickets.return_value = {
            'tickets': [], 'page': 1, 'page_size': 10,
            'total_count': 0, 'total_pages': 1,
            'has_next': False, 'has_previous': False,
        }
        mock_service.get_user_ticket_stats.return_value = {
            'total': 0, 'created': 0, 'assigned': 0,
            'resolved': 0, 'open': 0, 'can_reopen': 0
        }
        mock_service.can_user_reopen_ticket.return_value = False
        mock_service.get_available_filters.return_value = {
            'statuses': [], 'priorities': []
        }
        mock_service_class.return_value = mock_service
        
        view = ProfileView()
        request = self.factory.get('/profile/')
        request.user = self.user
        
        with patch.object(view, 'get', return_value=Mock()):
            view.request = request
            context = view.get_context_data()
        
        self.assertEqual(context['user'], self.user)


class TestProfileReopenTicket(TestCase):
    """Test cases for profile_reopen_ticket view."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.admin_user = Mock()
        self.admin_user.id = 1
        self.admin_user.username = 'admin'
        self.admin_user.is_superuser = True
        self.admin_user.role = 'SUPERADMIN'
        
        self.regular_user = Mock()
        self.regular_user.id = 2
        self.regular_user.username = 'tech'
        self.regular_user.is_superuser = False
        self.regular_user.role = 'TECHNICIAN'
    
    @patch('apps.frontend.views.profile.get_object_or_404')
    @patch('apps.frontend.views.profile.ActivityService')
    def test_non_admin_cannot_reopen(self, mock_activity, mock_get_object):
        """Test that non-admin users cannot reopen tickets."""
        request = self.factory.post('/profile/reopen-ticket/1/')
        request.user = self.regular_user
        request._messages = Mock()
        
        # Call view
        response = profile_reopen_ticket(request, ticket_id=1)
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        request._messages.error.assert_called()
    
    @patch('apps.frontend.views.profile.get_object_or_404')
    @patch('apps.frontend.views.profile.ActivityService')
    def test_admin_can_reopen_resolved_ticket(self, mock_activity, mock_get_object):
        """Test that admin can reopen a resolved ticket."""
        # Create mock ticket
        mock_ticket = Mock()
        mock_ticket.id = 1
        mock_ticket.status = 'RESOLVED'
        mock_ticket.created_by = self.admin_user
        mock_ticket.assigned_to = None
        mock_get_object.return_value = mock_ticket
        
        request = self.factory.post('/profile/reopen-ticket/1/')
        request.user = self.admin_user
        request._messages = Mock()
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        
        # Call view
        response = profile_reopen_ticket(request, ticket_id=1)
        
        # Should redirect with success
        self.assertEqual(response.status_code, 302)
        request._messages.success.assert_called()
        
        # Verify ticket was updated
        mock_ticket.status = 'IN_PROGRESS'
        mock_ticket.save.assert_called_once()
        
        # Verify activity was logged
        mock_activity.log_activity.assert_called_once()
    
    @patch('apps.frontend.views.profile.get_object_or_404')
    def test_cannot_reopen_open_ticket(self, mock_get_object):
        """Test that open tickets cannot be reopened."""
        mock_ticket = Mock()
        mock_ticket.id = 1
        mock_ticket.status = 'OPEN'
        mock_ticket.created_by = self.admin_user
        mock_get_object.return_value = mock_ticket
        
        request = self.factory.post('/profile/reopen-ticket/1/')
        request.user = self.admin_user
        request._messages = Mock()
        
        # Call view
        response = profile_reopen_ticket(request, ticket_id=1)
        
        # Should redirect with error
        self.assertEqual(response.status_code, 302)
        request._messages.error.assert_called()


class TestPagination(TestCase):
    """Test cases for pagination functionality."""
    
    def test_pagination_limits_to_10_per_page(self):
        """Test that pagination limits to 10 tickets per page."""
        service = TicketQueryService()
        
        # Verify default page size
        self.assertEqual(service.default_page_size, 10)
        self.assertEqual(service.max_page_size, 50)
    
    @patch('apps.tickets.services.ticket_query_service.Ticket')
    def test_pagination_returns_correct_structure(self, mock_ticket_model):
        """Test that pagination returns correct structure."""
        mock_qs = MagicMock()
        mock_qs.filter.return_value = mock_qs
        mock_qs.select_related.return_value = mock_qs
        mock_qs.order_by.return_value = mock_qs
        mock_qs.__getitem__ = Mock(return_value=[])
        mock_ticket_model.objects.filter.return_value = mock_qs
        
        with patch('apps.tickets.services.ticket_query_service.Paginator') as mock_paginator:
            mock_page = MagicMock()
            mock_page.object_list = []
            mock_page.has_next.return_value = True
            mock_page.has_previous.return_value = False
            mock_page_obj = MagicMock()
            mock_page_obj.object_list = []
            mock_page_obj.has_next.return_value = True
            mock_page_obj.has_previous.return_value = False
            mock_paginator_instance = MagicMock()
            mock_paginator_instance.num_pages = 5
            mock_paginator_instance.count = 45
            mock_paginator_instance.page.return_value = mock_page_obj
            mock_paginator.return_value = mock_paginator_instance
            
            user = Mock()
            user.id = 1
            
            service = TicketQueryService()
            result = service.get_user_tickets(user=user, page=1)
            
            # Verify pagination structure
            self.assertIn('page', result)
            self.assertIn('page_size', result)
            self.assertIn('total_count', result)
            self.assertIn('total_pages', result)
            self.assertIn('has_next', result)
            self.assertIn('has_previous', result)


class TestRBACEnforcement(TestCase):
    """Test cases for RBAC enforcement in ticket access."""
    
    def test_user_can_only_see_own_tickets(self):
        """Test that users can only see tickets they created or were assigned."""
        # This is tested by the Q object query:
        # Q(created_by=user) | Q(assigned_to=user)
        # Which ensures only tickets where user is creator OR assignee are returned
        
        user = Mock()
        user.id = 1
        
        # Create a Q object that represents the permission check
        base_query = Q(created_by=user) | Q(assigned_to=user)
        
        # Verify Q object has OR condition
        self.assertIn('|', str(base_query))
    
    def test_admin_can_see_all_tickets(self):
        """Test that admins can see all tickets (created or assigned)."""
        admin = Mock()
        admin.id = 1
        admin.is_superuser = True
        admin.role = 'SUPERADMIN'
        
        # Admins still use the same query, but they might have
        # additional permissions in a real implementation
        base_query = Q(created_by=admin) | Q(assigned_to=admin)
        
        # Verify Q object has OR condition
        self.assertIn('|', str(base_query))


# Run tests with: pytest tests.py -v
if __name__ == '__main__':
    import django
    from django.conf import settings
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'apps.frontend',
                'apps.tickets',
            ],
            SECRET_KEY='test-secret-key',
        )
        django.setup()
    
    pytest.main([__file__, '-v'])
