import sqlite3
import os
from datetime import datetime, timedelta
from pathlib import Path
from app.monthly_scheduler import MonthlyScheduler
from app.question_generator import generate_study_guide
from app.whatsapp import send_reminders as send_whatsapp_reminders
from app.meeting_minutes import generate_meeting_minutes
import click

# Test database path
TEST_DB = "test_kambari.db"

def setup_test_database():
    """Set up a test database with sample data."""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    
    conn = sqlite3.connect(TEST_DB)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create tables
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        is_active BOOLEAN DEFAULT 1
    );
    
    CREATE TABLE IF NOT EXISTS series (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        theme TEXT,
        start_date DATE,
        end_date DATE,
        is_active BOOLEAN DEFAULT 1
    );
    
    CREATE TABLE IF NOT EXISTS schedule (
        session_date DATE PRIMARY KEY,
        topic TEXT,
        passage TEXT,
        series_id INTEGER,
        FOREIGN KEY (series_id) REFERENCES series(id)
    );
    
    CREATE TABLE IF NOT EXISTS schedule_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_date DATE,
        role TEXT,
        member_id INTEGER,
        FOREIGN KEY (session_date) REFERENCES schedule(session_date),
        FOREIGN KEY (member_id) REFERENCES members(id)
    );
    
    CREATE TABLE IF NOT EXISTS study_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        passage_reference TEXT NOT NULL,
        questions_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Add sample members
    members = [
        ("John Doe", "+254700000001", "john@example.com"),
        ("Jane Smith", "+254700000002", "jane@example.com"),
        ("Mike Johnson", "+254700000003", "mike@example.com"),
        ("Sarah Williams", "+254700000004", "sarah@example.com"),
        ("David Brown", "+254700000005", "david@example.com"),
    ]
    
    cursor.executemany(
        "INSERT INTO members (name, phone, email) VALUES (?, ?, ?)",
        members
    )
    
    # Add a sample series
    cursor.execute("""
        INSERT INTO series (title, theme, start_date, end_date, is_active)
        VALUES (?, ?, ?, ?, ?)
    """, ("Gospel of John", "The Life and Teachings of Jesus", "2023-11-01", "2023-12-31", 1))
    
    conn.commit()
    conn.close()
    
    print("✅ Test database created successfully!")

def test_monthly_scheduler():
    """Test the monthly scheduler."""
    print("\n🧪 Testing Monthly Scheduler...")
    
    # Sample topics for the month
    topics = [
        {"title": "The New Birth", "passage": "John 3:1-21"},
        {"title": "Living Water", "passage": "John 4:1-42"},
        {"title": "The Bread of Life", "passage": "John 6:22-59"},
        {"title": "The Good Shepherd", "passage": "John 10:1-21"},
    ]
    
    # Create and test scheduler
    scheduler = MonthlyScheduler(TEST_DB)
    try:
        # Generate schedule for November 2023
        scheduler.generate_schedule(2023, 11, topics)
        scheduler.assign_roles()
        
        # Print the schedule
        print("\n📅 Generated Schedule:")
        scheduler.print_schedule()
        
        # Save to database
        if scheduler.save_to_database():
            print("\n✅ Schedule saved to test database!")
            
            # Export to JSON
            import json
            with open("test_schedule.json", "w") as f:
                json.dump(scheduler.to_dict(), f, indent=2)
            print("📄 Schedule exported to test_schedule.json")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        scheduler.close_connection()

def test_question_generator():
    """Test the question generator."""
    print("\n🧪 Testing Question Generator...")
    
    try:
        passage = "John 3:16-17"
        print(f"\n🔍 Generating questions for {passage}...")
        
        study_guide = generate_study_guide(passage, "God's Love for the World")
        
        print("\n📖 Study Guide:")
        for category, questions in study_guide.items():
            print(f"\n{category.upper()}:")
            for i, q in enumerate(questions, 1):
                print(f"  {i}. {q}")
        
        print("\n✅ Question generation test complete!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_whatsapp_reminders():
    """Test WhatsApp reminders."""
    print("\n🧪 Testing WhatsApp Reminders...")
    
    # Add a test session for tomorrow
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Add a test session
    cursor.execute("""
        INSERT OR REPLACE INTO schedule 
        (session_date, topic, passage, series_id)
        VALUES (?, ?, ?, 1)
    """, (tomorrow, "Test Session", "John 3:16-17"))
    
    # Assign roles
    cursor.execute("SELECT id FROM members LIMIT 3")
    members = cursor.fetchall()
    
    roles = [
        (tomorrow, "worship_leader", members[0][0]),
        (tomorrow, "discussion_leader", members[1][0]),
        (tomorrow, "prayer_leader", members[2][0]),
    ]
    
    cursor.executemany("""
        INSERT INTO schedule_roles (session_date, role, member_id)
        VALUES (?, ?, ?)
    """, roles)
    
    conn.commit()
    conn.close()
    
    # Test sending reminders
    try:
        print("\n💬 Sample WhatsApp messages (not actually sent):")
        send_whatsapp_reminders(test_mode=True)
        print("\n✅ WhatsApp reminder test complete!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_meeting_minutes():
    """Test meeting minutes generation."""
    print("\n🧪 Testing Meeting Minutes Generation...")
    
    # Add a test session that happened yesterday
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Add a test session
    cursor.execute("""
        INSERT OR REPLACE INTO schedule 
        (session_date, topic, passage, series_id)
        VALUES (?, ?, ?, 1)
    """, (yesterday, "Test Session", "John 3:16-17"))
    
    # Assign roles
    cursor.execute("SELECT id, name FROM members LIMIT 3")
    members = cursor.fetchall()
    
    roles = [
        (yesterday, "worship_leader", members[0][0]),
        (yesterday, "discussion_leader", members[1][0]),
        (yesterday, "prayer_leader", members[2][0]),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO schedule_roles (session_date, role, member_id)
        VALUES (?, ?, ?)
    """, roles)
    
    # Add attendance
    for member_id, _ in members:
        cursor.execute("""
            INSERT OR REPLACE INTO attendance 
            (session_date, member_id, attended, notes)
            VALUES (?, ?, 1, 'Test attendance')
        """, (yesterday, member_id))
    
    conn.commit()
    conn.close()
    
    # Test generating minutes
    try:
        print("\n📝 Sample Meeting Minutes:")
        minutes = generate_meeting_minutes(yesterday, test_mode=True)
        print("\n✅ Meeting minutes test complete!")
        
        # Save to file
        with open("test_meeting_minutes.md", "w", encoding="utf-8") as f:
            f.write(minutes)
        print("📄 Sample minutes saved to test_meeting_minutes.md")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

@click.command()
def run_tests():
    """Run all tests."""
    print("🚀 Starting Kambari Altar Agent Tests...")
    print("=" * 50)
    
    # Set up test environment
    setup_test_database()
    
    # Run tests
    test_monthly_scheduler()
    test_question_generator()
    test_whatsapp_reminders()
    test_meeting_minutes()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print(f"Test database: {os.path.abspath(TEST_DB)}")

if __name__ == "__main__":
    run_tests()
