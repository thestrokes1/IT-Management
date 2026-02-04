#!/usr/bin/env python
"""Fix indentation in activity_service.py"""

# Read the file
with open('apps/logs/services/activity_service.py', 'r') as f:
    content = f.read()

# Fix the indentation - replace 'def get_activity_logs(' with '    def get_activity_logs('
content = content.replace(
    'def get_activity_logs(',
    '    def get_activity_logs('
)

# Write back
with open('apps/logs/services/activity_service.py', 'w') as f:
    f.write(content)

print('Fixed indentation in activity_service.py')

