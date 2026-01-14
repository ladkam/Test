#!/usr/bin/env python3
"""
NYT Cooking Recipe Translator

Downloads recipes from New York Times Cooking, converts measurements to metric,
and translates them using the Grok API.
"""
import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from recipe_scraper import NYTRecipeScraper
from unit_converter import UnitConverter
from mistral_translator import MistralTranslator


def main():
    """Main application entry point."""
    # Load environment variables
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Download, convert, and translate NYT Cooking recipes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Translate to Spanish (default from .env)
  python recipe_translator.py https://cooking.nytimes.com/recipes/1234-chocolate-chip-cookies

  # Translate to a specific language
  python recipe_translator.py https://cooking.nytimes.com/recipes/1234-chocolate-chip-cookies --language French

  # Save to a specific file
  python recipe_translator.py https://cooking.nytimes.com/recipes/1234-chocolate-chip-cookies --output my_recipe.md

  # Skip translation (only convert to metric)
  python recipe_translator.py https://cooking.nytimes.com/recipes/1234-chocolate-chip-cookies --no-translate
        """
    )

    parser.add_argument(
        'url',
        help='NYT Cooking recipe URL'
    )

    parser.add_argument(
        '-l', '--language',
        help='Target language for translation (default: from .env or English)',
        default=os.getenv('TARGET_LANGUAGE', 'English')
    )

    parser.add_argument(
        '-o', '--output',
        help='Output file path (default: auto-generated from recipe title)',
        default=None
    )

    parser.add_argument(
        '--no-translate',
        action='store_true',
        help='Skip translation, only convert measurements to metric'
    )

    parser.add_argument(
        '--no-convert',
        action='store_true',
        help='Skip unit conversion to metric'
    )

    args = parser.parse_args()

    # Validate URL
    if 'cooking.nytimes.com' not in args.url:
        print("Error: Please provide a valid NYT Cooking URL", file=sys.stderr)
        sys.exit(1)

    print(f"🍳 Downloading recipe from NYT Cooking...")

    # Step 1: Scrape the recipe
    try:
        scraper = NYTRecipeScraper()
        recipe = scraper.scrape_recipe(args.url)
        recipe_text = scraper.format_recipe(recipe)
        print(f"✓ Recipe downloaded: {recipe['title']}")
    except Exception as e:
        print(f"Error downloading recipe: {e}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Convert measurements to metric
    if not args.no_convert:
        print(f"📏 Converting measurements to metric...")
        try:
            converter = UnitConverter()
            recipe_text = converter.convert_text(recipe_text)
            print(f"✓ Measurements converted to metric")
        except Exception as e:
            print(f"Warning: Failed to convert some measurements: {e}", file=sys.stderr)

    # Step 3: Translate the recipe
    if not args.no_translate:
        print(f"🌍 Translating to {args.language}...")
        try:
            translator = MistralTranslator()

            # Test connection first
            if not translator.test_connection():
                print("Warning: Could not connect to Mistral AI API. Check your API key.", file=sys.stderr)
                print("Continuing without translation...", file=sys.stderr)
            else:
                recipe_text = translator.translate_recipe(recipe_text, args.language)
                print(f"✓ Recipe translated to {args.language}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("Continuing without translation...", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Translation failed: {e}", file=sys.stderr)
            print("Continuing with original language...", file=sys.stderr)

    # Step 4: Save the recipe
    if args.output:
        output_path = Path(args.output)
    else:
        # Generate filename from recipe title
        filename = recipe['title'].lower()
        filename = ''.join(c if c.isalnum() or c.isspace() else '' for c in filename)
        filename = filename.replace(' ', '_')
        filename = f"{filename}.md"
        output_path = Path('recipes') / filename

    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(recipe_text)
        print(f"\n✓ Recipe saved to: {output_path}")
    except Exception as e:
        print(f"Error saving recipe: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"\n🎉 Done! Enjoy your recipe!")


if __name__ == '__main__':
    main()
