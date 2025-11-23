from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import random
from app.db import get_db_connection

def assign_roles(session_date: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Assign roles for a given session date (defaults to next Thursday).
    
    Args:
        session_date: Date in 'YYYY-MM-DD' format. If None, uses next Thursday.
        
    Returns:
        List of dictionaries containing role assignments
    """
    conn = get_db_connection()
    try:
        # Get or calculate the session date
        if not session_date:
            today = datetime.now().date()
            # 3 = Thursday (0=Monday, 6=Sunday)
            days_until_thursday = (3 - today.weekday()) % 7
            if days_until_thursday == 0:  # If today is Thursday, schedule for next week
                days_until_thursday = 7
            session_date = (today + timedelta(days=days_until_thursday)).isoformat()
        
        # Check if roles are already assigned for this date
        cursor = conn.execute(
            'SELECT role, member_id FROM schedule WHERE session_date = ?',
            (session_date,)
        )
        existing_assignments = {row['role']: row['member_id'] for row in cursor.fetchall()}
        
        if len(existing_assignments) == 3:  # All roles already assigned
            return [
                {'role': role, 'member_id': member_id}
                for role, member_id in existing_assignments.items()
            ]
            
        # Get all active members
        members = conn.execute(
            'SELECT id, name FROM members WHERE is_active = 1'
        ).fetchall()
        
        if not members:
            raise ValueError("No active members found")
            
        if len(members) < 3:
            raise ValueError("Need at least 3 active members to assign all roles")
            
        # Get recent role assignments to ensure fair rotation
        recent_assignments = conn.execute('''
            SELECT member_id, role, session_date 
            FROM schedule 
            WHERE session_date < ? 
            ORDER BY session_date DESC 
            LIMIT ?
        ''', (session_date, len(members) * 3)).fetchall()
        
        # Track who has had recent roles
        member_roles = {member['id']: [] for member in members}
        for assignment in recent_assignments:
            if assignment['member_id'] in member_roles:
                member_roles[assignment['member_id']].append(assignment['role'])
        
        # Available members (not assigned yet for this session)
        available_members = [m for m in members if m['id'] not in existing_assignments.values()]
        
        # Role assignment priority: least recently had each role
        roles = ['prayer_lead', 'scripture_reader', 'sharing_lead']
        assignments = {}
        
        for role in roles:
            if role in existing_assignments:
                assignments[role] = existing_assignments[role]
                continue
                
            # Sort members by how recently they had this role (least recent first)
            def sort_key(member):
                member_roles_list = member_roles.get(member['id'], [])
                try:
                    return member_roles_list[::-1].index(role)
                except ValueError:
                    return float('inf')  # Never had this role
            
            available_members.sort(key=sort_key)
            
            if not available_members:
                raise ValueError("Not enough available members to assign all roles")
                
            # Assign the role to the member who had it least recently
            assigned_member = available_members.pop(0)
            assignments[role] = assigned_member['id']
            
            # Add to database
            conn.execute('''
                INSERT INTO schedule (session_date, member_id, role)
                VALUES (?, ?, ?)
            ''', (session_date, assigned_member['id'], role))
        
        conn.commit()
        
        # Return the assignments with member names
        cursor = conn.execute('''
            SELECT m.name, s.role 
            FROM schedule s
            JOIN members m ON s.member_id = m.id
            WHERE s.session_date = ?
        ''', (session_date,))
        
        return [dict(row) for row in cursor.fetchall()]
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_role_assignments(session_date: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Get role assignments for a specific session date.
    
    Args:
        session_date: Date in 'YYYY-MM-DD' format. If None, gets next Thursday.
        
    Returns:
        List of dictionaries with role assignments
    """
    conn = get_db_connection()
    try:
        if not session_date:
            today = datetime.now().date()
            days_until_thursday = (3 - today.weekday()) % 7
            if days_until_thursday == 0:  # If today is Thursday
                days_until_thursday = 7
            session_date = (today + timedelta(days=days_until_thursday)).isoformat()
        
        cursor = conn.execute('''
            SELECT m.name, s.role, s.member_id, s.session_date
            FROM schedule s
            JOIN members m ON s.member_id = m.id
            WHERE s.session_date = ?
            ORDER BY 
                CASE s.role
                    WHEN 'prayer_lead' THEN 1
                    WHEN 'scripture_reader' THEN 2
                    WHEN 'sharing_lead' THEN 3
                    ELSE 4
                END
        ''', (session_date,))
        
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def update_role_assignment(session_date: str, role: str, member_id: int) -> bool:
    """
    Update or create a role assignment.
    
    Args:
        session_date: Date in 'YYYY-MM-DD' format
        role: One of 'prayer_lead', 'scripture_reader', 'sharing_lead'
        member_id: ID of the member to assign the role to
        
    Returns:
        bool: True if successful, False otherwise
    """
    if role not in ['prayer_lead', 'scripture_reader', 'sharing_lead']:
        raise ValueError("Invalid role. Must be one of: prayer_lead, scripture_reader, sharing_lead")
    
    conn = get_db_connection()
    try:
        # Check if member exists and is active
        member = conn.execute(
            'SELECT id FROM members WHERE id = ? AND is_active = 1',
            (member_id,)
        ).fetchone()
        
        if not member:
            raise ValueError("Member not found or inactive")
            
        # Check if the role is already assigned to someone else
        existing = conn.execute(
            'SELECT member_id FROM schedule WHERE session_date = ? AND role = ?',
            (session_date, role)
        ).fetchone()
        
        if existing and existing['member_id'] == member_id:
            return True  # No change needed
            
        if existing:
            # Update existing assignment
            conn.execute('''
                UPDATE schedule 
                SET member_id = ?, assigned_date = CURRENT_TIMESTAMP
                WHERE session_date = ? AND role = ?
            ''', (member_id, session_date, role))
        else:
            # Create new assignment
            conn.execute('''
                INSERT INTO schedule (session_date, member_id, role)
                VALUES (?, ?, ?)
            ''', (session_date, member_id, role))
            
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_member_roles(member_id: int, limit: int = 5) -> List[Dict[str, str]]:
    """
    Get recent and upcoming role assignments for a member.
    
    Args:
        member_id: ID of the member
        limit: Maximum number of assignments to return
        
    Returns:
        List of role assignments with session dates
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            SELECT s.session_date, s.role, s.assigned_date
            FROM schedule s
            WHERE s.member_id = ?
            ORDER BY s.session_date DESC
            LIMIT ?
        ''', (member_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()