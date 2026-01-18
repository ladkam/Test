"""
Database models for Recipe Translation App with multi-language support.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import JSON

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is admin."""
        return self.role == 'admin'


class Recipe(db.Model):
    """Recipe model storing ORIGINAL content only."""
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)

    # Original content (language specified in source_language)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Full text/markdown

    # Structured data (stored as JSON)
    ingredients = db.Column(JSON)  # Array of ingredient strings
    instructions = db.Column(JSON)  # Array of instruction strings

    # Metadata
    prep_time = db.Column(db.Integer)  # in minutes
    cook_time = db.Column(db.Integer)  # in minutes
    total_time = db.Column(db.Integer)  # in minutes
    servings = db.Column(db.String(100))

    # Additional info
    image_url = db.Column(db.String(1000))
    author = db.Column(db.String(200))
    source_url = db.Column(db.String(1000))
    source_language = db.Column(db.String(50), default='English')  # Language of original recipe
    nutrition = db.Column(JSON)  # Nutrition data object
    tags = db.Column(JSON)  # Array of tags/keywords

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    translations = db.relationship('RecipeTranslation', back_populates='recipe', cascade='all, delete-orphan')
    plan_recipes = db.relationship('PlanRecipe', back_populates='recipe', cascade='all, delete-orphan')

    def to_dict(self, include_translations=True):
        """Convert recipe to dictionary."""
        # Calculate health score from nutrition data
        health_score = None
        if self.nutrition:
            # Import here to avoid circular imports
            from app import calculate_health_score
            try:
                health_score = calculate_health_score(self.nutrition)
            except:
                health_score = None

        result = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'total_time': self.total_time,
            'servings': self.servings,
            'image_url': self.image_url,
            'author': self.author,
            'source_url': self.source_url,
            'source_language': self.source_language,
            'nutrition': self.nutrition,
            'health_score': health_score,
            'tags': self.tags,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if include_translations:
            result['translations'] = {
                t.language_code: t.to_dict() for t in self.translations
            }

        return result

    def get_translation(self, language_code):
        """Get a specific translation by language code."""
        for translation in self.translations:
            if translation.language_code == language_code:
                return translation
        return None


class RecipeTranslation(db.Model):
    """Translation of a recipe in a specific language."""
    __tablename__ = 'recipe_translations'

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)

    # Language info
    language_code = db.Column(db.String(10), nullable=False)  # 'es', 'fr'
    language_name = db.Column(db.String(50), nullable=False)  # 'Spanish', 'French'

    # Translated content
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text, nullable=False)
    ingredients = db.Column(JSON)  # Translated ingredients array
    instructions = db.Column(JSON)  # Translated instructions array

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    recipe = db.relationship('Recipe', back_populates='translations')

    # Unique constraint: one translation per language per recipe
    __table_args__ = (
        db.UniqueConstraint('recipe_id', 'language_code', name='uix_recipe_language'),
    )

    def to_dict(self):
        """Convert translation to dictionary."""
        return {
            'id': self.id,
            'language_code': self.language_code,
            'language_name': self.language_name,
            'title': self.title,
            'content': self.content,
            'ingredients': self.ingredients,
            'instructions': self.instructions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WeeklyPlan(db.Model):
    """Weekly meal plan."""
    __tablename__ = 'weekly_plans'

    id = db.Column(db.Integer, primary_key=True)
    week_start_date = db.Column(db.Date, nullable=False, unique=True)  # Monday of the week
    notes = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan_recipes = db.relationship('PlanRecipe', back_populates='weekly_plan', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert plan to dictionary."""
        return {
            'id': self.id,
            'week_start_date': self.week_start_date.isoformat(),
            'notes': self.notes,
            'recipes': [pr.to_dict() for pr in self.plan_recipes],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PlanRecipe(db.Model):
    """Junction table linking recipes to weekly plans."""
    __tablename__ = 'plan_recipes'

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('weekly_plans.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 1=Monday, 7=Sunday
    meal_order = db.Column(db.Integer, default=0)  # Order within the day
    servings = db.Column(db.Integer, default=1)  # Number of servings for this meal
    notes = db.Column(db.Text)

    # Relationships
    weekly_plan = db.relationship('WeeklyPlan', back_populates='plan_recipes')
    recipe = db.relationship('Recipe', back_populates='plan_recipes')

    def to_dict(self):
        """Convert plan recipe to dictionary."""
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'recipe_id': self.recipe_id,
            'day_of_week': self.day_of_week,
            'meal_order': self.meal_order,
            'servings': self.servings,
            'notes': self.notes,
            'recipe': self.recipe.to_dict() if self.recipe else None
        }


class Settings(db.Model):
    """Application settings and configuration."""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get(key, default=None):
        """Get a setting value by key."""
        setting = Settings.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value):
        """Set a setting value by key."""
        setting = Settings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            setting.updated_at = datetime.utcnow()
        else:
            setting = Settings(key=key, value=value)
            db.session.add(setting)
        db.session.commit()
        return setting
