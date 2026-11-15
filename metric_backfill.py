"""
One-time (idempotent) fix-up of recipes saved before the metric converter was
improved: older saves let things like "Heat oven to 425 degrees", "1 to 1½ pounds",
"9-by-13-inch" or "1 cup/240 milliliters" through, and the AI translations made
from them carried the imperial units into Spanish/French ("425 grados", "tazas").

* recipe.ingredients / recipe.instructions are regenerated from the stored
  originals with the current converter (falls back to the stored metric text).
* Every saved translation is passed through the converter too, which knows the
  Spanish/French/Portuguese unit names ("2 tazas" -> "480 ml").
* Ranges that the old converter half-converted ("1 to 1½ pounds" was saved as
  "1 to 680 g", then translated to "1 a 680 g") are repaired line by line from
  the recipe's original English text ("450 a 680 g").

No AI calls are made. Runs automatically at app start-up (once per
METRIC_BACKFILL_VERSION) and can be run by hand:

    python metric_backfill.py
"""
import json
import re

from unit_converter import NUM, convert_list_to_metric, convert_to_metric, is_us_source, parse_number

METRIC_BACKFILL_VERSION = '3'

_METRIC_RANGE_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*(?:to|or|-)\s*(\d+(?:\.\d+)?)\s*(kg|g|ml|l|°C|cm|mm)(?![A-Za-z])'
)
_ANY_SEP = r'(\s*(?:to|or|a|à|o|ou|-|–|—)\s*)'


def repair_ranges(translated: str, metric_english: str) -> str:
    """Fix the lower bound of ranges an old converter version left unconverted.

    metric_english "450 to 680 g chicken" + translated "1 a 680 g de pollo"
    -> "450 a 680 g de pollo". Only touches a range whose upper bound and unit
    match the English line and whose lower bound is clearly wrong."""
    if not isinstance(translated, str) or not isinstance(metric_english, str):
        return translated
    for low, high, unit in _METRIC_RANGE_RE.findall(metric_english):
        pattern = re.compile(
            r'(?<![\w.,/])(' + NUM + r')' + _ANY_SEP + re.escape(high) + r'\s*' + re.escape(unit) + r'(?![A-Za-z])'
        )

        def fix(m, low=low):
            try:
                if abs(parse_number(m.group(1)) - float(low)) < 1e-6:
                    return m.group(0)
            except (ValueError, ZeroDivisionError):
                return m.group(0)
            return low + m.group(0)[len(m.group(1)):]

        translated = pattern.sub(fix, translated)
    return translated


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
        recipe = translation.recipe
        assume_f = assume_fahrenheit_for(recipe) if recipe else True
        for field in ('ingredients', 'instructions'):
            current = _as_list(getattr(translation, field))
            if not current:
                continue
            new_value = convert_list_to_metric(current, assume_f)
            english = _as_list(getattr(recipe, field)) if recipe else []
            if len(english) == len(new_value):
                new_value = [repair_ranges(t, e) for t, e in zip(new_value, english)]
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
