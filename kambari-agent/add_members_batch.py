#!/usr/bin/env python3
"""
Script to add multiple members to the Kambari Altar Agent database.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

from app.db import get_db_connection

def add_members():
    members = [
        "Alvin", "Horace of God", "Roy", "Winnie", "Audrey", 
        "Danny", "Didi", "Edwin", "Grace", "Hillary", "Moses", 
        "Kyomugisha", "Mart T", "Labeka", "Lenace", "Lyezi", 
        "Maggie", "Nunu", "Pepe", "Pliss", "Simon", "Mathew", 
        "Nolanmark", "Uncle Rich", "A. Emily", "A. Kebi", 
        "Abaho", "Alfred", "Mama", "Taata", "U. Mike", "U. Henry"
    ]
    
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        
        # Create a phone number for each member (format: +2567 + 7 random digits)
        import random
        
        for name in members:
            # Generate a random phone number that starts with +2567
            phone = "+2567" + ''.join([str(random.randint(0, 9)) for _ in range(7)])
            email = f"{name.lower().replace(' ', '.')}@example.com"
            
            try:
                cur.execute(
                    'INSERT INTO members (name, phone, email) VALUES (?, ?, ?)',
                    (name, phone, email)
                )
                print(f"✅ Added: {name} ({phone})")
            except Exception as e:
                print(f"⚠️  Couldn't add {name}: {str(e)}")
                continue
        
        conn.commit()
        print("\nAll members have been added successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("Adding members to the database...\n")
    add_members()
    print("\nDone! Use 'python kambari_cli.py members list' to verify.")
