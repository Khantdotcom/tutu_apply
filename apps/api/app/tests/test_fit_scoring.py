from app.schemas.models import JobPost
from app.services.fit_scoring import get_default_fit_evaluator, score_job


def test_fit_score_output_is_structured_and_evidence_backed() -> None:
    job = JobPost(
        id="job_1",
        title="Junior Backend Engineer",
        company="Acme",
        location="Remote",
        requirements=["Python", "SQL", "APIs"],
    )
    result = score_job(
        evaluator=get_default_fit_evaluator(),
        job=job,
        user_id="demo-user",
        target_role="Backend Engineer",
        career_stage="Student",
        experience_items=[{"title": "API app", "skills": ["Python", "SQL", "APIs"]}],
    )
    assert result.score >= 66
    assert result.confidence > 0
    assert result.matched_requirements[0].evidence
    assert result.prompt_version == "fit-score-v1-stub"
