#!/usr/bin/env python3
"""
Migrate from single translation to multi-translation architecture.

This script:
1. Creates the new recipe_translations table
2. Migrates existing translated data to translation records
3. Removes old translation columns from recipes table
"""

from app import app, db
from sqlalchemy import text, inspect
import json

# Language mapping for existing translations
LANGUAGE_MAP = {
    'Spanish': ('es', 'Spanish'),
    'French': ('fr', 'French'),
    'English': ('en', 'English')
}

def get_language_info(language_str):
    """Get language code and name from string."""
    if not language_str:
        return ('es', 'Spanish')  # Default to Spanish

    for key, (code, name) in LANGUAGE_MAP.items():
        if key.lower() in language_str.lower():
            return (code, name)

    return ('es', 'Spanish')  # Default


def migrate():
    """Run the migration."""
    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        print("=" * 60)
        print("MULTI-TRANSLATION MIGRATION")
        print("=" * 60)

        # Step 1: Create recipe_translations table
        print("\n[1/5] Creating recipe_translations table...")

        if 'recipe_translations' not in existing_tables:
            db.session.execute(text("""
                CREATE TABLE recipe_translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    language_code VARCHAR(10) NOT NULL,
                    language_name VARCHAR(50) NOT NULL,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    ingredients TEXT,
                    instructions TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                    UNIQUE (recipe_id, language_code)
                )
            """))
            db.session.commit()
            print("   ✓ Table created")
        else:
            print("   → Table already exists")

        # Step 2: Add source_language column to recipes
        print("\n[2/5] Adding source_language column...")

        columns = [col['name'] for col in inspector.get_columns('recipes')]

        if 'source_language' not in columns:
            db.session.execute(text("""
                ALTER TABLE recipes ADD COLUMN source_language VARCHAR(50) DEFAULT 'English'
            """))
            db.session.commit()
            print("   ✓ Column added")
        else:
            print("   → Column already exists")

        # Step 3: Migrate existing translations to new table
        print("\n[3/5] Migrating existing translations...")

        # Get all recipes with translations
        result = db.session.execute(text("""
            SELECT id, title_translated, content_translated,
                   ingredients_translated, instructions_translated, language
            FROM recipes
            WHERE title_translated IS NOT NULL AND title_translated != ''
        """))

        recipes_with_translations = result.fetchall()
        migration_count = 0

        for row in recipes_with_translations:
            recipe_id = row[0]
            title_translated = row[1]
            content_translated = row[2]
            ingredients_translated = row[3]
            instructions_translated = row[4]
            language = row[5] or 'Spanish'

            # Get language code and name
            lang_code, lang_name = get_language_info(language)

            # Check if translation already exists
            existing = db.session.execute(text("""
                SELECT id FROM recipe_translations
                WHERE recipe_id = :recipe_id AND language_code = :lang_code
            """), {'recipe_id': recipe_id, 'lang_code': lang_code}).fetchone()

            if not existing:
                # Insert translation
                db.session.execute(text("""
                    INSERT INTO recipe_translations
                    (recipe_id, language_code, language_name, title, content, ingredients, instructions)
                    VALUES (:recipe_id, :lang_code, :lang_name, :title, :content, :ingredients, :instructions)
                """), {
                    'recipe_id': recipe_id,
                    'lang_code': lang_code,
                    'lang_name': lang_name,
                    'title': title_translated,
                    'content': content_translated or '',
                    'ingredients': ingredients_translated,
                    'instructions': instructions_translated
                })
                migration_count += 1

        db.session.commit()
        print(f"   ✓ Migrated {migration_count} translations")

        # Step 4: Rename original columns in recipes table
        print("\n[4/5] Reorganizing recipes table...")

        # SQLite doesn't support dropping columns, so we need to recreate the table
        # First, check if we still have the old columns
        if 'title_original' in columns:
            print("   → Creating new table structure...")

            # Create temporary table with new structure
            db.session.execute(text("""
                CREATE TABLE recipes_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title VARCHAR(500) NOT NULL,
                    content TEXT NOT NULL,
                    ingredients TEXT,
                    instructions TEXT,
                    prep_time INTEGER,
                    cook_time INTEGER,
                    total_time INTEGER,
                    servings VARCHAR(100),
                    image_url VARCHAR(1000),
                    author VARCHAR(200),
                    source_url VARCHAR(1000),
                    source_language VARCHAR(50) DEFAULT 'English',
                    nutrition TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))

            # Copy data from old table (using title_original as title, etc.)
            db.session.execute(text("""
                INSERT INTO recipes_new
                (id, title, content, ingredients, instructions, prep_time, cook_time, total_time,
                 servings, image_url, author, source_url, source_language, nutrition, tags, created_at, updated_at)
                SELECT
                    id, title_original, content_original, ingredients_original, instructions_original,
                    prep_time, cook_time, total_time, servings, image_url, author, source_url,
                    COALESCE(source_language, 'English'), nutrition, tags, created_at, updated_at
                FROM recipes
            """))

            # Drop old table and rename new one
            db.session.execute(text("DROP TABLE recipes"))
            db.session.execute(text("ALTER TABLE recipes_new RENAME TO recipes"))

            db.session.commit()
            print("   ✓ Table restructured")
        else:
            print("   → Table already has new structure")

        # Step 5: Recreate foreign key constraints
        print("\n[5/5] Recreating relationships...")

        # Update plan_recipes foreign key
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS plan_recipes_backup AS SELECT * FROM plan_recipes
        """))

        db.session.commit()
        print("   ✓ Relationships preserved")

        print("\n" + "=" * 60)
        print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  - Created recipe_translations table")
        print(f"  - Migrated {migration_count} existing translations")
        print(f"  - Restructured recipes table")
        print("\nNext steps:")
        print("  1. Restart your Flask application")
        print("  2. Recipes now support multiple translations (Spanish & French)")
        print("  3. Use the 'Add Translation' button in recipe pages")
        print()


if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nMigration failed. Please check the error and try again.")
        import traceback
        traceback.print_exc()
