"""
Database models for Recipe Management System.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model for authentication."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'

    def set_password(self, password):
        """Hash and set password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if password matches hash."""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """Check if user is admin."""
        return self.role == 'admin'


class Recipe(db.Model):
    """Recipe model storing both original and translated versions."""
    __tablename__ = 'recipes'

    id = db.Column(db.Integer, primary_key=True)

    # Titles
    title_original = db.Column(db.String(500), nullable=False)
    title_translated = db.Column(db.String(500))

    # Full content (markdown format)
    content_original = db.Column(db.Text, nullable=False)
    content_translated = db.Column(db.Text)

    # Structured data (stored as JSON)
    ingredients_original = db.Column(JSON)  # Array of ingredient strings
    ingredients_translated = db.Column(JSON)
    instructions_original = db.Column(JSON)  # Array of instruction strings
    instructions_translated = db.Column(JSON)

    # Metadata
    prep_time = db.Column(db.Integer)  # in minutes
    cook_time = db.Column(db.Integer)  # in minutes
    total_time = db.Column(db.Integer)  # in minutes
    servings = db.Column(db.String(100))

    # Additional info
    image_url = db.Column(db.String(1000))
    author = db.Column(db.String(200))
    source_url = db.Column(db.String(1000))
    nutrition = db.Column(JSON)  # Nutrition data object
    tags = db.Column(JSON)  # Array of tags/keywords
    language = db.Column(db.String(50))  # Target language

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    plan_recipes = db.relationship('PlanRecipe', back_populates='recipe', cascade='all, delete-orphan')

    def to_dict(self):
        """Convert recipe to dictionary."""
        return {
            'id': self.id,
            'title_original': self.title_original,
            'title_translated': self.title_translated,
            'content_original': self.content_original,
            'content_translated': self.content_translated,
            'ingredients_original': self.ingredients_original,
            'ingredients_translated': self.ingredients_translated,
            'instructions_original': self.instructions_original,
            'instructions_translated': self.instructions_translated,
            'prep_time': self.prep_time,
            'cook_time': self.cook_time,
            'total_time': self.total_time,
            'servings': self.servings,
            'image_url': self.image_url,
            'author': self.author,
            'source_url': self.source_url,
            'nutrition': self.nutrition,
            'tags': self.tags,
            'language': self.language,
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
        """Convert weekly plan to dictionary."""
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
