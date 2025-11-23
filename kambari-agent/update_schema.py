#!/usr/bin/env python3
"""
Script to update the database schema to include series_id in the schedule table.
"""
import sqlite3
from pathlib import Path

def update_database_schema():
    db_path = Path('kambari.db')
    backup_path = db_path.with_suffix('.db.backup')
    
    # Create a connection to the database
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Create a backup of the current database
        print("Creating backup of the database...")
        backup_conn = sqlite3.connect(str(backup_path))
        conn.backup(backup_conn)
        backup_conn.close()
        print(f"Backup created at: {backup_path}")
        
        # Check if the series_id column already exists
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(schedule)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'series_id' not in columns:
            print("Adding series_id column to schedule table...")
            # SQLite doesn't support adding a column with a NOT NULL constraint without a default
            # So we'll add it as nullable first, then update existing rows if needed
            cursor.execute('''
            ALTER TABLE schedule 
            ADD COLUMN series_id INTEGER REFERENCES series(id)
            ''')
            
            # If you want to set a default series_id for existing records, uncomment and modify this:
            # cursor.execute('''
            # UPDATE schedule 
            # SET series_id = (SELECT id FROM series LIMIT 1)
            # WHERE series_id IS NULL
            # ''')
            
            conn.commit()
            print("Database schema updated successfully!")
        else:
            print("series_id column already exists in the schedule table.")
            
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema()
