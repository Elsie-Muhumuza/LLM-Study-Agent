#!/usr/bin/env python3
"""
CLI tool to send Thursday reminders for upcoming Bible study sessions.
"""

import os
import sys
import json
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import after setting up the path
from app.db import get_db_connection as get_conn
from app.roles_engine import get_current_assignments

def get_upcoming_sessions(days_ahead=7):
    """Get all sessions happening in the next X days."""
    conn = get_conn()
    cur = conn.cursor()
    
    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)
    
    cur.execute("""
        SELECT s.id, s.title, sch.session_date, sch.week_number
        FROM schedule sch
        JOIN series s ON sch.series_id = s.id
        WHERE sch.session_date BETWEEN ? AND ?
        AND s.is_active = 1
        ORDER BY sch.session_date
    """, (today, end_date))
    
    sessions = []
    for row in cur.fetchall():
        sessions.append({
            'series_id': row[0],
            'series_title': row[1],
            'session_date': row[2],
            'week_number': row[3]
        })
    
    conn.close()
    return sessions

def get_session_materials(series_id, week_number):
    """Get study materials for a specific session."""
    conn = get_conn()
    cur = conn.cursor()
    
    # Get passage
    cur.execute("""
        SELECT passage_reference, passage_text, notes 
        FROM passages 
        WHERE series_id = ? AND week_number = ?
    """, (series_id, week_number))
    
    passage = cur.fetchone()
    if not passage:
        return None
    
    # Get generated materials
    cur.execute("""
        SELECT material_type, content 
        FROM generated_materials 
        WHERE series_id = ? AND week_number = ?
    """, (series_id, week_number))
    
    materials = {}
    for row in cur.fetchall():
        try:
            materials[row[0]] = json.loads(row[1])
        except json.JSONDecodeError:
            materials[row[0]] = row[1]
    
    conn.close()
    
    return {
        'passage_reference': passage[0],
        'passage_text': passage[1],
        'notes': passage[2],
        'materials': materials
    }

def get_member_emails():
    """Get email addresses of all members who want to receive reminders."""
    conn = get_conn()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT name, email, phone 
        FROM members 
        WHERE receive_reminders = 1 AND (email IS NOT NULL OR phone IS NOT NULL)
    """)
    
    members = []
    for row in cur.fetchall():
        members.append({
            'name': row[0],
            'email': row[1],
            'phone': row[2]
        })
    
    conn.close()
    return members

def send_email(recipient_email, subject, html_content, text_content=None):
    """Send an email using SMTP."""
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('DEFAULT_FROM_EMAIL', smtp_username)
    
    if not all([smtp_server, smtp_username, smtp_password]):
        print("Error: Email configuration is incomplete. Check your .env file.")
        return False
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = recipient_email
    
    # Attach both HTML and plain text versions
    if text_content:
        part1 = MIMEText(text_content, 'plain')
        msg.attach(part1)
    
    part2 = MIMEText(html_content, 'html')
    msg.attach(part2)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email to {recipient_email}: {str(e)}")
        return False

def send_whatsapp(phone_number, message):
    """Send a WhatsApp message using the Twilio API."""
    from twilio.rest import Client
    
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
    
    if not all([account_sid, auth_token, twilio_number]):
        print("Error: WhatsApp configuration is incomplete. Check your .env file.")
        return False
    
    try:
        client = Client(account_sid, auth_token)
        
        # Format phone number (remove any non-digit characters and add + if needed)
        phone_number = ''.join(filter(str.isdigit, phone_number))
        if not phone_number.startswith('+'):
            # Assuming default country code if not provided
            default_country_code = os.getenv('DEFAULT_COUNTRY_CODE', '1')
            phone_number = f"+{default_country_code}{phone_number}"
        
        message = client.messages.create(
            body=message,
            from_=f"whatsapp:{twilio_number}",
            to=f"whatsapp:{phone_number}"
        )
        return True
    except Exception as e:
        print(f"Error sending WhatsApp to {phone_number}: {str(e)}")
        return False

def format_reminder_message(session_info, materials, member_name, role=None):
    """Format the reminder message with session details."""
    session_date = datetime.strptime(session_info['session_date'], '%Y-%m-%d').strftime('%A, %B %d, %Y')
    
    # Format passage text for display
    passage_text = materials['passage_text']
    if len(passage_text) > 150:
        passage_text = passage_text[:147] + '...'
    
    # Format questions if available
    questions_html = ""
    questions_text = ""
    if 'study_questions' in materials['materials']:
        questions = materials['materials']['study_questions']
        questions_html = "<h3>Study Questions:</h3><ol>"
        questions_text = "\n\nStudy Questions:\n"
        
        if isinstance(questions, dict) and 'questions' in questions:
            for q in questions['questions']:
                questions_html += f"<li>{q}</li>"
                questions_text += f"- {q}\n"
        questions_html += "</ol>"
    
    # Role assignment message
    role_message = ""
    if role:
        role_message = f"<p>You have been assigned the role of <strong>{role.upper()}</strong> for this session. Please come prepared!</p>"
    
    # HTML version
    html_content = f"""
    <html>
    <body>
        <h2>📖 Bible Study Reminder: {session_info['series_title']}</h2>
        <p>Hello {member_name},</p>
        <p>This is a friendly reminder about our upcoming Bible study session:</p>
        
        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3>{session_info['series_title']} - Week {session_info['week_number']}</h3>
            <p><strong>📅 Date:</strong> {session_date}</p>
            <p><strong>📜 Passage:</strong> {materials['passage_reference']}</p>
            <p><strong>📝 Notes:</strong> {materials['notes'] or 'No additional notes'}</p>
            
            <div style="background-color: white; padding: 10px; margin: 10px 0; border-left: 4px solid #4CAF50;">
                <p>{passage_text}</p>
            </div>
            
            {questions_html}
            
            {role_message}
        </div>
        
        <p>We look forward to seeing you there!</p>
        <p>Blessings,<br>The Kambari Altar Team</p>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    BIBLE STUDY REMINDER: {session_info['series_title']}
    
    Hello {member_name},
    
    This is a friendly reminder about our upcoming Bible study session:
    
    {session_info['series_title']} - Week {session_info['week_number']}
    Date: {session_date}
    Passage: {materials['passage_reference']}
    Notes: {materials['notes'] or 'No additional notes'}
    
    {passage_text}
    {questions_text}
    {f'YOU HAVE BEEN ASSIGNED THE ROLE OF {role.upper()} FOR THIS SESSION. PLEASE COME PREPARED!' if role else ''}
    
    We look forward to seeing you there!
    
    Blessings,
    The Kambari Altar Team
    """
    
    return html_content, text_content

def send_reminders(test_mode=False):
    """Send reminders for upcoming sessions."""
    # Get upcoming sessions in the next 7 days
    upcoming_sessions = get_upcoming_sessions(days_ahead=7)
    
    if not upcoming_sessions:
        print("No upcoming sessions in the next 7 days.")
        return
    
    # Get members who want to receive reminders
    members = get_member_emails()
    
    if not members:
        print("No members found with email or phone number for reminders.")
        return
    
    # Get role assignments for the next session (assuming first one is the next)
    next_session = upcoming_sessions[0]
    role_assignments = get_current_assignments(next_session['series_id'], next_session['week_number'])
    
    # Get study materials
    materials = get_session_materials(next_session['series_id'], next_session['week_number'])
    if not materials:
        print(f"No materials found for {next_session['series_title']} Week {next_session['week_number']}")
        return
    
    # Send reminders
    success_count = 0
    failure_count = 0
    
    for member in members:
        # Get member's role for this session
        role = None
        for assignment in role_assignments:
            if assignment['member_name'].lower() == member['name'].lower():
                role = assignment['role']
                break
        
        # Format message
        html_content, text_content = format_reminder_message(
            next_session, 
            materials, 
            member['name'], 
            role
        )
        
        # Send via email if available
        email_sent = False
        if member.get('email'):
            subject = f"📖 Reminder: {next_session['series_title']} - Week {next_session['week_number']}"
            if test_mode:
                print(f"\n[TEST] Would send email to {member['email']}:")
                print(f"Subject: {subject}")
                print("-" * 50)
                print(text_content[:500] + "..." if len(text_content) > 500 else text_content)
                print("-" * 50)
                email_sent = True
            else:
                email_sent = send_email(
                    member['email'],
                    subject,
                    html_content,
                    text_content
                )
        
        # Send via WhatsApp if email failed or not available
        whatsapp_sent = False
        if not email_sent and member.get('phone'):
            if test_mode:
                print(f"\n[TEST] Would send WhatsApp to {member['phone']}:")
                print("-" * 50)
                print(text_content[:300] + "..." if len(text_content) > 300 else text_content)
                print("-" * 50)
                whatsapp_sent = True
            else:
                whatsapp_sent = send_whatsapp(
                    member['phone'],
                    text_content
                )
        
        if email_sent or whatsapp_sent:
            success_count += 1
            method = "email" if email_sent else "WhatsApp"
            print(f"✅ Sent {method} reminder to {member['name']}")
        else:
            failure_count += 1
            print(f"❌ Failed to send reminder to {member['name']}")
    
    print(f"\nReminder sending complete!")
    print(f"Successfully sent: {success_count}")
    if failure_count > 0:
        print(f"Failed to send: {failure_count}")

def main():
    """Main entry point for the send_reminders script."""
    # Load environment variables
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Check for test mode
    test_mode = '--test' in sys.argv
    
    if test_mode:
        print("📧 TEST MODE - No actual messages will be sent")
        print("To send real messages, run without --test\n")
    
    # Check if we should force send even if not Thursday
    force_send = '--force' in sys.argv
    today = datetime.now().strftime('%A').lower()
    
    if not force_send and today != 'thursday':
        print("Reminders are only sent on Thursdays. Use --force to override.")
        return
    
    print("🚀 Starting reminder process...")
    send_reminders(test_mode=test_mode)

if __name__ == "__main__":
    main()
