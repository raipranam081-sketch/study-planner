import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from db import get_db

class TestSubjectsAndTasks(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.db = get_db()
        self.db.users.delete_many({})
        self.db.subjects.delete_many({})
        self.db.tasks.delete_many({})

    def tearDown(self):
        self.db.users.delete_many({})
        self.db.subjects.delete_many({})
        self.db.tasks.delete_many({})

    def _register_user(self, name, email):
        self.client.post("/register", data={
            "name": name,
            "email": email,
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)
        user = self.db.users.find_one({"email": email})
        return str(user["_id"])

    def test_subject_crud_and_isolation(self):
        # Register User 1
        user1_id = self._register_user("Alice", "alice@college.edu")

        # Add custom subject for User 1
        add_resp = self.client.post("/subjects/add", data={
            "name": "Cloud Computing",
            "description": "Virtualization and Docker",
            "exam_date": "2026-12-10",
            "difficulty": "4",
            "confidence": "2",
            "syllabus_completion": "35",
            "previous_score": "58",
            "last_studied_date": "2026-11-15"
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)

        subject = self.db.subjects.find_one({"user_id": user1_id, "name": "Cloud Computing"})
        self.assertIsNotNone(subject)
        sub_id = str(subject["_id"])

        # Edit subject
        edit_resp = self.client.post(f"/subjects/{sub_id}/edit", data={
            "name": "Advanced Cloud Computing",
            "description": "Kubernetes and Microservices",
            "exam_date": "2026-12-15",
            "difficulty": "5",
            "confidence": "3",
            "syllabus_completion": "50",
            "previous_score": "70",
            "last_studied_date": "2026-11-20"
        }, follow_redirects=True)
        self.assertIn(b"Advanced Cloud Computing", edit_resp.data)

        updated_sub = self.db.subjects.find_one({"_id": subject["_id"]})
        self.assertEqual(updated_sub["name"], "Advanced Cloud Computing")
        self.assertEqual(updated_sub["difficulty"], 5)

        # Logout User 1 and register User 2
        self.client.get("/logout")
        user2_id = self._register_user("Bob", "bob@college.edu")

        # User 2 views subjects -> should NOT see Alice's Advanced Cloud Computing
        u2_page = self.client.get("/subjects")
        self.assertNotIn(b"Advanced Cloud Computing", u2_page.data)

        # User 2 tries to delete Alice's subject -> should be blocked
        malicious_del = self.client.post(f"/subjects/{sub_id}/delete", follow_redirects=True)
        self.assertIn(b"Subject not found or access denied", malicious_del.data)

        # Switch back to Alice and delete subject
        self.client.get("/logout")
        self.client.post("/login", data={"email": "alice@college.edu", "password": "password123"}, follow_redirects=True)
        del_resp = self.client.post(f"/subjects/{sub_id}/delete", follow_redirects=True)
        self.assertIn(b"deleted successfully", del_resp.data)

    def test_task_management(self):
        user_id = self._register_user("Charlie", "charlie@college.edu")

        # Add task
        add_task_resp = self.client.post("/tasks/add", data={
            "title": "Solve 10 SQL practice queries",
            "subject_id": "",
            "description": "Subqueries and joins",
            "due_date": "2026-11-30",
            "duration_mins": "60"
        }, follow_redirects=True)
        self.assertEqual(add_task_resp.status_code, 200)

        task = self.db.tasks.find_one({"user_id": user_id, "title": "Solve 10 SQL practice queries"})
        self.assertIsNotNone(task)
        task_id = str(task["_id"])
        self.assertEqual(task["status"], "Pending")

        # Toggle task via AJAX
        toggle_resp = self.client.post(f"/tasks/{task_id}/toggle", headers={"X-Requested-With": "XMLHttpRequest"})
        data = toggle_resp.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["new_status"], "Completed")

        updated_task = self.db.tasks.find_one({"_id": task["_id"]})
        self.assertEqual(updated_task["status"], "Completed")

if __name__ == "__main__":
    unittest.main()
