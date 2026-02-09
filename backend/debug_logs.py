#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.logs.models import ActivityLog
from apps.users.models import User
from django.db.models import Q

# Check users with activity logs via FK
users_with_logs = User.objects.filter(activity_logs__isnull=False).distinct()
print("Users with activity logs (via FK):")
print([u.username for u in users_with_logs])

# Check all logs for 'testuser'
testuser_logs = ActivityLog.objects.filter(user__username__iexact='testuser')
print(f"\nLogs for testuser (via FK): {testuser_logs.count()}")

# Check all logs for 'tech'
tech_logs = ActivityLog.objects.filter(user__username__iexact='tech')
print(f"Logs for tech (via FK): {tech_logs.count()}")

# Show sample logs
print("\nSample 5 recent logs:")
for log in ActivityLog.objects.order_by('-timestamp')[:5]:
    print(f"User: {log.user}, Action: {log.action}, Time: {log.timestamp}")
