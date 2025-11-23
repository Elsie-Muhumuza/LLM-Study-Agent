#!/usr/bin/env python3
"""
Kambari Altar Agent - Command Line Interface

A unified interface for managing Bible study groups, role assignments, and study materials.
"""

import os
import sys
import click
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Load environment variables
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

@click.group()
def cli():
    """Kambari Altar Agent - Manage Bible study groups and materials."""
    pass

@cli.group()
def members():
    """Manage group members."""
    pass

@members.command()
@click.option('--name', prompt='Full name', help="Member's full name")
@click.option('--phone', default='', help="Phone number (optional)")
@click.option('--preferred-name', help="Preferred name (optional)")
@click.option('--email', help="Email address (optional)")
@click.option('--receive-reminders/--no-reminders', default=True, 
              help="Opt in/out of reminders (default: on)")
def add(name, phone, preferred_name, email, receive_reminders):
    """Add a new member to the group."""
    from app.db import add_member, get_members
    
    # Add the member
    add_member(
        name=name,
        phone=phone,
        email=email
    )
    
    click.echo(f"✅ Added member: {name}")
    
    # Show current members
    members = get_members()
    
    if not members:
        click.echo("No members found.")
        return
    
    click.echo("\nCurrent Members:")
    click.echo("ID  | Name                | Phone          | Email")
    click.echo("----|---------------------|----------------|------------------")
    for member in members:
        # Handle both dictionary and sqlite3.Row objects
        member_id = member['id']
        name = member['name']
        phone = member['phone'] if 'phone' in member.keys() and member['phone'] else 'N/A'
        email = member['email'] if 'email' in member.keys() and member['email'] else 'N/A'
        click.echo(f"{member_id:<4}| {name:<20}| {phone:<15}| {email}")

@members.command(name='list')
def list_members_cmd():
    """List all members."""
    from app.db import get_members
    
    members = get_members()
    
    if not members:
        click.echo("No members found.")
        return
    
    click.echo("\nCurrent Members:")
    click.echo("ID  | Name                | Phone          | Email")
    click.echo("----|---------------------|----------------|------------------")
    for member in members:
        # Handle both dictionary and sqlite3.Row objects
        member_id = member['id']
        name = member['name']
        phone = member['phone'] if 'phone' in member.keys() and member['phone'] else 'N/A'
        email = member['email'] if 'email' in member.keys() and member['email'] else 'N/A'
        click.echo(f"{member_id:<4}| {name:<20}| {phone:<15}| {email}")

@members.command(name='delete')
@click.argument('identifier', required=False)
@click.option('--id', 'use_id', is_flag=True, help='Treat the identifier as an ID')
@click.option('--phone', is_flag=True, help='Treat the identifier as a phone number')
def delete_member_cmd(identifier, use_id, phone):
    """Delete a member by ID, name, or phone number.
    
    Examples:
        kambari_cli.py members delete 1 --id      # Delete by ID
        kambari_cli.py members delete "John"      # Delete by name (will prompt if multiple matches)
        kambari_cli.py members delete +1234567890 --phone  # Delete by phone
    """
    from app.db import (
        delete_member, 
        get_members, 
        find_member_by_phone, 
        find_members_by_name
    )
    
    def show_members(members):
        if not members:
            click.echo("No members found.")
            return False
            
        click.echo("\nMatching Members:")
        click.echo("ID  | Name                | Phone          | Email")
        click.echo("----|---------------------|----------------|------------------")
        for member in members:
            member_id = member['id']
            name = member['name']
            phone = member['phone'] if 'phone' in member.keys() and member['phone'] else 'N/A'
            email = member['email'] if 'email' in member.keys() and member['email'] else 'N/A'
            click.echo(f"{member_id:<4}| {name:<20}| {phone:<15}| {email}")
        return True
        
    def delete_by_id(member_id):
        if delete_member(member_id):
            click.echo(f"✅ Successfully deleted member with ID {member_id}")
            return True
        click.echo(f"❌ No member found with ID {member_id}")
        return False
    
    # If no identifier provided, show current members and prompt
    if not identifier:
        members = get_members()
        if not show_members(members):
            return
            
        identifier = click.prompt("\nEnter ID, name, or phone of member to delete")
        if not identifier:
            click.echo("No identifier provided. Operation cancelled.")
            return
    
    # Try to delete by ID if --id flag is used or if identifier is a number
    if use_id or (identifier.isdigit() and not phone):
        if delete_by_id(int(identifier)):
            show_members(get_members())
        return
    
    # Try to find by phone if --phone flag is used or if it looks like a phone number
    if phone or (any(c.isdigit() for c in identifier) and not any(c.isalpha() for c in identifier)):
        member = find_member_by_phone(identifier)
        if member:
            if click.confirm(f"Delete {member['name']} (Phone: {member.get('phone', 'N/A')})?"):
                if delete_member(member['id']):
                    click.echo(f"✅ Successfully deleted {member['name']}")
                    show_members(get_members())
        else:
            click.echo(f"❌ No member found with phone number {identifier}")
        return
    
    # Try to find by name
    members = find_members_by_name(identifier)
    if not members:
        click.echo(f"❌ No members found matching '{identifier}'")
        return
        
    if len(members) == 1:
        member = members[0]
        if click.confirm(f"Delete {member['name']} (Phone: {member.get('phone', 'N/A')})?"):
            if delete_member(member['id']):
                click.echo(f"✅ Successfully deleted {member['name']}")
                show_members(get_members())
    else:
        show_members(members)
        member_id = click.prompt("\nMultiple matches found. Enter the ID of the member to delete")
        if member_id and member_id.isdigit():
            delete_by_id(int(member_id))
            show_members(get_members())

def format_date(date_str):
    """Format date string to YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').strftime('%Y-%m-%d')
    except ValueError:
        return None

@cli.group()
def member():
    """Manage members and their availability."""
    pass

@member.command(name='availability')
@click.argument('member_id', type=int, required=False)
@click.option('--date', help="Date (YYYY-MM-DD) to set availability for")
@click.option('--available/--unavailable', default=True, help="Set availability status")
@click.option('--reason', help="Reason for unavailability")
def set_availability(member_id, date, available, reason):
    """Set a member's availability for a specific date."""
    from app.db import (
        get_db_connection as get_conn,
        set_member_availability,
        get_available_members
    )
    
    conn = get_conn()
    
    # If member_id not provided, list members
    if not member_id:
        members = conn.execute('SELECT id, name FROM members WHERE is_active = 1 ORDER BY name').fetchall()
        if not members:
            click.echo("No active members found.")
            return
            
        click.echo("\nAvailable Members:")
        for m in members:
            click.echo(f"{m['id']}. {m['name']}")
            
        member_id = click.prompt("\nEnter the ID of the member", type=int)
    
    # Validate member exists
    member = conn.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
    if not member:
        click.echo(f"❌ Member with ID {member_id} not found")
        return
    
    # Get or validate date
    if not date:
        date = click.prompt("Enter date (YYYY-MM-DD)")
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        date_str = date_obj.strftime('%Y-%m-%d')
    except ValueError:
        click.echo("❌ Invalid date format. Please use YYYY-MM-DD")
        return
    
    # Set availability
    if set_member_availability(member_id, date_str, available, reason):
        status = "available" if available else "unavailable"
        click.echo(f"✅ {member['name']} marked as {status} on {date_str}")
        
        # Show who's available on this date
        if not available:
            available_members = get_available_members(date_str)
            click.echo(f"\nAvailable members on {date_str}:")
            for m in available_members:
                click.echo(f"- {m['name']}")
    else:
        click.echo(f"❌ Failed to update availability for {member['name']}")
    
    conn.close()

@cli.group()
def series():
    """Manage Bible study series."""
    pass

@series.command(name='assign-roles')
@click.argument('series_id', type=int, required=False)
@click.option('--reshuffle/--no-reshuffle', default=True, 
              help="Automatically reshuffle when members are unavailable")
def assign_roles(series_id, reshuffle):
    """Automatically assign rotating roles to members for a series sessions.
    
    Roles are assigned in a rotating fashion, ensuring everyone gets a chance to serve.
    If a member is unavailable on a date, the system will automatically try to reschedule them.
    """
    from app.db import (
        get_db_connection as get_conn,
        get_available_members,
        set_member_availability,
        get_member_schedule
    )
    
    conn = get_conn()
    
    # If series_id not provided, list available series
    if not series_id:
        series_list = conn.execute('SELECT id, title FROM series ORDER BY id DESC').fetchall()
        if not series_list:
            click.echo("No series found. Please create a series first.")
            return
            
        click.echo("\nAvailable Series:")
        for s in series_list:
            click.echo(f"{s['id']}. {s['title']}")
            
        series_id = click.prompt("\nEnter the ID of the series to assign roles for", type=int)
    
    # Get series details
    series = conn.execute('SELECT * FROM series WHERE id = ?', (series_id,)).fetchone()
    if not series:
        click.echo(f"❌ Series with ID {series_id} not found")
        return
        
    # Get all active members
    members = conn.execute('SELECT id, name FROM members WHERE is_active = 1 ORDER BY name').fetchall()
    if not members:
        click.echo("No active members found. Please add members first.")
        return
    
    if len(members) < 3:
        click.echo("❌ You need at least 3 active members to assign all roles.")
        return
    
    click.echo(f"\nAssigning rotating roles for: {series['title']}")
    click.echo("-" * 50)
    
    # Get the session dates for this series
    start_date = datetime.strptime(series['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(series['end_date'], '%Y-%m-%d')
    
    # Calculate all session dates (weekly from start to end date)
    session_dates = []
    current_date = start_date
    while current_date <= end_date:
        session_dates.append(current_date.strftime('%Y-%m-%d'))
        current_date += timedelta(weeks=1)
    
    # Clear any existing schedule for this series
    conn.execute("""
        DELETE FROM schedule 
        WHERE session_date BETWEEN ? AND ?
    """, (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    
    # Prepare role assignments with rotation and availability check
    role_assignments = {}
    member_index = 0
    
    for week, session_date in enumerate(session_dates, 1):
        # Get available members for this date
        available_members = get_available_members(session_date)
        available_ids = {m['id'] for m in available_members}
        
        # If we don't have enough available members, show a warning
        if len(available_members) < 3:
            click.echo(f"\n⚠️  Warning: Only {len(available_members)} members available on {session_date} (need 3)")
            if not click.confirm("Continue with fewer members?"):
                return
        
        # Assign roles with rotation, considering availability
        roles = ['prayer_lead', 'scripture_reader', 'sharing_lead']
        assigned_members = set()
        
        for role in roles:
            # Try to find an available member who hasn't been assigned yet
            for _ in range(len(available_members)):
                member = members[member_index % len(members)]
                member_index += 1
                
                # Skip if member is not available or already assigned
                if member['id'] not in available_ids or member['id'] in assigned_members:
                    continue
                
                # Assign the role
                conn.execute("""
                    INSERT INTO schedule (session_date, member_id, role)
                    VALUES (?, ?, ?)
                """, (session_date, member['id'], role))
                
                assigned_members.add(member['id'])
                
                # Store for display
                if session_date not in role_assignments:
                    role_assignments[session_date] = {}
                role_assignments[session_date][role] = member['name']
                break
        
        # If we couldn't assign all roles, try to find a solution
        if len(assigned_members) < 3 and reshuffle:
            click.echo(f"\n🔍 Couldn't assign all roles for {session_date}. Trying to reshuffle...")
            # Try to find members who can be rescheduled
            for member_id in [m['id'] for m in members if m['id'] not in assigned_members]:
                # Find a future date where this member is available
                for future_date in session_dates[session_dates.index(session_date) + 1:]:
                    future_available = get_available_members(future_date)
                    future_available_ids = {m['id'] for m in future_available}
                    
                    if member_id in future_available_ids:
                        # Check if this member is already assigned on this date
                        existing = conn.execute("""
                            SELECT 1 FROM schedule 
                            WHERE member_id = ? AND session_date = ?
                        """, (member_id, future_date)).fetchone()
                        
                        if not existing:
                            # Assign this member to the future date
                            for role in roles:
                                existing_role = conn.execute("""
                                    SELECT 1 FROM schedule 
                                    WHERE session_date = ? AND role = ?
                                """, (future_date, role)).fetchone()
                                
                                if not existing_role:
                                    conn.execute("""
                                        INSERT INTO schedule (session_date, member_id, role)
                                        VALUES (?, ?, ?)
                                    """, (future_date, member_id, role))
                                    
                                    # Update the display
                                    if future_date not in role_assignments:
                                        role_assignments[future_date] = {}
                                    role_assignments[future_date][role] = next(
                                        m['name'] for m in members if m['id'] == member_id
                                    )
                                    
                                    click.echo(f"  ↳ Rescheduled to {future_date} as {role.replace('_', ' ').title()}")
                                    break
                            break
    
    # Display the assignments
    click.echo("\n📅 Final Role Assignments:")
    click.echo("=" * 50)
    
    for session_date, roles in sorted(role_assignments.items()):
        date_obj = datetime.strptime(session_date, '%Y-%m-%d')
        click.echo(f"\nWeek of {date_obj.strftime('%B %d, %Y')}:")
        for role, name in roles.items():
            emoji = '🙏' if 'prayer' in role else '📖' if 'scripture' in role else '💬'
            click.echo(f"  {emoji} {role.replace('_', ' ').title()} — {name}")
    
    # Save changes
    try:
        conn.commit()
        click.echo("\n✅ Rotating role assignments saved successfully!")
        
        # Add a command to view the schedule
        if click.confirm("\nWould you like to view the full schedule?"):
            view_schedule(series_id)
            
    except Exception as e:
        conn.rollback()
        click.echo(f"\n❌ Error saving role assignments: {str(e)}")
        if "UNIQUE constraint failed" in str(e):
            click.echo("  This usually happens when a member is assigned multiple roles on the same date.")
            click.echo("  Try running with --no-reshuffle or check for duplicate assignments.")
    
    conn.close()

def view_schedule(series_id=None):
    """View the schedule for a series."""
    from app.db import get_db_connection as get_conn
    
    conn = get_conn()
    
    # If series_id not provided, list available series
    if not series_id:
        series_list = conn.execute('SELECT id, title FROM series ORDER BY id DESC').fetchall()
        if not series_list:
            click.echo("No series found.")
            return
            
        click.echo("\nAvailable Series:")
        for s in series_list:
            click.echo(f"{s['id']}. {s['title']}")
            
        series_id = click.prompt("\nEnter the ID of the series to view", type=int)
    
    # Get series details
    series = conn.execute('SELECT * FROM series WHERE id = ?', (series_id,)).fetchone()
    if not series:
        click.echo(f"❌ Series with ID {series_id} not found")
        return
    
    # Get all schedule entries for this series
    schedule = conn.execute('''
        SELECT s.session_date, m.name, s.role 
        FROM schedule s
        JOIN members m ON s.member_id = m.id
        WHERE s.session_date BETWEEN ? AND ?
        ORDER BY s.session_date, s.role
    ''', (series['start_date'], series['end_date'])).fetchall()
    
    if not schedule:
        click.echo("\nNo schedule entries found for this series.")
        return
    
    # Group by date
    schedule_by_date = {}
    for entry in schedule:
        if entry['session_date'] not in schedule_by_date:
            schedule_by_date[entry['session_date']] = []
        schedule_by_date[entry['session_date']].append(entry)
    
    # Display the schedule
    click.echo(f"\n📅 Schedule for: {series['title']}")
    click.echo("=" * 50)
    
    for session_date, roles in sorted(schedule_by_date.items()):
        date_obj = datetime.strptime(session_date, '%Y-%m-%d')
        click.echo(f"\nWeek of {date_obj.strftime('%B %d, %Y')}:")
        for role in sorted(roles, key=lambda x: x['role']):
            role_name = role['role'].replace('_', ' ').title()
            emoji = '🙏' if 'prayer' in role['role'] else '📖' if 'scripture' in role['role'] else '💬'
            click.echo(f"  {emoji} {role_name} — {role['name']}")
    
    conn.close()

@series.command(name='create')
@click.option('--title', prompt='Series title', help="Title of the series")
@click.option('--theme', prompt='Theme', help="Theme or topic of the series")
@click.option('--start-date', prompt='Start date (YYYY-MM-DD)', help="When the series begins")
@click.option('--frequency', type=int, default=7, 
              help="Days between sessions (default: 7 for weekly)")
@click.option('--weeks', type=int, default=4, 
              help="Total number of weeks (default: 4)")
def create_series(title, theme, start_date, frequency, weeks):
    """Create a new Bible study series."""
    from app.db import get_db_connection as get_conn
    
    try:
        # Validate date format
        from datetime import datetime
        datetime.strptime(start_date, '%Y-%m-%d')
        
        # Add to database
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO series (title, theme, start_date, end_date, is_active)
            VALUES (?, ?, ?, date(?, '+' || ? || ' days'), ?)
            """, (title, theme, start_date, start_date, (weeks * 7) - 1, True))
        
        series_id = cur.lastrowid
        conn.commit()
        
        conn.close()
        
        click.echo(f"✅ Created series: {title} (ID: {series_id})")
        click.echo("Note: Use 'kambari_cli.py schedule assign' to assign members to roles for this series.")
        
    except ValueError as e:
        click.echo(f"❌ Error: {str(e)}")
        if 'does not match format' in str(e):
            click.echo("Please use YYYY-MM-DD format for dates.")
    except Exception as e:
        click.echo(f"❌ Error creating series: {str(e)}")

@series.command(name='list')
def list_series():
    """List all Bible study series."""
    from app.db import get_db_connection as get_conn
    
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, theme, start_date, end_date, is_active, created_at
        FROM series
        ORDER BY start_date DESC
    """)
    
    series_list = cur.fetchall()
    conn.close()
    
    if not series_list:
        click.echo("No series found.")
        return
    
    click.echo("\nBible Study Series:")
    click.echo("-" * 50)
    for series in series_list:
        status = "Active" if series['is_active'] else "Inactive"
        click.echo(f"ID: {series['id']}")
        click.echo(f"Title: {series['title']}")
        click.echo(f"Theme: {series['theme']}")
        click.echo(f"Start Date: {series['start_date']}")
        click.echo(f"End Date: {series['end_date']}")
        click.echo(f"Status: {status}")
        click.echo(f"Created: {series['created_at']}")
        click.echo("-" * 50)

@series.command(name='schedule')
@click.argument('series_id', type=int, required=False)
def show_schedule(series_id=None):
    """Show the schedule for a series."""
    view_schedule(series_id)

@cli.group()
def materials():
    """Manage study materials."""
    pass

@materials.command()
@click.argument('series_id', type=int)
@click.option('--week', type=int, help="Week number (default: all weeks)")
@click.option('--force', is_flag=True, help="Regenerate existing materials")
def generate(series_id, week, force):
    """Generate study materials for a series."""
    from app.question_generator import generate_study_questions
    from app.db import get_db_connection as get_conn
    
    # Get series info
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id, title FROM series WHERE id = ?", (series_id,))
    series = cur.fetchone()
    
    if not series:
        click.echo(f"❌ Series with ID {series_id} not found.")
        return
    
    # Get passages for the series
    query = """
        SELECT id, week_number, passage_reference, passage_text, notes 
        FROM passages 
        WHERE series_id = ?
    """
    params = [series_id]
    
    if week is not None:
        query += " AND week_number = ?"
        params.append(week)
    
    query += " ORDER BY week_number"
    
    cur.execute(query, tuple(params))
    passages = cur.fetchall()
    
    if not passages:
        click.echo(f"No passages found for series '{series[1]}'")
        if week is not None:
            click.echo(f"Week {week} may not exist for this series.")
        return
    
    # Generate materials for each passage
    for passage in passages:
        passage_id, week_num, ref, text, notes = passage
        
        click.echo(f"\n📖 Generating materials for Week {week_num}: {ref}")
        
        # Check if materials already exist
        if not force:
            cur.execute("""
                SELECT 1 FROM generated_materials 
                WHERE series_id = ? AND week_number = ?
            """, (series_id, week_num))
            
            if cur.fetchone():
                click.echo(f"  ⏩ Materials already exist for Week {week_num}. Use --force to regenerate.")
                continue
        
        try:
            # Generate questions
            click.echo("  - Generating study questions...")
            questions = generate_study_questions(ref, text, notes or "")
            
            # Save to database
            cur.execute("""
                INSERT OR REPLACE INTO generated_materials 
                (series_id, week_number, material_type, content)
                VALUES (?, ?, ?, ?)
            """, (series_id, week_num, 'study_questions', json.dumps(questions)))
            
            conn.commit()
            click.echo(f"  ✅ Saved study questions for Week {week_num}")
            
        except Exception as e:
            conn.rollback()
            click.echo(f"  ❌ Error generating materials: {str(e)}")
    
    conn.close()
    click.echo("\n🎉 Material generation complete!")

@cli.group()
def reminders():
    """Manage study session reminders."""
    pass

@reminders.command()
@click.option('--test', is_flag=True, help="Test mode (no actual messages sent)")
@click.option('--force', is_flag=True, help="Send even if not Thursday")
def send(test, force):
    """Send reminders for upcoming study sessions."""
    from send_thu_reminders import send_reminders
    
    if test:
        click.echo("🔧 Running in test mode - no actual messages will be sent")
    
    if force:
        click.echo("⚡ Force sending reminders (regardless of day)")
    
    click.echo("🚀 Starting reminder process...")
    send_reminders(test_mode=test)

@cli.command()
def web():
    """Launch the web interface."""
    import subprocess
    try:
        subprocess.run(["streamlit", "run", "main.py"], check=True)
    except KeyboardInterrupt:
        click.echo("\nWeb server stopped.")
    except Exception as e:
        click.echo(f"❌ Error starting web interface: {str(e)}")
        click.echo("Make sure Streamlit is installed: pip install streamlit")

if __name__ == '__main__':
    cli()
