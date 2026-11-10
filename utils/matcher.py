"""Hybrid resume/job matching: explicit skill evidence + lexical + optional semantic similarity.

Semantic embeddings are optional. Install requirements-ai.txt to enable the
Sentence Transformers encoder; otherwise the engine transparently uses TF-IDF.
Scores are decision-support signals, not automated hiring decisions.
"""
from __future__ import annotations

import math
import os
import re
from collections import Counter
from functools import lru_cache

STOP_WORDS = {
    "i", "me", "my", "myself", "we", "our", "ours", "you", "your", "he", "she", "they",
    "it", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "a", "an", "the", "and", "but", "if", "or",
    "as", "of", "at", "by", "for", "with", "about", "into", "through", "during", "before",
    "after", "to", "from", "in", "out", "on", "off", "over", "under", "will", "should",
    "can", "could", "would", "also", "than", "too", "very", "looking", "seeking", "required",
    "requirement", "candidate", "experience", "work", "team", "role", "position", "responsibility",
}


def _neutralize_contact_details(text: str) -> str:
    """Remove contact identifiers before comparing resume text to a job."""
    text = re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", " ", text, flags=re.I)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text, flags=re.I)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)", " ", text)
    return text


def preprocess(text):
    text = _neutralize_contact_details(text or "").lower()
    tokens = re.sub(r"[^a-z0-9+#.\s]", " ", text).split()
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 1]


def compute_tf(tokens):
    counts = Counter(tokens)
    total = max(len(tokens), 1)
    return {term: count / total for term, count in counts.items()}


def compute_idf(documents):
    total = len(documents)
    terms = set(term for doc in documents for term in doc)
    return {term: math.log((total + 1) / (sum(term in doc for doc in documents) + 1)) + 1 for term in terms}


def compute_tfidf_vector(tokens, idf):
    tf = compute_tf(tokens)
    return {term: value * idf.get(term, 1.0) for term, value in tf.items()}


def cosine_similarity(vec1, vec2):
    if not vec1 or not vec2:
        return 0.0
    dot = sum(value * vec2.get(term, 0.0) for term, value in vec1.items())
    mag1 = math.sqrt(sum(value * value for value in vec1.values()))
    mag2 = math.sqrt(sum(value * value for value in vec2.values()))
    return dot / (mag1 * mag2) if mag1 and mag2 else 0.0


def _tfidf_similarity(text_a, text_b):
    tokens_a, tokens_b = preprocess(text_a), preprocess(text_b)
    if not tokens_a or not tokens_b:
        return 0.0
    idf = compute_idf([tokens_a, tokens_b])
    return max(0.0, min(1.0, cosine_similarity(compute_tfidf_vector(tokens_a, idf), compute_tfidf_vector(tokens_b, idf))))


@lru_cache(maxsize=1)
def _load_sentence_model():
    from sentence_transformers import SentenceTransformer
    model_name = os.getenv("SENTENCE_TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    return SentenceTransformer(model_name)


def _semantic_similarity(text_a, text_b):
    """Return (similarity, enabled). A missing optional dependency/model falls back cleanly."""
    if os.getenv("USE_SEMANTIC_MODEL", "false").lower() != "true":
        return 0.0, False
    try:
        model = _load_sentence_model()
        vectors = model.encode([_neutralize_contact_details(text_a), _neutralize_contact_details(text_b)], normalize_embeddings=True)
        score = float((vectors[0] * vectors[1]).sum())
        return max(0.0, min(1.0, score)), True
    except Exception:
        return 0.0, False


def _fuzzy_match(a, b):
    a, b = (a or "").lower().strip(), (b or "").lower().strip()
    if not a or not b:
        return False
    if a == b or (len(a) >= 4 and (a in b or b in a)):
        return True
    if min(len(a), len(b)) < 4:
        return False
    grams_a = {a[i:i + 2] for i in range(len(a) - 1)}
    grams_b = {b[i:i + 2] for i in range(len(b) - 1)}
    return (2 * len(grams_a & grams_b) / (len(grams_a) + len(grams_b))) >= 0.82


def calculate_match_score(resume_text, job_description, resume_skills, job_skills):
    """Return explainable match components; no protected attributes are used intentionally."""
    resume_skills_norm = list(dict.fromkeys((s or "").lower().strip() for s in resume_skills if s and s.strip()))
    job_skills_norm = list(dict.fromkeys((s or "").lower().strip() for s in job_skills if s and s.strip()))
    matched, missing = [], []
    for required in job_skills_norm:
        if any(_fuzzy_match(required, candidate) for candidate in resume_skills_norm):
            matched.append(required.title())
        else:
            missing.append(required.title())

    skill_score = len(matched) / len(job_skills_norm) * 100 if job_skills_norm else 0.0
    tfidf_score = _tfidf_similarity(resume_text or "", job_description or "") * 100
    semantic_raw, semantic_enabled = _semantic_similarity(resume_text or "", job_description or "")
    if semantic_enabled:
        semantic_score = semantic_raw * 100
        final = (skill_score * 0.55) + (tfidf_score * 0.20) + (semantic_score * 0.25)
        method = "Hybrid: skills + TF-IDF + Sentence Transformers"
    else:
        semantic_score = None
        final = (skill_score * 0.60) + (tfidf_score * 0.40)
        method = "Hybrid: skills + TF-IDF (semantic model not enabled)"

    final = round(max(0.0, min(100.0, final)), 1)
    return {
        "score": final,
        "skill_score": round(skill_score, 1),
        "text_score": round(tfidf_score, 1),
        "semantic_score": round(semantic_score, 1) if semantic_score is not None else None,
        "matched_skills": matched,
        "missing_skills": missing,
        "total_required": len(job_skills_norm),
        "total_matched": len(matched),
        "matching_method": method,
        "explanation": {
            "skills": "Coverage of explicitly listed required skills.",
            "text": "Lexical relevance between resume content and job description.",
            "semantic": "Meaning-level similarity from a sentence embedding model." if semantic_enabled else "Not enabled; install requirements-ai.txt and set USE_SEMANTIC_MODEL=true.",
            "caution": "Use as decision support only. A recruiter must review the resume and assess job-related evidence."
        }
    }


def rank_candidates(candidates_data):
    return sorted(candidates_data, key=lambda item: item.get("score", 0), reverse=True)
