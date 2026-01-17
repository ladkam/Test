"""
Mistral AI API integration for recipe translation.
"""
import requests
import os
from typing import Optional
from settings import get_translation_prompt, get_system_prompt, get_ai_model


class MistralTranslator:
    """Translator using Mistral AI API."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Mistral translator.

        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            base_url: Mistral API base URL (defaults to MISTRAL_API_BASE_URL env var)
            model: Model to use (defaults to settings, then MISTRAL_MODEL env var, or open-mistral-nemo)
        """
        self.api_key = api_key or os.getenv('MISTRAL_API_KEY')
        self.base_url = base_url or os.getenv('MISTRAL_API_BASE_URL', 'https://api.mistral.ai/v1')
        self.model = model or os.getenv('MISTRAL_MODEL') or get_ai_model()

        if not self.api_key:
            raise ValueError("Mistral API key not provided. Set MISTRAL_API_KEY environment variable or pass it to the constructor.")

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
                raise Exception("Unexpected response format from Mistral API")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception(f"Authentication failed: Invalid API key. Please check your MISTRAL_API_KEY in .env file")
            elif e.response.status_code == 403:
                raise Exception(f"Access forbidden: Your API key doesn't have proper permissions. Verify your API key at https://console.mistral.ai")
            elif e.response.status_code == 404:
                raise Exception(f"Endpoint not found: The API URL might be incorrect. Current URL: {self.base_url}")
            elif e.response.status_code == 429:
                raise Exception(f"Rate limit exceeded: Too many requests. Wait a moment and try again or upgrade your plan at https://console.mistral.ai")
            else:
                raise Exception(f"Failed to translate recipe: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to translate recipe: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test the connection to Mistral API.

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
                    "max_tokens": 10
                },
                timeout=30
            )

            response.raise_for_status()
            return True

        except requests.exceptions.RequestException:
            return False


# Backwards compatibility alias
GrokTranslator = MistralTranslator
