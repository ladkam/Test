"""
Shared helpers for batch-translating lists of ingredients/instructions in a
single API call instead of one call per item.
"""


def build_numbered_prompt(items: list, target_language: str) -> str:
    """Build the numbered-list text to send to a chat-completion translator."""
    numbered_items = "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))
    return (
        f"Translate each numbered item below to {target_language}. "
        "Keep the exact same numbering, one item per line, same order. "
        "Never convert between measurement systems -- do not turn cup, cups, "
        "fl oz, oz, lb, or any other imperial unit into ml/g/l/kg, and do not "
        "turn ml, g, l, kg, or °C into an imperial unit. Keep every number and "
        "unit exactly as written, including anything in parentheses. Only "
        "translate unit NAMES into their target-language equivalent (e.g. "
        "tablespoon -> cucharada, cup -> taza) -- never their values or unit "
        "system. Provide only the translated numbered list, no explanations:"
        f"\n\n{numbered_items}"
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
