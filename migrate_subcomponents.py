#!/usr/bin/env python3
"""
Migration script to add subcomponents table to existing QuoteForge database.
"""

from app import app, db
from models import Subcomponent
import json
from datetime import datetime

def migrate_add_subcomponents():
    """Add the subcomponents table to the existing database."""
    with app.app_context():
        print("Starting subcomponents migration...")
        
        # Create the subcomponents table
        try:
            db.create_all()
            print("✅ Subcomponents table created successfully!")
        except Exception as e:
            print(f"❌ Error creating subcomponents table: {e}")
            return False
        
        print("Migration completed successfully!")
        return True

if __name__ == "__main__":
    migrate_add_subcomponents()
