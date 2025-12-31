import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'it_management_platform.settings')
django.setup()

from django.core.management import call_command
from django.db import connection

# Check if the table exists before migration
cursor = connection.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_categories'")
table_exists = cursor.fetchone() is not None
print(f"Table exists before migration: {table_exists}")

# Run the migration
print("\nRunning migration 0003_taskcategory_task_category...")
call_command('migrate', 'projects', '0003_taskcategory_task_category', verbosity=2)

# Check again after migration
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='task_categories'")
table_exists = cursor.fetchone() is not None
print(f"\nTable exists after migration: {table_exists}")

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()
print(f"\nAll tables: {[t[0] for t in tables]}")

