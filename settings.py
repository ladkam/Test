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

**CRITICAL MEASUREMENT RULES - READ CAREFULLY:**
5. Measurements have ALREADY been converted to metric (g, kg, ml, l, °C, cm). Keep ALL numbers and units EXACTLY as written.
6. NEVER convert anything to cups, ounces, pounds, inches or Fahrenheit, and never add imperial equivalents.
7. Spoon measures stay spoons: translate only the word (tablespoon→cucharada, teaspoon→cucharadita). Do NOT turn them into ml.
8. Keep metric symbols as symbols: "240 ml", "450 g", "220 °C", "2.5 cm".

**Translation Guidelines:**
9. Translate naturally and idiomatically in {language}, the way a native cookbook would -- not word for word
10. Translate cooking terms accurately (sauté, sear, blanch, fold, simmer, zest, etc.)
11. Use proper culinary vocabulary for ingredients in {language}

**Examples:**
Input: "3 tablespoons olive oil"
Output Spanish: "3 cucharadas de aceite de oliva" (NOT "45 ml de aceite de oliva")

Input: "240 ml whole milk"
Output Spanish: "240 ml de leche entera" (NOT "1 taza de leche entera")

Input: "Heat oven to 220 °C."
Output Spanish: "Precalienta el horno a 220 °C." (NOT "425 °F")

---

{recipe_text}

---

Translated recipe (remember: keep every metric number and unit exactly as written):''',
    'system_prompt': 'You are a professional culinary translator. Translate recipes naturally for home cooks while preserving all formatting, numbers and metric units.',
    'ai_provider': 'mistral',  # 'mistral', 'groq', 'gemini', or 'qwen'
    'ai_model': 'open-mistral-nemo',
    'nyt_cookie': ''
}


# Phrases that only appear in previous built-in prompts.
_OLD_DEFAULT_PROMPT_MARKERS = (
    'Output French: "237ml (1 tasse) de lait entier"',
    'If original says "3 tablespoons" you MUST write',
    'If you see measurements in parentheses (like "237ml (1 cup)")',
    'Keep ALL numbers and measurements in parentheses EXACTLY as shown (already converted to metric)',
)


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
            # Upgrade older *default* prompts (never a customised one): they
            # told the AI to keep "(1 cup)" asides, which leaked imperial units
            # into translations. The file is written once with the defaults of
            # the day, so without this the improved prompt would never apply.
            if any(marker in settings.get('translation_prompt', '') for marker in _OLD_DEFAULT_PROMPT_MARKERS):
                settings['translation_prompt'] = DEFAULT_SETTINGS['translation_prompt']
                settings['system_prompt'] = DEFAULT_SETTINGS['system_prompt']
                save_settings(settings)
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
    """Get the AI provider to use (mistral, groq, gemini, or qwen)."""
    settings = load_settings()
    return settings.get('ai_provider', DEFAULT_SETTINGS['ai_provider'])


def update_ai_provider(provider):
    """Update the AI provider."""
    settings = load_settings()
    settings['ai_provider'] = provider
    save_settings(settings)
