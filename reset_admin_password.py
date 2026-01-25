#!/usr/bin/env python3
"""
Reset admin user password
Usage: python reset_admin_password.py [new_password]
If no password is provided, it will reset to 'admin123'
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Flask app and models
from app import app, db
from models import User

def reset_admin_password(new_password='admin123'):
    """Reset the admin user password."""
    with app.app_context():
        # Find admin user
        admin = User.query.filter_by(username='admin').first()

        if not admin:
            print("❌ Admin user not found!")
            print("Creating new admin user...")
            admin = User(username='admin', role='admin')
            admin.set_password(new_password)
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Created admin user with password: {new_password}")
        else:
            # Reset password
            admin.set_password(new_password)
            db.session.commit()
            print(f"✅ Admin password reset successfully!")
            print(f"   Username: admin")
            print(f"   Password: {new_password}")

if __name__ == '__main__':
    # Get password from command line argument or use default
    new_password = sys.argv[1] if len(sys.argv) > 1 else 'admin123'

    print("Resetting admin password...")
    reset_admin_password(new_password)
