#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from apps.logs.models import ActivityLog

# Check all fields and their null constraints
model_fields = ActivityLog._meta.get_fields()
print("ActivityLog fields with NULL=False constraints:")
print("=" * 60)

null_not_allowed = []
for field in model_fields:
    if hasattr(field, 'null') and hasattr(field, 'name'):
        if not field.null and field.name not in ['log_id', 'id']:
            null_not_allowed.append(field.name)
            print(f"✓ {field.name}: NULL=False, Type={field.get_internal_type()}")

print("\n" + "=" * 60)
print(f"Total fields with NOT NULL constraint: {len(null_not_allowed)}")
print("\nFields that could be problematic if returning None:")
critical_fields = ['user_agent', 'ip_address', 'timestamp', 'action', 'actor_name']
for field_name in critical_fields:
    if field_name in null_not_allowed:
        print(f"  ❌ {field_name} - NOT NULL, could be problematic")
    else:
        print(f"  ✓ {field_name} - allows NULL")
