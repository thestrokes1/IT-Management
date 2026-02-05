"""
Test script to simulate CQRS command flow with transaction.on_commit
and capture any logging errors.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import transaction
from django.contrib.auth import get_user_model
from apps.tickets.models import Ticket, TicketCategory, TicketType
from apps.logs.services.activity_service import ActivityService

User = get_user_model()

def simulate_cqrs_ticket_creation():
    """
    Simulate the exact flow in CreateTicket.execute():
    1. Create ticket
    2. Schedule logging via transaction.on_commit
    3. Check if logging runs and if it succeeds
    """
    print("=" * 60)
    print("Simulating CQRS Ticket Creation Flow")
    print("=" * 60)
    
    # Get or create test user
    user, _ = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@test.com', 'role': 'TECHNICIAN', 'is_active': True}
    )
    print(f"User: {user.username} (id={user.id})")
    
    # Get or create category and ticket type
    category, _ = TicketCategory.objects.get_or_create(name='Test Category')
    ticket_type, _ = TicketType.objects.get_or_create(
        category=category,
        name='Test Type',
        defaults={'sla_hours': 24}
    )
    
    # Create ticket (simulating CQRS command)
    print("\n1. Creating ticket...")
    ticket = Ticket.objects.create(
        title='CQRS Test Ticket',
        description='Testing CQRS activity logging flow',
        category=category,
        ticket_type=ticket_type,
        priority='MEDIUM',
        status='NEW',
        created_by=user,
    )
    print(f"   Ticket created: id={ticket.id}")
    
    # Simulate transaction.on_commit callback (exact pattern from CreateTicket)
    print("\n2. Simulating transaction.on_commit callback...")
    
    def _log_ticket_created():
        """This is the exact pattern from CreateTicket._log_ticket_created"""
        print("   _log_ticket_created() called")
        try:
            from apps.logs.services.activity_service import ActivityService
            print("   Creating ActivityService instance...")
            service = ActivityService()
            print(f"   Calling log_ticket_created(ticket={ticket.id}, actor={user})...")
            result = service.log_ticket_created(ticket, user, None)
            print(f"   SUCCESS: ActivityLog created with id={result.id}")
            return result
        except Exception as e:
            print(f"   EXCEPTION in _log_ticket_created:")
            print(f"   Exception Type: {type(e).__name__}")
            print(f"   Exception Message: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    # Register the callback (this is what CQRS commands do)
    print("3. Registering transaction.on_commit callback...")
    transaction.on_commit(_log_ticket_created)
    print("   Callback registered (will execute after transaction commits)")
    
    # The transaction should auto-commit when the function ends
    print("\n4. Transaction should auto-commit now...")
    print("   (If no error above, the callback ran successfully)")
    
    # Check ActivityLog count
    from apps.logs.models import ActivityLog
    print(f"\n5. Checking ActivityLog records...")
    print(f"   Total ActivityLog records: {ActivityLog.objects.count()}")
    
    # Return the ticket for inspection
    return ticket

if __name__ == '__main__':
    simulate_cqrs_ticket_creation()

