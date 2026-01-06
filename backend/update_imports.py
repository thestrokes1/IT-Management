#!/usr/bin/env python
"""Script to update imports across the project."""
import os
import re

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Files to update
files_to_update = [
    'apps/frontend/services.py',
    'apps/frontend/views/projects.py',
    'apps/projects/application/__init__.py',
]

# Import mapping: old -> new
import_mapping = [
    ('from apps.core.policies import ProjectPolicy', 'from apps.projects.policies import ProjectPolicy'),
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        continue
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    original_content = content
    
    for old_import, new_import in import_mapping:
        content = content.replace(old_import, new_import)
    
    if content != original_content:
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Updated: {filepath}")
    else:
        print(f"No changes: {filepath}")

print("Done!")

