"""
Random Forest Model Training Module
Student Study Planner with Machine Learning Recommendation

This module generates a reproducible synthetic training dataset based on transparent educational
urgency heuristics and trains a Random Forest Classifier to categorize subjects into:
- HIGH PRIORITY
- MEDIUM PRIORITY
- LOW PRIORITY
"""

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import joblib

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "ml", "model")
DATA_FILE = os.path.join(DATA_DIR, "training_data.csv")
MODEL_FILE = os.path.join(MODEL_DIR, "study_recommender.joblib")

FEATURE_NAMES = [
    "difficulty",
    "confidence",
    "days_until_exam",
    "syllabus_completion",
    "previous_score",
    "days_since_last_studied"
]

def calculate_urgency_score(diff, conf, days_exam, syl_comp, score, days_studied):
    """
    Transparent educational urgency heuristic formula:
    - Higher difficulty increases urgency (up to 20 pts)
    - Lower confidence increases urgency (up to 20 pts)
    - Imminent examination increases urgency (up to 25 pts)
    - Incomplete syllabus increases urgency (up to 20 pts)
    - Lower prior exam score increases urgency (up to 15 pts)
    - Longer days without studying increases urgency (up to 10 pts)
    """
    # 1. Difficulty component (1 to 5) -> 0 to 20
    diff_comp = (diff / 5.0) * 20.0
    
    # 2. Confidence gap component (1 to 5) -> 0 to 20
    conf_comp = ((6.0 - conf) / 5.0) * 20.0
    
    # 3. Exam proximity component (days remaining) -> 0 to 25
    # Closest exam (< 7 days) gets highest score; > 45 days gets ~0
    if days_exam <= 5:
        exam_comp = 25.0
    elif days_exam <= 14:
        exam_comp = 20.0 + (14 - days_exam) / 9.0 * 5.0
    elif days_exam <= 30:
        exam_comp = 10.0 + (30 - days_exam) / 16.0 * 10.0
    elif days_exam <= 60:
        exam_comp = max(0.0, (60 - days_exam) / 30.0 * 10.0)
    else:
        exam_comp = 0.0

    # 4. Syllabus completion gap -> 0 to 20
    syl_comp_score = ((100.0 - syl_comp) / 100.0) * 20.0
    
    # 5. Prior performance deficit -> 0 to 15
    score_comp = ((100.0 - score) / 100.0) * 15.0
    
    # 6. Recency gap (days since last studied) -> 0 to 10
    recency_comp = min(days_studied / 14.0, 1.0) * 10.0

    raw_urgency = diff_comp + conf_comp + exam_comp + syl_comp_score + score_comp + recency_comp
    # Scale from max ~110 down to 100
    normalized_score = (raw_urgency / 110.0) * 100.0
    return normalized_score

def generate_synthetic_dataset(num_samples=1200, random_seed=42):
    """
    Generates a reproducible dataset simulating diverse student study profiles.
    Documented transparently for academic mini-project criteria.
    """
    np.random.seed(random_seed)
    
    difficulties = np.random.choice([1, 2, 3, 4, 5], size=num_samples, p=[0.12, 0.23, 0.35, 0.20, 0.10])
    confidences = np.random.choice([1, 2, 3, 4, 5], size=num_samples, p=[0.15, 0.25, 0.30, 0.20, 0.10])
    
    # Days until exam: clustered around upcoming periods (3 to 60 days)
    days_until_exam = np.random.exponential(scale=18, size=num_samples).astype(int) + 1
    days_until_exam = np.clip(days_until_exam, 1, 90)
    
    # Syllabus completion %: 0 to 100
    syllabus_completion = np.random.beta(a=3, b=2, size=num_samples) * 100.0
    syllabus_completion = np.clip(syllabus_completion.round(1), 0.0, 100.0)
    
    # Previous test scores: normal distribution around 68 with std 18
    previous_scores = np.random.normal(loc=68, scale=18, size=num_samples)
    previous_scores = np.clip(previous_scores.round(1), 10.0, 100.0)
    
    # Days since last studied: 0 to 25
    days_since_studied = np.random.geometric(p=0.25, size=num_samples) - 1
    days_since_studied = np.clip(days_since_studied, 0, 30)
    
    records = []
    for i in range(num_samples):
        d = int(difficulties[i])
        c = int(confidences[i])
        de = int(days_until_exam[i])
        sc = float(syllabus_completion[i])
        ps = float(previous_scores[i])
        ds = int(days_since_studied[i])
        
        urgency = calculate_urgency_score(d, c, de, sc, ps, ds)
        # Add slight natural Gaussian noise
        urgency_noisy = urgency + np.random.normal(0, 2.5)
        
        if urgency_noisy >= 58.0:
            priority = "HIGH PRIORITY"
        elif urgency_noisy >= 36.0:
            priority = "MEDIUM PRIORITY"
        else:
            priority = "LOW PRIORITY"
            
        records.append({
            "difficulty": d,
            "confidence": c,
            "days_until_exam": de,
            "syllabus_completion": sc,
            "previous_score": ps,
            "days_since_last_studied": ds,
            "urgency_score": round(urgency, 2),
            "priority": priority
        })
        
    df = pd.DataFrame(records)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(DATA_FILE, index=False)
    print(f"Dataset generated with {num_samples} records saved to: {DATA_FILE}")
    print("Class distribution:\n", df["priority"].value_counts(normalize=True).round(3))
    return df

def train_random_forest():
    """
    Trains and validates the Random Forest Classifier, then saves the serialized model bundle.
    """
    if not os.path.exists(DATA_FILE):
        df = generate_synthetic_dataset()
    else:
        df = pd.read_csv(DATA_FILE)
        
    X = df[FEATURE_NAMES]
    y = df["priority"]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    clf = RandomForestClassifier(
        n_estimators=70,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        n_jobs=1,
        random_state=42
    )
    
    print("\nTraining Random Forest Classifier on study data...")
    clf.fit(X_train, y_train)
    
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print("\n================ MODEL EVALUATION METRICS ================")
    print(f"Test Accuracy: {accuracy * 100:.2f}%\n")
    print("Classification Report:")
    report = classification_report(y_test, y_pred)
    print(report)
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    print("==========================================================\n")
    
    # Feature importances
    feature_importance_dict = dict(zip(FEATURE_NAMES, clf.feature_importances_))
    print("Feature Importances:")
    for feat, imp in sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {feat:25s}: {imp:.4f} ({imp*100:.1f}%)")
        
    os.makedirs(MODEL_DIR, exist_ok=True)
    model_payload = {
        "model": clf,
        "feature_names": FEATURE_NAMES,
        "classes": list(clf.classes_),
        "accuracy": accuracy,
        "feature_importances": feature_importance_dict
    }
    
    joblib.dump(model_payload, MODEL_FILE)
    print(f"\nTrained model successfully serialized to: {MODEL_FILE}")
    return clf, accuracy

if __name__ == "__main__":
    generate_synthetic_dataset()
    train_random_forest()
