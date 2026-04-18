from pydantic import BaseModel, Field
from typing import Literal


class Mission(BaseModel):
    id: str | int
    title: str
    xp: int
    status: Literal["todo", "done"]


class PathResponse(BaseModel):
    chapter: str
    daily_quest: str
    missions: list[Mission]
    level: int = 1
    xp: int = 0
    streak_days: int = 0


class OnboardingCompleteResponse(BaseModel):
    status: Literal["completed"]
    chapter: str
    level: int


class ExperienceItemInput(BaseModel):
    user_id: str = "demo-user"
    title: str
    impact: str
    skills: list[str]
    kind: Literal["project", "internship", "club", "volunteering"] = "project"


class ExperienceItemUpdate(ExperienceItemInput):
    pass


class StoryCard(BaseModel):
    id: int
    user_id: str
    experience_item_id: int
    headline: str
    summary: str
    evidence_points: list[str]
    skills: list[str]


class StoryRetrievalRequest(BaseModel):
    user_id: str
    job_id: str
    top_k: int = 3


class StoryRetrievalResponse(BaseModel):
    retrieval_audit_id: int
    cards: list[StoryCard]


class ApplicationDraftCreateRequest(BaseModel):
    user_id: str
    job_id: str
    selected_story_card_ids: list[int]
    retrieval_audit_id: int | None = None


class ApplicationCreateRequest(BaseModel):
    user_id: str
    job_id: str


class GeneratorInput(BaseModel):
    user_id: str
    selected_story_card_ids: list[int]


class CoverLetterGenerateRequest(GeneratorInput):
    pass


class ShortAnswerGenerateRequest(GeneratorInput):
    question: str


class GeneratedClaim(BaseModel):
    text: str
    evidence: list[str]


class CoverLetterOutput(BaseModel):
    opening: str
    body: list[str]
    closing: str
    evidence_used: list[str]
    claims: list[GeneratedClaim]
    guardrail_notes: list[str]


class ShortAnswerOutput(BaseModel):
    answer: str
    evidence_used: list[str]
    claims: list[GeneratedClaim]
    guardrail_notes: list[str]


class ReadinessPlanCreateRequest(BaseModel):
    user_id: str
    application_id: int
    duration_days: Literal[7, 14]


class ReadinessMissionUpdateRequest(BaseModel):
    user_id: str
    status: Literal["todo", "done"]


class ReadinessMission(BaseModel):
    id: int
    title: str
    mission_type: Literal["gap_task", "interview_drill", "application_followup"]
    day_number: int
    status: Literal["todo", "done"]


class ReadinessPlanResponse(BaseModel):
    id: int
    user_id: str
    application_id: int
    duration_days: int
    progress_pct: int
    missions: list[ReadinessMission]


class JobPost(BaseModel):
    id: str
    title: str
    company: str
    location: str
    requirements: list[str]
    fit_score: int | None = None


class FitScoreRequest(BaseModel):
    user_id: str
    job_id: str


class RequirementEvidence(BaseModel):
    requirement: str
    evidence: list[str]


class FitScoreOutput(BaseModel):
    score: int = Field(ge=0, le=100)
    confidence: float = Field(ge=0, le=1)
    matched_requirements: list[RequirementEvidence]
    missing_skills: list[str]
    reasoning: list[str]
    evidence_ids: list[str]
    prompt_version: str
    schema_version: str


class FitScoreAIInput(BaseModel):
    user_id: str
    job_id: str
    requirements: list[str]
    candidate_evidence: list[str]
