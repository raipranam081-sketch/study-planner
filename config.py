import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "college_study_planner_fallback_secret_key_2026")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "study_planner")
    USE_MOCK_IF_NO_MONGO = os.getenv("USE_MOCK_IF_NO_MONGO", "True").lower() in ("true", "1", "yes")
    
    # Model path
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    MODEL_DIR = os.path.join(BASE_DIR, "ml", "model")
    MODEL_PATH = os.path.join(MODEL_DIR, "study_recommender.joblib")
    DATA_PATH = os.path.join(BASE_DIR, "data", "training_data.csv")
    
    # Session config
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
