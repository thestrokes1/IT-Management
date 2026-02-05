"""
Test script to capture CQRS logging errors.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, 'backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.contrib.auth import get_user_model
from apps.tickets.application.create_ticket import CreateTicket
from apps.logs.models import ActivityLog

User = get_user_model()

def test_cqrs_logging():
    """Test CQRS command and capture any logging errors."""
    user = User.objects.first()
    
    if not user:
        print("No users found")
        return
    
    print(f"Testing with user: {user.username} (id={user.id})")
    
    # Run the CQRS command
    result = CreateTicket().execute(
        actor=user,
        ticket_data={
            'title': 'Error Capture Test',
            'description': 'Testing CQRS logging error capture',
            'category_id': 1,
            'ticket_type_id': 1,
            'priority': 'MEDIUM',
        }
    )
    
    print(f"CQRS result: success={result.success}")
    if result.success:
        print(f"Ticket: {result.data}")
    else:
        print(f"Error: {result.error}")
    
    # Check ActivityLog count
    count = ActivityLog.objects.count()
    print(f"ActivityLog count: {count}")

if __name__ == '__main__':
    test_cqrs_logging()
    print("\nCheck the console output above for any [CQRS_LOG_ERROR] messages.")
    print("If the callback runs, you should see the log attempt.")

