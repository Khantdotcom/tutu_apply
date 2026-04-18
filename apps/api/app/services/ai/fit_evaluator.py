from dataclasses import dataclass
from typing import Protocol

from app.schemas.models import FitScoreAIInput, FitScoreOutput, RequirementEvidence


class FitEvaluator(Protocol):
    def evaluate(self, payload: FitScoreAIInput) -> FitScoreOutput: ...


@dataclass
class DeterministicFitEvaluator:
    """Deterministic stub ready to be swapped for OpenAI Responses API."""

    prompt_version: str = "fit-score-v1-stub"
    schema_version: str = "2026-04-18"

    def evaluate(self, payload: FitScoreAIInput) -> FitScoreOutput:
        evidence_lower = [e.lower() for e in payload.candidate_evidence]
        matched: list[RequirementEvidence] = []
        missing: list[str] = []
        evidence_ids: list[str] = []

        for requirement in payload.requirements:
            requirement_lower = requirement.lower()
            supporting = [ev for ev in payload.candidate_evidence if requirement_lower in ev.lower()]
            if supporting:
                matched.append(RequirementEvidence(requirement=requirement, evidence=supporting[:2]))
                evidence_ids.append(f"req:{requirement_lower}")
            elif any(requirement_lower in ev for ev in evidence_lower):
                matched.append(
                    RequirementEvidence(
                        requirement=requirement,
                        evidence=[ev for ev in payload.candidate_evidence if requirement_lower in ev.lower()][:2],
                    )
                )
                evidence_ids.append(f"req:{requirement_lower}")
            else:
                missing.append(requirement)

        score = int((len(matched) / max(1, len(payload.requirements))) * 100)
        confidence = round(0.55 + (0.4 * len(matched) / max(1, len(payload.requirements))), 2)

        reasoning = [
            f"Matched {len(matched)} of {len(payload.requirements)} requirements using candidate evidence.",
            "Deterministic evaluator used; interface is compatible with OpenAI Responses structured outputs.",
        ]

        return FitScoreOutput(
            score=score,
            confidence=min(confidence, 0.99),
            matched_requirements=matched,
            missing_skills=missing,
            reasoning=reasoning,
            evidence_ids=evidence_ids,
            prompt_version=self.prompt_version,
            schema_version=self.schema_version,
        )
