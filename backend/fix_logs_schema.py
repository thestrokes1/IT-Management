#!/usr/bin/env python
"""Fix the activity_logs table schema by adding missing columns."""

import sqlite3
import sys

def main():
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()

    # Add missing columns to activity_logs table
    columns_to_add = [
        ('actor_type', 'VARCHAR(20) DEFAULT "user"'),
        ('actor_id', 'VARCHAR(255)'),
        ('actor_name', 'VARCHAR(255) DEFAULT "System"'),
        ('actor_role', 'VARCHAR(50) DEFAULT "VIEWER"'),
        ('event_type', 'VARCHAR(50)'),
        ('severity', 'VARCHAR(10) DEFAULT "INFO"'),
        ('intent', 'VARCHAR(20) DEFAULT "workflow"'),
        ('entity_type', 'VARCHAR(100)'),
        ('entity_id', 'INTEGER'),
        ('parent_log_id', 'UUID'),
        ('chain_depth', 'INTEGER DEFAULT 0'),
        ('chain_type', 'VARCHAR(50)'),
    ]

    for col_name, col_def in columns_to_add:
        try:
            cur.execute(f'ALTER TABLE activity_logs ADD COLUMN {col_name} {col_def}')
            print(f'Added column: {col_name}')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e):
                print(f'Column already exists: {col_name}')
            else:
                print(f'Error adding {col_name}: {e}')

    conn.commit()
    conn.close()
    print('Done!')

if __name__ == '__main__':
    main()

