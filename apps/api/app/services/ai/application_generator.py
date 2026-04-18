from dataclasses import dataclass
from typing import Protocol

from app.schemas.models import CoverLetterOutput, GeneratedClaim, ShortAnswerOutput


class ApplicationGenerator(Protocol):
    def generate_cover_letter(self, role: str, company: str, evidence: list[str]) -> CoverLetterOutput: ...

    def generate_short_answer(
        self, question: str, role: str, company: str, evidence: list[str]
    ) -> ShortAnswerOutput: ...


@dataclass
class DeterministicApplicationGenerator:
    prompt_version: str = "app-gen-v1-stub"
    schema_version: str = "2026-04-18"

    def _guardrails(self, evidence: list[str]) -> list[str]:
        return [
            "Only provided evidence points were used.",
            "No fabricated achievements or unverifiable claims were added.",
            f"Evidence count: {len(evidence)}",
        ]

    def generate_cover_letter(self, role: str, company: str, evidence: list[str]) -> CoverLetterOutput:
        used = evidence[:5]
        claims = [GeneratedClaim(text=f"Demonstrated: {ev}", evidence=[ev]) for ev in used]
        body = [
            f"I am excited to apply for the {role} role at {company}.",
            "My relevant evidence includes:",
            *[f"- {ev}" for ev in used],
        ]
        return CoverLetterOutput(
            opening=f"Dear Hiring Team at {company},",
            body=body,
            closing="Thank you for considering my application.",
            evidence_used=used,
            claims=claims,
            guardrail_notes=self._guardrails(used),
        )

    def generate_short_answer(
        self, question: str, role: str, company: str, evidence: list[str]
    ) -> ShortAnswerOutput:
        used = evidence[:4]
        answer = (
            f"For the question '{question}', I would highlight evidence directly tied to {role} at {company}: "
            + "; ".join(used)
        )
        claims = [GeneratedClaim(text=f"Evidence-backed point: {ev}", evidence=[ev]) for ev in used]
        return ShortAnswerOutput(
            answer=answer,
            evidence_used=used,
            claims=claims,
            guardrail_notes=self._guardrails(used),
        )
