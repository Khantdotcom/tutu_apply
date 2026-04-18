from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_application_requires_saved_job() -> None:
    bad = client.post("/applications", json={"user_id": "demo-user", "job_id": "job_missing"})
    assert bad.status_code == 400

    good = client.post("/applications", json={"user_id": "demo-user", "job_id": "job_1"})
    assert good.status_code == 200
    assert good.json()["status"] == "draft"


def test_cover_letter_and_short_answer_generation_store_artifacts_and_history() -> None:
    app_resp = client.post("/applications", json={"user_id": "demo-user", "job_id": "job_1"})
    application_id = app_resp.json()["id"]

    cards_resp = client.get("/story-cards", params={"user_id": "demo-user"})
    card_ids = [card["id"] for card in cards_resp.json()[:2]]

    cover = client.post(
        f"/applications/{application_id}/generate-cover-letter",
        json={"user_id": "demo-user", "selected_story_card_ids": card_ids},
    )
    assert cover.status_code == 200
    cover_json = cover.json()
    assert cover_json["artifact"]["artifact_type"] == "cover_letter"
    assert cover_json["output"]["evidence_used"]
    assert "No fabricated achievements" in " ".join(cover_json["output"]["guardrail_notes"])

    short = client.post(
        f"/applications/{application_id}/generate-short-answer",
        json={
            "user_id": "demo-user",
            "question": "Why are you a fit for this role?",
            "selected_story_card_ids": card_ids,
        },
    )
    assert short.status_code == 200
    assert short.json()["artifact"]["artifact_type"] == "short_answer"

    history = client.get(f"/applications/{application_id}/history", params={"user_id": "demo-user"})
    assert history.status_code == 200
    assert len(history.json()) >= 2
