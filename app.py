#!/usr/bin/env python3
"""
Flask web application for NYT Cooking Recipe Translator
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from recipe_scraper import NYTRecipeScraper
from unit_converter import UnitConverter
from mistral_translator import MistralTranslator

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure upload folder for temporary files
TEMP_FOLDER = Path(tempfile.gettempdir()) / 'recipe_translator'
TEMP_FOLDER.mkdir(exist_ok=True)


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/api/translate', methods=['POST'])
def translate_recipe():
    """
    API endpoint to translate a recipe.

    Expected JSON payload:
    {
        "url": "recipe URL",
        "language": "target language",
        "nyt_cookie": "optional NYT-S cookie",
        "convert_units": true/false,
        "translate": true/false
    }
    """
    try:
        data = request.json

        # Validate input
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        if 'cooking.nytimes.com' not in url:
            return jsonify({'error': 'Please provide a valid NYT Cooking URL'}), 400

        language = data.get('language', os.getenv('TARGET_LANGUAGE', 'English'))
        nyt_cookie = data.get('nyt_cookie', '').strip() or None
        convert_units = data.get('convert_units', True)
        do_translate = data.get('translate', True)

        # Step 1: Scrape the recipe
        try:
            scraper = NYTRecipeScraper(nyt_cookie=nyt_cookie)
            recipe = scraper.scrape_recipe(url)
            recipe_text = scraper.format_recipe(recipe)
        except Exception as e:
            return jsonify({'error': f'Failed to download recipe: {str(e)}'}), 500

        # Step 2: Convert measurements to metric
        if convert_units:
            try:
                converter = UnitConverter()
                recipe_text = converter.convert_text(recipe_text)
            except Exception as e:
                # Non-fatal error, continue without conversion
                pass

        # Step 3: Translate the recipe
        if do_translate:
            try:
                translator = MistralTranslator()
                recipe_text = translator.translate_recipe(recipe_text, language)
            except ValueError as e:
                return jsonify({'error': f'Mistral API error: {str(e)}'}), 500
            except Exception as e:
                return jsonify({'error': f'Translation failed: {str(e)}'}), 500

        # Return the processed recipe
        return jsonify({
            'success': True,
            'recipe': recipe_text,
            'title': recipe['title']
        })

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/download', methods=['POST'])
def download_recipe():
    """
    API endpoint to download a recipe as a markdown file.

    Expected JSON payload:
    {
        "content": "recipe content",
        "filename": "recipe filename"
    }
    """
    try:
        data = request.json
        content = data.get('content', '')
        filename = data.get('filename', 'recipe.md')

        # Sanitize filename
        filename = ''.join(c if c.isalnum() or c in (' ', '-', '_', '.') else '_' for c in filename)
        if not filename.endswith('.md'):
            filename += '.md'

        # Create temporary file
        temp_file = TEMP_FOLDER / filename
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return send_file(
            temp_file,
            as_attachment=True,
            download_name=filename,
            mimetype='text/markdown'
        )

    except Exception as e:
        return jsonify({'error': f'Failed to create download: {str(e)}'}), 500


@app.route('/api/test-mistral', methods=['GET'])
def test_mistral():
    """Test Mistral API connection."""
    try:
        translator = MistralTranslator()
        if translator.test_connection():
            return jsonify({'success': True, 'message': 'Mistral API connection successful'})
        else:
            return jsonify({'success': False, 'message': 'Failed to connect to Mistral API'}), 500
    except ValueError as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
