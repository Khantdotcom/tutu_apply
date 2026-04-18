from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_coach_unlock_and_plan_generation() -> None:
    unlock = client.get("/coach/unlock-status", params={"user_id": "demo-user"})
    assert unlock.status_code == 200
    assert unlock.json()["unlocked"] is True

    app_resp = client.post("/applications", json={"user_id": "demo-user", "job_id": "job_1"})
    application_id = app_resp.json()["id"]

    plan_resp = client.post(
        "/coach/readiness-plans",
        json={"user_id": "demo-user", "application_id": application_id, "duration_days": 7},
    )
    assert plan_resp.status_code == 200
    plan = plan_resp.json()
    assert plan["duration_days"] == 7
    assert len(plan["missions"]) == 7


def test_coach_mission_progress_updates() -> None:
    app_resp = client.post("/applications", json={"user_id": "demo-user", "job_id": "job_1"})
    application_id = app_resp.json()["id"]

    plan_resp = client.post(
        "/coach/readiness-plans",
        json={"user_id": "demo-user", "application_id": application_id, "duration_days": 14},
    )
    plan = plan_resp.json()
    mission_id = plan["missions"][0]["id"]

    update = client.patch(
        f"/coach/readiness-missions/{mission_id}",
        json={"user_id": "demo-user", "status": "done"},
    )
    assert update.status_code == 200
    assert update.json()["status"] == "done"

    list_resp = client.get(
        "/coach/readiness-plans",
        params={"user_id": "demo-user", "application_id": application_id},
    )
    assert list_resp.status_code == 200
    assert list_resp.json()[0]["progress_pct"] >= 1
