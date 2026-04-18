from app.schemas.models import CoverLetterOutput, ShortAnswerOutput
from app.services.ai.application_generator import (
    ApplicationGenerator,
    DeterministicApplicationGenerator,
)


def gather_selected_evidence(story_cards: list[dict], selected_story_card_ids: list[int]) -> list[str]:
    selected = [card for card in story_cards if card["id"] in selected_story_card_ids]
    evidence = [point for card in selected for point in card.get("evidence_points", [])]
    return evidence


def generate_cover_letter(
    generator: ApplicationGenerator,
    role: str,
    company: str,
    story_cards: list[dict],
    selected_story_card_ids: list[int],
) -> CoverLetterOutput:
    evidence = gather_selected_evidence(story_cards, selected_story_card_ids)
    return generator.generate_cover_letter(role=role, company=company, evidence=evidence)


def generate_short_answer(
    generator: ApplicationGenerator,
    question: str,
    role: str,
    company: str,
    story_cards: list[dict],
    selected_story_card_ids: list[int],
) -> ShortAnswerOutput:
    evidence = gather_selected_evidence(story_cards, selected_story_card_ids)
    return generator.generate_short_answer(
        question=question,
        role=role,
        company=company,
        evidence=evidence,
    )


def get_default_application_generator() -> ApplicationGenerator:
    return DeterministicApplicationGenerator()
