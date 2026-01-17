"""
Application settings management.
"""
import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent / 'data' / 'settings.json'

DEFAULT_SETTINGS = {
    'languages': [
        'Spanish',
        'French',
        'German',
        'Italian',
        'Portuguese',
        'Chinese',
        'Japanese',
        'Korean',
        'Arabic',
        'Russian',
        'Dutch',
        'Swedish',
        'Polish',
        'Turkish',
        'English'
    ],
    'translation_prompt': '''You are a professional recipe translator specializing in culinary translations. Translate the following recipe to {language}.

**CRITICAL FORMATTING RULES:**
1. For ingredients lists: Use a dash (-) or bullet (•) at the start of EACH ingredient line
2. For instruction steps: Use numbered format (1., 2., 3., etc.) at the start of EACH step
3. Keep ONE blank line between sections (Ingredients, Instructions, etc.)
4. Keep markdown headers (## for sections like "Ingrédients" and "Instructions")

**Translation Guidelines:**
5. Translate ALL text naturally and idiomatically in {language}
6. Keep ALL numbers and measurements in parentheses EXACTLY as shown (already converted to metric)
7. Translate cooking terms accurately (sauté, blanch, fold, etc.)
8. Use proper culinary vocabulary in {language}

**Example Format:**
## Ingrédients

- First ingredient here
- Second ingredient here
- Third ingredient here

## Instructions

1. First step of instructions here.
2. Second step here.
3. Third step here.

**Important:** Provide ONLY the translated recipe. No preamble, no explanations.

---

{recipe_text}

---

Translated recipe:''',
    'system_prompt': 'You are a professional recipe translator. Translate recipes accurately while preserving all formatting and measurements.',
    'ai_provider': 'mistral',  # 'mistral' or 'groq'
    'ai_model': 'open-mistral-nemo',
    'nyt_cookie': ''
}


def load_settings():
    """Load settings from JSON file."""
    if not SETTINGS_FILE.exists():
        # Create default settings
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            # Ensure all default keys exist
            for key, value in DEFAULT_SETTINGS.items():
                if key not in settings:
                    settings[key] = value
            return settings
    except Exception:
        return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """Save settings to JSON file."""
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_languages():
    """Get list of available languages."""
    settings = load_settings()
    return settings.get('languages', DEFAULT_SETTINGS['languages'])


def add_language(language):
    """Add a new language."""
    settings = load_settings()
    if language and language not in settings['languages']:
        settings['languages'].append(language)
        settings['languages'].sort()
        save_settings(settings)
        return True
    return False


def remove_language(language):
    """Remove a language."""
    settings = load_settings()
    if language in settings['languages'] and language != 'English':
        settings['languages'].remove(language)
        save_settings(settings)
        return True
    return False


def get_translation_prompt():
    """Get the translation prompt template."""
    settings = load_settings()
    return settings.get('translation_prompt', DEFAULT_SETTINGS['translation_prompt'])


def get_system_prompt():
    """Get the system prompt."""
    settings = load_settings()
    return settings.get('system_prompt', DEFAULT_SETTINGS['system_prompt'])


def update_translation_prompt(prompt):
    """Update the translation prompt template."""
    settings = load_settings()
    settings['translation_prompt'] = prompt
    save_settings(settings)


def update_system_prompt(prompt):
    """Update the system prompt."""
    settings = load_settings()
    settings['system_prompt'] = prompt
    save_settings(settings)


def reset_to_defaults():
    """Reset all settings to defaults."""
    save_settings(DEFAULT_SETTINGS.copy())


def get_ai_model():
    """Get the AI model to use for translations."""
    settings = load_settings()
    return settings.get('ai_model', DEFAULT_SETTINGS['ai_model'])


def update_ai_model(model):
    """Update the AI model."""
    settings = load_settings()
    settings['ai_model'] = model
    save_settings(settings)


def get_nyt_cookie():
    """Get the NYT cookie for recipe scraping."""
    settings = load_settings()
    return settings.get('nyt_cookie', DEFAULT_SETTINGS['nyt_cookie'])


def update_nyt_cookie(cookie):
    """Update the NYT cookie."""
    settings = load_settings()
    settings['nyt_cookie'] = cookie
    save_settings(settings)


def get_ai_provider():
    """Get the AI provider to use (mistral or groq)."""
    settings = load_settings()
    return settings.get('ai_provider', DEFAULT_SETTINGS['ai_provider'])


def update_ai_provider(provider):
    """Update the AI provider."""
    settings = load_settings()
    settings['ai_provider'] = provider
    save_settings(settings)
