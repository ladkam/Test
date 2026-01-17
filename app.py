#!/usr/bin/env python3
"""
Flask web application for NYT Cooking Recipe Translator with Authentication
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv

from recipe_scraper import NYTRecipeScraper
from unit_converter import UnitConverter
from mistral_translator import MistralTranslator
from groq_translator import GroqTranslator
from auth import User, change_password, delete_user
import settings

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app)

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure upload folder for temporary files
TEMP_FOLDER = Path(tempfile.gettempdir()) / 'recipe_translator'
TEMP_FOLDER.mkdir(exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.get(user_id)


def admin_required(f):
    """Decorator to require admin role."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def index():
    """Render the main page."""
    return render_template('index.html', languages=settings.get_languages())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.verify_password(username, password)
        if user:
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/results')
@login_required
def show_results():
    """Display recipe translation results."""
    recipe_data = session.get('current_recipe')

    if not recipe_data:
        flash('No recipe to display. Please translate a recipe first.', 'error')
        return redirect(url_for('index'))

    return render_template('results.html', recipe=recipe_data, languages=settings.get_languages())


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Render admin dashboard."""
    users = User.list_all()
    languages = settings.get_languages()
    translation_prompt = settings.get_translation_prompt()
    system_prompt = settings.get_system_prompt()
    ai_provider = settings.get_ai_provider()
    ai_model = settings.get_ai_model()
    nyt_cookie = settings.get_nyt_cookie()

    return render_template(
        'admin.html',
        users=users,
        languages=languages,
        translation_prompt=translation_prompt,
        system_prompt=system_prompt,
        ai_provider=ai_provider,
        ai_model=ai_model,
        nyt_cookie=nyt_cookie
    )


@app.route('/api/translate', methods=['POST'])
@login_required
def translate_recipe():
    """
    API endpoint to translate a recipe.

    Expected JSON payload:
    {
        "url": "recipe URL",
        "language": "target language",
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
        convert_units = data.get('convert_units', True)
        do_translate = data.get('translate', True)

        # Step 1: Scrape the recipe (uses global NYT cookie from settings)
        try:
            scraper = NYTRecipeScraper()
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
                # Get the selected AI provider from settings
                ai_provider = settings.get_ai_provider()

                # Initialize the appropriate translator
                if ai_provider == 'groq':
                    translator = GroqTranslator()
                else:  # Default to Mistral
                    translator = MistralTranslator()

                recipe_text = translator.translate_recipe(recipe_text, language)
            except ValueError as e:
                return jsonify({'error': f'AI API error: {str(e)}'}), 500
            except Exception as e:
                return jsonify({'error': f'Translation failed: {str(e)}'}), 500

        # Return the processed recipe
        # Store in session for the results page
        session['current_recipe'] = {
            'content': recipe_text,
            'title': recipe['title'],
            'image': recipe.get('image', ''),
            'url': url
        }

        return jsonify({
            'success': True,
            'recipe': recipe_text,
            'title': recipe['title'],
            'image': recipe.get('image', ''),
            'redirect': url_for('show_results')
        })

    except Exception as e:
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500


@app.route('/api/download', methods=['POST'])
@login_required
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


# Admin API routes
@app.route('/api/admin/languages', methods=['GET', 'POST', 'DELETE'])
@admin_required
def manage_languages():
    """Manage languages list."""
    if request.method == 'GET':
        return jsonify({'languages': settings.get_languages()})

    elif request.method == 'POST':
        data = request.json
        language = data.get('language', '').strip()
        if settings.add_language(language):
            return jsonify({'success': True, 'message': f'Added language: {language}'})
        else:
            return jsonify({'success': False, 'message': 'Language already exists or invalid'}), 400

    elif request.method == 'DELETE':
        data = request.json
        language = data.get('language', '').strip()
        if settings.remove_language(language):
            return jsonify({'success': True, 'message': f'Removed language: {language}'})
        else:
            return jsonify({'success': False, 'message': 'Cannot remove language'}), 400


@app.route('/api/admin/prompts', methods=['GET', 'POST'])
@admin_required
def manage_prompts():
    """Manage translation prompts."""
    if request.method == 'GET':
        return jsonify({
            'translation_prompt': settings.get_translation_prompt(),
            'system_prompt': settings.get_system_prompt()
        })

    elif request.method == 'POST':
        data = request.json
        translation_prompt = data.get('translation_prompt')
        system_prompt = data.get('system_prompt')

        if translation_prompt:
            settings.update_translation_prompt(translation_prompt)
        if system_prompt:
            settings.update_system_prompt(system_prompt)

        return jsonify({'success': True, 'message': 'Prompts updated successfully'})


@app.route('/api/admin/api-settings', methods=['GET', 'POST'])
@admin_required
def manage_api_settings():
    """Manage API settings (provider, model, and cookie)."""
    if request.method == 'GET':
        return jsonify({
            'ai_provider': settings.get_ai_provider(),
            'ai_model': settings.get_ai_model(),
            'nyt_cookie': settings.get_nyt_cookie()
        })

    elif request.method == 'POST':
        data = request.json
        ai_provider = data.get('ai_provider')
        ai_model = data.get('ai_model')
        nyt_cookie = data.get('nyt_cookie')

        if ai_provider is not None:
            settings.update_ai_provider(ai_provider)
        if ai_model is not None:
            settings.update_ai_model(ai_model)
        if nyt_cookie is not None:
            settings.update_nyt_cookie(nyt_cookie)

        return jsonify({'success': True, 'message': 'API settings updated successfully'})


@app.route('/api/admin/settings/reset', methods=['POST'])
@admin_required
def reset_settings():
    """Reset all settings to defaults."""
    settings.reset_to_defaults()
    return jsonify({'success': True, 'message': 'Settings reset to defaults'})


@app.route('/api/admin/users', methods=['GET'])
@admin_required
def list_users():
    """List all users."""
    return jsonify({'users': User.list_all()})


@app.route('/api/admin/users/create', methods=['POST'])
@admin_required
def create_user():
    """Create a new user."""
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    user = User.create(username, password, role)
    if user:
        return jsonify({'success': True, 'message': f'User {username} created successfully'})
    else:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400


@app.route('/api/admin/users/<user_id>/delete', methods=['DELETE'])
@admin_required
def delete_user_route(user_id):
    """Delete a user."""
    if delete_user(user_id):
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    else:
        return jsonify({'success': False, 'message': 'Cannot delete user'}), 400


@app.route('/api/admin/users/<user_id>/password', methods=['POST'])
@admin_required
def change_user_password(user_id):
    """Change user password."""
    data = request.json
    new_password = data.get('password', '').strip()

    if not new_password:
        return jsonify({'success': False, 'message': 'Password required'}), 400

    if change_password(user_id, new_password):
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to change password'}), 400


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
