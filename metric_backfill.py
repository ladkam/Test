"""
One-time (idempotent) fix-up of recipes saved before the metric converter was
improved: older saves let things like "Heat oven to 425 degrees", "1 to 1½ pounds",
"9-by-13-inch" or "1 cup/240 milliliters" through, and the AI translations made
from them carried the imperial units into Spanish/French ("425 grados", "tazas").

* recipe.ingredients / recipe.instructions are regenerated from the stored
  originals with the current converter (falls back to the stored metric text).
* Every saved translation is passed through the converter too, which knows the
  Spanish/French/Portuguese unit names ("2 tazas" -> "480 ml").

No AI calls are made. Runs automatically at app start-up (once per
METRIC_BACKFILL_VERSION) and can be run by hand:

    python metric_backfill.py
"""
import json

from unit_converter import convert_list_to_metric, convert_to_metric, is_us_source

METRIC_BACKFILL_VERSION = '2'
SETTINGS_KEY = 'metric_backfill_version'


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []
    return []


def assume_fahrenheit_for(recipe) -> bool:
    """US sources and English recipes write bare temperatures in Fahrenheit."""
    if is_us_source(getattr(recipe, 'source_url', None)):
        return True
    return (getattr(recipe, 'source_language', None) or 'English').lower().startswith('en')


def backfill_metric(db, Recipe, RecipeTranslation) -> int:
    """Re-run metric conversion over all saved recipes. Returns rows changed."""
    changed = 0

    for recipe in Recipe.query.all():
        assume_f = assume_fahrenheit_for(recipe)
        for field in ('ingredients', 'instructions'):
            source = _as_list(getattr(recipe, f'{field}_original')) or _as_list(getattr(recipe, field))
            if not source:
                continue
            new_value = convert_list_to_metric(source, assume_f)
            if new_value != _as_list(getattr(recipe, field)):
                setattr(recipe, field, new_value)
                changed += 1

    for translation in RecipeTranslation.query.all():
        assume_f = assume_fahrenheit_for(translation.recipe) if translation.recipe else True
        for field in ('ingredients', 'instructions'):
            current = _as_list(getattr(translation, field))
            if not current:
                continue
            new_value = convert_list_to_metric(current, assume_f)
            if new_value != current:
                setattr(translation, field, new_value)
                changed += 1
        if translation.content:
            new_content = convert_to_metric(translation.content, assume_f)
            if new_content != translation.content:
                translation.content = new_content
                changed += 1

    db.session.commit()
    return changed


def run_once(db, Recipe, RecipeTranslation, Settings) -> None:
    """Run the backfill if this version hasn't been applied yet."""
    if Settings.get(SETTINGS_KEY) == METRIC_BACKFILL_VERSION:
        return
    changed = backfill_metric(db, Recipe, RecipeTranslation)
    Settings.set(SETTINGS_KEY, METRIC_BACKFILL_VERSION)
    print(f"✓ Metric backfill v{METRIC_BACKFILL_VERSION}: updated {changed} field(s)")


if __name__ == '__main__':
    from app import app
    from models import db as _db, Recipe as _Recipe, RecipeTranslation as _RT, Settings as _Settings

    with app.app_context():
        n = backfill_metric(_db, _Recipe, _RT)
        _Settings.set(SETTINGS_KEY, METRIC_BACKFILL_VERSION)
        print(f"Updated {n} field(s).")
