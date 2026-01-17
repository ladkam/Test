# Multi-Translation Architecture

## Summary

The app now supports **multiple translations per recipe** instead of just one. Each recipe can have translations in **Spanish** and **French**, viewable separately.

## What Changed

### Before (Single Translation)
```
Recipe
├── title_original
├── title_translated  (only ONE translation)
├── content_original
├── content_translated (only ONE translation)
└── language (which language it was translated to)
```

### After (Multiple Translations)
```
Recipe (original only)
├── title
├── content
├── source_language (e.g., "English")
└── translations[]
    ├── Spanish Translation
    │   ├── title
    │   ├── content
    │   ├── ingredients
    │   └── instructions
    └── French Translation
        ├── title
        ├── content
        ├── ingredients
        └── instructions
```

## New Workflow

### 1. Import Recipe (Simplified)
- Import from NYT or OCR
- **No translation required** during import
- Recipe saved in original language only

### 2. Add Translations (On-Demand)
- Open recipe in library
- Click "Add Translation" → Select "Spanish" or "French"
- AI translates on-demand
- Translation saved separately

### 3. View Translations
- Recipe detail shows language selector: `[Original] [Spanish] [French]`
- Switch between languages instantly
- Servings adjuster works with any language
- Each translation is independent

### 4. Help Page for Staff
- Household staff can view recipes in their preferred language
- Can be configured to always show Spanish or French
- No login required

## Benefits

✅ **Cleaner Import** - No forced translation during import
✅ **Multiple Languages** - Same recipe in Spanish AND French
✅ **On-Demand** - Only translate what you need
✅ **Better Storage** - Don't duplicate recipe metadata
✅ **Flexible** - Easy to add more languages later

## Database Changes

### New Table: `recipe_translations`
```sql
CREATE TABLE recipe_translations (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER REFERENCES recipes(id),
    language_code VARCHAR(10),  -- 'es', 'fr'
    language_name VARCHAR(50),  -- 'Spanish', 'French'
    title VARCHAR(500),
    content TEXT,
    ingredients JSON,
    instructions JSON,
    UNIQUE(recipe_id, language_code)
)
```

### Updated Table: `recipes`
```sql
-- Removed: title_translated, content_translated,
--          ingredients_translated, instructions_translated, language
-- Added: source_language
-- Renamed: title_original → title, content_original → content, etc.
```

## Migration

The migration script (`migrate_to_multi_translation.py`):
1. ✅ Creates `recipe_translations` table
2. ✅ Migrates existing translations to new table
3. ✅ Removes old translation columns
4. ✅ Preserves all recipe data
5. ✅ Maintains foreign key relationships

**Your existing recipes and translations are safe** - they're automatically migrated to the new structure.

## API Changes

### New Endpoints
- `POST /api/recipes/<id>/translate` - Create new translation
- `GET /api/recipes/<id>` - Now includes all translations
- `DELETE /api/recipes/<id>/translations/<lang_code>` - Delete a translation

### Updated Response Format
```json
{
  "id": 1,
  "title": "Pasta Carbonara",
  "source_language": "English",
  "ingredients": [...],
  "translations": {
    "es": {
      "title": "Pasta a la Carbonara",
      "ingredients": [...],
      "instructions": [...]
    },
    "fr": {
      "title": "Pâtes à la Carbonara",
      "ingredients": [...],
      "instructions": [...]
    }
  }
}
```

## UI Changes

### Recipe Detail Modal
```
┌────────────────────────────────────────┐
│ Pasta Carbonara                        │
│ Original Language: English             │
│                                        │
│ 🌍 Add Translation ▾                   │
│    └─ Spanish  [Not translated]        │
│    └─ French   [Translated ✓]          │
│                                        │
│ [Original] [Français] [Español]  ← Tabs│
│                                        │
│ Ingredients (in selected language)     │
│ ...                                    │
└────────────────────────────────────────┘
```

### Language Selector
- Shows which translations exist
- Grayed out if not yet translated
- Click to add missing translation

## Configuration

### Supported Languages
Currently supports:
- 🇪🇸 Spanish (`es`)
- 🇫🇷 French (`fr`)

Easy to add more languages by updating the language list in the code.

### Help Page Language
Configure in app settings or URL parameter:
- `/help` - Default language
- `/help?lang=es` - Force Spanish
- `/help?lang=fr` - Force French

## Backward Compatibility

✅ **Existing translations are preserved** during migration
✅ **All recipe data remains intact**
✅ **Weekly plans continue to work**
✅ **No data loss**

The migration automatically converts your current translations to the new format.
