from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_experience_crud_and_story_refresh() -> None:
    created = client.post(
        "/vault/experience",
        json={
            "user_id": "demo-user",
            "title": "Built mock interview bot",
            "impact": "Improved prep completion by 20%",
            "skills": ["Python", "APIs"],
            "kind": "project",
        },
    )
    assert created.status_code == 200
    item_id = created.json()["id"]

    listed = client.get("/vault/experience", params={"user_id": "demo-user"})
    assert listed.status_code == 200
    assert any(item["id"] == item_id for item in listed.json())

    updated = client.put(
        f"/vault/experience/{item_id}",
        json={
            "user_id": "demo-user",
            "title": "Built interview prep bot",
            "impact": "Improved prep completion by 25%",
            "skills": ["Python", "APIs", "SQL"],
            "kind": "project",
        },
    )
    assert updated.status_code == 200

    deleted = client.delete(f"/vault/experience/{item_id}", params={"user_id": "demo-user"})
    assert deleted.status_code == 200


def test_story_retrieval_and_draft_attach_evidence() -> None:
    retrieve = client.post(
        "/story-cards/retrieve",
        json={"user_id": "demo-user", "job_id": "job_1", "top_k": 2},
    )
    assert retrieve.status_code == 200
    body = retrieve.json()
    assert "retrieval_audit_id" in body
    assert "cards" in body

    selected_ids = [card["id"] for card in body["cards"]]
    draft = client.post(
        "/applications/drafts",
        json={
            "user_id": "demo-user",
            "job_id": "job_1",
            "selected_story_card_ids": selected_ids,
            "retrieval_audit_id": body["retrieval_audit_id"],
        },
    )
    assert draft.status_code == 200
    draft_body = draft.json()
    assert len(draft_body["selected_evidence"]) >= 0
    assert draft_body["retrieval_audit_id"] == body["retrieval_audit_id"]
