from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional
import json

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(Path(__file__).parent.parent / 'kambari.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_study_session_info(session_date: str) -> Optional[Dict]:
    """Get all information needed for meeting minutes."""
    conn = get_db_connection()
    try:
        session = conn.execute('''
            SELECT p.*, s.title as series_title, s.theme
            FROM passages p
            JOIN series s ON p.series_id = s.id
            WHERE p.session_date = ?
        ''', (session_date,)).fetchone()
        
        if not session:
            return None
            
        questions = conn.execute('''
            SELECT question, question_type 
            FROM study_questions 
            WHERE passage_id = ?
            ORDER BY display_order
        ''', (session['id'],)).fetchall()
        
        next_session = conn.execute('''
            SELECT p.session_date, p.passage
            FROM passages p
            WHERE p.session_date > ?
            ORDER BY p.session_date
            LIMIT 1
        ''', (session_date,)).fetchone()
        
        return {
            'date': session_date,
            'series': session['series_title'],
            'theme': session['theme'],
            'passage': session['passage'],
            'questions': [dict(q) for q in questions],
            'next_session': dict(next_session) if next_session else None
        }
    finally:
        conn.close()

def generate_meeting_minutes(session_info: Dict) -> str:
    """Generate markdown formatted meeting minutes."""
    date_obj = datetime.strptime(session_info['date'], '%Y-%m-%d')
    date_str = date_obj.strftime('%A, %B %d, %Y')
    
    questions_by_type = {}
    for q in session_info['questions']:
        if q['question_type'] not in questions_by_type:
            questions_by_type[q['question_type']] = []
        questions_by_type[q['question_type']].append(q['question'])
    
    next_session_text = "TBD"
    if session_info['next_session']:
        next_date = datetime.strptime(session_info['next_session']['session_date'], '%Y-%m-%d')
        next_session_text = f"{next_date.strftime('%A, %B %d, %Y')} - {session_info['next_session']['passage']}"
    
    minutes = f"""# 📝 Bible Study Meeting Minutes
*{date_str}*

## 📖 {session_info['series']}
*{session_info['passage']}*  
*Theme: {session_info['theme']}*

---

## 🎯 Discussion Summary
[Add a brief summary of the key points discussed]

---

## 💡 Key Insights
- [Insight 1]
- [Insight 2]
- [Insight 3]
"""

    if 'discussion' in questions_by_type:
        minutes += "\n## ❓ Discussion Questions\n"
        for i, q in enumerate(questions_by_type['discussion'], 1):
            minutes += f"{i}. {q}\n"

    if 'reflection' in questions_by_type:
        minutes += "\n## 🤔 Reflection Questions\n"
        for q in questions_by_type['reflection']:
            minutes += f"- {q}\n"

    minutes += f"""
---

## 🙏 Prayer Points
- [Prayer point 1]
- [Prayer point 2]

---

## 📅 Next Session
*{next_session_text}*

---

*Thank you everyone for your participation and insights! See you next time!* 🙌
"""
    return minutes

def save_meeting_minutes(minutes: str, session_date: str = None) -> str:
    """Save meeting minutes to a file."""
    if not session_date:
        session_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    filename = f"meeting_minutes_{session_date}.md"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(minutes)
    return filename

def generate_friday_minutes(test_mode: bool = True):
    """Generate and save meeting minutes for the most recent Friday."""
    today = datetime.now()
    last_friday = today - timedelta(days=(today.weekday() - 4) % 7 + 3)
    session_date = last_friday.strftime('%Y-%m-%d')
    
    session_info = get_study_session_info(session_date)
    if not session_info:
        print(f"No study session found for {session_date}")
        return
    
    minutes = generate_meeting_minutes(session_info)
    
    if test_mode:
        print(f"\n{'='*50}\n")
        print(minutes)
        print(f"\n{'='*50}")
        print(f"\nMeeting minutes generated for {session_date} (test mode)")
    else:
        filename = save_meeting_minutes(minutes, session_date)
        print(f"✅ Meeting minutes saved to {filename}")

if __name__ == "__main__":
    generate_friday_minutes(test_mode=True)
