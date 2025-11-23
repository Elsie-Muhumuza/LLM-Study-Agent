import schedule
import time
from datetime import datetime
from pathlib import Path
import sys

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def thursday_job():
    """Job to run every Thursday at 10 AM"""
    from app.whatsapp import send_reminders
    print(f"Running Thursday reminder job at {datetime.now()}")
    send_reminders(test_mode=False)

def friday_job():
    """Job to run every Friday at 6 PM"""
    from app.meeting_minutes import generate_friday_minutes
    print(f"Running Friday minutes job at {datetime.now()}")
    generate_friday_minutes(test_mode=False)

def run_scheduler():
    """Run the scheduled jobs"""
    # Schedule Thursday job (10 AM)
    schedule.every().thursday.at("10:00").do(thursday_job)
    
    # Schedule Friday job (6 PM)
    schedule.every().friday.at("18:00").do(friday_job)
    
    print("Scheduler started. Press Ctrl+C to exit.")
    print("Scheduled jobs:")
    print("- Thursday 10:00 AM: Send WhatsApp reminders")
    print("- Friday 6:00 PM: Generate meeting minutes")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        print("\nScheduler stopped.")

if __name__ == "__main__":
    # For testing, you can run the jobs immediately
    if len(sys.argv) > 1:
        if '--test-reminders' in sys.argv:
            print("Running test reminders...")
            from app.whatsapp import send_reminders
            send_reminders(test_mode=True)
        elif '--test-minutes' in sys.argv:
            print("Running test minutes generation...")
            from app.meeting_minutes import generate_friday_minutes
            generate_friday_minutes(test_mode=True)
    else:
        run_scheduler()
