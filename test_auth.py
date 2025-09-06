#!/usr/bin/env python3
"""
Test script to debug authentication issues
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Backend'))

from Backend.app.database import get_db
from Backend.app.models import User
from Backend.app.schemas import UserCreate
from Backend.app.services.auth_service import create_user

def test_database():
    print("Testing database connection...")
    try:
        db = next(get_db())
        print("✅ Database connection successful")
        
        # Test creating a user
        user_data = UserCreate(
            name="Test User",
            email="test@example.com",
            password="password123",
            role="student"
        )
        
        print("Creating user...")
        user = create_user(db, user_data)
        print(f"✅ User created successfully: {user.email}")
        
        # Test querying users
        users = db.query(User).all()
        print(f"✅ Found {len(users)} users in database")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_database()
