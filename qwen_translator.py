"""
Alibaba Qwen-MT API integration for recipe translation.

Unlike the other translators in this project, Qwen-MT is a dedicated
machine-translation model rather than a general chat model instructed to
translate. It is invoked through DashScope's OpenAI-compatible endpoint via
the `translation_options` extra body field, and it translates the message
content literally -- it does not follow embedded instructions. That is a
deliberate choice here: numbers, units, and formatting are translated
verbatim by the model itself rather than relying on prompt engineering to
stop a chat model from "helpfully" rewriting them.
"""
import requests
import os
from typing import Optional


class QwenTranslator:
    """Translator using Alibaba's Qwen-MT model via DashScope."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Qwen translator.

        Args:
            api_key: DashScope API key (defaults to DASHSCOPE_API_KEY env var)
            base_url: DashScope OpenAI-compatible base URL (defaults to the
                international endpoint; use the Beijing endpoint for
                Chinese-mainland accounts)
            model: Model to use (defaults to QWEN_MODEL env var, or qwen-mt-turbo)
        """
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        self.base_url = base_url or os.getenv(
            'QWEN_API_BASE_URL', 'https://dashscope-intl.aliyuncs.com/compatible-mode/v1'
        )
        self.model = model or os.getenv('QWEN_MODEL', 'qwen-mt-turbo')

        if not self.api_key:
            raise ValueError("Qwen API key not provided. Set DASHSCOPE_API_KEY environment variable or pass it to the constructor.")

        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def _translate(self, text: str, target_language: str) -> str:
        """Send raw text to Qwen-MT for literal translation."""
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": text}
                    ],
                    "translation_options": {
                        "source_lang": "auto",
                        "target_lang": target_language
                    }
                },
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                return data['choices'][0]['message']['content'].strip()
            else:
                raise Exception("Unexpected response format from Qwen API")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Authentication failed: Invalid API key. Please check your DASHSCOPE_API_KEY")
            elif e.response.status_code == 429:
                raise Exception("Rate limit exceeded: Too many requests. Wait a moment and try again")
            else:
                raise Exception(f"Failed to translate: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to translate: {str(e)}")

    def translate_recipe(self, recipe_text: str, target_language: str) -> str:
        """
        Translate recipe text to target language.

        Args:
            recipe_text: The recipe text to translate
            target_language: Target language (e.g., "Spanish", "French", "Chinese")

        Returns:
            Translated recipe text
        """
        return self._translate(recipe_text, target_language)

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate a single string (title, ingredient, or instruction line).

        Args:
            text: The text to translate
            target_language: Target language (e.g., "Spanish", "French")

        Returns:
            Translated text
        """
        return self._translate(text, target_language)

    def test_connection(self) -> bool:
        """
        Test the connection to the Qwen API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            result = self._translate("Hello, world!", "French")
            return bool(result)
        except Exception:
            return False
