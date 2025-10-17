"""
Script to recreate the database with the new schema.

Usage:
    python recreate_db.py [--backup]

This will:
1. Optionally backup the existing database
2. Delete the old database file
3. Create a new database with the updated schema
"""

import sys
import os
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import engine, init_db
from sqlmodel import SQLModel


def main():
    db_path = Path(__file__).parent / "thesis_graph.db"
    backup_path = Path(__file__).parent / "thesis_graph.db.backup"

    # Check if --backup flag is provided
    should_backup = "--backup" in sys.argv

    if db_path.exists():
        if should_backup:
            print(f"Backing up existing database to {backup_path}...")
            try:
                # Copy instead of move to avoid file lock issues
                import shutil
                shutil.copy2(db_path, backup_path)
                print(f"[OK] Backup created: {backup_path}")
            except Exception as e:
                print(f"[WARNING] Could not create backup: {e}")
                response = input("Continue without backup? (y/N): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    return

        print(f"Deleting old database: {db_path}")
        try:
            db_path.unlink()
            print("[OK] Old database deleted")
        except Exception as e:
            print(f"[ERROR] Error deleting database: {e}")
            print("Make sure no processes are using the database file.")
            print("Try stopping the FastAPI server first.")
            return

    print("\nCreating new database with updated schema...")
    try:
        SQLModel.metadata.create_all(engine)
        print("[OK] Database recreated successfully!")
        print(f"\nNew schema includes:")
        print("  - GraphNode: name, kind, definition, synonyms, measurement_ideas, citations")
        print("  - GraphEdge: type, status, mechanisms, assumptions, confounders, citations")
        print("\nYou can now start the FastAPI server.")
    except Exception as e:
        print(f"[ERROR] Error creating database: {e}")
        raise


if __name__ == "__main__":
    main()
