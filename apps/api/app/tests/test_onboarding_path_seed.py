from app.db.sqlite import init_db, save_onboarding, get_path


def test_onboarding_creates_initial_path_missions() -> None:
    init_db()
    save_onboarding(
        {
            "user_id": "test-user",
            "target_role": "Data Analyst",
            "career_stage": "Recent Graduate",
            "preferred_industries": '["FinTech"]',
            "preferred_locations": '["Remote"]',
            "daily_commitment_minutes": 45,
            "resume_filename": "resume.pdf",
            "resume_storage_path": None,
        }
    )
    path = get_path("test-user")
    assert path is not None
    assert path["level"] == 1
    assert len(path["missions"]) == 3
