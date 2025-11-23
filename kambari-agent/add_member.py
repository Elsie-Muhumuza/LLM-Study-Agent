#!/usr/bin/env python3
"""
CLI tool to add members to the Kambari Altar Agent database.
"""

import os
import sys
import click
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import after setting up the path
from app.db import add_member, list_members

def main():
    """Main entry point for the add_member script."""
    # Load environment variables
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    
    # Check if running in interactive mode
    if len(sys.argv) == 1:
        print("Interactive mode. Enter member details (press Ctrl+C to exit):\n")
        try:
            while True:
                name = input("Full name: ").strip()
                if not name:
                    print("Name cannot be empty. Please try again.")
                    continue
                    
                phone = input("Phone number (optional): ").strip()
                preferred_name = input("Preferred name (optional, press Enter to use first name): ").strip()
                
                # Add the member
                add_member(name=name, phone=phone, preferred_name=preferred_name if preferred_name else None)
                print(f"✅ Successfully added member: {name}")
                
                # Ask if user wants to add another
                another = input("\nAdd another member? (y/n): ").strip().lower()
                if another != 'y':
                    break
                    
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return
    else:
        # Command-line arguments mode
        import argparse
        parser = argparse.ArgumentParser(description='Add a member to the Kambari Altar Agent database.')
        parser.add_argument('name', help='Full name of the member')
        parser.add_argument('--phone', default='', help='Phone number (optional)')
        parser.add_argument('--preferred-name', help='Preferred name (optional)')
        
        args = parser.parse_args()
        
        # Add the member
        add_member(
            name=args.name,
            phone=args.phone,
            preferred_name=args.preferred_name
        )
        print(f"✅ Successfully added member: {args.name}")
    
    # Show current members
    print("\nCurrent members:")
    print("ID  | Name                | Preferred Name | Phone")
    print("----|---------------------|----------------|-------------")
    for member in list_members():
        print(f"{member[0]:<4}| {member[1]:<20}| {member[2]:<15}| {member[3]}")

if __name__ == "__main__":
    main()
