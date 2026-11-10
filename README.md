# ResumeAI — Resume Analysis & Job Matching Platform

A Flask web application that parses candidate resumes, extracts job-related skills, compares resume evidence with job descriptions, and presents explainable match signals to candidates and recruiters.

> **Responsible-use note:** Match percentages are assistive signals, not hiring decisions. Recruiters should review the underlying evidence and assess candidates consistently against job-related criteria. Do not use protected or sensitive personal characteristics to rank candidates.

## Features

- Candidate registration and login with Werkzeug password hashing.
- Candidate resume upload (PDF, DOCX, TXT; 16 MB maximum).
- Resume text extraction and structured extraction of contact details, education, experience, links and skills.
- Resume completeness feedback and skill-based role-category suggestions.
- Job posting and candidate dashboards.
- Explainable job matching using explicit skill coverage and TF-IDF cosine similarity.
- Optional semantic similarity using Sentence Transformers.
- Missing-skill identification and learning-resource suggestions.
- SQLite persistence.
- CSRF protection, role-based route access, candidate resume ownership checks, secure upload filenames and environment-based secrets.

## Technology

- Python 3.10+
- Flask, Flask-WTF, Werkzeug, python-dotenv
- SQLite
- pdfplumber, python-docx
- Optional: Sentence Transformers (`all-MiniLM-L6-v2`)
- HTML, CSS, Bootstrap, JavaScript, Chart.js

## Run locally (Windows PowerShell)

```powershell
# From the project root
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Generate a unique Flask secret and set it in `.env`:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Open `.env` and replace `SECRET_KEY`. Set a private recruiter account by filling in `BOOTSTRAP_RECRUITER_EMAIL` and `BOOTSTRAP_RECRUITER_PASSWORD` with your own values. Do not commit `.env`.

Then run:

```powershell
python app.py
```

Open `http://127.0.0.1:5000`.

The database and upload directories are created automatically. Demo job listings are seeded only when the jobs table is empty. Public registration creates candidate accounts only; recruiter accounts must be provisioned using the private environment variables.

## Enable semantic matching (optional)

The default installation is lightweight and uses skills + TF-IDF matching. To enable the embedding model:

```powershell
pip install -r requirements-ai.txt
```

Set these values in `.env`:

```env
USE_SEMANTIC_MODEL=true
SENTENCE_TRANSFORMER_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The first semantic comparison downloads the model and may take time. If the optional package/model is unavailable, the matcher automatically falls back to skills + TF-IDF. When semantic mode is active, the score weights are 55% skill coverage, 20% TF-IDF similarity and 25% semantic similarity. Without semantic mode, the weights are 60% skill coverage and 40% TF-IDF similarity.

## Recruiter setup

Recruiter registration is intentionally disabled on the public registration page. Before the first run, set these variables in `.env`:

```env
BOOTSTRAP_RECRUITER_NAME=Recruiter Admin
BOOTSTRAP_RECRUITER_EMAIL=your-private-recruiter-email@example.com
BOOTSTRAP_RECRUITER_PASSWORD=use-a-unique-strong-password
```

Restart the application. The account is created or its password is updated. Remove these bootstrap variables after provisioning if you do not want them retained in the environment. Never publish the real credentials.

## Project structure

```text
resume_ai/
├── app.py
├── wsgi.py
├── requirements.txt
├── requirements-ai.txt
├── .env.example
├── .gitignore
├── README.md
├── database/              # SQLite database created at runtime (not committed)
├── uploads/               # Private uploaded resumes (not committed)
├── utils/
│   ├── parser.py
│   ├── extractor.py
│   ├── matcher.py
│   └── recommendation.py
├── templates/
└── static/
```

## Security and privacy notes

- `.env`, SQLite databases, uploaded resumes and model artifacts are excluded by `.gitignore`.
- Do not put real candidate resumes or production data in a public repository.
- Use HTTPS and set `COOKIE_SECURE=true` in production.
- Configure a strong unique `SECRET_KEY` before deployment.
- The app stores extracted resume text in SQLite. Restrict database and backup access and define a retention/deletion policy before using real candidate data.
- A public demo should use synthetic sample resumes only.

## Deployment

A WSGI entry point is provided as `wsgi.py`. Example command:

```bash
gunicorn wsgi:app
```

Set all required environment variables in the hosting provider's secret/environment settings. Use persistent storage for SQLite and uploads, or replace them with managed database/object storage for multi-instance production deployments. Set `COOKIE_SECURE=true` when served over HTTPS.

## Limitations

- Resume field and skill extraction uses heuristics and a curated skill vocabulary; extraction can miss context or produce false positives.
- Semantic matching is optional and measures textual similarity, not candidate ability.
- The resume completeness score measures the presence of selected resume sections; it is not a measure of a person's quality or employability.
- The project is a portfolio prototype, not a validated or legally compliant hiring decision system.

## License

Add a license before accepting external contributions or redistributing the project.
