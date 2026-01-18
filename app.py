#!/usr/bin/env python3
"""
Flask web application for Recipe Management System with Translation
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
import os
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import requests
import json
import re

from recipe_scraper import NYTRecipeScraper
from unit_converter import UnitConverter
from mistral_translator import MistralTranslator
from groq_translator import GroqTranslator
from models import db, User, Recipe, WeeklyPlan, PlanRecipe, Settings as SettingsModel
import settings

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration with absolute path to persist data
# Use absolute path to avoid losing data when instance/ folder is gitignored
basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, 'data')
os.makedirs(data_dir, exist_ok=True)  # Ensure data directory exists

default_db_path = f"sqlite:///{os.path.join(data_dir, 'recipes.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', default_db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

# Initialize database
db.init_app(app)

# Create tables on first run
with app.app_context():
    try:
        # Create all tables (idempotent - safe to run multiple times)
        db.create_all()
        print("✓ Database tables created/verified")

        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✓ Created default admin user (username: admin, password: admin123)")

        print("✓ Database initialized")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.session.rollback()

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Configure upload folder for temporary files
TEMP_FOLDER = Path(tempfile.gettempdir()) / 'recipe_translator'
TEMP_FOLDER.mkdir(exist_ok=True)

# Helper function to get API keys from database with fallback to environment
def get_api_key(key_name):
    """Get API key from database, fallback to environment variable. Returns None if not set."""
    with app.app_context():
        db_value = SettingsModel.get(key_name, '')
        if db_value and db_value.strip():  # Check for non-empty value
            return db_value
        # Fallback to environment variable
        env_var_name = key_name.upper()
        env_value = os.getenv(env_var_name, '')
        return env_value if env_value and env_value.strip() else None


def calculate_health_score(nutrition_data):
    """
    Calculate a health score (0-100) based on nutritional macros.

    Scoring criteria:
    - Balanced macros (protein, carbs, fats)
    - Reasonable calorie density
    - High protein relative to calories
    - Low saturated fat
    - High fiber
    - Reasonable sodium

    Args:
        nutrition_data: Dictionary with keys like calories, protein, carbs, fat, fiber, sodium

    Returns:
        Dictionary with 'score' (0-100), 'grade' (A-F), and 'details'
    """
    if not nutrition_data or not isinstance(nutrition_data, dict):
        return {'score': None, 'grade': None, 'details': 'No nutrition data available'}

    score = 100
    details = []

    # Extract nutrition values (handle various formats)
    calories = nutrition_data.get('calories', 0)
    protein = nutrition_data.get('protein', 0)
    carbs = nutrition_data.get('carbohydrates', nutrition_data.get('carbs', 0))
    fat = nutrition_data.get('fat', nutrition_data.get('totalFat', 0))
    saturated_fat = nutrition_data.get('saturatedFat', 0)
    fiber = nutrition_data.get('fiber', nutrition_data.get('dietaryFiber', 0))
    sodium = nutrition_data.get('sodium', 0)

    # Convert string values to numbers if needed
    def to_number(value):
        if isinstance(value, str):
            # Remove units and convert
            value = re.sub(r'[^\d.]', '', value)
            try:
                return float(value) if value else 0
            except:
                return 0
        return float(value) if value else 0

    calories = to_number(calories)
    protein = to_number(protein)
    carbs = to_number(carbs)
    fat = to_number(fat)
    saturated_fat = to_number(saturated_fat)
    fiber = to_number(fiber)
    sodium = to_number(sodium)

    # 1. Calorie density check (prefer 200-600 calories per serving)
    if calories > 0:
        if calories < 150:
            score -= 5
            details.append('Very low in calories')
        elif calories > 800:
            score -= 15
            details.append('High in calories')
        elif calories > 600:
            score -= 5
            details.append('Moderately high in calories')

    # 2. Protein quality (protein should be 15-35% of calories)
    if calories > 0 and protein > 0:
        protein_calories = protein * 4  # 4 calories per gram
        protein_percentage = (protein_calories / calories) * 100
        if protein_percentage >= 20:
            score += 5
            details.append('Good protein content')
        elif protein_percentage < 10:
            score -= 10
            details.append('Low in protein')

    # 3. Fat quality (20-35% of calories, penalize high saturated fat)
    if calories > 0 and fat > 0:
        fat_calories = fat * 9  # 9 calories per gram
        fat_percentage = (fat_calories / calories) * 100
        if fat_percentage > 45:
            score -= 15
            details.append('High in fat')
        elif fat_percentage > 35:
            score -= 5

        # Check saturated fat
        if saturated_fat > 0 and fat > 0:
            sat_fat_ratio = saturated_fat / fat
            if sat_fat_ratio > 0.5:
                score -= 10
                details.append('High in saturated fat')

    # 4. Fiber bonus (5g+ is good)
    if fiber >= 5:
        score += 10
        details.append('High in fiber')
    elif fiber >= 3:
        score += 5
        details.append('Good fiber content')

    # 5. Sodium check (per serving)
    if sodium > 0:
        if sodium > 800:
            score -= 15
            details.append('High in sodium')
        elif sodium > 600:
            score -= 8
            details.append('Moderately high in sodium')
        elif sodium < 200:
            score += 5
            details.append('Low in sodium')

    # 6. Carb quality (prefer complex carbs with fiber)
    if carbs > 0 and fiber > 0:
        fiber_to_carb_ratio = fiber / carbs
        if fiber_to_carb_ratio >= 0.1:  # 10% fiber to carbs
            score += 5
            details.append('Good fiber-to-carb ratio')

    # Ensure score is within bounds
    score = max(0, min(100, score))

    # Determine grade
    if score >= 90:
        grade = 'A'
    elif score >= 80:
        grade = 'B'
    elif score >= 70:
        grade = 'C'
    elif score >= 60:
        grade = 'D'
    else:
        grade = 'F'

    return {
        'score': round(score),
        'grade': grade,
        'details': ' | '.join(details) if details else 'Balanced nutrition'
    }


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


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
    """Dashboard - Weekly Planner (Home Page)."""
    return render_template('planner.html')

@app.route('/import')
@login_required
def import_recipe():
    """Import recipes from NYT or photo upload."""
    return render_template('import.html', languages=settings.get_languages())


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
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
    all_users = User.query.all()
    users = [{'id': str(u.id), 'username': u.username, 'role': u.role} for u in all_users]
    languages = settings.get_languages()
    translation_prompt = settings.get_translation_prompt()
    system_prompt = settings.get_system_prompt()
    ai_provider = settings.get_ai_provider()
    ai_model = settings.get_ai_model()
    nyt_cookie = settings.get_nyt_cookie()

    # Get API keys from database
    groq_api_key = SettingsModel.get('groq_api_key', '')
    mistral_api_key = SettingsModel.get('mistral_api_key', '')

    return render_template(
        'admin.html',
        users=users,
        languages=languages,
        translation_prompt=translation_prompt,
        system_prompt=system_prompt,
        ai_provider=ai_provider,
        ai_model=ai_model,
        nyt_cookie=nyt_cookie,
        groq_api_key=groq_api_key,
        mistral_api_key=mistral_api_key
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

                # Get API key and check if configured
                if ai_provider == 'groq':
                    api_key = get_api_key('groq_api_key')
                    if not api_key:
                        return jsonify({'error': 'Groq API key not configured. Please add it in the admin panel.'}), 500
                    translator = GroqTranslator(api_key=api_key)
                else:  # Default to Mistral
                    api_key = get_api_key('mistral_api_key')
                    if not api_key:
                        return jsonify({'error': 'Mistral API key not configured. Please add it in the admin panel.'}), 500
                    translator = MistralTranslator(api_key=api_key)

                recipe_text = translator.translate_recipe(recipe_text, language)
            except ValueError as e:
                return jsonify({'error': f'AI API error: {str(e)}'}), 500
            except Exception as e:
                return jsonify({'error': f'Translation failed: {str(e)}'}), 500

        # Return the processed recipe
        # Store in session for the results page with complete data
        original_formatted = scraper.format_recipe(recipe)
        session['current_recipe'] = {
            'content': recipe_text,
            'content_original': original_formatted,
            'title': recipe['title'],
            'image': recipe.get('image', ''),
            'url': url,
            'language': language,
            'ingredients': recipe.get('ingredients', []),
            'instructions': recipe.get('instructions', []),
            'prep_time': recipe.get('time', {}).get('prep', ''),
            'cook_time': recipe.get('time', {}).get('cook', ''),
            'total_time': recipe.get('time', {}).get('total', ''),
            'servings': recipe.get('yield', ''),
            'author': recipe.get('author', ''),
            'nutrition': recipe.get('nutrition', {})
        }

        return jsonify({
            'success': True,
            'recipe': {
                'content': recipe_text,
                'content_original': original_formatted,
                'title': recipe['title'],
                'image': recipe.get('image', ''),
                'url': url,
                'language': language,
                'ingredients': recipe.get('ingredients', []),
                'instructions': recipe.get('instructions', []),
                'prep_time': recipe.get('time', {}).get('prep', ''),
                'cook_time': recipe.get('time', {}).get('cook', ''),
                'total_time': recipe.get('time', {}).get('total', ''),
                'servings': recipe.get('yield', ''),
                'author': recipe.get('author', ''),
                'nutrition': recipe.get('nutrition', {})
            }
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
        api_key = get_api_key('mistral_api_key')
        if not api_key:
            return jsonify({'success': False, 'message': 'Mistral API key not configured. Please add it in the admin panel.'}), 400
        translator = MistralTranslator(api_key=api_key)
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
    """Manage API settings (provider, model, API keys, and cookie)."""
    if request.method == 'GET':
        return jsonify({
            'ai_provider': settings.get_ai_provider(),
            'ai_model': settings.get_ai_model(),
            'nyt_cookie': settings.get_nyt_cookie(),
            'groq_api_key': SettingsModel.get('groq_api_key', ''),
            'mistral_api_key': SettingsModel.get('mistral_api_key', '')
        })

    elif request.method == 'POST':
        data = request.json

        # Handle API keys
        groq_api_key = data.get('groq_api_key')
        mistral_api_key = data.get('mistral_api_key')

        if groq_api_key is not None:
            SettingsModel.set('groq_api_key', groq_api_key)
        if mistral_api_key is not None:
            SettingsModel.set('mistral_api_key', mistral_api_key)

        # Handle other settings
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
    all_users = User.query.all()
    users = [{'id': str(u.id), 'username': u.username, 'role': u.role} for u in all_users]
    return jsonify({'users': users})


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

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    # Create new user
    new_user = User(username=username, role=role)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': f'User {username} created successfully'})


@app.route('/api/admin/users/<user_id>/delete', methods=['DELETE'])
@admin_required
def delete_user_route(user_id):
    """Delete a user."""
    try:
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        # Don't allow deleting the last admin
        if user.role == 'admin':
            admin_count = User.query.filter_by(role='admin').count()
            if admin_count <= 1:
                return jsonify({'success': False, 'message': 'Cannot delete the last admin user'}), 400

        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': 'User deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting user: {str(e)}'}), 400


@app.route('/api/admin/users/<user_id>/password', methods=['POST'])
@admin_required
def change_user_password(user_id):
    """Change user password."""
    data = request.json
    new_password = data.get('password', '').strip()

    if not new_password:
        return jsonify({'success': False, 'message': 'Password required'}), 400

    try:
        user = User.query.get(int(user_id))
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        user.set_password(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'}), 400


# Recipe Library Routes
@app.route('/library')
@login_required
def library():
    """Render recipe library page."""
    return render_template('library.html')


@app.route('/planner')
@login_required
def planner():
    """Render weekly planner page."""
    return render_template('planner.html')


@app.route('/help')
def help_view():
    """Render simplified help view for household staff (no login required)."""
    return render_template('help_view.html')


@app.route('/api/recipes', methods=['GET'])
@login_required
def list_recipes():
    """List all recipes."""
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return jsonify({
        'success': True,
        'recipes': [r.to_dict() for r in recipes]
    })


@app.route('/api/recipes/<int:recipe_id>', methods=['GET'])
@login_required
def get_recipe(recipe_id):
    """Get a specific recipe."""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        return jsonify({'success': False, 'message': 'Recipe not found'}), 404

    return jsonify({
        'success': True,
        'recipe': recipe.to_dict()
    })


@app.route('/api/recipes/<int:recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Delete a recipe."""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'message': 'Recipe not found'}), 404

        db.session.delete(recipe)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Recipe deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting recipe: {str(e)}'}), 500


@app.route('/recipe/edit/<int:recipe_id>')
@login_required
def edit_recipe_page(recipe_id):
    """Render the edit recipe page."""
    recipe = Recipe.query.get(recipe_id)
    if not recipe:
        flash('Recipe not found', 'error')
        return redirect(url_for('library'))

    return render_template('edit_recipe.html', recipe=recipe)


@app.route('/api/recipes/<int:recipe_id>/update', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Update a recipe."""
    try:
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'message': 'Recipe not found'}), 404

        data = request.json

        # Helper function to parse time string to minutes
        def parse_time_to_minutes(time_str):
            if not time_str or not isinstance(time_str, str):
                return None
            time_str = time_str.lower().strip()
            total_mins = 0
            # Extract hours
            if 'hour' in time_str:
                hours = int(''.join(filter(str.isdigit, time_str.split('hour')[0].strip())))
                total_mins += hours * 60
            # Extract minutes
            if 'minute' in time_str:
                parts = time_str.split('hour')[-1] if 'hour' in time_str else time_str
                minutes = int(''.join(filter(str.isdigit, parts.split('minute')[0].strip())))
                total_mins += minutes
            return total_mins if total_mins > 0 else None

        # Update recipe fields
        if 'title' in data:
            recipe.title = data['title']
        if 'content' in data:
            recipe.content = data['content']
        if 'ingredients' in data:
            recipe.ingredients = data['ingredients']
        if 'instructions' in data:
            recipe.instructions = data['instructions']
        if 'prep_time' in data:
            recipe.prep_time = parse_time_to_minutes(data['prep_time'])
        if 'cook_time' in data:
            recipe.cook_time = parse_time_to_minutes(data['cook_time'])
        if 'servings' in data:
            recipe.servings = data['servings']
        if 'image_url' in data:
            recipe.image_url = data['image_url']
        if 'author' in data:
            recipe.author = data['author']
        if 'source_url' in data:
            recipe.source_url = data['source_url']

        # Calculate total time
        if recipe.prep_time and recipe.cook_time:
            recipe.total_time = recipe.prep_time + recipe.cook_time
        elif recipe.prep_time:
            recipe.total_time = recipe.prep_time
        elif recipe.cook_time:
            recipe.total_time = recipe.cook_time

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Recipe updated successfully',
            'recipe': recipe.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating recipe: {str(e)}'}), 500


@app.route('/api/recipes/ocr', methods=['POST'])
@login_required
def extract_recipe_from_image():
    """Extract recipe from image using Groq vision API."""
    try:
        data = request.json
        image_data = data.get('image')  # base64 encoded image

        if not image_data:
            return jsonify({'success': False, 'message': 'No image provided'}), 400

        # Ensure we have Groq API key
        groq_api_key = get_api_key('groq_api_key')
        if not groq_api_key:
            return jsonify({'success': False, 'message': 'Groq API key not configured. Please set it in the admin panel.'}), 500

        # Prepare the prompt for recipe extraction
        prompt = """Extract the recipe from this image. Please provide:
1. Recipe Title
2. Prep Time (if mentioned)
3. Cook Time (if mentioned)
4. Ingredients (list each ingredient on a separate line)
5. Instructions (list each step on a separate line)

Format your response as JSON with this structure:
{
    "title": "Recipe Name",
    "prep_time": "15 minutes",
    "cook_time": "30 minutes",
    "ingredients": ["ingredient 1", "ingredient 2", ...],
    "instructions": ["step 1", "step 2", ...]
}

If any field is not visible in the image, omit it or leave it empty."""

        # Call Groq vision API
        headers = {
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json'
        }

        # Use vision model
        vision_model = 'meta-llama/llama-4-scout-17b-16e-instruct'

        payload = {
            'model': vision_model,
            'messages': [{
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': prompt
                    },
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': image_data  # base64 data URL
                        }
                    }
                ]
            }],
            'temperature': 0.2,
            'max_tokens': 2000
        }

        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()
        result = response.json()

        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content'].strip()

            # Try to parse JSON from the response
            # Find JSON in the response (it might be wrapped in markdown code blocks)
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                recipe_data = json.loads(json_match.group())
            else:
                # If no JSON found, return raw content for manual parsing
                return jsonify({
                    'success': False,
                    'message': 'Could not parse recipe data from image',
                    'raw_content': content
                }), 400

            return jsonify({
                'success': True,
                'recipe': recipe_data
            })
        else:
            return jsonify({'success': False, 'message': 'Unexpected response from vision API'}), 500

    except requests.exceptions.HTTPError as e:
        error_msg = f'Vision API error: {str(e)}'
        if e.response.status_code == 401:
            error_msg = 'Invalid Groq API key'
        elif e.response.status_code == 429:
            error_msg = 'Rate limit exceeded. Please try again in a moment.'
        return jsonify({'success': False, 'message': error_msg}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error processing image: {str(e)}'}), 500


@app.route('/api/recipes/save', methods=['POST'])
@login_required
def save_recipe():
    """Save a recipe to the library."""
    try:
        data = request.json.get('recipeData', {})

        # Helper function to parse time string to minutes
        def parse_time_to_minutes(time_str):
            if not time_str or not isinstance(time_str, str):
                return None
            time_str = time_str.lower().strip()
            total_mins = 0
            # Extract hours
            if 'hour' in time_str:
                hours = int(''.join(filter(str.isdigit, time_str.split('hour')[0].strip())))
                total_mins += hours * 60
            # Extract minutes
            if 'minute' in time_str:
                parts = time_str.split('hour')[-1] if 'hour' in time_str else time_str
                minutes = int(''.join(filter(str.isdigit, parts.split('minute')[0].strip())))
                total_mins += minutes
            return total_mins if total_mins > 0 else None

        # Create new recipe (original content only)
        new_recipe = Recipe(
            title=data.get('title', ''),
            content=data.get('content_original', '') or data.get('content', ''),
            ingredients=data.get('ingredients', []),
            instructions=data.get('instructions', []),
            prep_time=parse_time_to_minutes(data.get('prep_time')),
            cook_time=parse_time_to_minutes(data.get('cook_time')),
            total_time=parse_time_to_minutes(data.get('total_time')),
            servings=data.get('servings', ''),
            image_url=data.get('image', ''),
            author=data.get('author', ''),
            source_url=data.get('url', ''),
            source_language=data.get('source_language', 'English'),
            nutrition=data.get('nutrition', {}),
            tags=[]
        )

        db.session.add(new_recipe)
        db.session.flush()  # Get the recipe ID

        # If there's a translation, save it as a RecipeTranslation record
        target_language = data.get('language', 'English')
        if target_language and target_language != 'English' and data.get('content'):
            from models import RecipeTranslation

            # Map language names to codes
            language_code_map = {
                'Spanish': 'es',
                'French': 'fr',
                'Español': 'es',
                'Français': 'fr'
            }

            language_code = language_code_map.get(target_language, target_language.lower()[:2])

            # Check if translation doesn't already exist
            existing_translation = RecipeTranslation.query.filter_by(
                recipe_id=new_recipe.id,
                language_code=language_code
            ).first()

            if not existing_translation:
                # Translate individual fields using AI
                try:
                    ai_provider = settings.get_ai_provider()
                    if ai_provider == 'groq':
                        api_key = get_api_key('groq_api_key')
                        if api_key:
                            translator = GroqTranslator(api_key=api_key)
                        else:
                            translator = None
                    else:
                        api_key = get_api_key('mistral_api_key')
                        if api_key:
                            translator = MistralTranslator(api_key=api_key)
                        else:
                            translator = None

                    if translator:
                        # Translate title, ingredients, and instructions
                        translated_title = translator.translate_text(new_recipe.title, target_language)
                        translated_ingredients = [
                            translator.translate_text(ing, target_language)
                            for ing in (new_recipe.ingredients or [])
                        ]
                        translated_instructions = [
                            translator.translate_text(inst, target_language)
                            for inst in (new_recipe.instructions or [])
                        ]

                        translation = RecipeTranslation(
                            recipe_id=new_recipe.id,
                            language_code=language_code,
                            language_name=target_language,
                            title=translated_title,
                            content=data.get('content', ''),  # Translated content from scraping
                            ingredients=translated_ingredients,
                            instructions=translated_instructions
                        )
                        db.session.add(translation)
                except Exception as e:
                    # If translation fails, still save the recipe but skip the translation
                    print(f"Warning: Failed to create translation: {e}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Recipe saved successfully',
            'recipe_id': new_recipe.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving recipe: {str(e)}'}), 500


# AI Ingredient Substitution
@app.route('/api/ingredients/substitute', methods=['POST'])
@login_required
def get_ingredient_substitute():
    """Get AI-powered ingredient substitutions."""
    try:
        data = request.json
        ingredient = data.get('ingredient', '')
        recipe_context = data.get('recipe_context', {})
        recipe_name = recipe_context.get('title', '')
        recipe_type = recipe_context.get('type', '')

        if not ingredient:
            return jsonify({'success': False, 'message': 'Ingredient required'}), 400

        # Build prompt for AI
        prompt = f"""Suggest 3-5 practical substitutes for the ingredient "{ingredient}" """
        if recipe_name:
            prompt += f"""in the recipe "{recipe_name}" """

        prompt += """.

For each substitute:
1. Name the substitute ingredient
2. Explain why it works
3. Note any adjustments needed (amount, cooking time, etc.)

Keep suggestions practical and commonly available. Format as a numbered list."""

        # Check if API keys are configured
        groq_api_key = get_api_key('groq_api_key')
        mistral_api_key = get_api_key('mistral_api_key')

        if not groq_api_key and not mistral_api_key:
            return jsonify({
                'success': False,
                'message': 'AI service not configured. Please set API keys in the admin panel.'
            }), 503

        # Get AI provider from settings
        ai_provider = settings.get_ai_provider()

        # Use available provider
        if ai_provider == 'groq' and groq_api_key:
            use_groq = True
        elif ai_provider == 'mistral' and mistral_api_key:
            use_groq = False
        elif groq_api_key:
            use_groq = True
        elif mistral_api_key:
            use_groq = False
        else:
            return jsonify({
                'success': False,
                'message': 'No AI service available. Please set API keys in the admin panel.'
            }), 503

        # Call AI
        try:
            if use_groq:
                from groq import Groq
                translator = GroqTranslator(api_key=groq_api_key)
                client = Groq(api_key=translator.api_key, base_url=translator.base_url)
                response = client.chat.completions.create(
                    model=translator.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant providing ingredient substitution advice."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                suggestions = response.choices[0].message.content
            else:
                from mistralai import Mistral
                translator = MistralTranslator(api_key=mistral_api_key)
                client = Mistral(api_key=translator.api_key)
                response = client.chat.complete(
                    model=translator.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful cooking assistant providing ingredient substitution advice."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                suggestions = response.choices[0].message.content

            return jsonify({
                'success': True,
                'ingredient': ingredient,
                'suggestions': suggestions
            })

        except Exception as e:
            return jsonify({'success': False, 'message': f'AI error: {str(e)}'}), 500

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# Weekly Planner Routes
@app.route('/api/planner/current', methods=['GET'])
@login_required
def get_current_plan():
    """Get current week's plan."""
    from datetime import date, timedelta

    # Get Monday of current week
    today = date.today()
    monday = today - timedelta(days=today.weekday())

    # Find or create plan for this week
    plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()

    if not plan:
        return jsonify({'success': True, 'recipes': []})

    # Get all recipes in the plan
    plan_recipes = PlanRecipe.query.filter_by(plan_id=plan.id).all()
    recipes = [pr.recipe.to_dict() for pr in plan_recipes if pr.recipe]

    return jsonify({'success': True, 'recipes': recipes})


@app.route('/api/planner/add', methods=['POST'])
@login_required
def add_to_plan():
    """Add a recipe to current week's plan."""
    from datetime import date, timedelta

    try:
        data = request.json
        recipe_id = data.get('recipe_id')
        servings = data.get('servings', 1)  # Default to 1 if not provided

        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Find or create plan for this week
        plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
        if not plan:
            plan = WeeklyPlan(week_start_date=monday)
            db.session.add(plan)
            db.session.flush()

        # Check if recipe already in plan
        existing = PlanRecipe.query.filter_by(plan_id=plan.id, recipe_id=recipe_id).first()
        if existing:
            return jsonify({'success': False, 'message': 'Recipe already in plan'}), 400

        # Add recipe to plan with servings
        plan_recipe = PlanRecipe(
            plan_id=plan.id,
            recipe_id=recipe_id,
            day_of_week=1,  # Not used, but required
            meal_order=0,
            servings=servings
        )
        db.session.add(plan_recipe)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Recipe added to plan'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error adding recipe: {str(e)}'}), 500


@app.route('/api/planner/remove', methods=['POST'])
@login_required
def remove_from_plan():
    """Remove a recipe from current week's plan."""
    from datetime import date, timedelta

    try:
        data = request.json
        recipe_id = data.get('recipe_id')

        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Find plan for this week
        plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
        if not plan:
            return jsonify({'success': False, 'message': 'No plan found'}), 404

        # Remove recipe from plan
        plan_recipe = PlanRecipe.query.filter_by(plan_id=plan.id, recipe_id=recipe_id).first()
        if plan_recipe:
            db.session.delete(plan_recipe)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Recipe removed from plan'})
        else:
            return jsonify({'success': False, 'message': 'Recipe not in plan'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error removing recipe: {str(e)}'}), 500


@app.route('/api/planner/clear', methods=['POST'])
@login_required
def clear_plan():
    """Clear all recipes from current week's plan."""
    from datetime import date, timedelta

    try:
        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Find plan for this week
        plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
        if plan:
            PlanRecipe.query.filter_by(plan_id=plan.id).delete()
            db.session.commit()

        return jsonify({'success': True, 'message': 'Plan cleared'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error clearing plan: {str(e)}'}), 500


@app.route('/api/planner/shopping-list', methods=['GET'])
@login_required
def get_shopping_list():
    """Generate shopping list from current week's plan."""
    from datetime import date, timedelta
    import re

    def get_recipe_ingredients(recipe):
        """Get ingredients from recipe, preferring translations."""
        # Try to get translated ingredients (prefer Spanish, then French)
        for translation in recipe.translations:
            if translation.language_code in ['es', 'fr'] and translation.ingredients:
                return translation.ingredients

        # Fall back to original ingredients
        return recipe.ingredients or []

    def get_recipe_title(recipe):
        """Get recipe title, preferring translations."""
        # Try to get translated title (prefer Spanish, then French)
        for translation in recipe.translations:
            if translation.language_code in ['es', 'fr'] and translation.title:
                return translation.title

        # Fall back to original title
        return recipe.title

    def scale_ingredient(ingredient, scale):
        """Scale ingredient amounts by a multiplier."""
        if scale == 1:
            return ingredient

        # Match numbers (including fractions and decimals)
        def scale_match(match):
            num_str = match.group(0)
            try:
                # Handle fractions
                if '/' in num_str:
                    parts = num_str.split('/')
                    num = float(parts[0]) / float(parts[1])
                else:
                    num = float(num_str)

                scaled = num * scale
                # Format nicely
                if scaled == int(scaled):
                    return str(int(scaled))
                else:
                    return f"{scaled:.1f}".rstrip('0').rstrip('.')
            except:
                return num_str

        # Replace numbers in the ingredient string
        return re.sub(r'\d+\.?\d*(?:/\d+)?', scale_match, ingredient)

    try:
        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Find plan for this week
        plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
        if not plan:
            return jsonify({'success': True, 'shopping_list': []})

        # Get all recipes in the plan
        plan_recipes = PlanRecipe.query.filter_by(plan_id=plan.id).all()

        shopping_list = []
        for pr in plan_recipes:
            if pr.recipe:
                # Get ingredients and title (prefer translated)
                ingredients = get_recipe_ingredients(pr.recipe)
                title = get_recipe_title(pr.recipe)

                if ingredients:
                    # Get original servings from recipe
                    recipe_servings = 1
                    if pr.recipe.servings:
                        match = re.search(r'\d+', str(pr.recipe.servings))
                        if match:
                            recipe_servings = int(match.group(0))

                    # Calculate scale factor
                    scale = pr.servings / recipe_servings if recipe_servings > 0 else 1

                    # Scale ingredients
                    scaled_ingredients = [scale_ingredient(ing, scale) for ing in ingredients]

                    shopping_list.append({
                        'recipe': f"{title} ({pr.servings} servings)" if pr.servings != recipe_servings else title,
                        'ingredients': scaled_ingredients
                    })

        return jsonify({'success': True, 'shopping_list': shopping_list})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error generating shopping list: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
@app.route('/api/recipes/<int:recipe_id>/translate', methods=['POST'])
@login_required
def create_recipe_translation(recipe_id):
    """Create a new translation for a recipe."""
    try:
        data = request.json
        language_code = data.get('language_code')  # 'es' or 'fr'
        
        if not language_code or language_code not in ['es', 'fr']:
            return jsonify({'success': False, 'message': 'Invalid language code. Use "es" or "fr"'}), 400
        
        # Get recipe
        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'message': 'Recipe not found'}), 404
        
        # Check if translation already exists
        from models import RecipeTranslation
        existing = RecipeTranslation.query.filter_by(
            recipe_id=recipe_id,
            language_code=language_code
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': f'Translation already exists for {language_code}'}), 400
        
        # Language names
        language_names = {'es': 'Spanish', 'fr': 'French'}
        language_name = language_names[language_code]
        
        # Translate using AI
        from groq_translator import GroqTranslator
        from mistral_translator import MistralTranslator
        import settings

        ai_provider = settings.get_ai_provider()
        if ai_provider == 'groq':
            api_key = get_api_key('groq_api_key')
            if not api_key:
                return jsonify({'success': False, 'message': 'Groq API key not configured. Please add it in the admin panel.'}), 500
            translator = GroqTranslator(api_key=api_key)
        else:
            api_key = get_api_key('mistral_api_key')
            if not api_key:
                return jsonify({'success': False, 'message': 'Mistral API key not configured. Please add it in the admin panel.'}), 500
            translator = MistralTranslator(api_key=api_key)
        
        # Translate title
        title_translation = translator.translate_text(recipe.title, language_name)
        
        # Translate ingredients
        ingredients_translated = []
        if recipe.ingredients:
            for ingredient in recipe.ingredients:
                translated = translator.translate_text(ingredient, language_name)
                ingredients_translated.append(translated)
        
        # Translate instructions
        instructions_translated = []
        if recipe.instructions:
            for instruction in recipe.instructions:
                translated = translator.translate_text(instruction, language_name)
                instructions_translated.append(translated)
        
        # Translate full content
        content_translated = translator.translate_text(recipe.content, language_name)
        
        # Create translation record
        translation = RecipeTranslation(
            recipe_id=recipe_id,
            language_code=language_code,
            language_name=language_name,
            title=title_translation,
            content=content_translated,
            ingredients=ingredients_translated,
            instructions=instructions_translated
        )
        
        db.session.add(translation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Recipe translated to {language_name}',
            'translation': translation.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Translation error: {str(e)}'}), 500


@app.route('/api/recipes/<int:recipe_id>/translations/<language_code>', methods=['DELETE'])
@login_required
def delete_translation(recipe_id, language_code):
    """Delete a recipe translation."""
    try:
        from models import RecipeTranslation
        translation = RecipeTranslation.query.filter_by(
            recipe_id=recipe_id,
            language_code=language_code
        ).first()
        
        if not translation:
            return jsonify({'success': False, 'message': 'Translation not found'}), 404
        
        db.session.delete(translation)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Translation deleted'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


