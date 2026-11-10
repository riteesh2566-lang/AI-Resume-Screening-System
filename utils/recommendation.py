"""
recommendation.py - Missing skill recommendations, course suggestions,
                    resume category prediction, and AI feedback generation
"""

# ─── COURSE RECOMMENDATIONS DATABASE ────────────────────────────────────────────

COURSE_RECOMMENDATIONS = {
    'docker': [
        {'title': 'Docker Mastery: with Kubernetes + Swarm', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/docker-mastery/', 'level': 'Beginner'},
        {'title': 'Docker for Beginners', 'platform': 'YouTube', 'url': 'https://www.youtube.com/results?search_query=docker+tutorial', 'level': 'Beginner'},
    ],
    'aws': [
        {'title': 'AWS Certified Solutions Architect', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/aws-certified-solutions-architect-associate/', 'level': 'Intermediate'},
        {'title': 'AWS Free Tier & Training', 'platform': 'AWS', 'url': 'https://aws.amazon.com/training/free/', 'level': 'All Levels'},
    ],
    'machine learning': [
        {'title': 'Machine Learning Specialization', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/machine-learning-introduction', 'level': 'Beginner'},
        {'title': 'Fast.ai Practical Deep Learning', 'platform': 'Fast.ai', 'url': 'https://course.fast.ai/', 'level': 'Intermediate'},
    ],
    'tensorflow': [
        {'title': 'TensorFlow Developer Certificate', 'platform': 'Coursera', 'url': 'https://www.coursera.org/professional-certificates/tensorflow-in-practice', 'level': 'Intermediate'},
        {'title': 'TensorFlow Official Tutorials', 'platform': 'TensorFlow.org', 'url': 'https://www.tensorflow.org/tutorials', 'level': 'All Levels'},
    ],
    'pytorch': [
        {'title': 'PyTorch for Deep Learning', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/pytorch-for-deep-learning/', 'level': 'Intermediate'},
        {'title': 'Official PyTorch Tutorials', 'platform': 'PyTorch.org', 'url': 'https://pytorch.org/tutorials/', 'level': 'All Levels'},
    ],
    'kubernetes': [
        {'title': 'Kubernetes for Beginners', 'platform': 'KodeKloud', 'url': 'https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners/', 'level': 'Beginner'},
        {'title': 'CKA Certification', 'platform': 'Linux Foundation', 'url': 'https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/', 'level': 'Advanced'},
    ],
    'react': [
        {'title': 'React - The Complete Guide', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/react-the-complete-guide-incl-redux/', 'level': 'Beginner'},
        {'title': 'Official React Docs', 'platform': 'React.dev', 'url': 'https://react.dev/learn', 'level': 'Beginner'},
    ],
    'sql': [
        {'title': 'The Complete SQL Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/the-complete-sql-bootcamp/', 'level': 'Beginner'},
        {'title': 'SQLZoo Interactive SQL', 'platform': 'SQLZoo', 'url': 'https://sqlzoo.net/', 'level': 'Beginner'},
    ],
    'python': [
        {'title': 'Python Bootcamp', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/complete-python-bootcamp/', 'level': 'Beginner'},
        {'title': 'Python.org Official Tutorial', 'platform': 'Python.org', 'url': 'https://docs.python.org/3/tutorial/', 'level': 'Beginner'},
    ],
    'power bi': [
        {'title': 'Microsoft Power BI - Full Course', 'platform': 'YouTube', 'url': 'https://www.youtube.com/results?search_query=power+bi+full+course', 'level': 'Beginner'},
        {'title': 'Power BI Learning Path', 'platform': 'Microsoft Learn', 'url': 'https://learn.microsoft.com/en-us/training/powerplatform/power-bi', 'level': 'All Levels'},
    ],
    'flask': [
        {'title': 'Flask Web Development with Python', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/python-and-flask-bootcamp/', 'level': 'Beginner'},
        {'title': 'Flask Official Documentation', 'platform': 'Flask.palletsprojects.com', 'url': 'https://flask.palletsprojects.com/en/latest/tutorial/', 'level': 'Beginner'},
    ],
    'django': [
        {'title': 'Django for Everybody Specialization', 'platform': 'Coursera', 'url': 'https://www.coursera.org/specializations/django', 'level': 'Beginner'},
    ],
    'git': [
        {'title': 'Git & GitHub Crash Course', 'platform': 'freeCodeCamp', 'url': 'https://www.freecodecamp.org/news/git-and-github-crash-course/', 'level': 'Beginner'},
    ],
    'tableau': [
        {'title': 'Tableau 2024 A-Z', 'platform': 'Udemy', 'url': 'https://www.udemy.com/course/tableau10/', 'level': 'Beginner'},
    ],
    'default': [
        {'title': 'Search on Coursera', 'platform': 'Coursera', 'url': 'https://www.coursera.org', 'level': 'All Levels'},
        {'title': 'Search on Udemy', 'platform': 'Udemy', 'url': 'https://www.udemy.com', 'level': 'All Levels'},
    ]
}

# ─── JOB CATEGORY PREDICTION ─────────────────────────────────────────────────────

CATEGORY_SKILL_MAP = {
    'Data Scientist': ['machine learning', 'python', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'statistics', 'r', 'data analysis', 'sklearn', 'scikit-learn'],
    'ML Engineer': ['tensorflow', 'pytorch', 'keras', 'machine learning', 'deep learning', 'mlflow', 'model deployment', 'python', 'scikit-learn'],
    'Web Developer': ['html', 'css', 'javascript', 'react', 'angular', 'vue', 'node.js', 'bootstrap', 'typescript', 'redux'],
    'Python Developer': ['python', 'flask', 'django', 'fastapi', 'rest api', 'sql', 'pytest'],
    'Java Developer': ['java', 'spring', 'spring boot', 'maven', 'hibernate', 'microservices', 'junit'],
    'DevOps Engineer': ['docker', 'kubernetes', 'aws', 'ci/cd', 'jenkins', 'terraform', 'ansible', 'linux', 'git'],
    'Data Analyst': ['sql', 'excel', 'power bi', 'tableau', 'python', 'pandas', 'data visualization', 'statistics'],
    'AI Engineer': ['nlp', 'computer vision', 'hugging face', 'transformers', 'deep learning', 'machine learning', 'openai', 'llm'],
    'Full Stack Developer': ['react', 'node.js', 'sql', 'mongodb', 'flask', 'django', 'html', 'css', 'javascript', 'docker'],
    'Mobile Developer': ['android', 'ios', 'react native', 'flutter', 'swift', 'kotlin'],
    'Cloud Engineer': ['aws', 'azure', 'gcp', 'terraform', 'kubernetes', 'docker', 'cloud computing'],
    'Backend Developer': ['sql', 'api', 'python', 'java', 'node.js', 'flask', 'django', 'spring', 'microservices'],
}

def predict_category(skills, text=''):
    """Predict resume category using skill-based scoring."""
    if not skills:
        return 'General'
    skills_lower = [s.lower() for s in skills]
    text_lower = (text or '').lower()

    scores = {}
    for category, category_skills in CATEGORY_SKILL_MAP.items():
        score = sum(1 for skill in category_skills if skill in skills_lower or skill in text_lower)
        if score > 0:
            scores[category] = score

    if not scores:
        return 'General'
    return max(scores, key=scores.get)

# ─── RECOMMENDATIONS ─────────────────────────────────────────────────────────────

def get_recommendations(missing_skills):
    """Get course recommendations for missing skills."""
    recommendations = []
    seen_skills = set()
    for skill in missing_skills:
        skill_lower = skill.lower()
        if skill_lower in seen_skills:
            continue
        seen_skills.add(skill_lower)
        courses = COURSE_RECOMMENDATIONS.get(skill_lower, COURSE_RECOMMENDATIONS['default'])
        recommendations.append({
            'skill': skill,
            'courses': courses
        })
    return recommendations[:8]  # Limit to 8 recommendations

# ─── AI RESUME FEEDBACK ──────────────────────────────────────────────────────────

def generate_ai_feedback(resume):
    """Generate structured feedback for a resume."""
    text_lower = (resume['raw_text'] or '').lower() if resume['raw_text'] else ''
    skills_count = len([s for s in (resume['skills'] or '').split(',') if s.strip()])
    score = resume['score'] or 0
    feedback = {'strengths': [], 'improvements': [], 'missing_sections': []}

    # Strengths
    if resume['email']:
        feedback['strengths'].append('Contact information is clearly provided')
    if skills_count >= 8:
        feedback['strengths'].append(f'Strong skill set detected ({skills_count} skills)')
    if 'project' in text_lower:
        feedback['strengths'].append('Projects section found — great for demonstrating experience')
    if any(k in text_lower for k in ['certif', 'certified', 'certificate']):
        feedback['strengths'].append('Certifications detected — adds credibility')
    if any(k in text_lower for k in ['bachelor', 'master', 'phd', 'degree', 'b.tech', 'm.tech']):
        feedback['strengths'].append('Educational qualifications clearly mentioned')
    if score >= 75:
        feedback['strengths'].append('Overall resume quality is strong')

    # Improvements
    if skills_count < 5:
        feedback['improvements'].append('Add more technical skills relevant to your target role')
    if score < 60:
        feedback['improvements'].append('Resume quality score is below average — add more details')
    if not resume['phone']:
        feedback['improvements'].append('Add a phone number for easy recruiter contact')
    if len(text_lower) < 300:
        feedback['improvements'].append('Resume seems too short — add more details about your experience and projects')
    if not any(k in text_lower for k in ['github', 'linkedin', 'portfolio']):
        feedback['improvements'].append('Add GitHub, LinkedIn, or portfolio links')

    # Missing sections
    if 'project' not in text_lower:
        feedback['missing_sections'].append('Projects (highly recommended for freshers)')
    if not any(k in text_lower for k in ['certif', 'certificate']):
        feedback['missing_sections'].append('Certifications (e.g., AWS, Google, Microsoft)')
    if not any(k in text_lower for k in ['cloud', 'aws', 'azure', 'gcp', 'docker']):
        feedback['missing_sections'].append('Cloud/DevOps Skills (in high demand)')
    if not any(k in text_lower for k in ['volunteer', 'achievement', 'award']):
        feedback['missing_sections'].append('Achievements / Awards / Volunteering')

    if not feedback['strengths']:
        feedback['strengths'].append('Resume uploaded successfully for analysis')
    if not feedback['improvements']:
        feedback['improvements'].append('Resume looks well-structured!')

    return feedback
