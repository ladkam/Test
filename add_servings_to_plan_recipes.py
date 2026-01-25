#!/usr/bin/env python3
"""Add servings column to plan_recipes table."""

from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("PRAGMA table_info(plan_recipes)"))
            columns = [row[1] for row in result.fetchall()]

            if 'servings' not in columns:
                # Add servings column
                db.session.execute(text(
                    "ALTER TABLE plan_recipes ADD COLUMN servings INTEGER DEFAULT 1"
                ))
                db.session.commit()
                print("✓ Successfully added servings column to plan_recipes table")
            else:
                print("→ Servings column already exists, skipping migration")

        except Exception as e:
            db.session.rollback()
            print(f"✗ Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate()
