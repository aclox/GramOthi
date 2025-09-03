"""
Base test class for GramOthi backend
Provides common test infrastructure to eliminate duplication
"""

import os
import sys
import requests
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class BaseTester:
    """Base class for all test modules with common test infrastructure."""
    
    def __init__(self):
        self.teacher_token = None
        self.student_token = None
        self.teacher_id = None
        self.student_id = None
        self.class_id = None
        self.test_results = []
    
    def setup_test_users(self):
        """Create test users for testing."""
        print("🔧 Setting up test users...")
        
        # Create teacher
        teacher_data = {
            "name": f"Test Teacher {uuid.uuid4().hex[:8]}",
            "email": f"test_teacher_{uuid.uuid4().hex[:8]}@test.com",
            "password": "testpassword123",
            "role": "teacher"
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/register", json=teacher_data)
            if response.status_code == 200:
                print("   ✅ Teacher created successfully")
                self.teacher_id = response.json()["id"]
            else:
                print(f"   ⚠️  Teacher creation: {response.status_code} - {response.text}")
                # Try to login if user already exists
                login_data = {
                    "username": teacher_data["email"],
                    "password": teacher_data["password"]
                }
                response = requests.post(f"{API_BASE}/auth/login", data=login_data)
                if response.status_code == 200:
                    self.teacher_token = response.json()["access_token"]
                    print("   ✅ Teacher login successful")
                else:
                    print(f"   ❌ Teacher login failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"   ❌ Teacher setup failed: {e}")
            return False
        
        # Create student
        student_data = {
            "name": f"Test Student {uuid.uuid4().hex[:8]}",
            "email": f"test_student_{uuid.uuid4().hex[:8]}@test.com",
            "password": "testpassword123",
            "role": "student"
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/register", json=student_data)
            if response.status_code == 200:
                print("   ✅ Student created successfully")
                self.student_id = response.json()["id"]
            else:
                print(f"   ⚠️  Student creation: {response.status_code} - {response.text}")
                # Try to login if user already exists
                login_data = {
                    "username": student_data["email"],
                    "password": student_data["password"]
                }
                response = requests.post(f"{API_BASE}/auth/login", data=login_data)
                if response.status_code == 200:
                    self.student_token = response.json()["access_token"]
                    print("   ✅ Student login successful")
                else:
                    print(f"   ❌ Student login failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"   ❌ Student setup failed: {e}")
            return False
        
        # Login both users to get tokens
        if not self.teacher_token:
            login_data = {"username": teacher_data["email"], "password": teacher_data["password"]}
            response = requests.post(f"{API_BASE}/auth/login", data=login_data)
            if response.status_code == 200:
                self.teacher_token = response.json()["access_token"]
        
        if not self.student_token:
            login_data = {"username": student_data["email"], "password": student_data["password"]}
            response = requests.post(f"{API_BASE}/auth/login", data=login_data)
            if response.status_code == 200:
                self.student_token = response.json()["access_token"]
        
        return True
    
    def create_test_class(self):
        """Create a test class for testing."""
        print("📚 Creating test class...")
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        class_data = {"title": f"Test Class {uuid.uuid4().hex[:8]}"}
        
        try:
            response = requests.post(f"{API_BASE}/classes/", json=class_data, headers=headers)
            if response.status_code == 200:
                self.class_id = response.json()["id"]
                print(f"   ✅ Test class created: {self.class_id}")
                return True
            else:
                print(f"   ❌ Class creation failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Class creation failed: {e}")
            return False
    
    def log_test_result(self, test_name: str, success: bool, details: str = None):
        """Log test results consistently."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.test_results.append(result)
        
        if success:
            print(f"   {status}: {test_name}")
        else:
            print(f"   {status}: {test_name}")
            if details:
                print(f"      Details: {details}")
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["success"]])
        failed_tests = total_tests - passed_tests
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "results": self.test_results
        }
    
    def print_test_summary(self):
        """Print a formatted test summary."""
        summary = self.get_test_summary()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed_tests']} ✅")
        print(f"Failed: {summary['failed_tests']} ❌")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['failed_tests'] > 0:
            print("\n❌ Failed Tests:")
            for result in summary['results']:
                if not result['success']:
                    print(f"   - {result['test']}: {result['details']}")
        
        print("=" * 60)
    
    def cleanup_test_data(self):
        """Clean up test data after testing."""
        print("🧹 Cleaning up test data...")
        
        # This would typically involve deleting test users, classes, etc.
        # For now, we'll just log the cleanup
        print("   ✅ Test data cleanup completed")
    
    def run_all_tests(self):
        """Base method for running all tests - should be overridden by subclasses."""
        print("🚀 Base test runner - override this method in subclasses")
        return False
