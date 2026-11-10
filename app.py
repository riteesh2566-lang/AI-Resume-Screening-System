"""ResumeAI: secure Flask application for resume analysis and job matching."""
from __future__ import annotations

import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import (Flask, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from utils.parser import extract_text_from_file
from utils.extractor import extract_information, extract_skills, calculate_resume_score
from utils.matcher import calculate_match_score, rank_candidates
from utils.recommendation import get_recommendations, predict_category, generate_ai_feedback

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY") or secrets.token_hex(32),
    UPLOAD_FOLDER=str(BASE_DIR / "uploads"),
    DATABASE=str(BASE_DIR / "database" / "resume_ai.db"),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "false").lower() == "true",
    PERMANENT_SESSION_LIFETIME=60 * 60 * 8,
)
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
csrf = CSRFProtect(app)

Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)
Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)


def get_db():
    conn = sqlite3.connect(app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def current_user():
    if "user_id" not in session:
        return None
    conn = get_db()
    user = conn.execute("SELECT id, name, email, role FROM users WHERE id = ?", (session["user_id"],)).fetchone()
    conn.close()
    return user


def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(role):
    from functools import wraps
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("user_role") != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def init_db():
    """Create schema and idempotently seed demo content."""
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'candidate' CHECK(role IN ('candidate','recruiter')),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        filename TEXT,
        resume_path TEXT,
        raw_text TEXT,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,
        education TEXT,
        experience TEXT,
        score INTEGER DEFAULT 0,
        category TEXT,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT,
        description TEXT,
        required_skills TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    );
    CREATE TABLE IF NOT EXISTS job_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER NOT NULL,
        job_id INTEGER NOT NULL,
        match_score REAL,
        matched_skills TEXT,
        missing_skills TEXT,
        matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(resume_id, job_id),
        FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_resumes_user ON resumes(user_id);
    CREATE INDEX IF NOT EXISTS idx_jobs_creator ON jobs(created_by);
    """)

    # Optional one-time recruiter bootstrap. Never expose recruiter signup publicly.
    recruiter_email = os.getenv("BOOTSTRAP_RECRUITER_EMAIL", "").strip().lower()
    recruiter_password = os.getenv("BOOTSTRAP_RECRUITER_PASSWORD", "")
    # The README's old public demo credentials are retired. Provision only from local env config.
    if recruiter_email and recruiter_password:
        conn.execute("""INSERT INTO users(name,email,password,role) VALUES(?,?,?,'recruiter')
                        ON CONFLICT(email) DO UPDATE SET name=excluded.name,
                        password=excluded.password, role='recruiter'""",
                     (os.getenv("BOOTSTRAP_RECRUITER_NAME", "Recruiter Admin"), recruiter_email,
                      generate_password_hash(recruiter_password)))
    else:
        # Invalidate the old demo password from earlier project versions.
        conn.execute("UPDATE users SET password=? WHERE email='recruiter@demo.com'",
                     (generate_password_hash(secrets.token_urlsafe(48)),))

    # Demo listings are inserted only when the jobs table is empty.
    if conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0] == 0:
        recruiter = conn.execute("SELECT id FROM users WHERE role='recruiter' ORDER BY id LIMIT 1").fetchone()
        creator_id = recruiter["id"] if recruiter else None
        demo_jobs = [
            ("Python ML Engineer", "TechCorp", "Python engineer with machine learning, data science and model deployment experience.", "Python,Machine Learning,TensorFlow,SQL,Docker,AWS,Scikit-learn,Pandas,NumPy"),
            ("Full Stack Developer", "WebAgency", "Full stack role requiring React, Flask, SQL and JavaScript knowledge.", "React,Flask,Python,SQL,JavaScript,HTML,CSS,Docker,Git"),
            ("Data Analyst", "DataCo", "Data analyst with SQL, Excel, dashboarding and statistical analysis skills.", "SQL,Excel,Power BI,Tableau,Python,Pandas,Statistics,Data Analysis"),
            ("DevOps Engineer", "CloudSys", "DevOps role requiring cloud, automation and containerization skills.", "Docker,AWS,Kubernetes,Linux,Python,CI/CD,Jenkins,Git,Terraform"),
        ]
        conn.executemany("""INSERT INTO jobs(title,company,description,required_skills,created_by)
                             VALUES(?,?,?,?,?)""", [(*job, creator_id) for job in demo_jobs])
    conn.commit()
    conn.close()


@app.context_processor
def inject_helpers():
    return {"csrf_token": __import__("flask_wtf.csrf", fromlist=["generate_csrf"]).generate_csrf}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or len(name) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Enter a valid name and email address.", "danger")
            return render_template("register.html")
        if len(password) < 10:
            flash("Use a password with at least 10 characters.", "danger")
            return render_template("register.html")
        conn = get_db()
        try:
            conn.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,'candidate')",
                         (name, email, generate_password_hash(password)))
            conn.commit()
            flash("Candidate account created. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "danger")
        finally:
            conn.close()
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        expected_role = request.form.get("expected_role", "").strip().lower()
        if expected_role not in ("", "candidate", "recruiter"):
            expected_role = ""
        if user and check_password_hash(user["password"], password):
            if expected_role and user["role"] != expected_role:
                flash(
                    "This account is registered as a "
                    + user["role"]
                    + ". Please use the "
                    + user["role"]
                    + " sign-in option.",
                    "danger",
                )
                return render_template("login.html", login_role=expected_role)
            session.clear()
            session.permanent = True
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_role"] = user["role"]
            flash(f"Welcome back, {user['name']}!", "success")
            return redirect(url_for("recruiter_dashboard" if user["role"] == "recruiter" else "candidate_dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template(
        "login.html",
        login_role=request.args.get("role", "").strip().lower()
        if request.args.get("role", "").strip().lower() in ("candidate", "recruiter")
        else "",
    )


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/candidate/dashboard")
@role_required("candidate")
def candidate_dashboard():
    conn = get_db()
    resumes = conn.execute("SELECT * FROM resumes WHERE user_id=? ORDER BY uploaded_at DESC", (session["user_id"],)).fetchall()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("candidate_dashboard.html", resumes=resumes, jobs=jobs)


@app.route("/upload", methods=["POST"])
@role_required("candidate")
def upload_resume():
    file = request.files.get("resume")
    if not file or not file.filename:
        flash("Choose a resume file first.", "danger")
        return redirect(url_for("candidate_dashboard"))
    if not allowed_file(file.filename):
        flash("Unsupported file. Upload PDF, DOCX or TXT.", "danger")
        return redirect(url_for("candidate_dashboard"))

    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    stored_name = f"{session['user_id']}_{uuid.uuid4().hex}.{extension}"
    destination = Path(app.config["UPLOAD_FOLDER"]) / stored_name
    file.save(destination)

    # Basic content-signature checks prevent obvious extension spoofing.
    with destination.open("rb") as handle:
        header = handle.read(8)
    valid = ((extension == "pdf" and header.startswith(b"%PDF-")) or
             (extension == "docx" and header.startswith(b"PK\x03\x04")) or
             (extension == "txt"))
    if not valid:
        destination.unlink(missing_ok=True)
        flash("The file content does not match its extension. Please upload a valid file.", "danger")
        return redirect(url_for("candidate_dashboard"))

    raw_text = extract_text_from_file(str(destination))
    if not raw_text or raw_text.startswith("[Could not") or len(raw_text.strip()) < 30:
        destination.unlink(missing_ok=True)
        flash("We could not extract enough text. Try a text-based PDF, DOCX or TXT file.", "danger")
        return redirect(url_for("candidate_dashboard"))

    info = extract_information(raw_text)
    skills = extract_skills(raw_text)
    category = predict_category(skills, raw_text)
    score = calculate_resume_score(info, skills, raw_text)
    conn = get_db()
    conn.execute("""INSERT INTO resumes(user_id,filename,resume_path,raw_text,name,email,phone,skills,education,experience,score,category)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (session["user_id"], original_name, str(destination.relative_to(BASE_DIR)), raw_text,
                  info.get("name", ""), info.get("email", ""), info.get("phone", ""),
                  ",".join(skills), info.get("education", ""), info.get("experience", ""), score, category))
    conn.commit()
    conn.close()
    flash("Resume uploaded and analyzed successfully.", "success")
    return redirect(url_for("candidate_dashboard"))


@app.route("/resume/<int:resume_id>")
@login_required
def view_resume(resume_id):
    conn = get_db()
    resume = conn.execute("SELECT * FROM resumes WHERE id=?", (resume_id,)).fetchone()
    conn.close()
    if not resume:
        abort(404)
    if session.get("user_role") != "recruiter" and resume["user_id"] != session["user_id"]:
        abort(403)
    skills_list = [s.strip() for s in (resume["skills"] or "").split(",") if s.strip()]
    feedback = generate_ai_feedback(resume)
    return render_template("resume_detail.html", resume=resume, skills_list=skills_list, feedback=feedback)


@app.route("/match/<int:resume_id>/<int:job_id>")
@role_required("candidate")
def match_resume_job(resume_id, job_id):
    conn = get_db()
    resume = conn.execute("SELECT * FROM resumes WHERE id=? AND user_id=?", (resume_id, session["user_id"])).fetchone()
    job = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if not resume or not job:
        conn.close()
        abort(404)
    resume_skills = [s.strip().lower() for s in (resume["skills"] or "").split(",") if s.strip()]
    job_skills = [s.strip().lower() for s in (job["required_skills"] or "").split(",") if s.strip()]
    result = calculate_match_score(resume["raw_text"] or "", job["description"] or "", resume_skills, job_skills)
    conn.execute("DELETE FROM job_matches WHERE resume_id=? AND job_id=?", (resume_id, job_id))
    conn.execute("""INSERT INTO job_matches(resume_id,job_id,match_score,matched_skills,missing_skills)
                    VALUES(?,?,?,?,?)""",
                 (resume_id, job_id, result["score"], ",".join(result["matched_skills"]), ",".join(result["missing_skills"])))
    conn.commit()
    conn.close()
    recommendations = get_recommendations(result["missing_skills"])
    return render_template("match_result.html", resume=resume, job=job, result=result, recommendations=recommendations)


@app.route("/recruiter/dashboard")
@role_required("recruiter")
def recruiter_dashboard():
    conn = get_db()
    jobs = conn.execute("SELECT * FROM jobs WHERE created_by=? ORDER BY created_at DESC", (session["user_id"],)).fetchall()
    all_resumes = conn.execute("SELECT r.*,u.name AS user_name FROM resumes r JOIN users u ON r.user_id=u.id ORDER BY r.uploaded_at DESC").fetchall()
    conn.close()
    return render_template("recruiter_dashboard.html", jobs=jobs, all_resumes=all_resumes)


@app.route("/job/create", methods=["GET", "POST"])
@role_required("recruiter")
def create_job():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        company = request.form.get("company", "").strip()
        description = request.form.get("description", "").strip()
        required_skills = request.form.get("required_skills", "").strip()
        if not title or not description or not required_skills:
            flash("Title, description and required skills are mandatory.", "danger")
            return render_template("create_job.html")
        conn = get_db()
        conn.execute("INSERT INTO jobs(title,company,description,required_skills,created_by) VALUES(?,?,?,?,?)",
                     (title[:150], company[:150], description[:10000], required_skills[:2000], session["user_id"]))
        conn.commit()
        conn.close()
        flash("Job posted successfully.", "success")
        return redirect(url_for("recruiter_dashboard"))
    return render_template("create_job.html")


@app.route("/job/<int:job_id>/candidates")
@role_required("recruiter")
def job_candidates(job_id):
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id=? AND created_by=?", (job_id, session["user_id"])).fetchone()
    if not job:
        conn.close()
        abort(404)
    all_resumes = conn.execute("SELECT r.*,u.name AS user_name FROM resumes r JOIN users u ON r.user_id=u.id").fetchall()
    conn.close()
    job_skills = [s.strip().lower() for s in (job["required_skills"] or "").split(",") if s.strip()]
    ranked = []
    for resume in all_resumes:
        resume_skills = [s.strip().lower() for s in (resume["skills"] or "").split(",") if s.strip()]
        result = calculate_match_score(resume["raw_text"] or "", job["description"] or "", resume_skills, job_skills)
        ranked.append({"resume": resume, "score": result["score"], "matched": result["matched_skills"], "missing": result["missing_skills"], "explanation": result.get("explanation", {})})
    ranked = rank_candidates(ranked)
    return render_template("job_candidates.html", job=job, ranked=ranked)


@app.route("/api/skills/<int:resume_id>")
@login_required
def api_skills(resume_id):
    conn = get_db()
    resume = conn.execute("SELECT user_id,skills FROM resumes WHERE id=?", (resume_id,)).fetchone()
    conn.close()
    if not resume:
        return jsonify({"error": "Not found"}), 404
    if session.get("user_role") != "recruiter" and resume["user_id"] != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"skills": [s.strip() for s in (resume["skills"] or "").split(",") if s.strip()]})


@app.route("/api/dashboard-stats")
@login_required
def api_dashboard_stats():
    conn = get_db()
    if session.get("user_role") == "recruiter":
        total_resumes = conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE created_by=?", (session["user_id"],)).fetchone()[0]
        avg_score = conn.execute("SELECT AVG(score) FROM resumes").fetchone()[0] or 0
        categories = conn.execute("SELECT category,COUNT(*) AS count FROM resumes GROUP BY category").fetchall()
    else:
        total_resumes = conn.execute("SELECT COUNT(*) FROM resumes WHERE user_id=?", (session["user_id"],)).fetchone()[0]
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        avg_score = conn.execute("SELECT AVG(score) FROM resumes WHERE user_id=?", (session["user_id"],)).fetchone()[0] or 0
        categories = conn.execute("SELECT category,COUNT(*) AS count FROM resumes WHERE user_id=? GROUP BY category", (session["user_id"],)).fetchall()
    conn.close()
    return jsonify({"total_resumes": total_resumes, "total_jobs": total_jobs, "avg_score": round(avg_score, 1),
                    "categories": [{"name": row["category"] or "Unknown", "count": row["count"]} for row in categories]})


@app.errorhandler(413)
def too_large(_error):
    flash("File is too large. Maximum upload size is 16 MB.", "danger")
    return redirect(url_for("candidate_dashboard"))


# Ensure schema exists for both `python app.py` and WSGI deployments (e.g. Gunicorn).
init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
