from utils.matcher import calculate_match_score, rank_candidates


def test_matcher_reports_matched_and_missing_skills():
    result = calculate_match_score(
        "Python developer with SQL, Flask and Docker project experience",
        "We need a Python developer who knows Flask, SQL and AWS.",
        ["python", "flask", "sql", "docker"],
        ["Python", "Flask", "SQL", "AWS"],
    )
    assert result["total_required"] == 4
    assert result["total_matched"] == 3
    assert "Aws" in result["missing_skills"]
    assert 0 <= result["score"] <= 100
    assert "caution" in result["explanation"]


def test_rank_candidates_descending():
    ranked = rank_candidates([{"score": 30}, {"score": 90}, {"score": 55}])
    assert [item["score"] for item in ranked] == [90, 55, 30]
