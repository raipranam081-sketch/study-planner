# Student Study Planner Using Random Forest Recommendation

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-indigo.svg)](https://palletsprojects.com/p/flask/)
[![MongoDB](https://img.shields.io/badge/Database-MongoDB-green.svg)](https://www.mongodb.com/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Random%20Forest-orange.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

An intelligent, full-stack college mini-project web application designed to help university and college students manage subjects, organize assignments, track study sessions, and receive **machine-learning-driven study recommendations** using a trained **Random Forest Classifier**.

---

## 📌 Project Overview & Objectives

College students routinely balance multiple challenging courses, laboratory assessments, assignments, and examinations. Without structured guidance, students struggle to prioritize which subject needs immediate attention versus which can be maintained with lighter revision.

### Project Objectives:
1. **Intelligent Prioritization**: Deploy a genuine Random Forest model to analyze multi-variable academic parameters and classify subject study priority into `HIGH PRIORITY`, `MEDIUM PRIORITY`, and `LOW PRIORITY`.
2. **Automated Weekly Study Timetable**: Automatically generate a balanced Monday-to-Sunday study timetable pairing prioritized courses with specific pending academic tasks.
3. **Productive Study Tracking**: Provide an integrated focus stopwatch and session logger that updates course review history and syllabus completion metrics in real time.
4. **Visual Analytics**: Render dynamic performance charts (Chart.js) illustrating subject distribution, weekly study hour trends, task completion rates, and syllabus coverage.
5. **Secure Multi-User Portal**: Implement password hashing with `bcrypt`, session state management, and strict student data isolation within MongoDB.

---

## 🛠️ Technology Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Jinja2 | Responsive modern dashboard, custom design system (Blue/Purple/White), modal dialogs, and AJAX state handlers. |
| **Icons & Visualization** | FontAwesome 6, Chart.js 4.4 | Vector iconography and interactive data visualizers (Doughnut, Bar, Pie charts). |
| **Backend** | Python, Flask 3.x | Lightweight, high-performance WSGI web application framework. |
| **Database** | MongoDB / PyMongo | Document-oriented NoSQL database supporting flexible schemas and BSON ObjectIds. |
| **Machine Learning** | Random Forest Classifier, Scikit-learn | Multi-tree ensemble learning with feature importance calculation and probability confidence scoring. |
| **Data Processing** | Pandas, NumPy, Joblib | Dataframe manipulation, array mathematical operations, and serialized model persistence. |
| **Security** | Bcrypt, Python-Dotenv | Cryptographic salt-hashed password authentication and environment variable separation. |

---

## 🧠 Random Forest Machine Learning Model

### 1. Six Multi-Dimensional Input Features:
The recommendation engine inspects 6 essential student parameters for each subject:
1. **Subject Difficulty** (`1 to 5`): Student's self-assessed difficulty level.
2. **Student Confidence** (`1 to 5`): Student's mastery/comfort level with course concepts.
3. **Days Remaining Until Examination** (`integer >= 0`): Computed from examination date vs. current date.
4. **Syllabus Completion Percentage** (`0.0% to 100.0%`): Progress through required syllabus chapters.
5. **Previous Quiz / Test Score** (`0.0% to 100.0%`): Historical performance indicating vulnerability.
6. **Days Since Subject Was Last Studied** (`integer >= 0`): Recency gap indicating revision decay.

### 2. Output Classifications:
* 🔴 **HIGH PRIORITY**: Approaching examination (< 14 days), low syllabus coverage (< 50%), high difficulty, low confidence, or neglected revision (> 7 days). Recommends **90 - 120 minutes** deep-work session.
* 🟡 **MEDIUM PRIORITY**: Moderate examination urgency (14 - 30 days), moderate progress, average test scores. Recommends **60 minutes** practice session.
* 🟢 **LOW PRIORITY**: Far examination (> 30 days), high syllabus completion (> 75%), high confidence and strong previous score. Recommends **30 - 45 minutes** maintenance revision.

### 3. Model Training & Synthetic Dataset:
* **Training Script**: Located at [`ml/train_model.py`](file:///c:/Users/pranam%20rai/OneDrive/Desktop/study%20planner/ml/train_model.py).
* **Dataset**: [`data/training_data.csv`](file:///c:/Users/pranam%20rai/OneDrive/Desktop/study%20planner/data/training_data.csv) containing 1,200 reproducible synthetic student profiles generated via a transparent, multi-factor educational urgency formula.
* **Model Serialization**: Saved as [`ml/model/study_recommender.joblib`](file:///c:/Users/pranam%20rai/OneDrive/Desktop/study%20planner/ml/model/study_recommender.joblib).
* **Fault-Tolerant Heuristic Fallback**: If the model file is not present or an edge case occurs, [`ml/recommendation.py`](file:///c:/Users/pranam%20rai/OneDrive/Desktop/study%20planner/ml/recommendation.py) executes a transparent educational heuristic rule engine, ensuring zero downtime.

---

## 🗄️ MongoDB Database Architecture

The application uses MongoDB collections structured with user scoping:

```
study_planner/
├── users               # Stores student name, email, salt-hashed bcrypt password, created_at
├── subjects            # user_id, name, description, exam_date, difficulty, confidence,
│                       # syllabus_completion, previous_score, last_studied_date
├── tasks               # user_id, subject_id, subject_name, title, description, due_date,
│                       # duration_mins, status ("Pending" / "Completed")
├── study_sessions      # user_id, subject_id, subject_name, duration_mins, notes,
│                       # session_date, created_at
└── study_plans         # user_id, day ("Monday"..."Sunday"), sessions array
```

> **Note on Database Connection**:
> The application automatically attempts to connect to MongoDB (`mongodb://localhost:27017/` or MongoDB Atlas URI set in `.env`). If your MongoDB server is offline, the application seamlessly activates an **in-memory database fallback (`mongomock`)**, allowing you to present and test all features instantly without system errors.

---

## 📂 Project Directory Structure

```
student-study-planner/
│
├── app.py                      # Flask backend application routes and controllers
├── config.py                   # Central configuration & environment variables
├── db.py                       # PyMongo client, connection verification & index setup
├── requirements.txt            # Python dependencies specification
├── .env.example                # Template for environment variables
├── .env                        # Local active environment configuration
├── README.md                   # Comprehensive project documentation
│
├── ml/                         # Machine Learning subsystem
│   ├── train_model.py          # Synthetic dataset generator & Random Forest training
│   ├── recommendation.py       # Inference, confidence score & reasoning generator
│   └── model/
│       └── study_recommender.joblib  # Serialized trained model bundle
│
├── data/
│   └── training_data.csv       # Reproducible training dataset (1,200 samples)
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Responsive layout with modern sidebar navigation
│   ├── index.html              # Landing page presenting features and tech stack
│   ├── login.html              # Student authentication login form
│   ├── register.html           # New student account registration
│   ├── dashboard.html          # Dynamic statistics, upcoming exams & AI priority preview
│   ├── subjects.html           # Subject management CRUD modal interface
│   ├── tasks.html              # Academic tasks and assignment tracking with AJAX toggle
│   ├── planner.html            # 7-day weekly timetable with automated plan generator
│   ├── recommendations.html    # Detailed Random Forest predictions & rationale
│   ├── tracker.html            # Live focus stopwatch & study session logging
│   └── progress.html           # Dynamic Chart.js progress analytics and history
│
├── static/                     # Static assets
│   ├── css/
│   │   └── style.css           # Professional blue/purple/white design system
│   └── js/
│       └── main.js             # Timer logic, AJAX toggles, modal dialogs, Chart.js
│
└── tests/                      # Automated test suite
    ├── test_auth.py            # Registration, login, duplicate detection, auth protection
    ├── test_subjects.py        # Subject CRUD, task management & data isolation
    ├── test_recommendation.py  # Model inference, priority ranking & heuristic fallback
    └── test_routes.py          # End-to-end HTTP route validation
```

---

## 🚀 Setup & Running Instructions (Windows Friendly)

### Step 1: Open Terminal in Project Directory
Open PowerShell or Command Prompt in the project folder:
```powershell
cd "c:\Users\pranam rai\OneDrive\Desktop\study planner"
```

### Step 2: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Train the Machine Learning Model (Pre-trained)
The Random Forest model has already been trained and saved into `ml/model/study_recommender.joblib`. If you wish to retrain it:
```powershell
python ml/train_model.py
```

### Step 4: Configure MongoDB
1. **Local MongoDB**: Ensure MongoDB Community Server is installed and running (`mongodb://localhost:27017/`).
2. **MongoDB Atlas (Cloud)**: Paste your Atlas connection string in `.env`:
   ```env
   MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/
   ```
3. **Offline Demo Mode**: If no MongoDB server is running, the app automatically runs on an in-memory mock MongoDB so you can demo the website immediately!

### Step 5: Start the Flask Application
```powershell
python app.py
```

### Step 6: Open the Website in Your Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🧪 Running Automated Tests

Run the comprehensive unit and integration test suite:
```powershell
python -m unittest discover -s tests -v
```

All 12 tests will run and verify:
* Student registration, secure password hashing, and login authorization.
* Data isolation between students.
* Subject & assignment creation, edits, and deletions.
* Random Forest feature extraction, priority ranking, and confidence metrics.
* Route availability and weekly timetable generation.

---

## 🎓 Faculty Mini-Project Viva Q&A Guide

When demonstrating this project to university evaluators, be prepared with these answers:

**Q1: Why did you choose Random Forest over simpler algorithms like Linear Regression or Naive Bayes?**
> *Answer*: Subject priority classification is a non-linear decision problem with interdependent features (e.g., high difficulty matters much more when exam days are short than when an exam is months away). Random Forest builds an ensemble of decorrelated decision trees, handles tabular numerical features without requiring arbitrary scaling, prevents overfitting via bagging, and outputs probability distributions for confidence scoring.

**Q2: What is the purpose of the synthetic dataset?**
> *Answer*: Genuine longitudinal student study records across semesters are rarely publicly available with ground-truth priority labels. Therefore, we generated 1,200 reproducible synthetic samples using transparent educational urgency heuristics. This allows the model to learn complex non-linear boundaries while maintaining full transparency. The model pipeline is structured so it can immediately be retrained on real institutional data when available.

**Q3: How does the application ensure user data isolation?**
> *Answer*: Every subject, task, study plan, and session record contains a `user_id` field corresponding to the authenticated student's MongoDB `ObjectId`. Every database query enforces `{"user_id": session["user_id"]}`, preventing any student from viewing or mutating another user's records.

**Q4: How does the Weekly Planner algorithm avoid task duplicates?**
> *Answer*: The generator tracks a set of scheduled task IDs. When distributing sessions across Monday to Sunday, it maps high-priority subjects to slots and attaches pending assignments that have not yet been assigned to any other day, preventing duplication.
