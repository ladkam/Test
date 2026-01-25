"""
Google Gemini API integration for recipe translation.
Uses non-deprecated Gemini models.
"""
import os
from typing import Optional
from settings import get_translation_prompt, get_system_prompt, get_ai_model

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiTranslator:
    """Translator using Google Gemini API."""

    # Available models (January 2026)
    # FREE: 3 Flash, 2.5 Flash, 2.5 Flash-Lite
    # PAID: 3 Pro, 2.5 Pro
    AVAILABLE_MODELS = {
        'gemini-3-flash-preview': 'Gemini 3 Flash (Preview) - Latest, fastest (FREE)',
        'gemini-2.5-flash': 'Gemini 2.5 Flash - Stable, production-ready (FREE, Recommended)',
        'gemini-2.5-flash-lite': 'Gemini 2.5 Flash-Lite - Cost-optimized (FREE)',
        'gemini-3-pro-preview': 'Gemini 3 Pro (Preview) - Best quality (PAID)',
        'gemini-2.5-pro': 'Gemini 2.5 Pro - Best reasoning (PAID)'
    }

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize Gemini translator.

        Args:
            api_key: Google API key (defaults to GEMINI_API_KEY env var)
            model: Model to use (defaults to gemini-2.5-flash)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "Google Generative AI library not installed. "
                "Install with: pip install google-generativeai"
            )

        self.api_key = api_key or os.getenv('GEMINI_API_KEY')

        if not self.api_key:
            raise ValueError(
                "Gemini API key not provided. "
                "Set GEMINI_API_KEY environment variable or pass it to the constructor."
            )

        # Configure the API
        genai.configure(api_key=self.api_key)

        # Set model (default to stable production Flash model)
        self.model_name = model or os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

        # Validate model
        if self.model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model: {self.model_name}. "
                f"Available models: {', '.join(self.AVAILABLE_MODELS.keys())}"
            )

        # Initialize the model
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                'temperature': 0.3,
                'top_p': 0.95,
                'top_k': 40,
                'max_output_tokens': 4096,
            }
        )

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
            response = self.model.generate_content(full_prompt)

            if not response or not response.text:
                raise Exception("Empty response from Gemini API")

            return response.text.strip()

        except Exception as e:
            # Handle specific Gemini errors
            error_msg = str(e)

            if "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
                raise Exception("Invalid API key. Please check your GEMINI_API_KEY")
            elif "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                raise Exception("API quota exceeded or rate limit hit. Please try again later")
            elif "safety" in error_msg.lower():
                raise Exception("Content was blocked by safety filters. Try rephrasing the recipe")
            else:
                raise Exception(f"Failed to translate recipe: {error_msg}")

    def translate_text(self, text: str, target_language: str) -> str:
        """
        Translate simple text to target language.

        Args:
            text: The text to translate
            target_language: Target language (e.g., "Spanish", "French")

        Returns:
            Translated text
        """
        prompt = f"Translate the following text to {target_language}. Provide only the translation, no explanations:\n\n{text}"

        try:
            response = self.model.generate_content(prompt)

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
            response = self.model.generate_content(prompt)

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
            response = self.model.generate_content("Hello, respond with 'OK'")
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
