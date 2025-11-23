import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from app.monthly_scheduler import MonthlyScheduler, SeriesType

def setup_test_database():
    """Set up a test database with sample data."""
    db_path = "test_kambari.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create necessary tables
    cursor.executescript("""
    CREATE TABLE members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        email TEXT,
        is_active BOOLEAN DEFAULT 1
    );
    
    CREATE TABLE schedule (
        session_date DATE PRIMARY KEY,
        topic TEXT,
        passage TEXT,
        series_id INTEGER
    );
    
    CREATE TABLE schedule_roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_date DATE,
        role TEXT,
        member_id INTEGER,
        FOREIGN KEY (session_date) REFERENCES schedule(session_date),
        FOREIGN KEY (member_id) REFERENCES members(id)
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
    
    conn.commit()
    conn.close()
    
    return db_path

def test_women_of_faith_series():
    """Test the Women of Faith series generation."""
    print("🚀 Setting up test database...")
    db_path = setup_test_database()
    
    print("\n🔍 Creating MonthlyScheduler instance...")
    scheduler = MonthlyScheduler(db_path)
    
    try:
        print("\n📅 Generating Women of Faith series...")
        sessions = scheduler.create_series(
            series_type=SeriesType.WOMEN_OF_FAITH,
            start_date=(datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),  # Start in 2 days
            frequency='weekly',
            excluded_days=[5, 6]  # Skip weekends
        )
        
        print(f"\n✅ Generated {len(sessions)} sessions in the series:")
        for i, session in enumerate(sessions[:5], 1):  # Show first 5 sessions
            print(f"\n{i}. {session.date} - {session.topic} ({session.passage})")
        
        if len(sessions) > 5:
            print(f"... and {len(sessions) - 5} more sessions")
        
        # Assign roles
        print("\n👥 Assigning roles to members...")
        scheduler.assign_roles()
        
        # Show schedule with role assignments
        print("\n📋 Schedule with Role Assignments:")
        print("=" * 60)
        for session in sessions[:3]:  # Show first 3 sessions with roles
            print(f"\n📅 {session.date} - {session.topic}")
            print("-" * 60)
            for role, member in session.roles.items():
                member_name = member.name if member else "Unassigned"
                print(f"• {role.replace('_', ' ').title()}: {member_name}")
        
        # Save to database
        print("\n💾 Saving to database...")
        if scheduler.save_to_database():
            print("✅ Schedule saved to database!")
            
            # Export to JSON
            import json
            filename = "women_of_faith_series.json"
            with open(filename, 'w') as f:
                json.dump(scheduler.to_dict(), f, indent=2)
            print(f"📄 Schedule exported to {filename}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        scheduler.close_connection()
        print("\n🧹 Test database cleaned up.")

if __name__ == "__main__":
    print("=" * 60)
    print("🌟 Kambari Altar Agent - Women of Faith Series Test 🌟")
    print("=" * 60)
    test_women_of_faith_series()
