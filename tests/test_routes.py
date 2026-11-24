import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import get_db

class TestAllRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.db = get_db()
        self.db.users.delete_many({})
        self.db.subjects.delete_many({})
        self.db.tasks.delete_many({})
        self.db.study_sessions.delete_many({})
        self.db.study_plans.delete_many({})

        # Create a test student and log in
        self.client.post("/register", data={
            "name": "Demo Student",
            "email": "demo@college.edu",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)

    def test_pages_render_200(self):
        routes = [
            "/dashboard",
            "/subjects",
            "/tasks",
            "/planner",
            "/recommendations",
            "/tracker",
            "/progress",
            "/api/progress_data"
        ]
        for route in routes:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200, f"Route {route} failed with status {resp.status_code}")

    def test_weekly_plan_generation(self):
        resp = self.client.post("/planner/generate", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Random Forest AI successfully generated", resp.data)

    def test_study_session_logging(self):
        # Fetch a subject
        user = self.db.users.find_one({"email": "demo@college.edu"})
        sub = self.db.subjects.find_one({"user_id": str(user["_id"])})
        resp = self.client.post("/tracker/log_session", data={
            "subject_id": str(sub["_id"]),
            "duration_mins": "45",
            "notes": "Reviewed decision tree formulas.",
            "session_date": "2026-11-22"
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Great work! Logged 45 minutes", resp.data)

if __name__ == "__main__":
    unittest.main()
