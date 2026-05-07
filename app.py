#!/usr/bin/env python3
"""
Flask web application for the recipe and meal-planning app.
"""
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, session, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from werkzeug.utils import secure_filename
import os
import tempfile
import uuid
from pathlib import Path
from dotenv import load_dotenv
import requests
import json
import re

from recipe_scraper import scrape_recipe, format_recipe, RecipeScrapeError
from unit_converter import convert_to_metric
from models import db, User, Recipe, WeeklyPlan, PlanRecipe, Settings as SettingsModel, RecipeMadeHistory

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration with absolute path to persist data
# Use absolute path to avoid losing data when instance/ folder is gitignored
basedir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(basedir, 'data')
os.makedirs(data_dir, exist_ok=True)  # Ensure data directory exists

# Upload configuration
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure uploads directory exists

default_db_path = f"sqlite:///{os.path.join(data_dir, 'recipes.db')}"
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', default_db_path)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

# Initialize database
db.init_app(app)

# Helper function to add missing columns to existing tables
def add_column_if_not_exists(table_name, column_name, column_type, default_value=None):
    """Add a column to an existing table if it doesn't exist.
    Works with both SQLite and PostgreSQL."""
    from sqlalchemy import text, inspect

    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]

    if column_name not in columns:
        # Build ALTER TABLE statement
        if 'sqlite' in str(db.engine.url):
            # SQLite syntax
            default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}"
        else:
            # PostgreSQL syntax
            default_clause = f" DEFAULT {default_value}" if default_value is not None else ""
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{default_clause}"

        db.session.execute(text(sql))
        db.session.commit()
        print(f"✓ Added missing column '{column_name}' to table '{table_name}'")
        return True
    return False

# Create tables on first run
with app.app_context():
    try:
        # Create all tables (idempotent - safe to run multiple times)
        db.create_all()
        print("✓ Database tables created/verified")

        # Run migrations for any missing columns
        add_column_if_not_exists('recipes', 'nutrition', 'TEXT', 'NULL')
        add_column_if_not_exists('recipes', 'tags', 'TEXT', 'NULL')
        add_column_if_not_exists('recipes', 'ingredients_original', 'TEXT', 'NULL')
        add_column_if_not_exists('recipes', 'instructions_original', 'TEXT', 'NULL')

        # Phase 1 cleanup: drop translation table and obsolete columns once
        from migrations.phase1_cleanup import run_phase1_cleanup
        run_phase1_cleanup(db)

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
    """Import recipes from a URL or photo upload."""
    return render_template('import.html')


@app.route('/api/recipes/scrape', methods=['POST'])
@login_required
def scrape_recipe_api():
    """Fetch and parse a recipe from any URL. Returns the recipe dict for review."""
    data = request.json or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'success': False, 'message': 'URL is required'}), 400

    try:
        recipe = scrape_recipe(url)
    except RecipeScrapeError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': f'Scrape failed: {e}'}), 500

    time_info = recipe.get('time') or {}
    return jsonify({
        'success': True,
        'recipe': {
            'title': recipe.get('title', ''),
            'content': format_recipe(recipe),
            'image': recipe.get('image', ''),
            'url': url,
            'ingredients': recipe.get('ingredients', []),
            'instructions': recipe.get('instructions', []),
            'prep_time': time_info.get('prep', ''),
            'cook_time': time_info.get('cook', ''),
            'total_time': time_info.get('total', ''),
            'servings': recipe.get('yield', ''),
            'author': recipe.get('author', ''),
            'nutrition': recipe.get('nutrition', {}),
        },
    })


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


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Render admin dashboard."""
    all_users = User.query.all()
    users = [{'id': str(u.id), 'username': u.username, 'role': u.role} for u in all_users]
    return render_template('admin.html', users=users)



@app.route('/api/admin/settings', methods=['GET', 'POST'])
@admin_required
def manage_app_settings():
    """Manage non-secret app settings (default servings, week start day)."""
    if request.method == 'GET':
        return jsonify({
            'default_servings': SettingsModel.get('default_servings', '4'),
            'week_starts_on': SettingsModel.get('week_starts_on', 'monday'),
        })

    data = request.json or {}
    if 'default_servings' in data:
        SettingsModel.set('default_servings', str(data['default_servings']))
    if 'week_starts_on' in data:
        SettingsModel.set('week_starts_on', str(data['week_starts_on']))
    return jsonify({'success': True, 'message': 'Settings updated'})


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

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    # Check if user already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    # Create new user (all users are admins)
    new_user = User(username=username, role='admin')
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


@app.route('/shopping-list')
@login_required
def shopping_list_page():
    """Render shopping list page."""
    return render_template('shopping_list.html')


@app.route('/api/recipes', methods=['GET'])
@login_required
def list_recipes():
    """List all recipes."""
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return jsonify({
        'success': True,
        'recipes': [r.to_dict(include_user_rating=current_user.id) for r in recipes]
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
        'recipe': recipe.to_dict(include_user_rating=current_user.id)
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


@app.route('/api/recipes/<int:recipe_id>/rate', methods=['POST'])
@login_required
def rate_recipe(recipe_id):
    """Rate a recipe."""
    try:
        from models import RecipeRating
        from datetime import date as date_class

        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'message': 'Recipe not found'}), 404

        data = request.json
        rating_value = data.get('rating')
        notes = data.get('notes', '')
        would_make_again = data.get('would_make_again', True)
        date_cooked = data.get('date_cooked')

        # Validate rating
        if not rating_value or not isinstance(rating_value, int) or rating_value < 1 or rating_value > 5:
            return jsonify({'success': False, 'message': 'Rating must be between 1 and 5'}), 400

        # Parse date if provided
        cooked_date = None
        if date_cooked:
            try:
                cooked_date = date_class.fromisoformat(date_cooked)
            except:
                cooked_date = date_class.today()
        else:
            cooked_date = date_class.today()

        # Check if user already rated this recipe
        existing_rating = RecipeRating.query.filter_by(
            recipe_id=recipe_id,
            user_id=current_user.id
        ).first()

        if existing_rating:
            # Update existing rating
            existing_rating.rating = rating_value
            existing_rating.notes = notes
            existing_rating.would_make_again = would_make_again
            existing_rating.date_cooked = cooked_date
            existing_rating.updated_at = datetime.utcnow()
        else:
            # Create new rating
            new_rating = RecipeRating(
                recipe_id=recipe_id,
                user_id=current_user.id,
                rating=rating_value,
                notes=notes,
                would_make_again=would_make_again,
                date_cooked=cooked_date
            )
            db.session.add(new_rating)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Rating saved successfully',
            'rating': existing_rating.to_dict() if existing_rating else new_rating.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving rating: {str(e)}'}), 500


@app.route('/api/recipes/<int:recipe_id>/rating', methods=['GET'])
@login_required
def get_user_rating(recipe_id):
    """Get current user's rating for a recipe."""
    try:
        from models import RecipeRating

        recipe = Recipe.query.get(recipe_id)
        if not recipe:
            return jsonify({'success': False, 'message': 'Recipe not found'}), 404

        rating = RecipeRating.query.filter_by(
            recipe_id=recipe_id,
            user_id=current_user.id
        ).first()

        if rating:
            return jsonify({
                'success': True,
                'rating': rating.to_dict()
            })
        else:
            return jsonify({
                'success': True,
                'rating': None
            })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error getting rating: {str(e)}'}), 500


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

        # Import unit converter for metric conversion
        from unit_converter import convert_to_metric

        # Update recipe fields
        if 'title' in data:
            recipe.title = data['title']
        if 'content' in data:
            recipe.content = data['content']
        if 'ingredients' in data:
            # Store original and convert to metric
            recipe.ingredients_original = data['ingredients']
            recipe.ingredients = [convert_to_metric(ing) for ing in data['ingredients']]
        if 'instructions' in data:
            # Store original and convert to metric
            recipe.instructions_original = data['instructions']
            recipe.instructions = [convert_to_metric(inst) for inst in data['instructions']]
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
        if 'tags' in data:
            recipe.tags = data['tags']

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
            'recipe': recipe.to_dict(),
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating recipe: {str(e)}'}), 500


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/upload-image', methods=['POST'])
@login_required
def upload_image():
    """Upload a recipe image."""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image file provided'}), 400

        file = request.files['image']

        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': 'File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP'}), 400

        # Generate unique filename to avoid conflicts
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        file.save(filepath)

        # Return the URL to access the uploaded image
        image_url = url_for('static', filename=f'uploads/{filename}', _external=False)

        return jsonify({
            'success': True,
            'image_url': image_url,
            'filename': filename
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error uploading image: {str(e)}'}), 500


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
2. Language - Identify the language of the text in the image (e.g., English, French, Spanish, German, Italian, etc.)
3. Prep Time (if mentioned)
4. Cook Time (if mentioned)
5. Servings (if mentioned)
6. Ingredients (list each ingredient on a separate line)
7. Instructions (list each step on a separate line)

Format your response as JSON with this structure:
{
    "title": "Recipe Name",
    "language": "English",
    "prep_time": "15 minutes",
    "cook_time": "30 minutes",
    "servings": "4 servings",
    "ingredients": ["ingredient 1", "ingredient 2", ...],
    "instructions": ["step 1", "step 2", ...]
}

If any field is not visible in the image, omit it or leave it empty. Make sure to correctly identify the language of the recipe text."""

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

            # Include the image in the response
            recipe_data['image'] = image_data

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

        source_url = data.get('url', '')

        ingredients_original = data.get('ingredients', [])
        instructions_original = data.get('instructions', [])
        ingredients_metric = [convert_to_metric(ing) for ing in ingredients_original]
        instructions_metric = [convert_to_metric(inst) for inst in instructions_original]

        new_recipe = Recipe(
            title=data.get('title', ''),
            content=data.get('content_original', '') or data.get('content', ''),
            ingredients=ingredients_metric,
            instructions=instructions_metric,
            ingredients_original=ingredients_original,
            instructions_original=instructions_original,
            prep_time=parse_time_to_minutes(data.get('prep_time')),
            cook_time=parse_time_to_minutes(data.get('cook_time')),
            total_time=parse_time_to_minutes(data.get('total_time')),
            servings=data.get('servings', ''),
            image_url=data.get('image', ''),
            author=data.get('author', ''),
            source_url=source_url,
            nutrition=data.get('nutrition', {}),
            tags=[]
        )

        db.session.add(new_recipe)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Recipe saved successfully',
            'recipe_id': new_recipe.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving recipe: {str(e)}'}), 500


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

    # Get all recipes in the plan with servings from PlanRecipe
    plan_recipes = PlanRecipe.query.filter_by(plan_id=plan.id).all()
    recipes = []
    for pr in plan_recipes:
        if pr.recipe:
            recipe_dict = pr.recipe.to_dict()
            # Store original servings and override with PlanRecipe servings
            recipe_dict['original_servings'] = recipe_dict.get('servings')
            recipe_dict['servings'] = pr.servings
            recipe_dict['plan_recipe_id'] = pr.id  # Include for future use
            recipes.append(recipe_dict)

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


@app.route('/api/planner/mark-as-made', methods=['POST'])
@login_required
def mark_recipe_as_made():
    """Mark a recipe as made, save to history, and remove from plan."""
    from datetime import date, timedelta

    try:
        data = request.json
        recipe_id = data.get('recipe_id')

        if not recipe_id:
            return jsonify({'success': False, 'message': 'Recipe ID required'}), 400

        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Find plan for this week
        plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
        if not plan:
            return jsonify({'success': False, 'message': 'No plan found'}), 404

        # Find the plan recipe
        plan_recipe = PlanRecipe.query.filter_by(plan_id=plan.id, recipe_id=recipe_id).first()
        if not plan_recipe:
            return jsonify({'success': False, 'message': 'Recipe not in plan'}), 404

        # Create history record
        history = RecipeMadeHistory(
            recipe_id=recipe_id,
            user_id=current_user.id,
            date_made=today,
            servings=plan_recipe.servings,
            plan_recipe_id=plan_recipe.id
        )
        db.session.add(history)

        # Remove from plan
        db.session.delete(plan_recipe)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Recipe marked as made and removed from plan',
            'history_id': history.id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


@app.route('/api/planner/shopping-list', methods=['GET'])
@login_required
def get_shopping_list():
    """Generate shopping list from current week's plan."""
    from datetime import date, timedelta
    import re

    def get_recipe_ingredients(recipe):
        """Get ingredients from recipe in English (original language)."""
        # Always use original English ingredients for shopping list
        return recipe.ingredients or []

    def get_recipe_title(recipe):
        """Get recipe title in English (original language)."""
        # Always use original English title for shopping list
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


@app.route('/api/planner/shopping-list/combined', methods=['GET'])
@login_required
def get_combined_shopping_list():
    """Generate a combined/aggregated shopping list using AI to merge similar ingredients."""
    from datetime import date, timedelta

    try:
        # Get Monday of current week
        today = date.today()
        monday = today - timedelta(days=today.weekday())

        # Find plan for this week
        plan = WeeklyPlan.query.filter_by(week_start_date=monday).first()
        if not plan:
            return jsonify({'success': True, 'combined_list': [], 'by_recipe': []})

        # Get all recipes in the plan
        plan_recipes = PlanRecipe.query.filter_by(plan_id=plan.id).all()

        # Collect all ingredients with recipe context
        all_ingredients = []
        by_recipe = []

        for pr in plan_recipes:
            if pr.recipe and pr.recipe.ingredients:
                recipe_title = pr.recipe.title
                ingredients = pr.recipe.ingredients

                # Scale ingredients based on servings
                recipe_servings = 1
                if pr.recipe.servings:
                    import re
                    match = re.search(r'\d+', str(pr.recipe.servings))
                    if match:
                        recipe_servings = int(match.group(0))

                scale = pr.servings / recipe_servings if recipe_servings > 0 else 1

                for ing in ingredients:
                    all_ingredients.append({
                        'ingredient': ing,
                        'recipe': recipe_title,
                        'scale': scale
                    })

                by_recipe.append({
                    'recipe': recipe_title,
                    'servings': pr.servings,
                    'ingredients': ingredients
                })

        if not all_ingredients:
            return jsonify({'success': True, 'combined_list': [], 'by_recipe': []})

        seen = {}
        combined_list = []
        for item in all_ingredients:
            ing = (item['ingredient'] or '').strip()
            if not ing:
                continue
            key = ing.lower()
            if key not in seen:
                seen[key] = True
                combined_list.append({'item': ing, 'display': ing})

        return jsonify({
            'success': True,
            'combined_list': combined_list,
            'by_recipe': by_recipe
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error generating combined list: {str(e)}'}), 500



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)


