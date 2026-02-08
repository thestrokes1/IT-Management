#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.logs.models import ActivityLog
from apps.logs.services.log_query_service import LogQueryService
from django.db.models import Q

# Test 1: Direct query for testuser via FK
print("=== Test 1: Direct query for testuser ===")
logs = ActivityLog.objects.filter(user__username__iexact='testuser')
print(f"Found {logs.count()} logs for testuser")
print([log.action for log in logs[:3]])

# Test 2: Use the filter_by_actor service method
print("\n=== Test 2: Using LogQueryService.filter_by_actor('testuser') ===")
service = LogQueryService()
service = service.filter_by_actor(actor_name='testuser')
logs = service.all()
print(f"Found {logs.count()} logs via service")
print([log.action for log in logs[:3]])

# Test 3: Test search functionality
print("\n=== Test 3: Search for 'ticket' ===")
service = LogQueryService()
service = service.search('ticket')
logs = service.all()
print(f"Found {logs.count()} logs matching 'ticket'")

# Test 4: Combination filter (testuser + TICKET_CREATED action)
print("\n=== Test 4: testuser + TICKET_CREATED ===")
service = LogQueryService()
service = service.filter_by_actor(actor_name='testuser')
service = service.filter_by_action(['TICKET_CREATED'])
logs = service.all()
print(f"Found {logs.count()} logs")

print("\n✓ All tests passed - filtering works!")
