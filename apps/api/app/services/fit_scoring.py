from app.schemas.models import FitScoreAIInput, FitScoreOutput, JobPost
from app.services.ai.fit_evaluator import DeterministicFitEvaluator, FitEvaluator


def build_candidate_evidence(target_role: str, career_stage: str, experience_items: list[dict]) -> list[str]:
    evidence = [
        f"target_role:{target_role}",
        f"career_stage:{career_stage}",
    ]
    for exp in experience_items:
        for skill in exp.get("skills", []):
            evidence.append(f"experience_skill:{skill}")
        if exp.get("title"):
            evidence.append(f"experience_title:{exp['title']}")
    return evidence


def score_job(
    evaluator: FitEvaluator,
    job: JobPost,
    user_id: str,
    target_role: str,
    career_stage: str,
    experience_items: list[dict],
) -> FitScoreOutput:
    payload = FitScoreAIInput(
        user_id=user_id,
        job_id=job.id,
        requirements=job.requirements,
        candidate_evidence=build_candidate_evidence(target_role, career_stage, experience_items),
    )
    return evaluator.evaluate(payload)


def get_default_fit_evaluator() -> FitEvaluator:
    return DeterministicFitEvaluator()
