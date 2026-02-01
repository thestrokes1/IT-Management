import sqlite3
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Check for foreign keys on assets table
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='assets'")
print('Assets table:')
print(cursor.fetchone()[0])

# Check hardware_assets
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='hardware_assets'")
print('\nHardware_assets table:')
print(cursor.fetchone()[0])

# Check for any other table that might reference assets
cursor.execute("SELECT name, sql FROM sqlite_master WHERE sql LIKE '%REFERENCES%assets%'")
print('\nTables referencing assets:')
for row in cursor.fetchall():
    print(row[0])
    print(row[1])
    print()

conn.close()
