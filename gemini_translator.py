"""
Google Gemini API integration for recipe translation.
Uses the current google-genai SDK and non-deprecated Gemini models.
(google-generativeai was deprecated by Google in August 2025.)
"""
import os
from typing import Optional
from settings import get_translation_prompt, get_system_prompt, get_ai_model

try:
    from google import genai
    from google.genai import types as genai_types
    from google.genai import errors as genai_errors
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiTranslator:
    """Translator using Google Gemini API."""

    # Available models (August 2026)
    # FREE: 3.7 Flash, 3.5 Flash-Lite, 2.5 Flash
    # PAID: 3.1 Pro (Preview), 2.5 Pro
    # Note: Gemini 2.5 models are GA-stable but Google has scheduled them
    # for deprecation on 2026-10-16; prefer the 3.x line for new setups.
    AVAILABLE_MODELS = {
        'gemini-3.7-flash': 'Gemini 3.7 Flash - Latest, best for complex tasks (FREE, Recommended)',
        'gemini-3.5-flash-lite': 'Gemini 3.5 Flash-Lite - Fastest, most cost-effective (FREE)',
        'gemini-2.5-flash': 'Gemini 2.5 Flash - Stable fallback, sunsetting Oct 2026 (FREE)',
        'gemini-3.1-pro-preview': 'Gemini 3.1 Pro (Preview) - Best quality, agentic (PAID)',
        'gemini-2.5-pro': 'Gemini 2.5 Pro - Advanced reasoning, sunsetting Oct 2026 (PAID)'
    }

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini translator.

        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
            model: Model to use (defaults to gemini-3.7-flash)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-genai library not installed. "
                "Install with: pip install google-genai"
            )

        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. "
                "Set GEMINI_API_KEY environment variable or pass it to the constructor."
            )

        # Set model (default to latest stable Flash model)
        self.model_name = model or os.getenv('GEMINI_MODEL', 'gemini-3.7-flash')

        # Validate model
        if self.model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {self.model_name}. "
                f"Available models: {', '.join(self.AVAILABLE_MODELS.keys())}"
            )

        self.client = genai.Client(api_key=self.api_key)
        self.generation_config = genai_types.GenerateContentConfig(
            temperature=0.3,
            top_p=0.95,
            top_k=40,
            max_output_tokens=4096,
        )

    def _generate(self, prompt: str):
        """Send a prompt to the configured Gemini model and return the raw response."""
        try:
            return self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=self.generation_config,
            )
        except genai_errors.ClientError as e:
            code = getattr(e, 'code', None)
            if code in (401, 403):
                raise Exception("Invalid API key. Please check your GEMINI_API_KEY")
            elif code == 429:
                raise Exception("API quota exceeded or rate limit hit. Please try again later")
            else:
                raise Exception(f"Gemini API error: {str(e)}")

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
        user_prompt = prompt_template.format(language=target_language, recipe_text=recipe_text)

        # Combine system prompt and user prompt
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            response = self._generate(full_prompt)

            if not response or not response.text:
                raise Exception("Empty response from Gemini API")

            return response.text.strip()

        except Exception as e:
            if "safety" in str(e).lower():
                raise Exception("Content was blocked by safety filters. Try rephrasing the recipe")
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
        prompt = (
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

        try:
            response = self._generate(prompt)

            if not response or not response.text:
                raise Exception("Empty response from Gemini API")

            return response.text.strip()

        except Exception as e:
            raise Exception(f"Failed to translate text: {str(e)}")

    def translate_list(self, items: list, target_language: str) -> list:
        """
        Translate a list of items (ingredients or instructions).

        Args:
            items: List of strings to translate
            target_language: Target language

        Returns:
            List of translated strings
        """
        if not items:
            return []

        # Join items with numbering for better context
        numbered_items = "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])

        prompt = (
            f"Translate the following items to {target_language}. "
            f"Keep the same numbering and format. Provide only the translations:\n\n"
            f"{numbered_items}"
        )

        try:
            response = self._generate(prompt)

            if not response or not response.text:
                raise Exception("Empty response from Gemini API")

            # Parse the response back into a list
            translated_text = response.text.strip()
            translated_items = []

            for line in translated_text.split('\n'):
                line = line.strip()
                if line:
                    # Remove numbering if present
                    if '. ' in line:
                        parts = line.split('. ', 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            line = parts[1]
                    translated_items.append(line)

            return translated_items

        except Exception as e:
            raise Exception(f"Failed to translate list: {str(e)}")

    def test_connection(self) -> bool:
        """
        Test the connection to Gemini API.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self._generate("Hello, respond with 'OK'")
            return response and response.text is not None
        except Exception:
            return False

    @classmethod
    def get_available_models(cls) -> dict:
        """
        Get dictionary of available non-deprecated models.

        Returns:
            Dictionary mapping model names to descriptions
        """
        return cls.AVAILABLE_MODELS.copy()
