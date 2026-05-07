"""
Phase 1 cleanup migration: drop translation table, drop obsolete recipe columns,
clear translation-related settings rows.

Idempotent — gated by a marker row in `settings`. Safe to run on every boot.
"""
from sqlalchemy import text, inspect


MARKER_KEY = 'phase1_cleanup_applied'

DROP_SETTINGS_KEYS = (
    'languages',
    'translation_prompt',
    'system_prompt',
    'ai_provider',
    'ai_model',
    'mistral_api_key',
    'groq_api_key',
    'gemini_api_key',
    'grok_api_key',
    'nyt_cookie',
    'translator_pin',
    'translator_access_pin',
)

DROP_RECIPE_COLUMNS = ('source_language', 'is_shareable')


def _marker_set(db) -> bool:
    row = db.session.execute(
        text("SELECT value FROM settings WHERE key = :k"),
        {'k': MARKER_KEY},
    ).fetchone()
    return row is not None


def _set_marker(db) -> None:
    db.session.execute(
        text("INSERT INTO settings (key, value, created_at, updated_at) "
             "VALUES (:k, '1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"),
        {'k': MARKER_KEY},
    )


def _drop_table(db, name: str) -> None:
    db.session.execute(text(f"DROP TABLE IF EXISTS {name}"))


def _existing_columns(db, table: str):
    return {col['name'] for col in inspect(db.engine).get_columns(table)}


def _rebuild_recipes_without_columns(db, columns_to_drop) -> None:
    """SQLite-only: rebuild `recipes` minus the given columns."""
    cols = _existing_columns(db, 'recipes')
    keep = [c for c in cols if c not in columns_to_drop]
    if not any(c in cols for c in columns_to_drop):
        return

    keep_csv = ', '.join(keep)
    db.session.execute(text(f"CREATE TABLE recipes_new AS SELECT {keep_csv} FROM recipes"))
    db.session.execute(text("DROP TABLE recipes"))
    db.session.execute(text("ALTER TABLE recipes_new RENAME TO recipes"))


def run_phase1_cleanup(db) -> None:
    """Apply phase-1 schema cleanup. Idempotent."""
    if _marker_set(db):
        return

    is_sqlite = 'sqlite' in str(db.engine.url)

    try:
        _drop_table(db, 'recipe_translations')

        if is_sqlite:
            _rebuild_recipes_without_columns(db, set(DROP_RECIPE_COLUMNS))
        else:
            cols = _existing_columns(db, 'recipes')
            for col in DROP_RECIPE_COLUMNS:
                if col in cols:
                    db.session.execute(text(f"ALTER TABLE recipes DROP COLUMN {col}"))

        for key in DROP_SETTINGS_KEYS:
            db.session.execute(
                text("DELETE FROM settings WHERE key = :k"),
                {'k': key},
            )

        _set_marker(db)
        db.session.commit()
        print("Phase 1 cleanup applied")
    except Exception as e:
        db.session.rollback()
        print(f"Phase 1 cleanup skipped: {e}")
