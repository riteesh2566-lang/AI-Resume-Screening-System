"""
extractor.py - NLP-based information and skill extraction from resume text
"""
import re

# ─── SKILL DATABASE ──────────────────────────────────────────────────────────────
SKILLS_DATABASE = {
    'programming_languages': [
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'ruby', 'php',
        'swift', 'kotlin', 'go', 'rust', 'scala', 'r', 'matlab', 'perl', 'bash', 'shell',
        'powershell', 'dart', 'lua', 'haskell', 'julia'
    ],
    'web_frontend': [
        'html', 'css', 'react', 'angular', 'vue', 'vue.js', 'react.js', 'next.js',
        'nuxt.js', 'bootstrap', 'tailwind', 'jquery', 'sass', 'less', 'webpack',
        'redux', 'graphql', 'typescript', 'material ui', 'ant design'
    ],
    'web_backend': [
        'flask', 'django', 'fastapi', 'express', 'node.js', 'nodejs', 'spring',
        'spring boot', 'laravel', 'rails', 'ruby on rails', 'asp.net', '.net',
        'nestjs', 'fastify', 'gin', 'fiber', 'rest api', 'restful', 'graphql'
    ],
    'databases': [
        'sql', 'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'oracle', 'sql server', 'dynamodb', 'firebase', 'supabase',
        'mariadb', 'neo4j', 'influxdb', 'nosql'
    ],
    'cloud_devops': [
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins',
        'ci/cd', 'terraform', 'ansible', 'linux', 'unix', 'git', 'github', 'gitlab',
        'bitbucket', 'nginx', 'apache', 'heroku', 'vercel', 'netlify', 'cloudflare'
    ],
    'data_science_ml': [
        'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'keras',
        'scikit-learn', 'sklearn', 'pandas', 'numpy', 'matplotlib', 'seaborn',
        'nlp', 'computer vision', 'opencv', 'hugging face', 'transformers',
        'neural networks', 'random forest', 'xgboost', 'lightgbm', 'svm',
        'statistics', 'data analysis', 'data visualization', 'feature engineering',
        'model deployment', 'mlflow', 'wandb', 'jupyter', 'colab'
    ],
    'business_intelligence': [
        'power bi', 'tableau', 'looker', 'qlikview', 'excel', 'google analytics',
        'data studio', 'metabase', 'superset', 'dbt', 'airflow', 'spark', 'hadoop'
    ],
    'mobile': [
        'android', 'ios', 'react native', 'flutter', 'swift', 'kotlin', 'xamarin',
        'ionic', 'cordova', 'mobile development'
    ],
    'other': [
        'agile', 'scrum', 'jira', 'trello', 'figma', 'adobe xd', 'photoshop',
        'selenium', 'pytest', 'junit', 'mocha', 'jest', 'cypress', 'postman',
        'swagger', 'microservices', 'api', 'blockchain', 'cybersecurity',
        'penetration testing', 'cloud computing', 'iot', 'arduino', 'raspberry pi'
    ]
}

ALL_SKILLS = []
for category_skills in SKILLS_DATABASE.values():
    ALL_SKILLS.extend(category_skills)

# ─── INFORMATION EXTRACTION ──────────────────────────────────────────────────────

def extract_information(text):
    """Extract structured information from resume text."""
    if not text:
        return {}
    return {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'education': extract_education(text),
        'experience': extract_experience(text),
        'links': extract_links(text)
    }

def extract_email(text):
    """Extract email address."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else ''

def extract_phone(text):
    """Extract phone number."""
    patterns = [
        r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\+\d{10,13}',
        r'\b\d{10}\b'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group().strip()
    return ''

def extract_name(text):
    """Extract candidate name (heuristic: first non-empty line that looks like a name)."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    for line in lines[:5]:
        # Skip lines that contain common non-name words
        skip_words = ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'objective',
                      'summary', '@', 'http', 'phone', 'email', 'address']
        if any(w in line.lower() for w in skip_words):
            continue
        # Name usually has 2-4 words, all capitalized-ish
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return line
    return lines[0] if lines else ''

def extract_education(text):
    """Extract education section."""
    edu_keywords = ['education', 'academic', 'qualification', 'degree', 'university',
                    'college', 'institute', 'school', 'bachelor', 'master', 'phd',
                    'b.tech', 'm.tech', 'bsc', 'msc', 'b.e', 'm.e', 'mba']
    lines = text.split('\n')
    edu_lines = []
    in_section = False
    for line in lines:
        line_lower = line.lower()
        if any(k in line_lower for k in ['education', 'academic', 'qualification']):
            in_section = True
        elif in_section and any(k in line_lower for k in ['experience', 'skills', 'project', 'certif', 'work']):
            in_section = False
        if any(k in line_lower for k in edu_keywords):
            edu_lines.append(line.strip())
        elif in_section and line.strip():
            edu_lines.append(line.strip())
    return ' | '.join(edu_lines[:5]) if edu_lines else 'Not specified'

def extract_experience(text):
    """Extract experience section."""
    exp_keywords = ['experience', 'work history', 'employment', 'internship',
                    'worked at', 'working at', 'position', 'role']
    lines = text.split('\n')
    exp_lines = []
    in_section = False
    for line in lines:
        line_lower = line.lower()
        if any(k in line_lower for k in ['experience', 'employment', 'work history']):
            in_section = True
        elif in_section and any(k in line_lower for k in ['education', 'skills', 'project', 'certif']):
            in_section = False
        if in_section and line.strip():
            exp_lines.append(line.strip())
    return ' | '.join(exp_lines[:8]) if exp_lines else 'Not specified'

def extract_links(text):
    """Extract URLs from text."""
    pattern = r'https?://[^\s)>]+'
    return re.findall(pattern, text)

# ─── SKILL EXTRACTION ────────────────────────────────────────────────────────────

def extract_skills(text):
    """Extract skills from resume text."""
    if not text:
        return []
    text_lower = text.lower()
    found_skills = []
    for skill in ALL_SKILLS:
        # Use word boundary matching for short skills to avoid false positives
        if len(skill) <= 3:
            pattern = r'\b' + re.escape(skill) + r'\b'
        else:
            pattern = re.escape(skill)
        if re.search(pattern, text_lower):
            # Normalize skill name
            normalized = skill.title()
            if normalized not in found_skills:
                found_skills.append(normalized)
    # Remove duplicates and sort
    seen = set()
    unique_skills = []
    for s in found_skills:
        sl = s.lower()
        if sl not in seen:
            seen.add(sl)
            unique_skills.append(s)
    return sorted(unique_skills)

# ─── RESUME SCORE GENERATOR ──────────────────────────────────────────────────────

def calculate_resume_score(info, skills, text):
    """
    Calculate resume quality score out of 100.
    Criteria: Contact Info (20), Skills (25), Education (15),
               Experience (20), Projects (10), Certifications (10)
    """
    score = 0
    text_lower = text.lower() if text else ''

    # Contact info (20 pts)
    if info.get('email'): score += 8
    if info.get('phone'): score += 7
    if info.get('name') and len(info['name']) > 2: score += 5

    # Skills (25 pts)
    skill_count = len(skills)
    if skill_count >= 15: score += 25
    elif skill_count >= 10: score += 20
    elif skill_count >= 6: score += 15
    elif skill_count >= 3: score += 10
    elif skill_count >= 1: score += 5

    # Education (15 pts)
    edu_keywords = ['bachelor', 'master', 'phd', 'degree', 'university', 'college', 'b.tech', 'm.tech', 'bsc', 'msc']
    if any(k in text_lower for k in edu_keywords): score += 15

    # Experience (20 pts)
    exp_keywords = ['experience', 'worked', 'internship', 'employed', 'engineer', 'developer', 'analyst']
    exp_count = sum(1 for k in exp_keywords if k in text_lower)
    if exp_count >= 3: score += 20
    elif exp_count >= 2: score += 15
    elif exp_count >= 1: score += 10

    # Projects (10 pts)
    if 'project' in text_lower: score += 10

    # Certifications (10 pts)
    cert_keywords = ['certif', 'certified', 'certificate', 'aws certified', 'google certified', 'microsoft certified']
    if any(k in text_lower for k in cert_keywords): score += 10

    return min(score, 100)
