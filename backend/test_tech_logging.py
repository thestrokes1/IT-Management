#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.logs.models import ActivityLog
from apps.users.models import User
from apps.logs.services.activity_service import ActivityService
from apps.tickets.models import Ticket

# Get tech user
tech = User.objects.get(username='tech')
print(f"Testing ActivityService.log_ticket_created with tech user...\n")

# Get a ticket created by tech
ticket = Ticket.objects.filter(created_by=tech).first()
if not ticket:
    print("No ticket found for tech user")
else:
    print(f"Test ticket: {ticket.id} - {ticket.title}")
    print(f"Created by: {ticket.created_by.username}")
    
    # Try to manually log it using the service
    try:
        service = ActivityService()
        log = service.log_ticket_created(ticket, tech, None)
        print(f"\n✓ Logging succeeded! Created ActivityLog ID: {log.id}")
        print(f"  actor_name: {repr(log.actor_name)}")
        print(f"  user: {log.user}")
        print(f"  user_id: {log.user_id}")
        print(f"  extra_data: {log.extra_data}")
    except Exception as e:
        print(f"\n❌ Logging failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

# Now check if ANY recent logs have been created for tech
recent_tech_logs = ActivityLog.objects.filter(
    user_id=tech.id
).order_by('-id')[:5]
print(f"\n\nRecent logs for tech (last 5): {recent_tech_logs.count()}")
for log in recent_tech_logs:
    print(f"  - {log.id}: {log.action} (actor_name={repr(log.actor_name)})")
