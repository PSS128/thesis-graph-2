#!/usr/bin/env python3
"""
Migration: Add LLMMetrics table to track LLM API performance.

Run this script to add the LLMMetrics table to your existing database:
    python migrations/add_llm_metrics.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import SQLModel, create_engine, Session
from app.models.store import User, Project, GraphNode, GraphEdge, Feedback, LLMMetrics
from app.db import engine


def run_migration():
    """Create the LLMMetrics table if it doesn't exist."""
    print("Running migration: add_llm_metrics")
    print(f"Database: {engine.url}")

    try:
        # Create only the LLMMetrics table (won't affect existing tables)
        print("Creating LLMMetrics table...")
        LLMMetrics.__table__.create(engine, checkfirst=True)
        print("[SUCCESS] LLMMetrics table created successfully!")

        # Verify the table was created
        with Session(engine) as session:
            # Try a simple query
            from sqlmodel import select
            result = session.exec(select(LLMMetrics).limit(1)).first()
            print(f"[SUCCESS] Table verification successful (found {0 if result is None else 1} rows)")

        print("\nMigration completed successfully!")
        print("\nThe LLMMetrics table has been added with the following schema:")
        print("  - id (primary key)")
        print("  - prompt_type (indexed)")
        print("  - prompt_version")
        print("  - latency_ms")
        print("  - success")
        print("  - input_tokens")
        print("  - output_tokens")
        print("  - cache_hit")
        print("  - error_message")
        print("  - created_at (indexed)")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
