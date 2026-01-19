"""
OCR Service using Groq Vision API
Extracts text from recipe images with automatic language detection
"""

import requests
import os
import base64
import json
from typing import Optional
from settings import get_ai_model


# Vision model for OCR - Groq's Llama 3.2 Vision
VISION_MODEL = 'llama-3.2-11b-vision-preview'

# Supported languages for detection
SUPPORTED_LANGUAGES = [
    'English', 'Spanish', 'French', 'German', 'Italian', 'Portuguese',
    'Dutch', 'Swedish', 'Polish', 'Turkish', 'Russian', 'Arabic',
    'Chinese', 'Japanese', 'Korean'
]


def extract_text_with_language(image_bytes: bytes, hint_language: Optional[str] = None) -> dict:
    """
    Extract text from an image using Groq Vision API with automatic language detection.

    Args:
        image_bytes: The image data as bytes
        hint_language: Optional hint for the expected language (not used with AI, but kept for API compatibility)

    Returns:
        dict with 'text', 'detected_language', 'confidence', and 'success'
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return {
            'text': '',
            'detected_language': 'Unknown',
            'confidence': 0,
            'success': False,
            'error': 'Groq API key not configured. Set GROQ_API_KEY environment variable.'
        }

    # Convert image to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')

    # Determine image type (default to jpeg)
    image_type = 'jpeg'
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        image_type = 'png'
    elif image_bytes[:4] == b'GIF8':
        image_type = 'gif'
    elif image_bytes[:4] == b'RIFF' and image_bytes[8:12] == b'WEBP':
        image_type = 'webp'

    # Build the prompt for OCR and language detection
    system_prompt = """You are an expert OCR system specialized in extracting recipe text from images.
Your task is to:
1. Extract ALL text visible in the image accurately
2. Detect the language of the text
3. Preserve the structure (title, ingredients, instructions)

Always respond in valid JSON format."""

    user_prompt = f"""Please analyze this recipe image and extract all the text.

Respond with a JSON object containing:
{{
    "text": "the complete extracted text with proper formatting (use newlines to separate sections)",
    "detected_language": "the primary language of the text (choose from: {', '.join(SUPPORTED_LANGUAGES)})",
    "confidence": a number from 0-100 indicating your confidence in the extraction accuracy,
    "title": "the recipe title if identifiable",
    "has_ingredients": true/false,
    "has_instructions": true/false
}}

Extract the text exactly as written, preserving ingredient lists and numbered instructions.
If the image doesn't contain readable text, set confidence to 0 and explain in the text field."""

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': VISION_MODEL,
                'messages': [
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': user_prompt
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/{image_type};base64,{base64_image}'
                                }
                            }
                        ]
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 4000
            },
            timeout=90
        )

        response.raise_for_status()
        data = response.json()

        if 'choices' not in data or len(data['choices']) == 0:
            return {
                'text': '',
                'detected_language': 'Unknown',
                'confidence': 0,
                'success': False,
                'error': 'No response from Groq Vision API'
            }

        # Parse the AI response
        ai_response = data['choices'][0]['message']['content'].strip()

        # Try to parse as JSON
        try:
            # Handle cases where the response might have markdown code blocks
            if ai_response.startswith('```'):
                # Extract JSON from code block
                lines = ai_response.split('\n')
                json_lines = []
                in_block = False
                for line in lines:
                    if line.startswith('```json'):
                        in_block = True
                        continue
                    elif line.startswith('```'):
                        in_block = False
                        continue
                    elif in_block:
                        json_lines.append(line)
                ai_response = '\n'.join(json_lines)

            result = json.loads(ai_response)

            return {
                'text': result.get('text', ''),
                'detected_language': result.get('detected_language', 'Unknown'),
                'confidence': result.get('confidence', 85),
                'title': result.get('title', ''),
                'has_ingredients': result.get('has_ingredients', False),
                'has_instructions': result.get('has_instructions', False),
                'success': True
            }

        except json.JSONDecodeError:
            # If JSON parsing fails, use the raw response as text
            return {
                'text': ai_response,
                'detected_language': 'Unknown',
                'confidence': 70,
                'success': True
            }

    except requests.exceptions.HTTPError as e:
        error_msg = str(e)
        if e.response is not None:
            try:
                error_data = e.response.json()
                error_msg = error_data.get('error', {}).get('message', str(e))
            except Exception:
                pass

        if e.response and e.response.status_code == 401:
            error_msg = 'Invalid Groq API key'
        elif e.response and e.response.status_code == 429:
            error_msg = 'Rate limit exceeded. Please try again in a moment.'
        elif e.response and e.response.status_code == 400:
            error_msg = f'Invalid request: {error_msg}'

        return {
            'text': '',
            'detected_language': 'Unknown',
            'confidence': 0,
            'success': False,
            'error': error_msg
        }

    except requests.exceptions.Timeout:
        return {
            'text': '',
            'detected_language': 'Unknown',
            'confidence': 0,
            'success': False,
            'error': 'Request timed out. The image may be too large or complex.'
        }

    except Exception as e:
        return {
            'text': '',
            'detected_language': 'Unknown',
            'confidence': 0,
            'success': False,
            'error': f'OCR processing failed: {str(e)}'
        }


def get_supported_languages():
    """Return list of supported languages for OCR."""
    return SUPPORTED_LANGUAGES
