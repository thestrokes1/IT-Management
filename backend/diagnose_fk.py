#!/usr/bin/env python
"""Diagnose foreign key constraint issues."""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check for foreign keys
cursor.execute('PRAGMA foreign_keys;')
print('Foreign keys:', cursor.fetchone())

# Check for triggers
cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger';")
triggers = cursor.fetchall()
print('Triggers:', triggers)

# Check the assets table structure
cursor.execute("PRAGMA table_info(assets);")
print('\nAssets table structure:')
for row in cursor.fetchall():
    print(row)

# Check hardware_assets table
cursor.execute("PRAGMA table_info(hardware_assets);")
print('\nHardware_assets table structure:')
for row in cursor.fetchall():
    print(row)

# Check software_assets table
cursor.execute("PRAGMA table_info(software_assets);")
print('\nSoftware_assets table structure:')
for row in cursor.fetchall():
    print(row)

# Check for foreign key constraints on assets table
cursor.execute("""
SELECT 
    sql 
FROM 
    sqlite_master 
WHERE 
    type='table' AND 
    name='assets'
""")
print('\nAssets table SQL:')
print(cursor.fetchone()[0])

# Check for any foreign key constraints that reference assets
cursor.execute("""
SELECT 
    name, sql 
FROM 
    sqlite_master 
WHERE 
    sql LIKE '%FOREIGN KEY%' AND 
    sql LIKE '%assets%'
""")
print('\nForeign keys referencing assets:')
for row in cursor.fetchall():
    print(row[0], ':', row[1])

# Check for any pending foreign keys
cursor.execute("PRAGMA foreign_key_check;")
print('\nForeign key check:', cursor.fetchall())

conn.close()
