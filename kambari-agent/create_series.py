#!/usr/bin/env python3
"""
CLI tool to create a new Bible study series in the Kambari Altar Agent.
"""

import os
import sys
import click
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import after setting up the path
from app.db import get_conn

def add_series(title: str, description: str, start_date: str, frequency_days: int, total_weeks: int):
    """Add a new series to the database."""
    conn = get_conn()
    cur = conn.cursor()
    
    # Insert the series
    cur.execute(
        """
        INSERT INTO series (title, description, start_date, frequency_days, total_weeks, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, description, start_date, frequency_days, total_weeks, True)
    )
    
    series_id = cur.lastrowid
    conn.commit()
    conn.close()
    
    return series_id

def list_series():
    """List all series in the database."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, start_date, frequency_days, total_weeks, is_active 
        FROM series 
        ORDER BY start_date DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def main():
    """Main entry point for the create_series script."""
    # Load environment variables
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Check if running in interactive mode
    if len(sys.argv) == 1:
        print("Create a new Bible Study Series\n")
        print("Enter the following details (press Ctrl+C to cancel):\n")
        
        try:
            while True:
                title = input("Series title: ").strip()
                if not title:
                    print("Title cannot be empty. Please try again.")
                    continue
                    
                description = input("Series description (optional): ").strip()
                
                # Get start date with validation
                while True:
                    start_date = input("Start date (YYYY-MM-DD): ").strip()
                    try:
                        datetime.strptime(start_date, '%Y-%m-%d')
                        break
                    except ValueError:
                        print("Invalid date format. Please use YYYY-MM-DD.")
                
                # Get frequency with validation
                while True:
                    try:
                        frequency = int(input("Frequency (days between sessions, e.g., 7 for weekly): ").strip())
                        if frequency < 1:
                            print("Frequency must be at least 1 day.")
                            continue
                        break
                    except ValueError:
                        print("Please enter a valid number.")
                
                # Get total weeks with validation
                while True:
                    try:
                        total_weeks = int(input("Total number of weeks: ").strip())
                        if total_weeks < 1:
                            print("Total weeks must be at least 1.")
                            continue
                        break
                    except ValueError:
                        print("Please enter a valid number.")
                
                # Confirm
                print("\nSeries details:")
                print(f"Title: {title}")
                print(f"Description: {description or 'None'}")
                print(f"Start Date: {start_date}")
                print(f"Frequency: Every {frequency} days")
                print(f"Duration: {total_weeks} weeks")
                
                confirm = input("\nIs this correct? (y/n): ").strip().lower()
                if confirm == 'y':
                    # Add the series
                    series_id = add_series(
                        title=title,
                        description=description,
                        start_date=start_date,
                        frequency_days=frequency,
                        total_weeks=total_weeks
                    )
                    print(f"✅ Successfully created series: {title} (ID: {series_id})")
                    
                    # Ask if user wants to add another
                    another = input("\nCreate another series? (y/n): ").strip().lower()
                    if another != 'y':
                        break
                else:
                    print("\nSeries creation cancelled. Starting over...\n")
                    
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return
    else:
        # Command-line arguments mode
        import argparse
        parser = argparse.ArgumentParser(description='Create a new Bible study series.')
        parser.add_argument('title', help='Title of the series')
        parser.add_argument('start_date', help='Start date (YYYY-MM-DD)')
        parser.add_argument('--description', default='', help='Series description (optional)')
        parser.add_argument('--frequency', type=int, default=7, help='Days between sessions (default: 7)')
        parser.add_argument('--weeks', type=int, default=4, help='Total number of weeks (default: 4)')
        
        args = parser.parse_args()
        
        # Validate date format
        try:
            datetime.strptime(args.start_date, '%Y-%m-%d')
        except ValueError:
            print("Error: Invalid date format. Please use YYYY-MM-DD.")
            sys.exit(1)
        
        # Add the series
        series_id = add_series(
            title=args.title,
            description=args.description,
            start_date=args.start_date,
            frequency_days=args.frequency,
            total_weeks=args.weeks
        )
        print(f"✅ Successfully created series: {args.title} (ID: {series_id})")
    
    # Show current series
    print("\nCurrent series:")
    print("ID  | Title                | Start Date  | Frequency | Weeks | Active")
    print("----|----------------------|-------------|-----------|-------|-------")
    for series in list_series():
        active = "Yes" if series[5] else "No"
        print(f"{series[0]:<4}| {series[1][:20]:<21}| {series[2]} | {str(series[3]) + ' days':<9} | {series[4]:<5} | {active}")

if __name__ == "__main__":
    main()
