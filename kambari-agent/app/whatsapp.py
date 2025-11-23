import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(Path(__file__).parent.parent / 'kambari.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_members_with_roles_for_date(target_date: str) -> List[Dict]:
    """Get all members with their roles for a specific date."""
    conn = get_db_connection()
    try:
        rows = conn.execute('''
            SELECT m.id, m.name, m.phone, s.role, p.passage, se.title as series_title
            FROM schedule s
            JOIN members m ON s.member_id = m.id
            JOIN passages p ON s.session_date = p.session_date
            JOIN series se ON p.series_id = se.id
            WHERE s.session_date = ? AND m.is_active = 1
        ''', (target_date,)).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

def generate_whatsapp_link(phone: str, message: str) -> str:
    """Generate a WhatsApp click-to-send link."""
    phone = ''.join(c for c in phone if c.isdigit())
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    message = quote(message)
    return f"https://wa.me/{phone}?text={message}"

def send_reminders(test_mode: bool = True):
    """Send reminder messages for the next day's Bible study."""
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    members = get_members_with_roles_for_date(tomorrow)
    
    if not members:
        print(f"No scheduled members found for {tomorrow}")
        return
    
    member_roles = {}
    for m in members:
        if m['id'] not in member_roles:
            member_roles[m['id']] = {
                'name': m['name'],
                'phone': m['phone'],
                'roles': [],
                'passage': m['passage'],
                'series': m['series_title']
            }
        member_roles[m['id']]['roles'].append(m['role'].replace('_', ' ').title())
    
    for member_id, data in member_roles.items():
        role_text = " and ".join(data['roles'])
        message = f"""🙏 *Bible Study Reminder - {tomorrow}*

Hello {data['name']},

This is a friendly reminder that you're scheduled for *{role_text}* tomorrow at Bible study.

📖 *Passage:* {data['passage']}
📚 *Series:* {data['series']}

Please come prepared to share and participate. We're looking forward to seeing you there!

Blessings,
Your Bible Study Team
"""
        whatsapp_link = generate_whatsapp_link(data['phone'], message)
        
        if test_mode:
            print(f"\nTo: {data['name']} ({data['phone']})")
            print("=" * 50)
            print(message)
            print(f"\nWhatsApp Link: {whatsapp_link}")
        else:
            print(f"📱 Sending reminder to {data['name']}...")
            # send_whatsapp_message(data['phone'], message)  # Uncomment to enable actual sending

if __name__ == "__main__":
    send_reminders(test_mode=True)
