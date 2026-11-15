"""
Shared helpers for translating recipes: the prompts every AI provider uses, and
batch-translating lists of ingredients/instructions in a single API call.

Measurements are converted to metric by ``unit_converter`` BEFORE text is sent
to the AI, and the AI output is run through the converter again afterwards as a
safety net (the converter understands "tazas", "onzas", "libras", "grados"...).
So the AI only has one job regarding units: leave them alone.
"""
from unit_converter import convert_list_to_metric, convert_to_metric


SYSTEM_PROMPT = (
    "You are a professional culinary translator who translates cookbook recipes "
    "for home cooks. You use natural, idiomatic kitchen vocabulary in the target "
    "language, and you never change quantities or measurement units."
)

MEASUREMENT_RULES = (
    "Measurement rules (very important):\n"
    "- All measurements are already metric (g, kg, ml, l, °C, cm, mm). Copy every "
    "number and unit exactly as written. Never convert anything to cups, ounces, "
    "pounds, inches or Fahrenheit, and never write imperial units.\n"
    "- Spoon measures stay spoons: translate only the word (tablespoon -> "
    "cucharada / cuillère à soupe, teaspoon -> cucharadita / cuillère à café). "
    "Do not turn them into ml.\n"
    "- Keep metric symbols as symbols (write \"240 ml\", \"450 g\", \"220 °C\", "
    "\"2.5 cm\"), do not spell them out.\n"
)

STYLE_RULES = (
    "Style rules:\n"
    "- This is a recipe: translate ingredient names and cooking techniques the way a "
    "native cookbook would (e.g. sauté, sear, fold, simmer, zest), not word for word.\n"
    "- Keep brand names and dish names that have no common translation.\n"
    "- Output only the translation, no notes, quotes or explanations.\n"
)


def build_text_prompt(text: str, target_language: str) -> str:
    """Prompt for translating a single string (title, ingredient, step, intro)."""
    return (
        f"Translate the following recipe text to {target_language}.\n\n"
        f"{MEASUREMENT_RULES}\n{STYLE_RULES}\nText:\n{text}"
    )


def build_numbered_prompt(items: list, target_language: str) -> str:
    """Build the numbered-list text to send to a chat-completion translator."""
    numbered_items = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    return (
        f"Translate each numbered recipe line below to {target_language}. "
        "Keep the exact same numbering, one item per line, same order, and never "
        "merge or split lines.\n\n"
        f"{MEASUREMENT_RULES}\n{STYLE_RULES}\n{numbered_items}"
    )


def parse_numbered_list(text: str) -> list:
    """Parse a numbered-list response ("1. foo\\n2. bar") back into a plain list."""
    items = []
    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        if '. ' in line:
            parts = line.split('. ', 1)
            if len(parts) == 2 and parts[0].strip().isdigit():
                line = parts[1]
        items.append(line)
    return items


def metricize(value, assume_fahrenheit: bool = True):
    """Safety net for AI output: convert any imperial unit that slipped through.

    Accepts a string or a list of strings. Idempotent on already-metric text."""
    if isinstance(value, list):
        return convert_list_to_metric(value, assume_fahrenheit)
    if isinstance(value, str):
        return convert_to_metric(value, assume_fahrenheit)
    return value
