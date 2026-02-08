#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.logs.models import ActivityLog
from apps.users.models import User
from apps.tickets.models import Ticket
from apps.assets.models import Asset
from django.db.models import Q

# Get tech user
tech = User.objects.get(username='tech')
print(f"Tech user ID: {tech.id}")
print(f"Tech role: {tech.role}")

# Check if tech has any logs at all (any field)
tech_logs_via_fk = ActivityLog.objects.filter(user_id=tech.id)
print(f"\n1. Logs where user_id={tech.id}: {tech_logs_via_fk.count()}")

# Check if tech username appears in extra_data
tech_logs_extra = ActivityLog.objects.filter(
    extra_data__actor_username__iexact='tech'
)
print(f"2. Logs where extra_data has actor_username='tech': {tech_logs_extra.count()}")

# Check if tech username appears in actor_name field
tech_logs_actor = ActivityLog.objects.filter(actor_name__iexact='tech')
print(f"3. Logs where actor_name='tech': {tech_logs_actor.count()}")

# Total logs for tech
all_tech_logs = ActivityLog.objects.filter(
    Q(user_id=tech.id) | 
    Q(extra_data__actor_username__iexact='tech') |
    Q(actor_name__iexact='tech')
)
print(f"4. Total unique logs for tech (all sources): {all_tech_logs.distinct().count()}")

# Check tickets created by tech
tech_tickets = Ticket.objects.filter(created_by=tech)
print(f"\n5. Tickets created by tech: {tech_tickets.count()}")
if tech_tickets.exists():
    print(f"   Sample: {tech_tickets.first().id} - {tech_tickets.first().title}")

# Check assets created by tech
tech_assets = Asset.objects.filter(created_by=tech)
print(f"6. Assets created by tech: {tech_assets.count()}")
if tech_assets.exists():
    print(f"   Sample: {tech_assets.first().id} - {tech_assets.first().name}")

# Check if there are TICKET_CREATED logs at all
ticket_created_logs = ActivityLog.objects.filter(action='TICKET_CREATED')
print(f"\n7. Total TICKET_CREATED logs: {ticket_created_logs.count()}")
if ticket_created_logs.exists():
    sample = ticket_created_logs.first()
    print(f"   Sample: user={sample.user}, user_id={sample.user_id}, actor_name={repr(sample.actor_name)}")

# Check if there are ASSET_CREATED logs at all
asset_created_logs = ActivityLog.objects.filter(action='ASSET_CREATED')
print(f"8. Total ASSET_CREATED logs: {asset_created_logs.count()}")
if asset_created_logs.exists():
    sample = asset_created_logs.first()
    print(f"   Sample: user={sample.user}, user_id={sample.user_id}, actor_name={repr(sample.actor_name)}")

print("\n" + "="*60)
print("ISSUE DIAGNOSIS:")
if tech_tickets.count() > 0 and all_tech_logs.count() == 0:
    print("❌ LOGGING NOT WORKING: Tech has created tickets but no logs exist!")
    print("   The logging system is not being called during ticket creation.")
elif all_tech_logs.count() > 0:
    print("✓ Logs DO exist for tech - filter should work")
else:
    print("⚠ Tech hasn't created any activities yet")
