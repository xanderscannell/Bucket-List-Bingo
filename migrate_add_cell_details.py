"""
Migration script to add cell_details column to progress table
Run this once to update your existing database
"""

import sqlite3
import os

# Get the database path
db_path = os.path.join('instance', 'bingo.db')

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    print("No migration needed - new database will be created with the correct schema.")
    exit(0)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if column already exists
    cursor.execute("PRAGMA table_info(progress)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'cell_details' in columns:
        print("[OK] Migration already applied - cell_details column exists")
    else:
        # Add the new column
        print("Adding cell_details column to progress table...")
        cursor.execute("ALTER TABLE progress ADD COLUMN cell_details TEXT")
        conn.commit()
        print("[OK] Migration successful - cell_details column added")

except Exception as e:
    print(f"[ERROR] Migration failed: {e}")
    conn.rollback()
finally:
    conn.close()

print("\nMigration complete!")
