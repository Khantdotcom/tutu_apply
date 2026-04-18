from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_fit_score_endpoint_contract() -> None:
    response = client.post("/fit-score", json={"user_id": "demo-user", "job_id": "job_1"})
    assert response.status_code == 200
    body = response.json()
    assert "score" in body
    assert "confidence" in body
    assert "matched_requirements" in body
    assert "missing_skills" in body
    assert isinstance(body["matched_requirements"], list)


def test_job_detail_contains_fit_preview() -> None:
    response = client.get("/jobs/job_1", params={"user_id": "demo-user"})
    assert response.status_code == 200
    body = response.json()
    assert "fit_preview" in body
    assert "matched_requirements" in body["fit_preview"]
