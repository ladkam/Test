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
    'translation_prompt': '''You are a professional recipe translator. Translate the following recipe to {language}.

Important instructions:
1. Translate the recipe title, description, ingredients, and instructions
2. Keep the markdown formatting intact (headers, lists, bold text)
3. Keep numbers, measurements, and quantities EXACTLY as they appear (including any metric conversions in parentheses)
4. Maintain the structure and formatting of the original recipe
5. Translate cooking terms accurately
6. Do not add any additional commentary or explanations
7. Preserve all special characters and formatting

Recipe to translate:

{recipe_text}

Provide ONLY the translated recipe, maintaining the exact same markdown structure:''',
    'system_prompt': 'You are a professional recipe translator. Translate recipes accurately while preserving all formatting and measurements.'
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
