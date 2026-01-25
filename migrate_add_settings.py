#!/usr/bin/env python3
"""
Migration script to add settings table for API key management.
"""
import os
from app import app, db
from sqlalchemy import text

def migrate():
    """Add settings table to database."""
    with app.app_context():
        print("Starting settings table migration...")

        try:
            # Create settings table
            db.session.execute(text("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key VARCHAR(100) NOT NULL UNIQUE,
                    value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            db.session.commit()
            print("✅ Settings table created successfully")

            # Check if we have environment variables to migrate
            groq_key = os.getenv('GROQ_API_KEY')
            mistral_key = os.getenv('MISTRAL_API_KEY')

            if groq_key:
                db.session.execute(text("""
                    INSERT OR IGNORE INTO settings (key, value) VALUES ('groq_api_key', :value)
                """), {'value': groq_key})
                print(f"✅ Migrated GROQ_API_KEY from environment")

            if mistral_key:
                db.session.execute(text("""
                    INSERT OR IGNORE INTO settings (key, value) VALUES ('mistral_api_key', :value)
                """), {'value': mistral_key})
                print(f"✅ Migrated MISTRAL_API_KEY from environment")

            db.session.commit()

            print("\n✅ Migration completed successfully!")
            print("\nYou can now manage API keys through the admin panel at /admin")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate()
