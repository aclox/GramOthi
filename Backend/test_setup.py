#!/usr/bin/env python3
"""
Test script to verify GramOthi backend setup
Run this script to check if everything is configured correctly
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from app.config import Base, engine, SessionLocal
        print("✅ SQLAlchemy configuration imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy configuration import failed: {e}")
        return False
    
    try:
        from app.models import User, Class, Slide, Recording, Quiz, Response, LiveSession, Poll, PollVote, DiscussionPost
        print("✅ Database models imported successfully")
    except ImportError as e:
        print(f"❌ Database models import failed: {e}")
        return False
    
    try:
        from app.schemas import UserCreate, ClassCreate, QuizCreate
        print("✅ Pydantic schemas imported successfully")
    except ImportError as e:
        print(f"❌ Pydantic schemas import failed: {e}")
        return False
    
    try:
        from app.services.auth_service import verify_password, get_password_hash
        print("✅ Authentication service imported successfully")
    except ImportError as e:
        print(f"❌ Authentication service import failed: {e}")
        return False
    
    return True

def test_database_connection():
    """Test database connection."""
    print("\n🔍 Testing database connection...")
    
    try:
        from app.config import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Make sure PostgreSQL is running and DATABASE_URL is correct in .env")
        return False

def test_file_structure():
    """Test if all required files and directories exist."""
    print("\n🔍 Testing file structure...")
    
    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/models.py",
        "app/schemas.py",
        "app/config.py",
        "app/database.py",
        "app/init_db.py",
        "app/routes/auth.py",
        "app/routes/class.py",
        "app/routes/quiz.py",
        "app/routes/live.py",
        "app/services/auth_service.py",
        "requirements.txt",
        "alembic.ini",
        "alembic/env.py",
        "alembic/script.py.mako"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files exist")
        return True

def test_environment():
    """Test environment variables."""
    print("\n🔍 Testing environment variables...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("   Please check your .env file")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def test_dependencies():
    """Test if all required packages are installed."""
    print("\n🔍 Testing dependencies...")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "alembic",
        "psycopg2-binary",
        "python-jose",
        "passlib",
        "python-multipart"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages are installed")
        return True

def main():
    """Run all tests."""
    print("🚀 GramOthi Backend Setup Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_file_structure,
        test_dependencies,
        test_environment,
        test_database_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("\n🚀 To start the server, run:")
        print("   ./start.sh")
        print("   or")
        print("   python -m app.main")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
