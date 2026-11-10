# 🧠 ResumeAI — AI-Powered Resume Screening & Job Matching System

A full-stack AI system built with **Python, Flask, NLP, and Machine Learning** that:
- Extracts information from resumes (PDF/DOCX/TXT) using NLP
- Calculates job match scores using **TF-IDF + Cosine Similarity**
- Ranks candidates automatically
- Predicts resume category (Data Scientist, Web Developer, etc.)
- Recommends courses for missing skills
- Generates AI resume quality scores (0–100)

---

## 🚀 Quick Start (VS Code)

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000
```

---

## 🔐 Demo Login

| Role      | Email                | Password |
|-----------|----------------------|----------|
| Recruiter | recruiter@demo.com   | demo123  |
| Candidate | Register a new account | —      |

---

## 📂 Project Structure

```
resume_ai/
│
├── app.py                      ← Main Flask application
├── requirements.txt            ← Python dependencies
├── README.md
│
├── utils/
│   ├── parser.py               ← PDF/DOCX text extraction
│   ├── extractor.py            ← NLP: name, email, skills, score
│   ├── matcher.py              ← TF-IDF cosine similarity matching
│   └── recommendation.py      ← Course recs, category prediction, feedback
│
├── templates/
│   ├── base.html               ← Navbar, footer, flash messages
│   ├── index.html              ← Landing page
│   ├── login.html / register.html
│   ├── candidate_dashboard.html
│   ├── recruiter_dashboard.html
│   ├── resume_detail.html      ← Resume analysis + AI feedback
│   ├── match_result.html       ← Match score + recommendations
│   ├── job_candidates.html     ← Ranked candidate list
│   └── create_job.html
│
├── static/
│   ├── css/style.css           ← Custom styles
│   └── js/main.js              ← Frontend logic
│
├── uploads/                    ← Uploaded resume files (auto-created)
├── database/                   ← SQLite database (auto-created)
└── models/                     ← Reserved for ML model files
```

---

## ✨ Features

### Phase 1: Resume Upload
- Upload PDF, DOCX, DOC, TXT (up to 16MB)
- Drag & drop support
- Automatic text extraction via `pdfplumber` and `python-docx`

### Phase 2: NLP Information Extraction
- **Name** — heuristic line detection
- **Email** — regex pattern matching
- **Phone** — multi-format regex
- **Education** — keyword section detection
- **Experience** — keyword section detection

### Phase 3: Skill Extraction
- 100+ skills across 9 categories:
  - Programming Languages, Web Frontend, Web Backend
  - Databases, Cloud/DevOps, Data Science/ML
  - Business Intelligence, Mobile, Other
- Fuzzy matching for partial skill names

### Phase 4: Job Matching Engine
- **TF-IDF + Cosine Similarity** on full resume/job text (40% weight)
- **Skill overlap scoring** (60% weight)
- Combined weighted match percentage

### Phase 5: Candidate Ranking
- Automatically sorts all candidates by match score
- Gold/Silver/Bronze 🥇🥈🥉 ranking display

### Phase 6: Missing Skill Recommendations
- Identifies missing skills vs. job requirements
- Recommends courses from Udemy, Coursera, YouTube, official docs

### Advanced AI Features
- **Resume Score (0–100)** based on contact info, skills, education, experience, projects, certifications
- **Category Prediction** — Data Scientist, ML Engineer, Web Developer, DevOps, etc.
- **AI Resume Feedback** — Strengths, Improvements, Missing Sections

---

## 🗄️ Database Schema (SQLite)

**users** — id, name, email, password (hashed), role  
**resumes** — id, user_id, filename, raw_text, name, email, phone, skills, education, experience, score, category  
**jobs** — id, title, company, description, required_skills, created_by  
**job_matches** — id, resume_id, job_id, match_score, matched_skills, missing_skills

---

## 💻 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.8+, Flask |
| Database | SQLite (via Python's sqlite3) |
| NLP / Text | Regex, Custom TF-IDF, pdfplumber, python-docx |
| ML | Cosine Similarity, Skill-based category prediction |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js |
| Security | Werkzeug password hashing, Session management |

---

## 🔧 Troubleshooting

**PDF not extracting text?**
Install pdfplumber: `pip install pdfplumber`

**DOCX upload failing?**
Install python-docx: `pip install python-docx`

**Database error?**
Delete `database/resume_ai.db` and restart — it will be recreated.

**Port already in use?**
Change port in app.py: `app.run(debug=True, port=5001)`

---

## 📈 Future Enhancements
- spaCy Named Entity Recognition for better name/org extraction
- scikit-learn Random Forest for category prediction
- Resume PDF generation
- Email notifications to candidates
- Interview scheduling integration
- REST API for mobile app

---

Built with ❤️ using Python & Flask
