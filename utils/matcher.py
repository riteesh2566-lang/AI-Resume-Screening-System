"""
matcher.py - TF-IDF Cosine Similarity based job matching engine
"""
import re
import math
from collections import Counter

# ─── TEXT PREPROCESSING ──────────────────────────────────────────────────────────

STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your',
    'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her',
    'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs',
    'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those',
    'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
    'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with',
    'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after',
    'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over',
    'under', 'again', 'further', 'then', 'once', 'will', 'just', 'should', 'now',
    'also', 'than', 'too', 'very', 'can', 'need', 'looking', 'seeking', 'required',
    'requirement', 'candidate', 'experience', 'work', 'team', 'role', 'position'
}

def preprocess(text):
    """Tokenize and clean text for TF-IDF."""
    if not text:
        return []
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    return tokens

def compute_tf(tokens):
    """Compute term frequency."""
    tf = Counter(tokens)
    total = len(tokens) if tokens else 1
    return {term: count / total for term, count in tf.items()}

def compute_idf(documents):
    """Compute inverse document frequency across a corpus of token lists."""
    N = len(documents)
    idf = {}
    all_terms = set(term for doc in documents for term in doc)
    for term in all_terms:
        doc_count = sum(1 for doc in documents if term in doc)
        idf[term] = math.log((N + 1) / (doc_count + 1)) + 1
    return idf

def compute_tfidf_vector(tokens, idf):
    """Compute TF-IDF vector."""
    tf = compute_tf(tokens)
    return {term: tf[term] * idf.get(term, 1) for term in tf}

def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two TF-IDF vectors."""
    if not vec1 or not vec2:
        return 0.0
    all_keys = set(vec1.keys()) | set(vec2.keys())
    dot_product = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in all_keys)
    mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)

# ─── MATCH SCORING ───────────────────────────────────────────────────────────────

def calculate_match_score(resume_text, job_description, resume_skills, job_skills):
    """
    Calculate comprehensive match score between resume and job.
    Combines:
      - TF-IDF cosine similarity on full text (40%)
      - Skill overlap score (60%)
    Returns dict with score, matched_skills, missing_skills.
    """
    # Skill matching (60% weight)
    resume_skills_lower = [s.lower().strip() for s in resume_skills]
    job_skills_lower = [s.lower().strip() for s in job_skills]

    matched_skills = []
    missing_skills = []
    for skill in job_skills_lower:
        # Check exact or partial match
        found = any(
            skill in rs or rs in skill or _fuzzy_match(skill, rs)
            for rs in resume_skills_lower
        )
        if found:
            matched_skills.append(skill.title())
        else:
            missing_skills.append(skill.title())

    skill_score = (len(matched_skills) / len(job_skills_lower) * 100) if job_skills_lower else 0

    # TF-IDF text similarity (40% weight)
    text_similarity = 0.0
    if resume_text and job_description:
        resume_tokens = preprocess(resume_text)
        job_tokens = preprocess(job_description)
        if resume_tokens and job_tokens:
            idf = compute_idf([resume_tokens, job_tokens])
            resume_vec = compute_tfidf_vector(resume_tokens, idf)
            job_vec = compute_tfidf_vector(job_tokens, idf)
            text_similarity = cosine_similarity(resume_vec, job_vec) * 100

    # Weighted final score
    final_score = round((skill_score * 0.60) + (text_similarity * 0.40), 1)
    final_score = min(final_score, 100)

    return {
        'score': final_score,
        'skill_score': round(skill_score, 1),
        'text_score': round(text_similarity, 1),
        'matched_skills': matched_skills,
        'missing_skills': missing_skills,
        'total_required': len(job_skills_lower),
        'total_matched': len(matched_skills)
    }

def _fuzzy_match(a, b):
    """Simple fuzzy matching - checks if strings share 80%+ characters."""
    if not a or not b:
        return False
    shorter, longer = (a, b) if len(a) < len(b) else (b, a)
    if len(shorter) < 3:
        return False
    # Check if shorter is a prefix of longer
    if longer.startswith(shorter):
        return True
    # Bigram similarity
    def bigrams(s):
        return set(s[i:i+2] for i in range(len(s)-1))
    ba, bb = bigrams(a), bigrams(b)
    if not ba or not bb:
        return False
    overlap = len(ba & bb)
    similarity = (2.0 * overlap) / (len(ba) + len(bb))
    return similarity >= 0.75

def rank_candidates(candidates_data):
    """
    Rank a list of candidate dicts by match score.
    Each dict: {name, resume_id, skills, raw_text}
    Returns sorted list with scores.
    """
    return sorted(candidates_data, key=lambda x: x.get('score', 0), reverse=True)
