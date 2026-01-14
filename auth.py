"""
User authentication and management system.
"""
import json
import os
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

USERS_FILE = Path(__file__).parent / 'data' / 'users.json'


class User(UserMixin):
    """User model for authentication."""

    def __init__(self, user_id, username, role='user'):
        self.id = user_id
        self.username = username
        self.role = role

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'

    @staticmethod
    def get(user_id):
        """Get user by ID."""
        users = load_users()
        user_data = users.get(user_id)
        if user_data:
            return User(user_id, user_data['username'], user_data['role'])
        return None

    @staticmethod
    def get_by_username(username):
        """Get user by username."""
        users = load_users()
        for user_id, user_data in users.items():
            if user_data['username'] == username:
                return User(user_id, user_data['username'], user_data['role'])
        return None

    @staticmethod
    def verify_password(username, password):
        """Verify user password."""
        users = load_users()
        for user_id, user_data in users.items():
            if user_data['username'] == username:
                if check_password_hash(user_data['password'], password):
                    return User(user_id, user_data['username'], user_data['role'])
        return None

    @staticmethod
    def create(username, password, role='user'):
        """Create a new user."""
        users = load_users()

        # Check if username already exists
        for user_data in users.values():
            if user_data['username'] == username:
                return None

        # Generate new user ID
        user_id = str(max([int(uid) for uid in users.keys()] + [0]) + 1)

        # Hash password
        password_hash = generate_password_hash(password)

        # Add user
        users[user_id] = {
            'username': username,
            'password': password_hash,
            'role': role
        }

        save_users(users)
        return User(user_id, username, role)

    @staticmethod
    def list_all():
        """List all users."""
        users = load_users()
        return [
            {'id': user_id, 'username': data['username'], 'role': data['role']}
            for user_id, data in users.items()
        ]


def load_users():
    """Load users from JSON file."""
    if not USERS_FILE.exists():
        # Create default admin user
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        default_users = {
            '1': {
                'username': 'admin',
                'password': generate_password_hash('admin123'),
                'role': 'admin'
            }
        }
        save_users(default_users)
        return default_users

    with open(USERS_FILE, 'r') as f:
        return json.load(f)


def save_users(users):
    """Save users to JSON file."""
    USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def change_password(user_id, new_password):
    """Change user password."""
    users = load_users()
    if user_id in users:
        users[user_id]['password'] = generate_password_hash(new_password)
        save_users(users)
        return True
    return False


def delete_user(user_id):
    """Delete a user."""
    users = load_users()
    if user_id in users and user_id != '1':  # Prevent deleting default admin
        del users[user_id]
        save_users(users)
        return True
    return False
