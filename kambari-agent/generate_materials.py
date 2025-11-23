#!/usr/bin/env python3
"""
CLI tool to generate study materials for a Bible study series.
"""

import os
import sys
import json
import click
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import after setting up the path
from app.db import get_conn
from app.question_generator import generate_study_questions

def get_series(series_id: int):
    """Get series details by ID."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM series WHERE id = ?", (series_id,))
    series = cur.fetchone()
    conn.close()
    
    if not series:
        raise ValueError(f"Series with ID {series_id} not found")
    
    return {
        'id': series[0],
        'title': series[1],
        'description': series[2],
        'start_date': series[3],
        'frequency_days': series[4],
        'total_weeks': series[5],
        'is_active': bool(series[6])
    }

def get_passages(series_id: int):
    """Get all passages for a series."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, week_number, passage_reference, passage_text, notes 
        FROM passages 
        WHERE series_id = ? 
        ORDER BY week_number
    """, (series_id,))
    
    passages = []
    for row in cur.fetchall():
        passages.append({
            'id': row[0],
            'week_number': row[1],
            'passage_reference': row[2],
            'passage_text': row[3],
            'notes': row[4]
        })
    
    conn.close()
    return passages

def save_generated_material(series_id: int, week_number: int, material_type: str, content: dict):
    """Save generated material to the database."""
    conn = get_conn()
    cur = conn.cursor()
    
    # Check if material already exists
    cur.execute("""
        SELECT id FROM generated_materials 
        WHERE series_id = ? AND week_number = ? AND material_type = ?
    """, (series_id, week_number, material_type))
    
    if cur.fetchone():
        # Update existing
        cur.execute("""
            UPDATE generated_materials 
            SET content = ?, generated_at = CURRENT_TIMESTAMP
            WHERE series_id = ? AND week_number = ? AND material_type = ?
        """, (json.dumps(content), series_id, week_number, material_type))
    else:
        # Insert new
        cur.execute("""
            INSERT INTO generated_materials 
            (series_id, week_number, material_type, content)
            VALUES (?, ?, ?, ?)
        """, (series_id, week_number, material_type, json.dumps(content)))
    
    conn.commit()
    conn.close()

def generate_weekly_materials(series_id: int, week_number: int = None):
    """Generate study materials for a specific week or all weeks."""
    # Get series and passages
    series = get_series(series_id)
    passages = get_passages(series_id)
    
    if not passages:
        print(f"No passages found for series ID {series_id}")
        return
    
    # Filter passages by week if specified
    if week_number is not None:
        passages = [p for p in passages if p['week_number'] == week_number]
        if not passages:
            print(f"No passage found for week {week_number}")
            return
    
    # Generate materials for each passage
    for passage in passages:
        print(f"\nGenerating materials for Week {passage['week_number']}: {passage['passage_reference']}")
        
        # Generate study questions
        print("  - Generating study questions...")
        try:
            questions = generate_study_questions(
                passage['passage_reference'],
                passage['passage_text'],
                passage.get('notes', '')
            )
            
            # Save questions
            save_generated_material(
                series_id=series_id,
                week_number=passage['week_number'],
                material_type='study_questions',
                content=questions
            )
            print("    ✅ Saved study questions")
            
        except Exception as e:
            print(f"    ❌ Error generating study questions: {str(e)}")
            
        # Add more material generation here as needed
        # e.g., discussion prompts, prayer points, etc.
    
    print("\n✅ Material generation complete!")

def list_series():
    """List all series in the database."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, title, start_date, total_weeks 
        FROM series 
        WHERE is_active = 1 
        ORDER BY start_date DESC
    """)
    
    print("\nAvailable series:")
    print("ID  | Title")
    print("----|----------------------")
    for row in cur.fetchall():
        print(f"{row[0]:<4}| {row[1]}")
    
    conn.close()

def main():
    """Main entry point for the generate_materials script."""
    # Load environment variables
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Check if running in interactive mode
    if len(sys.argv) == 1:
        print("Bible Study Material Generator\n")
        
        # Show available series
        list_series()
        
        try:
            while True:
                series_id = input("\nEnter series ID (or 'q' to quit): ").strip()
                if series_id.lower() == 'q':
                    return
                
                try:
                    series_id = int(series_id)
                    # Verify series exists
                    get_series(series_id)
                    break
                except (ValueError, Exception) as e:
                    print(f"Error: {str(e)}. Please try again or press 'q' to quit.")
            
            # Ask for week number (optional)
            week_input = input("Enter week number (leave blank for all weeks): ").strip()
            week_number = int(week_input) if week_input else None
            
            # Confirm
            if week_number:
                confirm = input(f"Generate materials for Week {week_number}? (y/n): ").strip().lower()
            else:
                confirm = input("Generate materials for all weeks? (y/n): ").strip().lower()
            
            if confirm == 'y':
                generate_weekly_materials(series_id, week_number)
            else:
                print("Operation cancelled.")
                
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return
    else:
        # Command-line arguments mode
        import argparse
        parser = argparse.ArgumentParser(description='Generate study materials for a Bible study series.')
        parser.add_argument('series_id', type=int, help='ID of the series')
        parser.add_argument('--week', type=int, help='Week number (optional)')
        
        args = parser.parse_args()
        
        # Generate materials
        generate_weekly_materials(args.series_id, args.week)

if __name__ == "__main__":
    main()
