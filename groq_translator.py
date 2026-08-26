"""
Groq API integration for recipe translation.
"""
import requests
import os
from typing import Optional
from settings import get_translation_prompt, get_system_prompt, get_ai_model
from translation_utils import build_numbered_prompt, parse_numbered_list


class GroqTranslator:
    """Translator using Groq API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Groq translator.

        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            base_url: Groq API base URL (defaults to https://api.groq.com/openai/v1)
            model: Model to use (defaults to settings, then GROQ_MODEL env var, or llama-3.3-70b-versatile)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.base_url = base_url or os.getenv('GROQ_API_BASE_URL', 'https://api.groq.com/openai/v1')
        self.model = model or os.getenv('GROQ_MODEL') or get_ai_model()

        if not self.api_key:
            raise ValueError("Groq API key not provided. Set GROQ_API_KEY environment variable or pass it to the constructor.")

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
        # Get prompt templates from settings
        prompt_template = get_translation_prompt()
        system_prompt = get_system_prompt()

        # Format the prompt with the recipe text and language
        prompt = prompt_template.format(language=target_language, recipe_text=recipe_text)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.3,
                    "max_completion_tokens": 4000
                },
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                translated_text = data['choices'][0]['message']['content'].strip()
                return translated_text
            else:
                raise Exception("Unexpected response format from Groq API")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception(f"Authentication failed: Invalid API key. Please check your GROQ_API_KEY")
            elif e.response.status_code == 403:
                raise Exception(f"Access forbidden: Your API key doesn't have proper permissions")
            elif e.response.status_code == 404:
                raise Exception(f"Endpoint not found: The API URL might be incorrect. Current URL: {self.base_url}")
            elif e.response.status_code == 429:
                raise Exception(f"Rate limit exceeded: Too many requests. Wait a moment and try again")
            else:
                raise Exception(f"Failed to translate recipe: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to translate recipe: {str(e)}")

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate simple text to target language.

        Args:
            text: The text to translate
            target_language: Target language (e.g., "Spanish", "French")

        Returns:
            Translated text
        """
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional translator. Translate text accurately while preserving meaning."
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Translate the following text to {target_language}. "
                                "Never convert between measurement systems -- do not turn "
                                "cup, cups, fl oz, oz, lb, or any other imperial unit into "
                                "ml/g/l/kg, and do not turn ml, g, l, kg, or °C into an "
                                "imperial unit. Keep every number and unit exactly as "
                                "written, including anything in parentheses. Only translate "
                                "unit NAMES into their target-language equivalent (e.g. "
                                "tablespoon -> cucharada, cup -> taza) -- never their values "
                                "or unit system. Provide only the translation, no "
                                f"explanations:\n\n{text}"
                            )
                        }
                    ],
                    "temperature": 0.3,
                    "max_completion_tokens": 500
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            else:
                raise Exception("Unexpected response format from Groq API")

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to translate text: {str(e)}")

    def translate_list(self, items: list, target_language: str) -> list:
        """
        Translate a list of items (ingredients or instructions) in a single
        API call instead of one call per item -- this is the difference
        between one request and N requests when saving/editing a recipe.

        Args:
            items: List of strings to translate
            target_language: Target language

        Returns:
            List of translated strings, same length/order as items
        """
        if not items:
            return []

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional translator. Translate text accurately while preserving meaning."
                        },
                        {
                            "role": "user",
                            "content": build_numbered_prompt(items, target_language)
                        }
                    ],
                    "temperature": 0.3,
                    "max_completion_tokens": max(500, 60 * len(items))
                },
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' not in data or not data['choices']:
                raise Exception("Unexpected response format from Groq API")

            translated_text = data['choices'][0]['message']['content'].strip()
            translated_items = parse_numbered_list(translated_text)

            if len(translated_items) != len(items):
                # Batched response didn't line up 1:1 -- fall back to
                # per-item calls so data doesn't end up misaligned.
                return [self.translate_text(item, target_language) for item in items]

            return translated_items

        except requests.exceptions.RequestException:
            return [self.translate_text(item, target_language) for item in items]

    def test_connection(self) -> bool:
        """
        Test the connection to Groq API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_completion_tokens": 10
                },
                timeout=30
            )

            response.raise_for_status()
            return True

        except requests.exceptions.RequestException:
            return False
