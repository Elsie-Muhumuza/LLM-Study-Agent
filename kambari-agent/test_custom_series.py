import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from app.monthly_scheduler import MonthlyScheduler, SeriesType, BibleStudyGenerator

def test_custom_series():
    """Test generating a custom Bible study series."""
    print("🌟 Kambari Altar Agent - Custom Bible Study Series Generator 🌟")
    print("=" * 70)
    
    # Initialize the generator
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    generator = BibleStudyGenerator(gemini_api_key=gemini_api_key)
    
    while True:
        print("\n🎯 Choose an option:")
        print("1. Generate a series on a specific theme (e.g., forgiveness, faith, love)")
        print("2. Generate a series on a specific Bible character or story")
        print("3. Generate a series on a book of the Bible")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '4':
            print("\n👋 Goodbye!")
            break
            
        theme = input("\n🔍 Enter your theme/topic: ").strip()
        num_sessions = int(input("📅 How many sessions? (1-12): ").strip() or "4")
        
        print(f"\n✨ Generating {num_sessions} sessions on '{theme}'...")
        
        try:
            # Generate the series
            if choice == '1':
                # Theme-based series (e.g., forgiveness, faith, love)
                series = generator.generate_series(theme, num_sessions)
            elif choice == '2':
                # Character/story based series
                series = generator.generate_series(f"Bible stories about {theme}", num_sessions)
            elif choice == '3':
                # Book of the Bible
                series = generator.generate_series(f"Study of {theme}", num_sessions)
            else:
                print("❌ Invalid choice. Please try again.")
                continue
            
            # Display the generated series
            print("\n📖 GENERATED BIBLE STUDY SERIES")
            print("=" * 50)
            
            for i, session in enumerate(series, 1):
                print(f"\n📅 Session {i}: {session.title}")
                print(f"📜 {session.reference}")
                print(f"📝 {session.summary[:150]}...")
                
                if session.key_verses:
                    print("\n📖 Key Verses:")
                    for verse in session.key_verses[:3]:  # Show first 3 key verses
                        print(f"- {verse}")
                
                print("\n💭 Discussion Questions:")
                for q in session.discussion_questions[:3]:  # Show first 3 questions
                    print(f"• {q}")
            
            # Save to file
            save_choice = input("\n💾 Save this series to a file? (y/n): ").lower()
            if save_choice == 'y':
                filename = f"bible_study_{theme.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump([s.to_dict() for s in series], f, indent=2)
                print(f"✅ Series saved to {filename}")
            
            # Schedule the series
            schedule_choice = input("\n📅 Schedule these sessions? (y/n): ").lower()
            if schedule_choice == 'y':
                start_date = input(f"📆 Start date (YYYY-MM-DD, leave blank for next Friday): ").strip()
                frequency = input("🔄 Frequency? (weekly/biweekly, default: weekly): ").strip().lower() or 'weekly'
                
                scheduler = MonthlyScheduler()
                
                # Create sessions
                current_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
                if not current_date:
                    today = datetime.now()
                    days_until_friday = (4 - today.weekday()) % 7  # 4 = Friday (0=Monday)
                    if days_until_friday == 0 and today.hour >= 18:  # If it's Friday evening
                        days_until_friday = 7  # Schedule for next Friday
                    current_date = today + timedelta(days=days_until_friday)
                
                # Clear existing sessions and add new ones
                scheduler.sessions = []
                for session in series:
                    scheduler.sessions.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'topic': session.title,
                        'passage': session.reference,
                        'roles': {role: None for role in scheduler.ROLES}
                    })
                    
                    # Move to next session date
                    current_date += timedelta(weeks=1 if frequency == 'weekly' else 2)
                
                # Assign roles
                assign_roles = input("👥 Assign roles automatically? (y/n): ").lower() == 'y'
                if assign_roles:
                    scheduler.load_members()
                    scheduler.load_role_history()
                    scheduler.assign_roles()
                
                # Show schedule
                print("\n📅 SCHEDULED SESSIONS")
                print("=" * 50)
                for session in scheduler.sessions[:5]:  # Show first 5 sessions
                    print(f"\n📅 {session['date']} - {session['topic']} ({session['passage']})")
                    if assign_roles:
                        for role, member in session['roles'].items():
                            member_name = member.name if member else "Unassigned"
                            print(f"  • {role.replace('_', ' ').title()}: {member_name}")
                
                # Save to database
                save_db = input("\n💾 Save to database? (y/n): ").lower() == 'y'
                if save_db:
                    if scheduler.save_to_database():
                        print("✅ Schedule saved to database!")
                    else:
                        print("❌ Failed to save to database.")
            
        except Exception as e:
            print(f"\n❌ An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_custom_series()
