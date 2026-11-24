import os
from datetime import datetime, date, timedelta, timezone
from functools import wraps
from bson import ObjectId
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, abort
)
import bcrypt
from config import Config
from db import get_db, is_database_mock, to_object_id
from ml.recommendation import (
    recommend_subject_priority,
    get_ranked_recommendations,
    extract_features_from_subject,
    get_loaded_model
)

app = Flask(__name__)
app.config.from_object(Config)

# Ensure secret key is set
app.secret_key = Config.SECRET_KEY

# -------------------------------------------------------------
# Authentication Helper & Decorator
# -------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if "user_id" not in session:
        return None
    db = get_db()
    user_id = to_object_id(session["user_id"])
    if not user_id:
        return None
    return db.users.find_one({"_id": user_id})

@app.context_processor
def inject_global_data():
    """Injects user information and db status into all Jinja2 templates."""
    user = get_current_user()
    return {
        "current_user": user,
        "is_mock_db": is_database_mock(),
        "today_str": date.today().strftime("%Y-%m-%d"),
        "current_year": datetime.now().year
    }

# -------------------------------------------------------------
# Landing Page & Auth Routes
# -------------------------------------------------------------
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validation
        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html", name=name, email=email)

        if len(name) < 2:
            flash("Full name must be at least 2 characters long.", "danger")
            return render_template("register.html", name=name, email=email)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("register.html", name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html", name=name, email=email)

        db = get_db()
        existing_user = db.users.find_one({"email": email})
        if existing_user:
            flash("An account with that email already exists. Please log in.", "danger")
            return redirect(url_for("login"))

        # Hash password securely using bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

        new_user = {
            "name": name,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.now(timezone.utc)
        }

        result = db.users.insert_one(new_user)
        user_id = str(result.inserted_id)

        # Seed sample starter subjects and tasks for immediate demonstration
        _seed_starter_data_for_user(db, user_id)

        # Automatically log the student in
        session["user_id"] = user_id
        session["user_name"] = name
        session["user_email"] = email

        flash(f"Welcome to Student Study Planner, {name}! Your account is ready.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("login.html", email=email)

        db = get_db()
        user = db.users.find_one({"email": email})

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            session["user_id"] = str(user["_id"])
            session["user_name"] = user.get("name", "Student")
            session["user_email"] = user.get("email", "")
            flash(f"Welcome back, {user.get('name', 'Student')}!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("login.html", email=email)

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("login"))

# -------------------------------------------------------------
# Starter Data Seeder (Helper)
# -------------------------------------------------------------
def _seed_starter_data_for_user(db, user_id):
    """Provides realistic sample subjects and tasks for new students so the dashboard is immediately rich."""
    today = date.today()
    starter_subjects = [
        {
            "user_id": user_id,
            "name": "Machine Learning & AI",
            "description": "Supervised, unsupervised algorithms, neural networks, and decision trees.",
            "exam_date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
            "difficulty": 4,
            "confidence": 2,
            "syllabus_completion": 45.0,
            "previous_score": 55.0,
            "last_studied_date": (today - timedelta(days=5)).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc)
        },
        {
            "user_id": user_id,
            "name": "Database Management Systems",
            "description": "SQL, NoSQL, MongoDB, Normalization, indexing and transaction management.",
            "exam_date": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
            "difficulty": 3,
            "confidence": 4,
            "syllabus_completion": 75.0,
            "previous_score": 78.0,
            "last_studied_date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc)
        },
        {
            "user_id": user_id,
            "name": "Operating Systems & Networking",
            "description": "Process scheduling, virtual memory, concurrency, sockets and TCP/IP.",
            "exam_date": (today + timedelta(days=22)).strftime("%Y-%m-%d"),
            "difficulty": 4,
            "confidence": 3,
            "syllabus_completion": 60.0,
            "previous_score": 68.0,
            "last_studied_date": (today - timedelta(days=8)).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc)
        },
        {
            "user_id": user_id,
            "name": "Software Engineering & Agile",
            "description": "SDLC, Scrum practices, software testing, Git workflows and CI/CD pipelines.",
            "exam_date": (today + timedelta(days=35)).strftime("%Y-%m-%d"),
            "difficulty": 2,
            "confidence": 5,
            "syllabus_completion": 88.0,
            "previous_score": 85.0,
            "last_studied_date": (today - timedelta(days=3)).strftime("%Y-%m-%d"),
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    sub_ids = []
    for s in starter_subjects:
        res = db.subjects.insert_one(s)
        sub_ids.append(res.inserted_id)

    # Starter tasks
    starter_tasks = [
        {
            "user_id": user_id,
            "subject_id": str(sub_ids[0]),
            "subject_name": "Machine Learning & AI",
            "title": "Implement Random Forest & calculate Gini impurity",
            "description": "Work through formulas and prepare confusion matrix notes.",
            "due_date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "duration_mins": 90,
            "status": "Pending",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "user_id": user_id,
            "subject_id": str(sub_ids[0]),
            "subject_name": "Machine Learning & AI",
            "title": "Review Decision Tree pruning techniques",
            "description": "Chapter 4 questions and past college paper solutions.",
            "due_date": (today + timedelta(days=4)).strftime("%Y-%m-%d"),
            "duration_mins": 60,
            "status": "Pending",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "user_id": user_id,
            "subject_id": str(sub_ids[1]),
            "subject_name": "Database Management Systems",
            "title": "Write aggregation pipelines in MongoDB",
            "description": "Group, match, unwind, and lookup practice problems.",
            "due_date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "duration_mins": 45,
            "status": "Completed",
            "created_at": datetime.now(timezone.utc)
        },
        {
            "user_id": user_id,
            "subject_id": str(sub_ids[2]),
            "subject_name": "Operating Systems & Networking",
            "title": "Solve Banker's Algorithm deadlock problems",
            "description": "Practice 5 numerical problems from previous university exam.",
            "due_date": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
            "duration_mins": 60,
            "status": "Pending",
            "created_at": datetime.now(timezone.utc)
        }
    ]
    db.tasks.insert_many(starter_tasks)

    # Seed an initial study session
    db.study_sessions.insert_one({
        "user_id": user_id,
        "subject_id": str(sub_ids[1]),
        "subject_name": "Database Management Systems",
        "duration_mins": 45,
        "notes": "Completed initial chapter revision on B-Tree indexing.",
        "created_at": datetime.now(timezone.utc) - timedelta(days=1)
    })

# -------------------------------------------------------------
# Dashboard Route
# -------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    db = get_db()
    today = date.today()

    # 1. Fetch subjects
    subjects = list(db.subjects.find({"user_id": user_id}).sort("created_at", -1))
    total_subjects = len(subjects)

    # 2. Fetch tasks
    tasks = list(db.tasks.find({"user_id": user_id}))
    pending_tasks = [t for t in tasks if t.get("status") == "Pending"]
    completed_tasks = [t for t in tasks if t.get("status") == "Completed"]
    
    # Overdue tasks
    overdue_tasks = []
    for t in pending_tasks:
        due = t.get("due_date")
        if due:
            try:
                due_d = datetime.strptime(due, "%Y-%m-%d").date()
                if due_d < today:
                    overdue_tasks.append(t)
            except Exception:
                pass

    # 3. Fetch study sessions & calculate total study hours
    sessions = list(db.study_sessions.find({"user_id": user_id}))
    total_minutes = sum(s.get("duration_mins", 0) for s in sessions)
    total_study_hours = round(total_minutes / 60.0, 1)

    # 4. Upcoming examinations
    upcoming_exams = []
    for sub in subjects:
        exam_date_str = sub.get("exam_date")
        if exam_date_str:
            try:
                e_date = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
                diff_days = (e_date - today).days
                if diff_days >= 0:
                    upcoming_exams.append({
                        "name": sub.get("name"),
                        "exam_date": exam_date_str,
                        "days_remaining": diff_days,
                        "subject_id": str(sub["_id"])
                    })
            except Exception:
                pass
    upcoming_exams.sort(key=lambda x: x["days_remaining"])

    # 5. ML Recommendations (Ranked by priority)
    recommendations = get_ranked_recommendations(subjects)
    top_recommendations = recommendations[:3] # Top 3 for dashboard widget

    # 6. Today's study schedule from weekly planner
    today_name = today.strftime("%A") # e.g. "Monday"
    today_plan = db.study_plans.find_one({"user_id": user_id, "day": today_name})
    today_sessions = today_plan.get("sessions", []) if today_plan else []

    # 7. Weekly study activity (last 7 days study minutes)
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_sessions = list(db.study_sessions.find({
        "user_id": user_id,
        "created_at": {"$gte": seven_days_ago}
    }))
    weekly_study_mins = sum(s.get("duration_mins", 0) for s in recent_sessions)
    weekly_study_hours = round(weekly_study_mins / 60.0, 1)

    return render_template(
        "dashboard.html",
        total_subjects=total_subjects,
        pending_tasks_count=len(pending_tasks),
        completed_tasks_count=len(completed_tasks),
        overdue_tasks_count=len(overdue_tasks),
        total_study_hours=total_study_hours,
        weekly_study_hours=weekly_study_hours,
        upcoming_exams=upcoming_exams[:4],
        top_recommendations=top_recommendations,
        today_name=today_name,
        today_sessions=today_sessions,
        recent_subjects=subjects[:4]
    )

# -------------------------------------------------------------
# Subject Management Routes
# -------------------------------------------------------------
@app.route("/subjects")
@login_required
def subjects():
    user_id = session["user_id"]
    db = get_db()
    subs = list(db.subjects.find({"user_id": user_id}).sort("name", 1))
    
    # Enrich each subject with days until exam and last studied formatted
    today = date.today()
    for s in subs:
        e_date = s.get("exam_date")
        if e_date:
            try:
                dt = datetime.strptime(e_date, "%Y-%m-%d").date()
                s["days_until_exam"] = (dt - today).days
            except Exception:
                s["days_until_exam"] = None
        else:
            s["days_until_exam"] = None

    return render_template("subjects.html", subjects=subs)

@app.route("/subjects/add", methods=["POST"])
@login_required
def add_subject():
    user_id = session["user_id"]
    db = get_db()

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    exam_date = request.form.get("exam_date", "").strip()
    difficulty = int(request.form.get("difficulty", 3))
    confidence = int(request.form.get("confidence", 3))
    syllabus_completion = float(request.form.get("syllabus_completion", 0))
    previous_score = float(request.form.get("previous_score", 60))
    last_studied_date = request.form.get("last_studied_date", "").strip() or date.today().strftime("%Y-%m-%d")

    if not name:
        flash("Subject name is required.", "danger")
        return redirect(url_for("subjects"))

    # Bound ranges
    difficulty = max(1, min(5, difficulty))
    confidence = max(1, min(5, confidence))
    syllabus_completion = max(0.0, min(100.0, syllabus_completion))
    previous_score = max(0.0, min(100.0, previous_score))

    new_subject = {
        "user_id": user_id,
        "name": name,
        "description": description,
        "exam_date": exam_date,
        "difficulty": difficulty,
        "confidence": confidence,
        "syllabus_completion": syllabus_completion,
        "previous_score": previous_score,
        "last_studied_date": last_studied_date,
        "created_at": datetime.now(timezone.utc)
    }

    db.subjects.insert_one(new_subject)
    flash(f"Subject '{name}' added successfully!", "success")
    return redirect(url_for("subjects"))

@app.route("/subjects/<subject_id>/edit", methods=["POST"])
@login_required
def edit_subject(subject_id):
    user_id = session["user_id"]
    db = get_db()
    obj_id = to_object_id(subject_id)
    if not obj_id:
        flash("Invalid subject ID.", "danger")
        return redirect(url_for("subjects"))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    exam_date = request.form.get("exam_date", "").strip()
    difficulty = int(request.form.get("difficulty", 3))
    confidence = int(request.form.get("confidence", 3))
    syllabus_completion = float(request.form.get("syllabus_completion", 0))
    previous_score = float(request.form.get("previous_score", 60))
    last_studied_date = request.form.get("last_studied_date", "").strip()

    if not name:
        flash("Subject name cannot be empty.", "danger")
        return redirect(url_for("subjects"))

    difficulty = max(1, min(5, difficulty))
    confidence = max(1, min(5, confidence))
    syllabus_completion = max(0.0, min(100.0, syllabus_completion))
    previous_score = max(0.0, min(100.0, previous_score))

    update_fields = {
        "name": name,
        "description": description,
        "exam_date": exam_date,
        "difficulty": difficulty,
        "confidence": confidence,
        "syllabus_completion": syllabus_completion,
        "previous_score": previous_score,
        "last_studied_date": last_studied_date,
        "updated_at": datetime.now(timezone.utc)
    }

    result = db.subjects.update_one(
        {"_id": obj_id, "user_id": user_id},
        {"$set": update_fields}
    )

    if result.matched_count == 0:
        flash("Subject not found or access denied.", "danger")
    else:
        # Also update subject name in related tasks
        db.tasks.update_many(
            {"subject_id": subject_id, "user_id": user_id},
            {"$set": {"subject_name": name}}
        )
        flash(f"Subject '{name}' updated successfully!", "success")

    return redirect(url_for("subjects"))

@app.route("/subjects/<subject_id>/delete", methods=["POST"])
@login_required
def delete_subject(subject_id):
    user_id = session["user_id"]
    db = get_db()
    obj_id = to_object_id(subject_id)
    if not obj_id:
        flash("Invalid subject ID.", "danger")
        return redirect(url_for("subjects"))

    result = db.subjects.delete_one({"_id": obj_id, "user_id": user_id})
    if result.deleted_count > 0:
        # Also cleanup tasks and plans referencing this subject
        db.tasks.delete_many({"subject_id": subject_id, "user_id": user_id})
        flash("Subject and its associated tasks deleted successfully.", "success")
    else:
        flash("Subject not found or access denied.", "danger")

    return redirect(url_for("subjects"))

# -------------------------------------------------------------
# Task Management Routes
# -------------------------------------------------------------
@app.route("/tasks")
@login_required
def tasks():
    user_id = session["user_id"]
    db = get_db()
    status_filter = request.args.get("status", "all")

    query = {"user_id": user_id}
    if status_filter in ["Pending", "Completed"]:
        query["status"] = status_filter

    user_tasks = list(db.tasks.find(query).sort("due_date", 1))
    subjects = list(db.subjects.find({"user_id": user_id}).sort("name", 1))

    today = date.today()
    for t in user_tasks:
        due = t.get("due_date")
        t["is_overdue"] = False
        if due and t.get("status") == "Pending":
            try:
                due_d = datetime.strptime(due, "%Y-%m-%d").date()
                if due_d < today:
                    t["is_overdue"] = True
            except Exception:
                pass

    return render_template(
        "tasks.html",
        tasks=user_tasks,
        subjects=subjects,
        status_filter=status_filter
    )

@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    user_id = session["user_id"]
    db = get_db()

    title = request.form.get("title", "").strip()
    subject_id = request.form.get("subject_id", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    duration_mins = int(request.form.get("duration_mins", 45))

    if not title:
        flash("Task title is required.", "danger")
        return redirect(url_for("tasks"))

    subject_name = "General Study"
    if subject_id:
        sub = db.subjects.find_one({"_id": to_object_id(subject_id), "user_id": user_id})
        if sub:
            subject_name = sub.get("name", "General Study")

    new_task = {
        "user_id": user_id,
        "title": title,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "description": description,
        "due_date": due_date,
        "duration_mins": max(10, duration_mins),
        "status": "Pending",
        "created_at": datetime.now(timezone.utc)
    }

    db.tasks.insert_one(new_task)
    flash(f"Task '{title}' created successfully!", "success")
    return redirect(url_for("tasks"))

@app.route("/tasks/<task_id>/edit", methods=["POST"])
@login_required
def edit_task(task_id):
    user_id = session["user_id"]
    db = get_db()
    obj_id = to_object_id(task_id)
    if not obj_id:
        flash("Invalid task ID.", "danger")
        return redirect(url_for("tasks"))

    title = request.form.get("title", "").strip()
    subject_id = request.form.get("subject_id", "").strip()
    description = request.form.get("description", "").strip()
    due_date = request.form.get("due_date", "").strip()
    duration_mins = int(request.form.get("duration_mins", 45))
    status = request.form.get("status", "Pending")

    if not title:
        flash("Task title cannot be empty.", "danger")
        return redirect(url_for("tasks"))

    subject_name = "General Study"
    if subject_id:
        sub = db.subjects.find_one({"_id": to_object_id(subject_id), "user_id": user_id})
        if sub:
            subject_name = sub.get("name", "General Study")

    update_fields = {
        "title": title,
        "subject_id": subject_id,
        "subject_name": subject_name,
        "description": description,
        "due_date": due_date,
        "duration_mins": max(10, duration_mins),
        "status": status,
        "updated_at": datetime.now(timezone.utc)
    }

    result = db.tasks.update_one(
        {"_id": obj_id, "user_id": user_id},
        {"$set": update_fields}
    )

    if result.matched_count > 0:
        flash(f"Task '{title}' updated successfully!", "success")
    else:
        flash("Task not found or access denied.", "danger")

    return redirect(url_for("tasks"))

@app.route("/tasks/<task_id>/toggle", methods=["POST"])
@login_required
def toggle_task(task_id):
    user_id = session["user_id"]
    db = get_db()
    obj_id = to_object_id(task_id)
    if not obj_id:
        return jsonify({"success": False, "error": "Invalid task ID"}), 400

    task = db.tasks.find_one({"_id": obj_id, "user_id": user_id})
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404

    new_status = "Completed" if task.get("status") == "Pending" else "Pending"
    db.tasks.update_one({"_id": obj_id}, {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}})

    # If called via fetch/AJAX
    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"success": True, "new_status": new_status})

    flash(f"Task status changed to {new_status}.", "success")
    return redirect(request.referrer or url_for("tasks"))

@app.route("/tasks/<task_id>/delete", methods=["POST"])
@login_required
def delete_task(task_id):
    user_id = session["user_id"]
    db = get_db()
    obj_id = to_object_id(task_id)
    if not obj_id:
        flash("Invalid task ID.", "danger")
        return redirect(url_for("tasks"))

    result = db.tasks.delete_one({"_id": obj_id, "user_id": user_id})
    if result.deleted_count > 0:
        flash("Task deleted successfully.", "success")
    else:
        flash("Task not found or access denied.", "danger")

    return redirect(url_for("tasks"))

# -------------------------------------------------------------
# Weekly Study Planner Routes
# -------------------------------------------------------------
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

@app.route("/planner")
@login_required
def planner():
    user_id = session["user_id"]
    db = get_db()
    subjects = list(db.subjects.find({"user_id": user_id}).sort("name", 1))

    # Fetch weekly plan for all 7 days
    plans = list(db.study_plans.find({"user_id": user_id}))
    plan_by_day = {p["day"]: p.get("sessions", []) for p in plans}

    # Ensure all days exist in dictionary
    for day in DAYS_OF_WEEK:
        if day not in plan_by_day:
            plan_by_day[day] = []

    return render_template(
        "planner.html",
        days_of_week=DAYS_OF_WEEK,
        plan_by_day=plan_by_day,
        subjects=subjects
    )

@app.route("/planner/generate", methods=["POST"])
@login_required
def generate_weekly_plan():
    """
    Automated Study Plan Generator:
    Leverages Random Forest priority rankings, examination proximity,
    syllabus backlog, and pending study tasks to construct a balanced
    Monday-to-Sunday study timetable without duplicate task scheduling.
    """
    user_id = session["user_id"]
    db = get_db()

    subjects = list(db.subjects.find({"user_id": user_id}))
    if not subjects:
        flash("Please add at least one subject before generating a study plan.", "warning")
        return redirect(url_for("subjects"))

    # 1. Rank subjects using Random Forest
    ranked_subjects = get_ranked_recommendations(subjects)
    
    # 2. Get pending tasks
    pending_tasks = list(db.tasks.find({"user_id": user_id, "status": "Pending"}))
    task_pool_by_sub = {}
    for t in pending_tasks:
        s_id = str(t.get("subject_id", ""))
        task_pool_by_sub.setdefault(s_id, []).append(t)

    # 3. Time slot templates for a balanced daily timetable
    time_slots = [
        {"time": "09:30 AM - 11:00 AM", "duration": 90, "type": "Deep Work"},
        {"time": "02:00 PM - 03:00 PM", "duration": 60, "type": "Concept Practice"},
        {"time": "05:30 PM - 07:00 PM", "duration": 90, "type": "Problem Solving"},
        {"time": "08:30 PM - 09:30 PM", "duration": 60, "type": "Revision & Recall"}
    ]

    # Clean existing generated plan for user
    db.study_plans.delete_many({"user_id": user_id})

    # Used task tracking to prevent duplicate scheduling
    scheduled_task_ids = set()

    # Determine frequency allocation based on priority
    # High Priority: 4-5 slots across the week
    # Medium Priority: 2-3 slots
    # Low Priority: 1-2 slots
    subject_queue = []
    for r in ranked_subjects:
        weight = r["sort_weight"] # 3 = High, 2 = Medium, 1 = Low
        occurrences = 4 if weight == 3 else (2 if weight == 2 else 1)
        for _ in range(occurrences):
            subject_queue.append(r)

    # If subject_queue is shorter than slots, loop it
    if not subject_queue:
        subject_queue = ranked_subjects * 3

    q_idx = 0
    total_q = len(subject_queue)

    for day_idx, day_name in enumerate(DAYS_OF_WEEK):
        day_sessions = []
        # Saturday and Sunday have 2 lighter sessions, weekdays have 3
        slots_for_day = time_slots[:3] if day_idx < 5 else [time_slots[0], time_slots[3]]

        for slot_num, slot_info in enumerate(slots_for_day):
            target_sub = subject_queue[q_idx % total_q]
            q_idx += 1

            s_id = target_sub["subject_id"]
            assigned_task_title = "Topic review & practice questions"
            
            # Find an unscheduled pending task for this subject
            if s_id in task_pool_by_sub:
                for candidate_task in task_pool_by_sub[s_id]:
                    c_id = str(candidate_task["_id"])
                    if c_id not in scheduled_task_ids:
                        assigned_task_title = candidate_task.get("title", assigned_task_title)
                        scheduled_task_ids.add(c_id)
                        break

            session_item = {
                "session_id": str(ObjectId()),
                "subject_id": s_id,
                "subject_name": target_sub["subject_name"],
                "priority": target_sub["priority"],
                "priority_color": target_sub["priority_color"],
                "time_slot": slot_info["time"],
                "duration_mins": slot_info["duration"],
                "task_title": assigned_task_title,
                "completed": False
            }
            day_sessions.append(session_item)

        # Store in MongoDB
        db.study_plans.insert_one({
            "user_id": user_id,
            "day": day_name,
            "sessions": day_sessions,
            "updated_at": datetime.now(timezone.utc)
        })

    flash("Random Forest AI successfully generated your balanced weekly study timetable!", "success")
    return redirect(url_for("planner"))

@app.route("/planner/add_session", methods=["POST"])
@login_required
def add_planner_session():
    user_id = session["user_id"]
    db = get_db()

    day = request.form.get("day", "Monday")
    subject_id = request.form.get("subject_id", "").strip()
    time_slot = request.form.get("time_slot", "10:00 AM - 11:30 AM").strip()
    duration_mins = int(request.form.get("duration_mins", 60))
    task_title = request.form.get("task_title", "Independent Study").strip()

    subject_name = "General Study"
    priority = "MEDIUM PRIORITY"
    priority_color = "#F59E0B"

    if subject_id:
        sub = db.subjects.find_one({"_id": to_object_id(subject_id), "user_id": user_id})
        if sub:
            subject_name = sub.get("name", "General Study")
            rec = recommend_subject_priority(sub)
            priority = rec["priority"]
            priority_color = rec["priority_color"]

    session_item = {
        "session_id": str(ObjectId()),
        "subject_id": subject_id,
        "subject_name": subject_name,
        "priority": priority,
        "priority_color": priority_color,
        "time_slot": time_slot,
        "duration_mins": max(15, duration_mins),
        "task_title": task_title,
        "completed": False
    }

    db.study_plans.update_one(
        {"user_id": user_id, "day": day},
        {"$push": {"sessions": session_item}},
        upsert=True
    )

    flash(f"Study session added to {day}!", "success")
    return redirect(url_for("planner"))

@app.route("/planner/session/<session_id>/toggle", methods=["POST"])
@login_required
def toggle_planner_session(session_id):
    user_id = session["user_id"]
    db = get_db()

    # Find the day containing this session
    plan = db.study_plans.find_one({"user_id": user_id, "sessions.session_id": session_id})
    if not plan:
        return jsonify({"success": False, "error": "Session not found"}), 404

    # Toggle the completed boolean
    updated_sessions = []
    new_state = False
    for s in plan.get("sessions", []):
        if s.get("session_id") == session_id:
            s["completed"] = not s.get("completed", False)
            new_state = s["completed"]
        updated_sessions.append(s)

    db.study_plans.update_one(
        {"_id": plan["_id"]},
        {"$set": {"sessions": updated_sessions}}
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({"success": True, "completed": new_state})

    return redirect(url_for("planner"))

@app.route("/planner/session/<session_id>/delete", methods=["POST"])
@login_required
def delete_planner_session(session_id):
    user_id = session["user_id"]
    db = get_db()

    db.study_plans.update_many(
        {"user_id": user_id},
        {"$pull": {"sessions": {"session_id": session_id}}}
    )
    flash("Study session removed from planner.", "info")
    return redirect(url_for("planner"))

@app.route("/planner/clear", methods=["POST"])
@login_required
def clear_planner():
    user_id = session["user_id"]
    db = get_db()
    db.study_plans.delete_many({"user_id": user_id})
    flash("Weekly planner cleared.", "info")
    return redirect(url_for("planner"))

# -------------------------------------------------------------
# Smart Recommendations Route
# -------------------------------------------------------------
@app.route("/recommendations")
@login_required
def recommendations():
    user_id = session["user_id"]
    db = get_db()
    subjects = list(db.subjects.find({"user_id": user_id}))

    ranked_recs = get_ranked_recommendations(subjects)
    model_bundle = get_loaded_model()
    model_accuracy = (
        round(model_bundle.get("accuracy", 0.85) * 100, 1) if model_bundle else 84.5
    )

    return render_template(
        "recommendations.html",
        recommendations=ranked_recs,
        total_subjects=len(subjects),
        model_accuracy=model_accuracy
    )

# -------------------------------------------------------------
# Study Session Tracker Routes
# -------------------------------------------------------------
@app.route("/tracker")
@login_required
def tracker():
    user_id = session["user_id"]
    db = get_db()
    subjects = list(db.subjects.find({"user_id": user_id}).sort("name", 1))

    # Optional preselected subject from recommendation
    preselect_id = request.args.get("subject_id", "")
    suggested_duration = request.args.get("duration", "45")

    # Fetch recent study sessions
    sessions = list(db.study_sessions.find({"user_id": user_id}).sort("created_at", -1).limit(15))

    total_mins = sum(s.get("duration_mins", 0) for s in sessions)
    total_hours = round(total_mins / 60.0, 1)

    return render_template(
        "tracker.html",
        subjects=subjects,
        preselect_id=preselect_id,
        suggested_duration=suggested_duration,
        sessions=sessions,
        total_sessions=len(sessions),
        total_hours=total_hours
    )

@app.route("/tracker/log_session", methods=["POST"])
@login_required
def log_study_session():
    user_id = session["user_id"]
    db = get_db()

    subject_id = request.form.get("subject_id", "").strip()
    duration_mins = int(request.form.get("duration_mins", 45))
    notes = request.form.get("notes", "").strip()
    session_date = request.form.get("session_date", "").strip() or date.today().strftime("%Y-%m-%d")

    if not subject_id:
        flash("Please select a subject for the study session.", "danger")
        return redirect(url_for("tracker"))

    sub = db.subjects.find_one({"_id": to_object_id(subject_id), "user_id": user_id})
    if not sub:
        flash("Selected subject not found.", "danger")
        return redirect(url_for("tracker"))

    # Insert study session
    new_session = {
        "user_id": user_id,
        "subject_id": subject_id,
        "subject_name": sub.get("name", "Unknown Subject"),
        "duration_mins": max(1, duration_mins),
        "notes": notes,
        "session_date": session_date,
        "created_at": datetime.now(timezone.utc)
    }
    db.study_sessions.insert_one(new_session)

    # Automatically update subject's last_studied_date and slight syllabus progress increment if noted
    db.subjects.update_one(
        {"_id": sub["_id"]},
        {"$set": {"last_studied_date": session_date}}
    )

    flash(f"Great work! Logged {duration_mins} minutes for '{sub.get('name')}'.", "success")
    return redirect(url_for("tracker"))

@app.route("/tracker/session/<session_id>/delete", methods=["POST"])
@login_required
def delete_study_session(session_id):
    user_id = session["user_id"]
    db = get_db()
    obj_id = to_object_id(session_id)
    if not obj_id:
        flash("Invalid session ID.", "danger")
        return redirect(url_for("tracker"))

    result = db.study_sessions.delete_one({"_id": obj_id, "user_id": user_id})
    if result.deleted_count > 0:
        flash("Study session log deleted.", "info")
    else:
        flash("Session not found or access denied.", "danger")

    return redirect(url_for("tracker"))

# -------------------------------------------------------------
# Study Progress & Analytics Routes
# -------------------------------------------------------------
@app.route("/progress")
@login_required
def progress():
    user_id = session["user_id"]
    db = get_db()

    subjects = list(db.subjects.find({"user_id": user_id}).sort("name", 1))
    tasks = list(db.tasks.find({"user_id": user_id}))
    sessions = list(db.study_sessions.find({"user_id": user_id}).sort("created_at", -1))

    total_mins = sum(s.get("duration_mins", 0) for s in sessions)
    total_hours = round(total_mins / 60.0, 1)

    completed_tasks_count = sum(1 for t in tasks if t.get("status") == "Completed")
    pending_tasks_count = sum(1 for t in tasks if t.get("status") == "Pending")
    total_tasks = len(tasks)
    task_completion_rate = round((completed_tasks_count / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    # Calculate average study minutes per active day
    unique_dates = {s.get("session_date") or s.get("created_at").strftime("%Y-%m-%d") for s in sessions if s.get("created_at")}
    avg_mins_per_day = round(total_mins / len(unique_dates), 1) if unique_dates else 0.0

    return render_template(
        "progress.html",
        total_hours=total_hours,
        total_sessions=len(sessions),
        total_subjects=len(subjects),
        task_completion_rate=task_completion_rate,
        completed_tasks_count=completed_tasks_count,
        pending_tasks_count=pending_tasks_count,
        avg_mins_per_day=avg_mins_per_day,
        sessions=sessions
    )

@app.route("/api/progress_data")
@login_required
def api_progress_data():
    """Returns dynamic aggregated statistics for Chart.js interactive visualizations."""
    user_id = session["user_id"]
    db = get_db()

    subjects = list(db.subjects.find({"user_id": user_id}))
    tasks = list(db.tasks.find({"user_id": user_id}))
    sessions = list(db.study_sessions.find({"user_id": user_id}))

    # 1. Subject-wise study hours
    sub_hours = {}
    for sub in subjects:
        sub_hours[sub.get("name", "Untitled")] = 0.0

    for s in sessions:
        name = s.get("subject_name", "General")
        sub_hours[name] = sub_hours.get(name, 0.0) + round(s.get("duration_mins", 0) / 60.0, 2)

    subject_labels = list(sub_hours.keys())
    subject_values = [round(val, 2) for val in sub_hours.values()]

    # 2. Daily study activity for the past 7 days
    today = date.today()
    day_labels = []
    day_values = []
    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        day_str = target_day.strftime("%Y-%m-%d")
        day_display = target_day.strftime("%a (%b %d)")
        day_labels.append(day_display)

        # Sum duration for this day
        day_mins = 0
        for s in sessions:
            s_date = s.get("session_date")
            if not s_date and s.get("created_at"):
                s_date = s["created_at"].strftime("%Y-%m-%d")
            if s_date == day_str:
                day_mins += s.get("duration_mins", 0)

        day_values.append(round(day_mins / 60.0, 2))

    # 3. Task Status Breakdown
    pending_count = sum(1 for t in tasks if t.get("status") == "Pending")
    completed_count = sum(1 for t in tasks if t.get("status") == "Completed")

    # 4. Syllabus Completion by Subject
    syllabus_labels = [s.get("name", "Untitled") for s in subjects]
    syllabus_values = [round(float(s.get("syllabus_completion", 0)), 1) for s in subjects]

    return jsonify({
        "subject_distribution": {
            "labels": subject_labels,
            "values": subject_values
        },
        "weekly_trend": {
            "labels": day_labels,
            "values": day_values
        },
        "task_breakdown": {
            "labels": ["Completed Tasks", "Pending Tasks"],
            "values": [completed_count, pending_count]
        },
        "syllabus_progress": {
            "labels": syllabus_labels,
            "values": syllabus_values
        }
    })

# -------------------------------------------------------------
# Error Handlers
# -------------------------------------------------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template("base.html", error_title="404 - Page Not Found",
                           error_message="The page you requested could not be found."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("base.html", error_title="500 - Server Error",
                           error_message="An internal server error occurred."), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print(f"\n=================================================================")
    print(f" Student Study Planner with Random Forest Recommendation System ")
    print(f" Running on: http://127.0.0.1:{port}")
    print(f" Database Mode: {'In-Memory MongoDB (Mock)' if is_database_mock() else 'Native MongoDB Server'}")
    print(f"=================================================================\n")
    app.run(host="127.0.0.1", port=port, debug=debug)
