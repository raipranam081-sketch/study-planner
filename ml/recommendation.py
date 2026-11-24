"""
Recommendation Service Module
Loads the trained Random Forest Classifier and provides inference, confidence estimation,
human-readable explanations, and fallback logic for student study planning.
"""

import os
import logging
from datetime import datetime, date
import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "model", "study_recommender.joblib")

_model_cache = None

def get_loaded_model():
    """
    Loads and caches the Random Forest model bundle.
    Returns the model payload dictionary, or None if unavailable.
    """
    global _model_cache
    if _model_cache is not None:
        return _model_cache
        
    if os.path.exists(MODEL_PATH):
        try:
            _model_cache = joblib.load(MODEL_PATH)
            logger.info("Random Forest study recommender model loaded successfully.")
            return _model_cache
        except Exception as e:
            logger.error(f"Error loading trained ML model from {MODEL_PATH}: {e}")
            return None
    return None

def extract_features_from_subject(subject):
    """
    Extracts the 6 required model input features from a MongoDB subject document:
    1. difficulty (1 to 5)
    2. confidence (1 to 5)
    3. days_until_exam (integer >= 0)
    4. syllabus_completion (float 0 to 100)
    5. previous_score (float 0 to 100)
    6. days_since_last_studied (integer >= 0)
    """
    difficulty = int(subject.get("difficulty", 3))
    confidence = int(subject.get("confidence", 3))
    
    # Days until examination
    exam_date_val = subject.get("exam_date")
    today = date.today()
    if exam_date_val:
        if isinstance(exam_date_val, str):
            try:
                parsed_exam = datetime.strptime(exam_date_val, "%Y-%m-%d").date()
                days_until_exam = (parsed_exam - today).days
            except Exception:
                days_until_exam = 30
        elif isinstance(exam_date_val, datetime):
            days_until_exam = (exam_date_val.date() - today).days
        elif isinstance(exam_date_val, date):
            days_until_exam = (exam_date_val - today).days
        else:
            days_until_exam = 30
    else:
        days_until_exam = 30
        
    # Cap days until exam at non-negative
    days_until_exam = max(0, days_until_exam)
    
    syllabus_completion = float(subject.get("syllabus_completion", 0))
    previous_score = float(subject.get("previous_score", 60))
    
    # Days since last studied
    last_studied = subject.get("last_studied_date")
    if last_studied:
        if isinstance(last_studied, str):
            try:
                parsed_last = datetime.strptime(last_studied, "%Y-%m-%d").date()
                days_since_last_studied = (today - parsed_last).days
            except Exception:
                days_since_last_studied = 7
        elif isinstance(last_studied, datetime):
            days_since_last_studied = (today - last_studied.date()).days
        elif isinstance(last_studied, date):
            days_since_last_studied = (today - last_studied).days
        else:
            days_since_last_studied = 7
    else:
        # Default to 14 days if never studied
        days_since_last_studied = 14
        
    days_since_last_studied = max(0, days_since_last_studied)

    return {
        "difficulty": difficulty,
        "confidence": confidence,
        "days_until_exam": days_until_exam,
        "syllabus_completion": syllabus_completion,
        "previous_score": previous_score,
        "days_since_last_studied": days_since_last_studied
    }

def generate_recommendation_reason(features, priority):
    """
    Generates human-readable, context-aware educational reasoning
    explaining why the Random Forest classified the subject with this priority.
    """
    reasons = []
    
    # Exam urgency
    d_exam = features["days_until_exam"]
    if d_exam <= 3:
        reasons.append(f"Examination is imminent (in {d_exam} day{'s' if d_exam != 1 else ''})")
    elif d_exam <= 7:
        reasons.append(f"Examination is just {d_exam} days away")
    elif d_exam <= 14:
        reasons.append(f"Examination in {d_exam} days")
    elif d_exam >= 45:
        reasons.append(f"Examination is {d_exam} days away")

    # Syllabus
    syl = features["syllabus_completion"]
    if syl < 35:
        reasons.append(f"syllabus coverage is low at {syl:.0f}%")
    elif syl < 65:
        reasons.append(f"syllabus is {syl:.0f}% covered with pending topics")
    else:
        reasons.append(f"syllabus is comfortably completed ({syl:.0f}%)")

    # Difficulty & Confidence
    diff = features["difficulty"]
    conf = features["confidence"]
    if diff >= 4 and conf <= 2:
        reasons.append("high subject difficulty combined with low personal confidence")
    elif diff >= 4:
        reasons.append(f"challenging material (Difficulty {diff}/5)")
    elif conf <= 2:
        reasons.append(f"low self-rated confidence ({conf}/5)")

    # Score
    score = features["previous_score"]
    if score < 50:
        reasons.append(f"previous test score was critical ({score:.0f}%)")
    elif score < 65:
        reasons.append(f"prior score has room for improvement ({score:.0f}%)")

    # Recency
    days_since = features["days_since_last_studied"]
    if days_since >= 10:
        reasons.append(f"not reviewed in {days_since} days")
    elif days_since == 0:
        reasons.append("studied today")

    if priority == "HIGH PRIORITY":
        prefix = "High Priority: "
        if reasons:
            return prefix + "; ".join(reasons).capitalize() + ". Immediate focus recommended."
        return prefix + "Urgent review required due to approaching exam and lower progress."
        
    elif priority == "MEDIUM PRIORITY":
        prefix = "Medium Priority: "
        if reasons:
            return prefix + "; ".join(reasons).capitalize() + ". Steady practice advised."
        return prefix + "Moderate study session recommended to maintain steady learning progress."
        
    else: # LOW PRIORITY
        prefix = "Low Priority: "
        if reasons:
            return prefix + "; ".join(reasons).capitalize() + ". Revision session recommended."
        return prefix + "Good progress maintained. Brief maintenance review suggested."

def fallback_rule_recommendation(features):
    """
    Documented transparent educational fallback heuristic when ML model is unavailable.
    """
    diff = features["difficulty"]
    conf = features["confidence"]
    d_exam = features["days_until_exam"]
    syl = features["syllabus_completion"]
    score = features["previous_score"]
    days_rec = features["days_since_last_studied"]
    
    score_raw = (
        (diff / 5.0) * 20.0 +
        ((6.0 - conf) / 5.0) * 20.0 +
        (max(0.0, (30.0 - min(d_exam, 30)) / 30.0) * 25.0) +
        (((100.0 - syl) / 100.0) * 20.0) +
        (((100.0 - score) / 100.0) * 15.0) +
        (min(days_rec / 14.0, 1.0) * 10.0)
    )
    urgency = (score_raw / 110.0) * 100.0
    
    if urgency >= 56.0:
        priority = "HIGH PRIORITY"
        conf_score = round(min(80.0 + (urgency - 56) * 0.5, 98.0), 1)
    elif urgency >= 36.0:
        priority = "MEDIUM PRIORITY"
        conf_score = 85.0
    else:
        priority = "LOW PRIORITY"
        conf_score = round(min(80.0 + (36 - urgency) * 0.5, 97.0), 1)
        
    return priority, conf_score

def recommend_subject_priority(subject):
    """
    Generates a priority classification and rich metadata for a given subject.
    """
    features = extract_features_from_subject(subject)
    model_payload = get_loaded_model()
    
    if model_payload is not None:
        try:
            clf = model_payload["model"]
            feat_names = model_payload["feature_names"]
            input_vector = [features[col] for col in feat_names]
            input_df = pd.DataFrame([input_vector], columns=feat_names)
            
            # Predict class and probabilities
            pred_class = clf.predict(input_df)[0]
            classes = list(clf.classes_)
            probs = clf.predict_proba(input_df)[0]
            confidence_score = round(float(np.max(probs)) * 100.0, 1)
            priority = pred_class
            model_used = "Random Forest Classifier (Scikit-learn)"
        except Exception as e:
            logger.warning(f"Error executing Random Forest prediction, using fallback: {e}")
            priority, confidence_score = fallback_rule_recommendation(features)
            model_used = "Educational Heuristic Engine (Fallback)"
    else:
        priority, confidence_score = fallback_rule_recommendation(features)
        model_used = "Educational Heuristic Engine (Pre-trained Fallback)"

    # Recommended duration
    if priority == "HIGH PRIORITY":
        recommended_duration_mins = 90
        priority_color = "#EF4444" # red
        priority_badge = "badge-danger"
        sort_weight = 3
    elif priority == "MEDIUM PRIORITY":
        recommended_duration_mins = 60
        priority_color = "#F59E0B" # orange
        priority_badge = "badge-warning"
        sort_weight = 2
    else:
        recommended_duration_mins = 45
        priority_color = "#10B981" # green
        priority_badge = "badge-success"
        sort_weight = 1

    reason = generate_recommendation_reason(features, priority)

    return {
        "subject_id": str(subject.get("_id", "")),
        "subject_name": subject.get("name", "Untitled Subject"),
        "description": subject.get("description", ""),
        "priority": priority,
        "priority_badge": priority_badge,
        "priority_color": priority_color,
        "sort_weight": sort_weight,
        "confidence_score": confidence_score,
        "recommended_duration_mins": recommended_duration_mins,
        "recommended_duration_text": f"{recommended_duration_mins} mins",
        "reason": reason,
        "features": features,
        "days_until_exam": features["days_until_exam"],
        "syllabus_completion": features["syllabus_completion"],
        "difficulty": features["difficulty"],
        "confidence": features["confidence"],
        "previous_score": features["previous_score"],
        "model_used": model_used
    }

def get_ranked_recommendations(subjects):
    """
    Takes a list of subjects and returns them ranked with high priority first,
    sorted secondarily by days until exam ascending (soonest first) and lowest syllabus completion.
    """
    recommendations = []
    for sub in subjects:
        rec = recommend_subject_priority(sub)
        recommendations.append(rec)
        
    # Sort key:
    # 1. sort_weight descending (High=3, Medium=2, Low=1)
    # 2. days_until_exam ascending (nearest exam first)
    # 3. syllabus_completion ascending (least completed first)
    recommendations.sort(
        key=lambda r: (
            -r["sort_weight"],
            r["days_until_exam"],
            r["syllabus_completion"]
        )
    )
    return recommendations
