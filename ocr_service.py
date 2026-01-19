"""
OCR Service with Language Detection
Uses EasyOCR for text extraction with automatic language detection
"""

import easyocr
import os
from PIL import Image
import io


# Map of supported languages to EasyOCR language codes
# EasyOCR uses specific codes for each language
LANGUAGE_MAP = {
    'English': ['en'],
    'Spanish': ['es'],
    'French': ['fr'],
    'German': ['de'],
    'Italian': ['it'],
    'Portuguese': ['pt'],
    'Dutch': ['nl'],
    'Polish': ['pl'],
    'Turkish': ['tr'],
    'Russian': ['ru'],
    'Arabic': ['ar'],
    'Chinese': ['ch_sim', 'ch_tra'],
    'Japanese': ['ja'],
    'Korean': ['ko'],
    'Swedish': ['sv'],
}

# Reverse mapping for language detection
EASYOCR_TO_LANGUAGE = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'tr': 'Turkish',
    'ru': 'Russian',
    'ar': 'Arabic',
    'ch_sim': 'Chinese',
    'ch_tra': 'Chinese',
    'ja': 'Japanese',
    'ko': 'Korean',
    'sv': 'Swedish',
}

# Language groups that can be processed together (same script)
LATIN_LANGUAGES = ['en', 'es', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'tr', 'sv']
CYRILLIC_LANGUAGES = ['ru']
ARABIC_LANGUAGES = ['ar']
CJK_LANGUAGES = ['ch_sim', 'ch_tra', 'ja', 'ko']

# Cache for EasyOCR readers (they take time to initialize)
_readers = {}


def get_reader(languages):
    """Get or create an EasyOCR reader for the specified languages."""
    key = tuple(sorted(languages))
    if key not in _readers:
        _readers[key] = easyocr.Reader(languages, gpu=False)
    return _readers[key]


def detect_script_from_image(image_path_or_bytes):
    """
    Attempt to detect the script type from an image.
    Returns the most likely language group.
    """
    # First try with Latin languages (most common)
    # Then try others based on results
    return LATIN_LANGUAGES[:3]  # Start with English, Spanish, French


def extract_text_with_language(image_path_or_bytes, hint_language=None):
    """
    Extract text from an image with automatic language detection.

    Args:
        image_path_or_bytes: Either a file path string or bytes of the image
        hint_language: Optional hint for the language (from user selection)

    Returns:
        dict with 'text', 'detected_language', 'confidence', and 'raw_results'
    """
    try:
        # If a hint language is provided, use it directly
        if hint_language and hint_language in LANGUAGE_MAP:
            ocr_languages = LANGUAGE_MAP[hint_language]
            # Always include English as fallback for mixed content
            if 'en' not in ocr_languages:
                ocr_languages = ocr_languages + ['en']
        else:
            # Multi-pass detection strategy
            # Start with common Latin languages
            ocr_languages = ['en', 'es', 'fr', 'de', 'it']

        reader = get_reader(ocr_languages)

        # Handle both file paths and bytes
        if isinstance(image_path_or_bytes, bytes):
            results = reader.readtext(image_path_or_bytes)
        else:
            results = reader.readtext(image_path_or_bytes)

        if not results:
            return {
                'text': '',
                'detected_language': 'Unknown',
                'confidence': 0,
                'raw_results': [],
                'success': False,
                'error': 'No text detected in image'
            }

        # Combine all detected text
        text_parts = []
        total_confidence = 0

        for detection in results:
            bbox, text, confidence = detection
            text_parts.append(text)
            total_confidence += confidence

        combined_text = '\n'.join(text_parts)
        avg_confidence = total_confidence / len(results) if results else 0

        # Detect the primary language from the extracted text
        detected_lang = detect_language_from_text(combined_text)

        return {
            'text': combined_text,
            'detected_language': detected_lang,
            'confidence': round(avg_confidence * 100, 2),
            'raw_results': [(text, round(conf * 100, 2)) for _, text, conf in results],
            'success': True
        }

    except Exception as e:
        return {
            'text': '',
            'detected_language': 'Unknown',
            'confidence': 0,
            'raw_results': [],
            'success': False,
            'error': str(e)
        }


def detect_language_from_text(text):
    """
    Detect the language of the extracted text based on character analysis.
    """
    if not text:
        return 'Unknown'

    # Count character types
    cyrillic = 0
    arabic = 0
    cjk = 0
    latin = 0

    for char in text:
        code = ord(char)
        if 0x0400 <= code <= 0x04FF:
            cyrillic += 1
        elif 0x0600 <= code <= 0x06FF:
            arabic += 1
        elif (0x4E00 <= code <= 0x9FFF or  # CJK Unified Ideographs
              0x3040 <= code <= 0x309F or  # Hiragana
              0x30A0 <= code <= 0x30FF or  # Katakana
              0xAC00 <= code <= 0xD7AF):   # Korean Hangul
            cjk += 1
        elif 0x0041 <= code <= 0x007A or 0x00C0 <= code <= 0x024F:
            latin += 1

    total = cyrillic + arabic + cjk + latin
    if total == 0:
        return 'Unknown'

    # Determine primary script
    if cyrillic / total > 0.3:
        return 'Russian'
    elif arabic / total > 0.3:
        return 'Arabic'
    elif cjk / total > 0.3:
        # Try to distinguish between Chinese, Japanese, and Korean
        return detect_cjk_language(text)
    else:
        # Latin-based language - use common words detection
        return detect_latin_language(text)


def detect_cjk_language(text):
    """Detect whether CJK text is Chinese, Japanese, or Korean."""
    hiragana = 0
    katakana = 0
    hangul = 0

    for char in text:
        code = ord(char)
        if 0x3040 <= code <= 0x309F:
            hiragana += 1
        elif 0x30A0 <= code <= 0x30FF:
            katakana += 1
        elif 0xAC00 <= code <= 0xD7AF:
            hangul += 1

    if hiragana + katakana > 0:
        return 'Japanese'
    elif hangul > 0:
        return 'Korean'
    else:
        return 'Chinese'


def detect_latin_language(text):
    """Detect which Latin-script language the text is in."""
    text_lower = text.lower()

    # Common words for each language
    language_markers = {
        'Spanish': ['el', 'la', 'de', 'que', 'en', 'los', 'del', 'las', 'con', 'para', 'por', 'una', 'son', 'se', 'como', 'ingredientes', 'preparacion', 'minutos', 'cocinar'],
        'French': ['le', 'la', 'de', 'et', 'les', 'des', 'en', 'un', 'une', 'du', 'que', 'est', 'dans', 'pour', 'au', 'avec', 'sur', 'ingredients', 'preparation', 'cuisson'],
        'German': ['der', 'die', 'und', 'in', 'den', 'von', 'zu', 'das', 'mit', 'sich', 'des', 'auf', 'fur', 'ist', 'im', 'dem', 'nicht', 'ein', 'eine', 'zutaten', 'zubereitung'],
        'Italian': ['il', 'di', 'che', 'la', 'in', 'un', 'per', 'del', 'con', 'non', 'una', 'sono', 'da', 'gli', 'si', 'ha', 'ingredienti', 'preparazione', 'cottura'],
        'Portuguese': ['de', 'que', 'em', 'um', 'para', 'com', 'nao', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'ingredientes', 'preparacao', 'cozinhar'],
        'Dutch': ['de', 'van', 'een', 'het', 'en', 'in', 'is', 'dat', 'op', 'te', 'zijn', 'voor', 'met', 'die', 'ingredienten', 'bereiding'],
        'Swedish': ['och', 'att', 'det', 'en', 'av', 'pa', 'ar', 'for', 'med', 'som', 'har', 'de', 'till', 'ingredienser', 'tillagning'],
        'Polish': ['i', 'w', 'na', 'do', 'z', 'sie', 'nie', 'to', 'jest', 'ze', 'za', 'co', 'jak', 'po', 'skladniki', 'przygotowanie'],
        'Turkish': ['ve', 'bir', 'bu', 'da', 'de', 'ne', 'ile', 'mi', 'mu', 'ama', 'icin', 'var', 'daha', 'en', 'malzemeler', 'hazirlama'],
        'English': ['the', 'and', 'to', 'of', 'a', 'in', 'is', 'it', 'for', 'that', 'was', 'on', 'are', 'with', 'as', 'be', 'at', 'this', 'have', 'ingredients', 'instructions', 'cook', 'bake'],
    }

    # Count matches for each language
    scores = {}
    words = text_lower.split()

    for lang, markers in language_markers.items():
        score = sum(1 for word in words if word in markers)
        scores[lang] = score

    # Return language with highest score
    if scores:
        best_lang = max(scores, key=scores.get)
        if scores[best_lang] > 0:
            return best_lang

    return 'English'  # Default fallback


def ocr_with_specific_languages(image_path_or_bytes, languages):
    """
    Perform OCR with a specific set of EasyOCR language codes.

    Args:
        image_path_or_bytes: Image file path or bytes
        languages: List of EasyOCR language codes (e.g., ['en', 'es'])

    Returns:
        dict with extraction results
    """
    try:
        reader = get_reader(languages)

        if isinstance(image_path_or_bytes, bytes):
            results = reader.readtext(image_path_or_bytes)
        else:
            results = reader.readtext(image_path_or_bytes)

        if not results:
            return {
                'text': '',
                'confidence': 0,
                'success': False,
                'error': 'No text detected'
            }

        text_parts = []
        total_confidence = 0

        for detection in results:
            bbox, text, confidence = detection
            text_parts.append(text)
            total_confidence += confidence

        return {
            'text': '\n'.join(text_parts),
            'confidence': round((total_confidence / len(results)) * 100, 2),
            'success': True
        }

    except Exception as e:
        return {
            'text': '',
            'confidence': 0,
            'success': False,
            'error': str(e)
        }


def get_supported_languages():
    """Return list of supported languages for OCR."""
    return list(LANGUAGE_MAP.keys())
