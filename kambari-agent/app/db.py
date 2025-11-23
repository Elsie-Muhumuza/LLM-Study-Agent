import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

# Database file path
DB_PATH = os.path.join(Path(__file__).parent.parent, 'kambari.db')

def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row factory set to return dictionaries."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with required tables."""
    conn = get_db_connection()
    
    try:
        with conn:
            # Create members table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE,
                email TEXT UNIQUE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create member_availability table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS member_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                is_available BOOLEAN DEFAULT 1,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members (id),
                UNIQUE(member_id, date)
            )
            ''')
            
            # Create series table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                theme TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')

            # Create passages table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS passages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_id INTEGER,
                title TEXT NOT NULL,
                reference TEXT NOT NULL,
                study_notes TEXT,
                session_date DATE NOT NULL,
                FOREIGN KEY (series_id) REFERENCES series (id)
            )
            ''')

            # Create schedule table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date DATE NOT NULL,
                member_id INTEGER NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('prayer_lead', 'scripture_reader', 'sharing_lead')),
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES members (id),
                UNIQUE(session_date, role)
            )
            ''')

            # Create generated_materials table
            conn.execute('''
            CREATE TABLE IF NOT EXISTS generated_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passage_id INTEGER NOT NULL,
                questions TEXT NOT NULL,
                discussion_points TEXT,
                prayer_points TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (passage_id) REFERENCES passages (id)
            )
            ''')

            # Create indexes for better performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_schedule_date ON schedule(session_date)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_passages_series ON passages(series_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_passages_date ON passages(session_date)')

            conn.commit()
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        raise e
    finally:
        if 'conn' in locals():
            conn.close()

def add_member(name: str, phone: str, email: str = None) -> int:
    """Add a new member to the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO members (name, phone, email) VALUES (?, ?, ?)',
            (name, phone, email)
        )
        member_id = cursor.lastrowid
        conn.commit()
        return member_id
    except sqlite3.IntegrityError:
        raise ValueError(f"A member with phone {phone} already exists")
    finally:
        conn.close()

def get_members(active_only: bool = True):
    """Get all members, optionally filtered by active status."""
    conn = get_db_connection()
    try:
        if active_only:
            return conn.execute('SELECT * FROM members WHERE is_active = 1').fetchall()
        return conn.execute('SELECT * FROM members').fetchall()
    finally:
        conn.close()

def set_member_availability(member_id: int, date: str, is_available: bool = True, reason: str = None):
    """Set a member's availability for a specific date."""
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO member_availability (member_id, date, is_available, reason)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(member_id, date) 
            DO UPDATE SET is_available = excluded.is_available, 
                         reason = excluded.reason,
                         created_at = CURRENT_TIMESTAMP
        ''', (member_id, date, is_available, reason))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error setting member availability: {e}")
        return False
    finally:
        conn.close()

def get_available_members(date: str):
    """Get all members available on a specific date."""
    conn = get_db_connection()
    try:
        return conn.execute('''
            SELECT m.* FROM members m
            LEFT JOIN member_availability ma ON m.id = ma.member_id AND ma.date = ?
            WHERE m.is_active = 1 AND (ma.id IS NULL OR ma.is_available = 1)
            ORDER BY m.name
        ''', (date,)).fetchall()
    finally:
        conn.close()

def get_member_schedule(member_id: int, start_date: str = None, end_date: str = None):
    """Get a member's schedule and availability."""
    conn = get_db_connection()
    try:
        query = '''
            SELECT s.session_date, s.role, 
                   CASE WHEN ma.is_available = 0 THEN 0 ELSE 1 END as is_available,
                   ma.reason
            FROM schedule s
            LEFT JOIN member_availability ma ON s.member_id = ma.member_id 
                AND s.session_date = ma.date
            WHERE s.member_id = ?
        '''
        params = [member_id]
        
        if start_date and end_date:
            query += " AND s.session_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND s.session_date >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND s.session_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY s.session_date"
        
        return conn.execute(query, tuple(params)).fetchall()
    finally:
        conn.close()

def list_members():
    """List all members with their basic information.
    
    Returns:
        list: List of tuples containing (id, name, phone, email, is_active)
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, phone, email, is_active 
            FROM members 
            ORDER BY name
        ''')
        return cursor.fetchall()
    finally:
        conn.close()

def delete_member(member_id: int) -> bool:
    """Delete a member by ID.
    
    Args:
        member_id: The ID of the member to delete
        
    Returns:
        bool: True if member was deleted, False if not found
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM members WHERE id = ?', (member_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def find_member_by_phone(phone: str):
    """Find a member by phone number.
    
    Args:
        phone: The phone number to search for
        
    Returns:
        dict: Member details if found, None otherwise
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM members WHERE phone = ?', (phone,))
        return cursor.fetchone()
    finally:
        conn.close()

def find_members_by_name(name: str):
    """Find members by name (case-insensitive partial match).
    
    Args:
        name: The name to search for (can be partial)
        
    Returns:
        list: List of matching members
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM members WHERE LOWER(name) LIKE ?', (f'%{name.lower()}%',))
        return cursor.fetchall()
    finally:
        conn.close()

def get_upcoming_sessions(days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Get all scheduled sessions within the next N days."""
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            SELECT s.session_date, m.name as member_name, s.role
            FROM schedule s
            JOIN members m ON s.member_id = m.id
            WHERE s.session_date >= date('now')
            AND s.session_date <= date('now', ? || ' days')
            ORDER BY s.session_date, s.role
        ''', (str(days_ahead),))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

# Initialize the database when this module is imported
init_db()