"""
Test script to trigger activity logging directly and capture any exceptions.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.logs.services.activity_service import ActivityService
from apps.tickets.models import Ticket, TicketCategory, TicketType

User = get_user_model()

def test_activity_logging():
    """Test activity logging directly."""
    print("=" * 60)
    print("Testing Activity Logging Directly")
    print("=" * 60)
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@example.com',
            'role': 'TECHNICIAN',
            'is_active': True,
        }
    )
    print(f"User: {user.username} (role: {user.role}, id: {user.id})")
    
    # Get or create a ticket category and type
    category, _ = TicketCategory.objects.get_or_create(
        name='Test Category',
        defaults={'description': 'Test category for activity logging'}
    )
    print(f"Category: {category.name} (id: {category.id})")
    
    # Get or create a ticket type
    ticket_type, _ = TicketType.objects.get_or_create(
        category=category,
        name='Test Type',
        defaults={'description': 'Test type', 'sla_hours': 24}
    )
    print(f"Ticket Type: {ticket_type.name} (id: {ticket_type.id})")
    
    # Create a test ticket
    ticket = Ticket.objects.create(
        title="Test Ticket for Activity Logging",
        description="This is a test ticket to diagnose activity logging issues.",
        category=category,
        ticket_type=ticket_type,
        priority='MEDIUM',
        status='NEW',
    )
    print(f"Created Ticket: {ticket.title} (id: {ticket.id})")
    
    # Now test activity logging
    print("\nTesting ActivityService.log_ticket_created()...")
    
    service = ActivityService()
    
    try:
        result = service.log_ticket_created(
            ticket=ticket,
            actor=user,
            request=None,  # No request for direct test
        )
        print(f"✓ Activity log created successfully: {result}")
    except Exception as e:
        print(f"✗ Exception during activity logging: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nTesting ActivityService.log_ticket_action()...")
    
    try:
        result = service.log_ticket_action(
            action='TICKET_STATUS_CHANGED',
            ticket=ticket,
            actor=user,
            metadata={'from_status': 'NEW', 'to_status': 'OPEN'},
            request=None,
        )
        print(f"✓ Activity log created successfully: {result}")
    except Exception as e:
        print(f"✗ Exception during activity logging: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
    
    # Check if logs were actually persisted
    print("\nChecking ActivityLog table...")
    from apps.logs.models import ActivityLog
    count = ActivityLog.objects.count()
    print(f"Total ActivityLog records: {count}")
    
    if count > 0:
        print("\nRecent logs:")
        for log in ActivityLog.objects.order_by('-timestamp')[:5]:
            print(f"  - {log.action}: {log.title} (user: {log.user})")

if __name__ == '__main__':
    test_activity_logging()

