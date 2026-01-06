"""
Comprehensive migration script for legacy database
Safely migrates from commit a365c54 to latest version with photo upload support

This script:
1. Validates the source database
2. Creates a backup
3. Adds the cell_details column if missing
4. Verifies data integrity
5. Provides rollback capability
"""

import sqlite3
import os
import shutil
import sys
from datetime import datetime

# Fix Unicode output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
LEGACY_DB_PATH = os.path.join('legacy data', 'legacy_bingo.db')
TARGET_DB_PATH = os.path.join('instance', 'bingo.db')
BACKUP_DIR = 'database_backups'

def create_backup_dir():
    """Create backup directory if it doesn't exist"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"✓ Created backup directory: {BACKUP_DIR}")

def backup_database(db_path, backup_name):
    """Create a timestamped backup of the database"""
    if not os.path.exists(db_path):
        print(f"⚠ Database not found: {db_path}")
        return None

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'{backup_name}_{timestamp}.db')

    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def validate_database_structure(db_path, expected_tables):
    """Validate that database has expected tables"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    missing_tables = [t for t in expected_tables if t not in tables]

    conn.close()

    if missing_tables:
        print(f"✗ Missing tables: {', '.join(missing_tables)}")
        return False

    print(f"✓ All expected tables present: {', '.join(expected_tables)}")
    return True

def check_column_exists(db_path, table_name, column_name):
    """Check if a column exists in a table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]

    conn.close()

    return column_name in columns

def add_cell_details_column(db_path):
    """Add cell_details column to progress table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        if check_column_exists(db_path, 'progress', 'cell_details'):
            print("✓ cell_details column already exists")
            conn.close()
            return True

        # Add the column
        print("Adding cell_details column to progress table...")
        cursor.execute("ALTER TABLE progress ADD COLUMN cell_details TEXT")
        conn.commit()
        print("✓ cell_details column added successfully")

        conn.close()
        return True

    except Exception as e:
        print(f"✗ Failed to add cell_details column: {e}")
        conn.rollback()
        conn.close()
        return False

def verify_data_integrity(db_path):
    """Verify that all data is intact after migration"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    issues = []

    # Check users table
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"✓ Users found: {user_count}")

    # Check bingo_data table
    cursor.execute("SELECT COUNT(*) FROM bingo_data")
    bingo_data_count = cursor.fetchone()[0]
    print(f"✓ Bingo data records: {bingo_data_count}")

    # Check progress table
    cursor.execute("SELECT COUNT(*) FROM progress")
    progress_count = cursor.fetchone()[0]
    print(f"✓ Progress records: {progress_count}")

    # Verify all users have bingo_data and progress
    cursor.execute("""
        SELECT u.id, u.name
        FROM users u
        LEFT JOIN bingo_data b ON u.id = b.user_id
        WHERE b.user_id IS NULL
    """)
    users_without_bingo = cursor.fetchall()

    if users_without_bingo:
        issues.append(f"Users without bingo_data: {users_without_bingo}")

    cursor.execute("""
        SELECT u.id, u.name
        FROM users u
        LEFT JOIN progress p ON u.id = p.user_id
        WHERE p.user_id IS NULL
    """)
    users_without_progress = cursor.fetchall()

    if users_without_progress:
        issues.append(f"Users without progress: {users_without_progress}")

    # Check for corrupted JSON in marked_cells
    cursor.execute("SELECT user_id, marked_cells FROM progress WHERE marked_cells IS NOT NULL")
    for user_id, marked_cells in cursor.fetchall():
        try:
            import json
            json.loads(marked_cells)
        except json.JSONDecodeError:
            issues.append(f"Corrupted marked_cells JSON for user {user_id}")

    conn.close()

    if issues:
        print("\n⚠ Data integrity issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False

    print("✓ Data integrity verified - no issues found")
    return True

def migrate_legacy_to_current():
    """Main migration function"""
    print("\n" + "="*60)
    print("LEGACY DATABASE MIGRATION")
    print("="*60 + "\n")

    # Step 1: Create backup directory
    create_backup_dir()

    # Step 2: Validate legacy database exists
    if not os.path.exists(LEGACY_DB_PATH):
        print(f"✗ Legacy database not found at: {LEGACY_DB_PATH}")
        return False

    print(f"✓ Legacy database found: {LEGACY_DB_PATH}")

    # Step 3: Validate database structure
    expected_tables = ['users', 'bingo_data', 'progress']
    if not validate_database_structure(LEGACY_DB_PATH, expected_tables):
        print("✗ Legacy database structure validation failed")
        return False

    # Step 4: Create backup of legacy database
    legacy_backup = backup_database(LEGACY_DB_PATH, 'legacy_bingo_backup')
    if not legacy_backup:
        return False

    # Step 5: Create backup of current instance database (if exists)
    if os.path.exists(TARGET_DB_PATH):
        current_backup = backup_database(TARGET_DB_PATH, 'current_bingo_backup')
        print(f"✓ Current database backed up: {current_backup}")

    # Step 6: Copy legacy database to instance folder
    print(f"\nCopying legacy database to {TARGET_DB_PATH}...")

    # Create instance directory if it doesn't exist
    os.makedirs(os.path.dirname(TARGET_DB_PATH), exist_ok=True)

    shutil.copy2(LEGACY_DB_PATH, TARGET_DB_PATH)
    print(f"✓ Database copied to instance folder")

    # Step 7: Add cell_details column
    print("\nApplying schema migration...")
    if not add_cell_details_column(TARGET_DB_PATH):
        print("✗ Migration failed - restoring from backup")
        if legacy_backup and os.path.exists(legacy_backup):
            shutil.copy2(legacy_backup, TARGET_DB_PATH)
        return False

    # Step 8: Verify data integrity
    print("\nVerifying data integrity...")
    if not verify_data_integrity(TARGET_DB_PATH):
        print("⚠ Data integrity check found issues (non-critical)")

    # Step 9: Success!
    print("\n" + "="*60)
    print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\nYour migrated database is ready at: {TARGET_DB_PATH}")
    print(f"Backups are stored in: {BACKUP_DIR}/")
    print("\nYou can now start your Flask application.")
    print("\nTo rollback, copy the backup file back to instance/bingo.db")

    return True

def verify_schema_only(db_path):
    """Just check if the database needs migration (for deployment checks)"""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return None

    has_cell_details = check_column_exists(db_path, 'progress', 'cell_details')

    if has_cell_details:
        print("✓ Database schema is up to date (cell_details column exists)")
        return True
    else:
        print("✗ Database schema is outdated (cell_details column missing)")
        print("  Run this script to migrate, or run migrate_add_cell_details.py")
        return False

if __name__ == '__main__':
    import sys

    # Check if we're just verifying schema
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        db_to_check = sys.argv[2] if len(sys.argv) > 2 else TARGET_DB_PATH
        verify_schema_only(db_to_check)
        sys.exit(0)

    # Run full migration
    success = migrate_legacy_to_current()
    sys.exit(0 if success else 1)
