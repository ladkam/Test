"""
Initialize the database and migrate existing users from auth.py.
"""
import os
from models import db, User
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def init_database(app):
    """Initialize database and create tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")

        # Migrate existing users from auth.py if they exist
        migrate_users_from_auth()

        # Ensure admin user exists
        ensure_admin_user()

        print("✓ Database initialization complete")


def migrate_users_from_auth():
    """Migrate users from auth.py JSON file to database."""
    try:
        # Import the old auth system
        from auth import User as OldUser

        # Get all users from JSON file
        old_users_data = OldUser.load_users()

        migrated_count = 0
        for user_id, user_data in old_users_data.items():
            # Check if user already exists in database
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                # Create new user in database
                new_user = User(
                    username=user_data['username'],
                    password_hash=user_data['password_hash'],
                    role=user_data['role']
                )
                db.session.add(new_user)
                migrated_count += 1

        if migrated_count > 0:
            db.session.commit()
            print(f"✓ Migrated {migrated_count} users from auth.py")
        else:
            print("✓ No users to migrate (or already migrated)")

    except Exception as e:
        print(f"! Error migrating users: {e}")
        print("  Continuing with default admin user...")


def ensure_admin_user():
    """Ensure at least one admin user exists."""
    admin = User.query.filter_by(username='admin').first()

    if not admin:
        # Create default admin user
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Created default admin user (username: admin, password: admin123)")
    else:
        print("✓ Admin user already exists")


if __name__ == '__main__':
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Initialize database
    db.init_app(app)

    # Run initialization
    init_database(app)
