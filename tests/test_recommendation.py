import unittest
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.recommendation import (
    extract_features_from_subject,
    recommend_subject_priority,
    get_ranked_recommendations,
    fallback_rule_recommendation,
    generate_recommendation_reason
)

class TestMLRecommendation(unittest.TestCase):
    def test_feature_extraction(self):
        today = date.today()
        exam_date_str = (today + timedelta(days=5)).strftime("%Y-%m-%d")
        last_studied_str = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        subject = {
            "name": "Compiler Design",
            "difficulty": 4,
            "confidence": 2,
            "exam_date": exam_date_str,
            "syllabus_completion": 30.0,
            "previous_score": 45.0,
            "last_studied_date": last_studied_str
        }

        features = extract_features_from_subject(subject)
        self.assertEqual(features["difficulty"], 4)
        self.assertEqual(features["confidence"], 2)
        self.assertEqual(features["days_until_exam"], 5)
        self.assertEqual(features["syllabus_completion"], 30.0)
        self.assertEqual(features["previous_score"], 45.0)
        self.assertEqual(features["days_since_last_studied"], 7)

    def test_high_priority_prediction(self):
        # Critical subject: exam in 3 days, hard, low confidence, low syllabus completion
        today = date.today()
        subject_urgent = {
            "name": "Design & Analysis of Algorithms",
            "difficulty": 5,
            "confidence": 1,
            "exam_date": (today + timedelta(days=3)).strftime("%Y-%m-%d"),
            "syllabus_completion": 25.0,
            "previous_score": 42.0,
            "last_studied_date": (today - timedelta(days=12)).strftime("%Y-%m-%d")
        }

        rec = recommend_subject_priority(subject_urgent)
        self.assertEqual(rec["priority"], "HIGH PRIORITY")
        self.assertEqual(rec["priority_color"], "#EF4444")
        self.assertGreaterEqual(rec["confidence_score"], 50.0)
        self.assertIn("High Priority", rec["reason"])
        self.assertEqual(rec["recommended_duration_mins"], 90)

    def test_low_priority_prediction(self):
        # Relaxed subject: exam in 50 days, high syllabus completion, high confidence
        today = date.today()
        subject_relaxed = {
            "name": "Environmental Science",
            "difficulty": 1,
            "confidence": 5,
            "exam_date": (today + timedelta(days=50)).strftime("%Y-%m-%d"),
            "syllabus_completion": 95.0,
            "previous_score": 90.0,
            "last_studied_date": (today - timedelta(days=1)).strftime("%Y-%m-%d")
        }

        rec = recommend_subject_priority(subject_relaxed)
        self.assertEqual(rec["priority"], "LOW PRIORITY")
        self.assertEqual(rec["priority_color"], "#10B981")
        self.assertIn("Low Priority", rec["reason"])

    def test_ranked_recommendations_sorting(self):
        today = date.today()
        subjects = [
            {
                "name": "Easy Course",
                "difficulty": 1,
                "confidence": 5,
                "exam_date": (today + timedelta(days=40)).strftime("%Y-%m-%d"),
                "syllabus_completion": 90.0,
                "previous_score": 88.0,
                "last_studied_date": (today - timedelta(days=2)).strftime("%Y-%m-%d")
            },
            {
                "name": "Urgent Course",
                "difficulty": 5,
                "confidence": 2,
                "exam_date": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
                "syllabus_completion": 30.0,
                "previous_score": 48.0,
                "last_studied_date": (today - timedelta(days=10)).strftime("%Y-%m-%d")
            },
            {
                "name": "Medium Course",
                "difficulty": 3,
                "confidence": 3,
                "exam_date": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
                "syllabus_completion": 60.0,
                "previous_score": 70.0,
                "last_studied_date": (today - timedelta(days=4)).strftime("%Y-%m-%d")
            }
        ]

        ranked = get_ranked_recommendations(subjects)
        # First item should be the urgent high priority course
        self.assertEqual(ranked[0]["subject_name"], "Urgent Course")
        self.assertEqual(ranked[0]["priority"], "HIGH PRIORITY")

    def test_fallback_heuristic_engine(self):
        # Ensure fallback returns valid priority even if ML model was somehow unloaded
        features = {
            "difficulty": 5,
            "confidence": 1,
            "days_until_exam": 2,
            "syllabus_completion": 20.0,
            "previous_score": 40.0,
            "days_since_last_studied": 14
        }
        priority, conf = fallback_rule_recommendation(features)
        self.assertEqual(priority, "HIGH PRIORITY")
        self.assertGreater(conf, 50.0)

if __name__ == "__main__":
    unittest.main()
