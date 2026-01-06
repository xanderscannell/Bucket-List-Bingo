# Bucket List Bingo - Deployment Guide

## Overview

This guide ensures safe deployment of Bucket List Bingo with photo upload support, preventing data corruption issues.

## Pre-Deployment Checklist

### 1. **Backup Current Database** (CRITICAL!)

Before deploying any new version:

```bash
# Create a backup of the production database
cp instance/bingo.db instance/bingo_backup_$(date +%Y%m%d_%H%M%S).db
```

Or use the migration script's built-in backup:

```bash
python migrate_legacy_database.py
```

### 2. **Identify Current Version**

Check which commit is currently deployed:

```bash
git log --oneline -1
```

The photo upload feature was added in commit `cdcee89` ("Added Completion Details").

## Migration Scenarios

### Scenario A: Migrating from Pre-Photo-Upload Version

**If your current production database is from commit `a365c54` or earlier** (before photo upload):

1. **Stop the application**

2. **Run the comprehensive migration script:**

```bash
python migrate_legacy_database.py
```

This script will:
- ✓ Validate your current database
- ✓ Create timestamped backups
- ✓ Add the `cell_details` column to the `progress` table
- ✓ Verify data integrity
- ✓ Provide rollback instructions

3. **Verify migration success:**

```bash
python migrate_legacy_database.py --verify instance/bingo.db
```

Expected output: `✓ Database schema is up to date (cell_details column exists)`

4. **Deploy new code** (pull latest changes)

5. **Start the application**

6. **Test with one user** before announcing to everyone

### Scenario B: Quick Migration (Existing Database)

**If you already have a database and just need to add the missing column:**

```bash
python migrate_add_cell_details.py
```

This simpler script just adds the column without extensive validation.

### Scenario C: Fresh Install

**If this is a brand new deployment:**

1. Pull the latest code
2. Run the application - it will create a fresh database with the correct schema
3. No migration needed!

## Post-Deployment Verification

### 1. Test Core Functionality

- [ ] Users can log in
- [ ] Existing progress is preserved (marked cells still marked)
- [ ] Users are NOT prompted to randomize if already randomized
- [ ] "Save & Mark Complete" button works
- [ ] Cell details can be added (photos, dates, notes)
- [ ] Leaderboard displays correctly

### 2. Check for Errors

Monitor the Flask console for:
- Database errors
- API endpoint failures
- JavaScript console errors

### 3. Verify Data Integrity

```bash
python -c "import sqlite3; conn = sqlite3.connect('instance/bingo.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM users'); print(f'Users: {cursor.fetchone()[0]}'); cursor.execute('SELECT COUNT(*) FROM progress WHERE randomized = 1'); print(f'Randomized cards: {cursor.fetchone()[0]}'); conn.close()"
```

## Troubleshooting

### Issue: "Save & Mark Complete" Button Does Nothing

**Symptoms:** Users click the button but nothing happens, modal doesn't close

**Causes:**
1. Database missing `cell_details` column
2. API errors (check Flask console)
3. JavaScript errors (check browser console)

**Solution:**
1. Check if migration was run: `python migrate_legacy_database.py --verify`
2. Check Flask console for API errors
3. Open browser DevTools Console and look for errors

### Issue: Users Prompted to Randomize Again

**Symptoms:** Users who already randomized their cards are asked to randomize again

**Causes:**
1. `randomized` flag was reset (data corruption)
2. Progress not loading correctly from API

**Solution:**
1. Restore from backup
2. Re-run migration properly
3. Check that `/api/users/<user_id>/progress` returns correct data

### Issue: App Won't Start - "Database schema is outdated"

**Symptoms:** Flask exits immediately with schema validation error

**This is intentional!** The app now validates the schema at startup to prevent data corruption.

**Solution:**
```bash
python migrate_legacy_database.py
# OR
python migrate_add_cell_details.py
```

Then restart the app.

## Rollback Procedure

If something goes wrong after deployment:

### 1. **Quick Rollback** (Restore Database Only)

```bash
# Stop the application
# Restore from backup
cp database_backups/legacy_bingo_backup_TIMESTAMP.db instance/bingo.db
# Restart the application
```

### 2. **Full Rollback** (Code + Database)

```bash
# Stop the application
# Revert to previous commit
git checkout a365c54  # or whichever commit was working
# Restore database from backup
cp database_backups/legacy_bingo_backup_TIMESTAMP.db instance/bingo.db
# Restart the application
```

## Database Schema Changes

### Current Schema (Post-Migration)

**Progress Table:**
- `id` (INTEGER, Primary Key)
- `user_id` (VARCHAR, Foreign Key → users.id)
- `marked_cells` (TEXT, JSON array of cell indices)
- `cell_details` (TEXT, JSON object with photos/dates/notes) **← ADDED IN cdcee89**
- `randomized` (BOOLEAN, default False)
- `updated_at` (DATETIME)

### Legacy Schema (Pre-cdcee89)

**Progress Table:**
- Same as above, **WITHOUT** `cell_details` column

## Deployment Safeguards

The latest version includes:

1. **Startup Schema Validation** - App won't start if schema is outdated
2. **Error Handling** - API failures show user-friendly messages instead of silent failures
3. **Automatic Backups** - Migration script creates timestamped backups
4. **Data Integrity Checks** - Verifies all users have progress/bingo_data

## Best Practices for Future Deployments

1. **Always backup before deploying**
2. **Run migrations BEFORE deploying new code**
3. **Test with one user first**
4. **Keep migration scripts in version control**
5. **Document schema changes in commit messages**
6. **Have a rollback plan ready**

## Support

If you encounter issues not covered in this guide:

1. Check Flask application logs
2. Check browser console (F12 → Console)
3. Verify database schema: `python migrate_legacy_database.py --verify`
4. Review git history to identify when the issue started

## Files Reference

- `migrate_legacy_database.py` - Comprehensive migration with backups and validation
- `migrate_add_cell_details.py` - Simple column addition script
- `app.py` - Flask application with schema validation
- `models.py` - Database models and schema definitions
- `instance/bingo.db` - Production SQLite database
- `database_backups/` - Timestamped database backups
