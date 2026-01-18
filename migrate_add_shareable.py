#!/usr/bin/env python3
"""
Migration script to add is_shareable column to recipes table.
Automatically marks NYT recipes as not shareable.
"""
from app import app, db
from models import Recipe
from sqlalchemy import text

def migrate():
    """Add is_shareable column and update existing recipes."""
    with app.app_context():
        try:
            # Try to add the column (will fail if it already exists)
            with db.engine.connect() as conn:
                try:
                    conn.execute(text('ALTER TABLE recipes ADD COLUMN is_shareable BOOLEAN DEFAULT 1'))
                    conn.commit()
                    print("✓ Added is_shareable column to recipes table")
                except Exception as e:
                    if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                        print("✓ is_shareable column already exists")
                    else:
                        raise e

            # Update existing recipes to mark NYT recipes as not shareable
            recipes = Recipe.query.all()
            updated_count = 0

            for recipe in recipes:
                # If is_shareable attribute doesn't exist, set default
                if not hasattr(recipe, 'is_shareable') or recipe.is_shareable is None:
                    # Check if from NYT
                    if recipe.source_url and 'nytimes.com' in recipe.source_url.lower():
                        recipe.is_shareable = False
                        updated_count += 1
                    else:
                        recipe.is_shareable = True

            db.session.commit()
            print(f"✓ Updated {updated_count} NYT recipes to not shareable")
            print(f"✓ Migration completed successfully!")

        except Exception as e:
            print(f"✗ Migration failed: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
