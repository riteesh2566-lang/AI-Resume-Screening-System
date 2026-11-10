from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from datetime import datetime
from utils.parser import extract_text_from_file
from utils.extractor import extract_information, extract_skills, calculate_resume_score
from utils.matcher import calculate_match_score, rank_candidates
from utils.recommendation import get_recommendations, predict_category, generate_ai_feedback

app = Flask(__name__)
app.secret_key = 'resume_ai_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database', 'resume_ai.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'candidate',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
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
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT,
        description TEXT,
        required_skills TEXT,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS job_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resume_id INTEGER,
        job_id INTEGER,
        match_score REAL,
        matched_skills TEXT,
        missing_skills TEXT,
        matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (resume_id) REFERENCES resumes(id),
        FOREIGN KEY (job_id) REFERENCES jobs(id)
    )''')
    # Insert demo recruiter account
    try:
        c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                  ('Admin Recruiter', 'recruiter@demo.com', generate_password_hash('demo123'), 'recruiter'))
    except:
        pass
    # Insert demo jobs
    demo_jobs = [
        ('Python ML Engineer', 'TechCorp', 'We need a Python ML engineer with experience in machine learning and data science.',
         'Python,Machine Learning,TensorFlow,SQL,Docker,AWS,Scikit-learn,Pandas,NumPy', 1),
        ('Full Stack Developer', 'WebAgency', 'Full stack role requiring React, Flask and SQL knowledge.',
         'React,Flask,Python,SQL,JavaScript,HTML,CSS,Docker,Git', 1),
        ('Data Scientist', 'DataCo', 'Seeking a data scientist with strong analytical and ML skills.',
         'Python,SQL,Machine Learning,Pandas,NumPy,Tableau,Power BI,Statistics,R', 1),
        ('DevOps Engineer', 'CloudSys', 'DevOps role requiring cloud and containerization skills.',
         'Docker,AWS,Kubernetes,Linux,Python,CI/CD,Jenkins,Git,Terraform', 1),
    ]
    for job in demo_jobs:
        try:
            c.execute("INSERT INTO jobs (title, company, description, required_skills, created_by) VALUES (?,?,?,?,?)", job)
        except:
            pass
    conn.commit()
    conn.close()

# ─── AUTH ROUTES ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'candidate')
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                         (name, email, generate_password_hash(password), role))
            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Email already registered.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            flash(f'Welcome back, {user["name"]}!', 'success')
            if user['role'] == 'recruiter':
                return redirect(url_for('recruiter_dashboard'))
            return redirect(url_for('candidate_dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ─── CANDIDATE ROUTES ────────────────────────────────────────────────────────────

@app.route('/candidate/dashboard')
def candidate_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    resumes = conn.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC", (session['user_id'],)).fetchall()
    jobs = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('candidate_dashboard.html', resumes=resumes, jobs=jobs)

@app.route('/upload', methods=['POST'])
def upload_resume():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if 'resume' not in request.files:
        flash('No file selected.', 'danger')
        return redirect(url_for('candidate_dashboard'))
    file = request.files['resume']
    if file.filename == '' or not allowed_file(file.filename):
        flash('Invalid file. Please upload PDF, DOCX, or TXT.', 'danger')
        return redirect(url_for('candidate_dashboard'))
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract and analyze
    raw_text = extract_text_from_file(filepath)
    info = extract_information(raw_text)
    skills = extract_skills(raw_text)
    category = predict_category(skills, raw_text)
    score = calculate_resume_score(info, skills, raw_text)

    conn = get_db()
    conn.execute("""INSERT INTO resumes (user_id, filename, resume_path, raw_text, name, email, phone, skills, education, experience, score, category)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                 (session['user_id'], filename, filepath, raw_text,
                  info.get('name', ''), info.get('email', ''), info.get('phone', ''),
                  ','.join(skills), info.get('education', ''), info.get('experience', ''),
                  score, category))
    conn.commit()
    conn.close()
    flash('Resume uploaded and analyzed successfully!', 'success')
    return redirect(url_for('candidate_dashboard'))

@app.route('/resume/<int:resume_id>')
def view_resume(resume_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    resume = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    if not resume:
        flash('Resume not found.', 'danger')
        return redirect(url_for('candidate_dashboard'))
    skills_list = [s.strip() for s in resume['skills'].split(',') if s.strip()] if resume['skills'] else []
    feedback = generate_ai_feedback(resume)
    return render_template('resume_detail.html', resume=resume, skills_list=skills_list, feedback=feedback)

@app.route('/match/<int:resume_id>/<int:job_id>')
def match_resume_job(resume_id, job_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db()
    resume = conn.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not resume or not job:
        flash('Resume or job not found.', 'danger')
        return redirect(url_for('candidate_dashboard'))

    resume_skills = [s.strip().lower() for s in resume['skills'].split(',') if s.strip()]
    job_skills = [s.strip().lower() for s in job['required_skills'].split(',') if s.strip()]
    result = calculate_match_score(resume['raw_text'], job['description'], resume_skills, job_skills)

    # Save match
    conn.execute("""INSERT OR REPLACE INTO job_matches (resume_id, job_id, match_score, matched_skills, missing_skills)
                    VALUES (?,?,?,?,?)""",
                 (resume_id, job_id, result['score'],
                  ','.join(result['matched_skills']), ','.join(result['missing_skills'])))
    conn.commit()
    recommendations = get_recommendations(result['missing_skills'])
    conn.close()
    return render_template('match_result.html', resume=resume, job=job, result=result, recommendations=recommendations)

# ─── RECRUITER ROUTES ────────────────────────────────────────────────────────────

@app.route('/recruiter/dashboard')
def recruiter_dashboard():
    if 'user_id' not in session or session.get('user_role') != 'recruiter':
        return redirect(url_for('login'))
    conn = get_db()
    jobs = conn.execute("SELECT * FROM jobs WHERE created_by = ? ORDER BY created_at DESC", (session['user_id'],)).fetchall()
    all_resumes = conn.execute("SELECT r.*, u.name as user_name FROM resumes r JOIN users u ON r.user_id = u.id ORDER BY r.score DESC").fetchall()
    conn.close()
    return render_template('recruiter_dashboard.html', jobs=jobs, all_resumes=all_resumes)

@app.route('/job/create', methods=['GET', 'POST'])
def create_job():
    if 'user_id' not in session or session.get('user_role') != 'recruiter':
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        company = request.form['company']
        description = request.form['description']
        required_skills = request.form['required_skills']
        conn = get_db()
        conn.execute("INSERT INTO jobs (title, company, description, required_skills, created_by) VALUES (?,?,?,?,?)",
                     (title, company, description, required_skills, session['user_id']))
        conn.commit()
        conn.close()
        flash('Job posted successfully!', 'success')
        return redirect(url_for('recruiter_dashboard'))
    return render_template('create_job.html')

@app.route('/job/<int:job_id>/candidates')
def job_candidates(job_id):
    if 'user_id' not in session or session.get('user_role') != 'recruiter':
        return redirect(url_for('login'))
    conn = get_db()
    job = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    all_resumes = conn.execute("SELECT r.*, u.name as user_name FROM resumes r JOIN users u ON r.user_id = u.id").fetchall()

    job_skills = [s.strip().lower() for s in job['required_skills'].split(',') if s.strip()]
    ranked = []
    for resume in all_resumes:
        resume_skills = [s.strip().lower() for s in resume['skills'].split(',') if s.strip()] if resume['skills'] else []
        result = calculate_match_score(resume['raw_text'] or '', job['description'], resume_skills, job_skills)
        ranked.append({
            'resume': resume,
            'score': result['score'],
            'matched': result['matched_skills'],
            'missing': result['missing_skills']
        })
    ranked = sorted(ranked, key=lambda x: x['score'], reverse=True)
    conn.close()
    return render_template('job_candidates.html', job=job, ranked=ranked)

# ─── API ROUTES ────────────────────────────────────────────────────────────────

@app.route('/api/skills/<int:resume_id>')
def api_skills(resume_id):
    conn = get_db()
    resume = conn.execute("SELECT skills FROM resumes WHERE id = ?", (resume_id,)).fetchone()
    conn.close()
    if resume:
        skills = [s.strip() for s in resume['skills'].split(',') if s.strip()]
        return jsonify({'skills': skills})
    return jsonify({'skills': []})

@app.route('/api/dashboard-stats')
def api_dashboard_stats():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    total_resumes = conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
    total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    avg_score = conn.execute("SELECT AVG(score) FROM resumes").fetchone()[0] or 0
    categories = conn.execute("SELECT category, COUNT(*) as count FROM resumes GROUP BY category").fetchall()
    conn.close()
    return jsonify({
        'total_resumes': total_resumes,
        'total_jobs': total_jobs,
        'avg_score': round(avg_score, 1),
        'categories': [{'name': r['category'] or 'Unknown', 'count': r['count']} for r in categories]
    })

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('database', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    init_db()
    app.run(debug=True, port=5000)
