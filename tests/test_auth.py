import unittest
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import get_db

class TestAuth(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()
        self.db = get_db()
        # Clean users collection in test
        self.db.users.delete_many({})

    def tearDown(self):
        self.db.users.delete_many({})

    def test_registration_and_login(self):
        # 1. Register new user
        reg_response = self.client.post("/register", data={
            "name": "Jane Doe",
            "email": "jane@college.edu",
            "password": "securepassword123",
            "confirm_password": "securepassword123"
        }, follow_redirects=True)
        self.assertEqual(reg_response.status_code, 200)
        self.assertIn(b"Welcome to Student Study Planner", reg_response.data)

        # 2. Check user exists in database with hashed password
        user = self.db.users.find_one({"email": "jane@college.edu"})
        self.assertIsNotNone(user)
        self.assertNotEqual(user["password"], "securepassword123")
        self.assertTrue(user["password"].startswith("$2b$")) # bcrypt hash

        # 3. Logout before testing duplicate registration
        logout_response = self.client.get("/logout", follow_redirects=True)
        self.assertIn(b"logged out", logout_response.data)

        # 4. Prevent duplicate email registration
        dup_response = self.client.post("/register", data={
            "name": "Jane Copy",
            "email": "jane@college.edu",
            "password": "password456",
            "confirm_password": "password456"
        }, follow_redirects=True)
        self.assertIn(b"already exists", dup_response.data)

        # 5. Login with correct credentials
        login_response = self.client.post("/login", data={
            "email": "jane@college.edu",
            "password": "securepassword123"
        }, follow_redirects=True)
        self.assertIn(b"Welcome back, Jane Doe!", login_response.data)

        # 6. Login with incorrect password
        self.client.get("/logout")
        bad_login = self.client.post("/login", data={
            "email": "jane@college.edu",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertIn(b"Invalid email or password", bad_login.data)

    def test_unauthorized_dashboard_access(self):
        # Visiting dashboard without session should redirect to login
        response = self.client.get("/dashboard", follow_redirects=True)
        self.assertIn(b"Please log in to access this page", response.data)

if __name__ == "__main__":
    unittest.main()
