import json
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile

from app.core.config import settings
from app.core.supabase import get_supabase_client
from app.db.sqlite import (
    coach_unlocked,
    create_application_draft,
    create_application_from_saved_job,
    create_artifact,
    create_experience_item,
    create_generation_run,
    create_readiness_plan,
    delete_experience_item,
    get_application_draft,
    get_onboarding_profile,
    get_path as db_get_path,
    init_db,
    list_applications,
    list_experience_items,
    list_generation_history,
    list_readiness_plans,
    list_story_cards,
    refresh_story_cards,
    retrieve_story_cards_for_job,
    save_job_record,
    save_onboarding,
    seed_demo_onboarding,
    update_experience_item,
    update_readiness_mission_status,
)
from app.schemas.models import (
    ApplicationCreateRequest,
    ApplicationDraftCreateRequest,
    CoverLetterGenerateRequest,
    ExperienceItemInput,
    ExperienceItemUpdate,
    FitScoreRequest,
    JobPost,
    Mission,
    OnboardingCompleteResponse,
    PathResponse,
    ReadinessMissionUpdateRequest,
    ReadinessPlanCreateRequest,
    ShortAnswerGenerateRequest,
    StoryRetrievalRequest,
)
from app.services.ai.readiness_coach import DeterministicReadinessCoach
from app.services.application_generator import (
    generate_cover_letter,
    generate_short_answer,
    get_default_application_generator,
)
from app.services.fit_scoring import get_default_fit_evaluator, score_job
from app.services.repositories import DATA

app = FastAPI(title=settings.app_name)
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
fit_evaluator = get_default_fit_evaluator()
application_generator = get_default_application_generator()
readiness_coach = DeterministicReadinessCoach()


@app.on_event("startup")
def startup() -> None:
    init_db()
    seed_demo_onboarding()


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "supabase_configured": bool(get_supabase_client())}


@app.get("/path", response_model=PathResponse)
def get_path(user_id: str = "demo-user") -> PathResponse:
    db_path = db_get_path(user_id)
    if db_path:
        return PathResponse(**db_path)
    return PathResponse(
        chapter="Chapter 1: Find the Right Role",
        daily_quest="Save 1 relevant job",
        missions=[
            Mission(id="m1", title="Complete onboarding", xp=50, status="done"),
            Mission(id="m2", title="Save 3 jobs", xp=80, status="todo"),
            Mission(id="m3", title="Add 2 story cards", xp=70, status="todo"),
        ],
        level=1,
        xp=120,
        streak_days=1,
    )


@app.post("/onboarding/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding(
    user_id: str = Form(...),
    target_role: str = Form(...),
    career_stage: str = Form(...),
    preferred_industries: str = Form(...),
    preferred_locations: str = Form(...),
    daily_commitment_minutes: int = Form(...),
    resume: UploadFile | None = File(default=None),
) -> OnboardingCompleteResponse:
    resume_path = None
    resume_name = None
    if resume is not None:
        resume_name = resume.filename
        destination = UPLOAD_DIR / f"{uuid4()}_{resume.filename}"
        destination.write_bytes(await resume.read())
        resume_path = str(destination)

    save_onboarding(
        {
            "user_id": user_id,
            "target_role": target_role,
            "career_stage": career_stage,
            "preferred_industries": json.dumps([i.strip() for i in preferred_industries.split(",") if i.strip()]),
            "preferred_locations": json.dumps([i.strip() for i in preferred_locations.split(",") if i.strip()]),
            "daily_commitment_minutes": daily_commitment_minutes,
            "resume_filename": resume_name,
            "resume_storage_path": resume_path,
        }
    )

    return OnboardingCompleteResponse(status="completed", chapter="Chapter 1: Find the Right Role", level=1)


@app.get("/vault/experience")
def api_list_experience(user_id: str = Query("demo-user")) -> list[dict]:
    return list_experience_items(user_id)


@app.post("/vault/experience")
def api_create_experience(payload: ExperienceItemInput) -> dict:
    item = create_experience_item(
        user_id=payload.user_id,
        title=payload.title,
        impact=payload.impact,
        skills=payload.skills,
        kind=payload.kind,
    )
    refresh_story_cards(payload.user_id)
    return item


@app.put("/vault/experience/{item_id}")
def api_update_experience(item_id: int, payload: ExperienceItemUpdate) -> dict:
    item = update_experience_item(
        item_id=item_id,
        user_id=payload.user_id,
        title=payload.title,
        impact=payload.impact,
        skills=payload.skills,
        kind=payload.kind,
    )
    if not item:
        raise HTTPException(status_code=404, detail="Experience item not found")
    refresh_story_cards(payload.user_id)
    return item


@app.delete("/vault/experience/{item_id}")
def api_delete_experience(item_id: int, user_id: str = Query("demo-user")) -> dict[str, str]:
    if not delete_experience_item(item_id, user_id):
        raise HTTPException(status_code=404, detail="Experience item not found")
    refresh_story_cards(user_id)
    return {"status": "deleted"}


@app.post("/story-cards/refresh")
def api_refresh_story_cards(user_id: str = Query("demo-user")) -> list[dict]:
    return refresh_story_cards(user_id)


@app.get("/story-cards")
def api_list_story_cards(user_id: str = Query("demo-user")) -> list[dict]:
    return list_story_cards(user_id)


@app.post("/story-cards/retrieve")
def api_retrieve_story_cards(payload: StoryRetrievalRequest) -> dict:
    job = next((j for j in DATA["jobs"] if j.id == payload.job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return retrieve_story_cards_for_job(payload.user_id, payload.job_id, job.requirements, payload.top_k)


@app.post("/applications/drafts")
def api_create_application_draft(payload: ApplicationDraftCreateRequest) -> dict:
    return create_application_draft(
        user_id=payload.user_id,
        job_id=payload.job_id,
        selected_story_card_ids=payload.selected_story_card_ids,
        retrieval_audit_id=payload.retrieval_audit_id,
    )


@app.get("/applications/drafts/{draft_id}")
def api_get_application_draft(draft_id: int, user_id: str = Query("demo-user")) -> dict:
    draft = get_application_draft(draft_id, user_id)
    if draft is None:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@app.post("/applications")
def api_create_application(payload: ApplicationCreateRequest) -> dict:
    application = create_application_from_saved_job(payload.user_id, payload.job_id)
    if application is None:
        raise HTTPException(status_code=400, detail="Job must be saved before creating application")
    return application


@app.get("/applications")
def api_list_applications(user_id: str = Query("demo-user")) -> list[dict]:
    return list_applications(user_id)


@app.post("/applications/{application_id}/generate-cover-letter")
def api_generate_cover_letter(application_id: int, payload: CoverLetterGenerateRequest) -> dict:
    application = next((a for a in list_applications(payload.user_id) if a["id"] == application_id), None)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = next((j for j in DATA["jobs"] if j.id == application["job_id"]), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    output = generate_cover_letter(
        generator=application_generator,
        role=job.title,
        company=job.company,
        story_cards=list_story_cards(payload.user_id),
        selected_story_card_ids=payload.selected_story_card_ids,
    )
    artifact = create_artifact(
        application_id=application_id,
        user_id=payload.user_id,
        artifact_type="cover_letter",
        content="\n".join([output.opening, *output.body, output.closing]),
        metadata={
            "schema": "CoverLetterOutput",
            "prompt_version": "app-gen-v1-stub",
            "selected_story_card_ids": payload.selected_story_card_ids,
            "evidence_used": output.evidence_used,
            "guardrail_notes": output.guardrail_notes,
        },
    )
    run = create_generation_run(
        application_id=application_id,
        artifact_id=artifact["id"],
        user_id=payload.user_id,
        run_type="cover_letter",
        status="completed",
        metadata={"artifact_id": artifact["id"], "evidence_count": len(output.evidence_used)},
    )
    return {"artifact": artifact, "run": run, "output": output.model_dump()}


@app.post("/applications/{application_id}/generate-short-answer")
def api_generate_short_answer(application_id: int, payload: ShortAnswerGenerateRequest) -> dict:
    application = next((a for a in list_applications(payload.user_id) if a["id"] == application_id), None)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    job = next((j for j in DATA["jobs"] if j.id == application["job_id"]), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    output = generate_short_answer(
        generator=application_generator,
        question=payload.question,
        role=job.title,
        company=job.company,
        story_cards=list_story_cards(payload.user_id),
        selected_story_card_ids=payload.selected_story_card_ids,
    )
    artifact = create_artifact(
        application_id=application_id,
        user_id=payload.user_id,
        artifact_type="short_answer",
        content=output.answer,
        metadata={
            "schema": "ShortAnswerOutput",
            "prompt_version": "app-gen-v1-stub",
            "question": payload.question,
            "selected_story_card_ids": payload.selected_story_card_ids,
            "evidence_used": output.evidence_used,
            "guardrail_notes": output.guardrail_notes,
        },
    )
    run = create_generation_run(
        application_id=application_id,
        artifact_id=artifact["id"],
        user_id=payload.user_id,
        run_type="short_answer",
        status="completed",
        metadata={"artifact_id": artifact["id"], "evidence_count": len(output.evidence_used)},
    )
    return {"artifact": artifact, "run": run, "output": output.model_dump()}


@app.get("/applications/{application_id}/history")
def api_application_history(application_id: int, user_id: str = Query("demo-user")) -> list[dict]:
    return list_generation_history(application_id, user_id)


# Readiness Coach MVP
@app.get("/coach/unlock-status")
def coach_unlock_status(user_id: str = Query("demo-user")) -> dict:
    unlocked = coach_unlocked(user_id)
    return {
        "unlocked": unlocked,
        "reason": "saved_or_submitted_application" if unlocked else "save_or_submit_application_required",
    }


@app.post("/coach/readiness-plans")
def create_coach_plan(payload: ReadinessPlanCreateRequest) -> dict:
    if not coach_unlocked(payload.user_id):
        raise HTTPException(status_code=403, detail="Coach unlock requires a saved or submitted application")

    application = next((a for a in list_applications(payload.user_id) if a["id"] == payload.application_id), None)
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    fit = next((j for j in DATA["jobs"] if j.id == application["job_id"]), None)
    if not fit:
        raise HTTPException(status_code=404, detail="Job not found")
    fit_output = _score_for_user(fit, payload.user_id)
    missing_skills = fit_output.missing_skills if fit_output else ["Core role fundamentals"]

    missions = readiness_coach.build_plan(missing_skills=missing_skills, duration_days=payload.duration_days)
    return create_readiness_plan(
        user_id=payload.user_id,
        application_id=payload.application_id,
        duration_days=payload.duration_days,
        missions=missions,
    )


@app.get("/coach/readiness-plans")
def list_coach_plans(
    user_id: str = Query("demo-user"),
    application_id: int | None = Query(default=None),
) -> list[dict]:
    return list_readiness_plans(user_id=user_id, application_id=application_id)


@app.patch("/coach/readiness-missions/{mission_id}")
def update_coach_mission(mission_id: int, payload: ReadinessMissionUpdateRequest) -> dict:
    updated = update_readiness_mission_status(mission_id, payload.user_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Mission not found")
    return updated


def _score_for_user(job: JobPost, user_id: str):
    profile = get_onboarding_profile(user_id)
    if not profile:
        return None
    return score_job(
        evaluator=fit_evaluator,
        job=job,
        user_id=user_id,
        target_role=profile["target_role"],
        career_stage=profile["career_stage"],
        experience_items=list_experience_items(user_id),
    )


@app.get("/jobs")
def list_jobs(user_id: str = "demo-user") -> list[dict]:
    enriched = []
    for job in DATA["jobs"]:
        item = job.model_dump()
        fit = _score_for_user(job, user_id)
        if fit:
            item["fit_score"] = fit.score
        enriched.append(item)
    return enriched


@app.get("/jobs/{job_id}")
def get_job(job_id: str, user_id: str = "demo-user") -> dict:
    job = next((j for j in DATA["jobs"] if j.id == job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    item = job.model_dump()
    fit = _score_for_user(job, user_id)
    if fit:
        item["fit_score"] = fit.score
        item["fit_preview"] = fit.model_dump()
    return item


@app.post("/jobs/{job_id}/save")
def save_job(job_id: str, payload: dict) -> dict[str, str]:
    user_id = payload.get("user_id", "demo-user")
    save_job_record(user_id, job_id)
    DATA["saved_jobs"].add((user_id, job_id))
    return {"status": "saved"}


@app.post("/fit-score")
def fit_score(payload: FitScoreRequest):
    job = next((j for j in DATA["jobs"] if j.id == payload.job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    fit = _score_for_user(job, payload.user_id)
    if fit is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return fit
