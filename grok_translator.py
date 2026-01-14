"""
Grok API integration for recipe translation.
"""
import requests
import os
from typing import Optional


class GrokTranslator:
    """Translator using Grok API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Grok translator.

        Args:
            api_key: Grok API key (defaults to GROK_API_KEY env var)
            base_url: Grok API base URL (defaults to GROK_API_BASE_URL env var)
        """
        self.api_key = api_key or os.getenv('GROK_API_KEY')
        self.base_url = base_url or os.getenv('GROK_API_BASE_URL', 'https://api.x.ai/v1')

        if not self.api_key:
            raise ValueError("Grok API key not provided. Set GROK_API_KEY environment variable or pass it to the constructor.")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def translate_recipe(self, recipe_text: str, target_language: str) -> str:
        """
        Translate recipe text to target language.

        Args:
            recipe_text: The recipe text to translate
            target_language: Target language (e.g., "Spanish", "French", "German")

        Returns:
            Translated recipe text
        """
        prompt = f"""You are a professional recipe translator. Translate the following recipe to {target_language}.

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

Provide ONLY the translated recipe, maintaining the exact same markdown structure:"""

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "grok-beta",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional recipe translator. Translate recipes accurately while preserving all formatting and measurements."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                },
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                translated_text = data['choices'][0]['message']['content'].strip()
                return translated_text
            else:
                raise Exception("Unexpected response format from Grok API")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to translate recipe: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test the connection to Grok API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": "grok-beta",
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_tokens": 10
                },
                timeout=30
            )

            response.raise_for_status()
            return True

        except requests.exceptions.RequestException:
            return False
