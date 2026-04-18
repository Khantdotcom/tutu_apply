import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "tutu.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_conn()
    conn.executescript(
        """
        create table if not exists onboarding_profiles (
            user_id text primary key,
            target_role text not null,
            career_stage text not null,
            preferred_industries text not null,
            preferred_locations text not null,
            daily_commitment_minutes integer not null,
            resume_filename text,
            resume_storage_path text,
            created_at text default (datetime('now')),
            updated_at text default (datetime('now'))
        );

        create table if not exists path_progress (
            user_id text primary key,
            level integer not null,
            chapter_title text not null,
            xp integer not null,
            streak_days integer not null
        );

        create table if not exists user_missions (
            id integer primary key autoincrement,
            user_id text not null,
            title text not null,
            xp integer not null,
            status text not null
        );

        create table if not exists experience_items (
            id integer primary key autoincrement,
            user_id text not null,
            title text not null,
            impact text not null,
            skills text not null,
            kind text default 'project',
            created_at text default (datetime('now')),
            updated_at text default (datetime('now'))
        );

        create table if not exists story_cards (
            id integer primary key autoincrement,
            user_id text not null,
            experience_item_id integer not null,
            headline text not null,
            summary text not null,
            evidence_points text not null,
            skills text not null,
            created_at text default (datetime('now')),
            updated_at text default (datetime('now'))
        );

        create table if not exists retrieval_audit_logs (
            id integer primary key autoincrement,
            user_id text not null,
            job_id text not null,
            boundary text not null,
            candidate_story_card_ids text not null,
            selected_story_card_ids text not null,
            created_at text default (datetime('now'))
        );

        create table if not exists application_drafts (
            id integer primary key autoincrement,
            user_id text not null,
            job_id text not null,
            selected_story_card_ids text not null,
            selected_evidence text not null,
            body text not null,
            retrieval_audit_id integer,
            created_at text default (datetime('now'))
        );

        create table if not exists saved_jobs (
            id integer primary key autoincrement,
            user_id text not null,
            job_id text not null,
            created_at text default (datetime('now')),
            unique(user_id, job_id)
        );

        create table if not exists applications (
            id integer primary key autoincrement,
            user_id text not null,
            job_id text not null,
            status text not null default 'draft',
            created_at text default (datetime('now'))
        );

        create table if not exists artifacts (
            id integer primary key autoincrement,
            application_id integer not null,
            user_id text not null,
            artifact_type text not null,
            content text not null,
            metadata text not null,
            created_at text default (datetime('now'))
        );

        create table if not exists generation_runs (
            id integer primary key autoincrement,
            application_id integer not null,
            artifact_id integer,
            user_id text not null,
            run_type text not null,
            status text not null,
            metadata text not null,
            created_at text default (datetime('now'))
        );

        create table if not exists readiness_plans (
            id integer primary key autoincrement,
            user_id text not null,
            application_id integer not null,
            duration_days integer not null,
            status text not null default 'active',
            created_at text default (datetime('now'))
        );

        create table if not exists readiness_missions (
            id integer primary key autoincrement,
            plan_id integer not null,
            user_id text not null,
            title text not null,
            mission_type text not null,
            day_number integer not null,
            status text not null default 'todo'
        );
        """
    )
    conn.commit()
    conn.close()


def build_initial_missions(payload: dict[str, Any]) -> list[dict[str, Any]]:
    role = payload["target_role"]
    stage = payload["career_stage"]
    industries = json.loads(payload["preferred_industries"])
    locations = json.loads(payload["preferred_locations"])

    return [
        {"title": f"Validate {role} skill map for {stage} stage", "xp": 50, "status": "todo"},
        {
            "title": f"Save 3 {industries[0] if industries else 'target'} jobs in {locations[0] if locations else 'your location'}",
            "xp": 80,
            "status": "todo",
        },
        {"title": "Add 2 story cards from your resume evidence", "xp": 70, "status": "todo"},
    ]


def save_onboarding(payload: dict[str, Any]) -> None:
    conn = get_conn()
    conn.execute(
        """
        insert into onboarding_profiles (
            user_id, target_role, career_stage, preferred_industries,
            preferred_locations, daily_commitment_minutes, resume_filename,
            resume_storage_path, updated_at
        ) values (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        on conflict(user_id) do update set
            target_role = excluded.target_role,
            career_stage = excluded.career_stage,
            preferred_industries = excluded.preferred_industries,
            preferred_locations = excluded.preferred_locations,
            daily_commitment_minutes = excluded.daily_commitment_minutes,
            resume_filename = excluded.resume_filename,
            resume_storage_path = excluded.resume_storage_path,
            updated_at = datetime('now')
        """,
        (
            payload["user_id"],
            payload["target_role"],
            payload["career_stage"],
            payload["preferred_industries"],
            payload["preferred_locations"],
            payload["daily_commitment_minutes"],
            payload.get("resume_filename"),
            payload.get("resume_storage_path"),
        ),
    )

    conn.execute("delete from user_missions where user_id = ?", (payload["user_id"],))
    for mission in build_initial_missions(payload):
        conn.execute(
            "insert into user_missions (user_id, title, xp, status) values (?, ?, ?, ?)",
            (payload["user_id"], mission["title"], mission["xp"], mission["status"]),
        )

    conn.execute(
        """
        insert into path_progress (user_id, level, chapter_title, xp, streak_days)
        values (?, ?, ?, ?, ?)
        on conflict(user_id) do update set
            level = excluded.level,
            chapter_title = excluded.chapter_title,
            xp = excluded.xp,
            streak_days = excluded.streak_days
        """,
        (payload["user_id"], 1, "Chapter 1: Find the Right Role", min(250, int(payload["daily_commitment_minutes"]) * 2), 1),
    )

    conn.commit()
    conn.close()


def get_path(user_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    progress = conn.execute("select * from path_progress where user_id = ?", (user_id,)).fetchone()
    if progress is None:
        conn.close()
        return None

    missions = conn.execute(
        "select id, title, xp, status from user_missions where user_id = ? order by id", (user_id,)
    ).fetchall()
    conn.close()
    return {
        "chapter": progress["chapter_title"],
        "daily_quest": "Complete one mission from your path map",
        "missions": [dict(m) for m in missions],
        "level": progress["level"],
        "xp": progress["xp"],
        "streak_days": progress["streak_days"],
    }


def get_onboarding_profile(user_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute("select * from onboarding_profiles where user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# Experience CRUD

def create_experience_item(user_id: str, title: str, impact: str, skills: list[str], kind: str) -> dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        """
        insert into experience_items (user_id, title, impact, skills, kind, updated_at)
        values (?, ?, ?, ?, ?, datetime('now'))
        """,
        (user_id, title, impact, json.dumps(skills), kind),
    )
    conn.commit()
    item_id = cur.lastrowid
    row = conn.execute("select * from experience_items where id = ?", (item_id,)).fetchone()
    conn.close()
    return _deserialize_experience(dict(row))


def list_experience_items(user_id: str) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "select * from experience_items where user_id = ? order by updated_at desc, id desc", (user_id,)
    ).fetchall()
    conn.close()
    return [_deserialize_experience(dict(row)) for row in rows]


def get_experience_item(item_id: int, user_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "select * from experience_items where id = ? and user_id = ?", (item_id, user_id)
    ).fetchone()
    conn.close()
    return _deserialize_experience(dict(row)) if row else None


def update_experience_item(item_id: int, user_id: str, title: str, impact: str, skills: list[str], kind: str) -> dict[str, Any] | None:
    conn = get_conn()
    conn.execute(
        """
        update experience_items
        set title = ?, impact = ?, skills = ?, kind = ?, updated_at = datetime('now')
        where id = ? and user_id = ?
        """,
        (title, impact, json.dumps(skills), kind, item_id, user_id),
    )
    conn.commit()
    row = conn.execute(
        "select * from experience_items where id = ? and user_id = ?", (item_id, user_id)
    ).fetchone()
    conn.close()
    return _deserialize_experience(dict(row)) if row else None


def delete_experience_item(item_id: int, user_id: str) -> bool:
    conn = get_conn()
    cur = conn.execute("delete from experience_items where id = ? and user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def refresh_story_cards(user_id: str) -> list[dict[str, Any]]:
    conn = get_conn()
    items = conn.execute("select * from experience_items where user_id = ?", (user_id,)).fetchall()
    conn.execute("delete from story_cards where user_id = ?", (user_id,))
    for row in items:
        item = _deserialize_experience(dict(row))
        evidence_points = [f"Impact: {item['impact']}"] + [f"Skill evidence: {skill}" for skill in item["skills"]]
        conn.execute(
            """
            insert into story_cards (user_id, experience_item_id, headline, summary, evidence_points, skills, updated_at)
            values (?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                user_id,
                item["id"],
                item["title"],
                f"{item['title']} resulted in measurable impact.",
                json.dumps(evidence_points),
                json.dumps(item["skills"]),
            ),
        )
    conn.commit()
    rows = conn.execute(
        "select * from story_cards where user_id = ? order by updated_at desc, id desc", (user_id,)
    ).fetchall()
    conn.close()
    return [_deserialize_story_card(dict(row)) for row in rows]


def list_story_cards(user_id: str) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "select * from story_cards where user_id = ? order by updated_at desc, id desc", (user_id,)
    ).fetchall()
    conn.close()
    return [_deserialize_story_card(dict(row)) for row in rows]


def retrieve_story_cards_for_job(user_id: str, job_id: str, requirements: list[str], top_k: int) -> dict[str, Any]:
    cards = list_story_cards(user_id)

    ranked: list[tuple[int, dict[str, Any]]] = []
    for card in cards:
        score = 0
        lower_skills = [s.lower() for s in card["skills"]]
        for req in requirements:
            if req.lower() in lower_skills:
                score += 2
            if any(req.lower() in evidence.lower() for evidence in card["evidence_points"]):
                score += 1
        ranked.append((score, card))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = [card for score, card in ranked if score > 0][:top_k]
    candidate_ids = [card["id"] for _, card in ranked]
    selected_ids = [card["id"] for card in selected]

    conn = get_conn()
    cur = conn.execute(
        """
        insert into retrieval_audit_logs (user_id, job_id, boundary, candidate_story_card_ids, selected_story_card_ids)
        values (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            job_id,
            "Only user-owned story_cards table considered. No external memory/tools used.",
            json.dumps(candidate_ids),
            json.dumps(selected_ids),
        ),
    )
    conn.commit()
    audit_id = cur.lastrowid
    conn.close()

    return {
        "retrieval_audit_id": audit_id,
        "cards": selected,
    }


def create_application_draft(
    user_id: str,
    job_id: str,
    selected_story_card_ids: list[int],
    retrieval_audit_id: int | None,
) -> dict[str, Any]:
    conn = get_conn()
    placeholders = ",".join(["?"] * len(selected_story_card_ids))
    if selected_story_card_ids:
        query = f"select * from story_cards where user_id = ? and id in ({placeholders})"
        params = [user_id, *selected_story_card_ids]
        rows = conn.execute(query, params).fetchall()
    else:
        rows = []

    cards = [_deserialize_story_card(dict(row)) for row in rows]
    selected_evidence = [point for card in cards for point in card["evidence_points"]]
    draft_body = (
        "Draft generated from selected evidence only:\n"
        + "\n".join([f"- {evidence}" for evidence in selected_evidence])
    )

    cur = conn.execute(
        """
        insert into application_drafts (user_id, job_id, selected_story_card_ids, selected_evidence, body, retrieval_audit_id)
        values (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            job_id,
            json.dumps(selected_story_card_ids),
            json.dumps(selected_evidence),
            draft_body,
            retrieval_audit_id,
        ),
    )
    conn.commit()
    draft_id = cur.lastrowid
    row = conn.execute("select * from application_drafts where id = ?", (draft_id,)).fetchone()
    conn.close()
    return _deserialize_draft(dict(row))


def get_application_draft(draft_id: int, user_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    row = conn.execute(
        "select * from application_drafts where id = ? and user_id = ?", (draft_id, user_id)
    ).fetchone()
    conn.close()
    return _deserialize_draft(dict(row)) if row else None


def seed_demo_onboarding() -> None:
    conn = get_conn()
    existing = conn.execute("select 1 from onboarding_profiles where user_id = 'demo-user'").fetchone()
    conn.close()
    if not existing:
        save_onboarding(
            {
                "user_id": "demo-user",
                "target_role": "Junior Backend Engineer",
                "career_stage": "Student",
                "preferred_industries": json.dumps(["SaaS", "EdTech"]),
                "preferred_locations": json.dumps(["Remote", "New York"]),
                "daily_commitment_minutes": 30,
                "resume_filename": "demo_resume.pdf",
                "resume_storage_path": None,
            }
        )

    if not list_experience_items("demo-user"):
        create_experience_item(
            user_id="demo-user",
            title="Built student scheduler API",
            impact="Reduced admin coordination time by 30%",
            skills=["Python", "SQL", "APIs"],
            kind="project",
        )
        create_experience_item(
            user_id="demo-user",
            title="Data dashboard for club metrics",
            impact="Enabled weekly decisions with usage analytics",
            skills=["SQL", "Analytics", "Visualization"],
            kind="club",
        )
    refresh_story_cards("demo-user")
    save_job_record("demo-user", "job_1")


def _deserialize_experience(item: dict[str, Any]) -> dict[str, Any]:
    item["skills"] = json.loads(item["skills"]) if isinstance(item.get("skills"), str) else item.get("skills", [])
    return item


def _deserialize_story_card(item: dict[str, Any]) -> dict[str, Any]:
    item["skills"] = json.loads(item["skills"]) if isinstance(item.get("skills"), str) else item.get("skills", [])
    item["evidence_points"] = (
        json.loads(item["evidence_points"])
        if isinstance(item.get("evidence_points"), str)
        else item.get("evidence_points", [])
    )
    return item


def _deserialize_draft(item: dict[str, Any]) -> dict[str, Any]:
    item["selected_story_card_ids"] = (
        json.loads(item["selected_story_card_ids"])
        if isinstance(item.get("selected_story_card_ids"), str)
        else item.get("selected_story_card_ids", [])
    )
    item["selected_evidence"] = (
        json.loads(item["selected_evidence"])
        if isinstance(item.get("selected_evidence"), str)
        else item.get("selected_evidence", [])
    )
    return item


def save_job_record(user_id: str, job_id: str) -> None:
    conn = get_conn()
    conn.execute(
        "insert or ignore into saved_jobs (user_id, job_id) values (?, ?)",
        (user_id, job_id),
    )
    conn.commit()
    conn.close()


def create_application_from_saved_job(user_id: str, job_id: str) -> dict[str, Any] | None:
    conn = get_conn()
    saved = conn.execute(
        "select 1 from saved_jobs where user_id = ? and job_id = ?",
        (user_id, job_id),
    ).fetchone()
    if not saved:
        conn.close()
        return None

    cur = conn.execute(
        "insert into applications (user_id, job_id, status) values (?, ?, 'draft')",
        (user_id, job_id),
    )
    conn.commit()
    app_id = cur.lastrowid
    row = conn.execute("select * from applications where id = ?", (app_id,)).fetchone()
    conn.close()
    return dict(row)


def list_applications(user_id: str) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "select * from applications where user_id = ? order by id desc", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_artifact(
    application_id: int,
    user_id: str,
    artifact_type: str,
    content: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        """
        insert into artifacts (application_id, user_id, artifact_type, content, metadata)
        values (?, ?, ?, ?, ?)
        """,
        (application_id, user_id, artifact_type, content, json.dumps(metadata)),
    )
    conn.commit()
    artifact_id = cur.lastrowid
    row = conn.execute("select * from artifacts where id = ?", (artifact_id,)).fetchone()
    conn.close()
    artifact = dict(row)
    artifact["metadata"] = json.loads(artifact["metadata"])
    return artifact


def create_generation_run(
    application_id: int,
    artifact_id: int | None,
    user_id: str,
    run_type: str,
    status: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        """
        insert into generation_runs (application_id, artifact_id, user_id, run_type, status, metadata)
        values (?, ?, ?, ?, ?, ?)
        """,
        (application_id, artifact_id, user_id, run_type, status, json.dumps(metadata)),
    )
    conn.commit()
    run_id = cur.lastrowid
    row = conn.execute("select * from generation_runs where id = ?", (run_id,)).fetchone()
    conn.close()
    run = dict(row)
    run["metadata"] = json.loads(run["metadata"])
    return run


def list_generation_history(application_id: int, user_id: str) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        """
        select gr.*, a.artifact_type
        from generation_runs gr
        left join artifacts a on a.id = gr.artifact_id
        where gr.application_id = ? and gr.user_id = ?
        order by gr.id desc
        """,
        (application_id, user_id),
    ).fetchall()
    conn.close()
    history: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["metadata"] = json.loads(item["metadata"])
        history.append(item)
    return history


def coach_unlocked(user_id: str) -> bool:
    conn = get_conn()
    saved = conn.execute("select 1 from saved_jobs where user_id = ? limit 1", (user_id,)).fetchone()
    submitted = conn.execute(
        "select 1 from applications where user_id = ? and status = 'submitted' limit 1", (user_id,)
    ).fetchone()
    conn.close()
    return bool(saved or submitted)


def create_readiness_plan(
    user_id: str,
    application_id: int,
    duration_days: int,
    missions: list[dict[str, Any]],
) -> dict[str, Any]:
    conn = get_conn()
    cur = conn.execute(
        "insert into readiness_plans (user_id, application_id, duration_days) values (?, ?, ?)",
        (user_id, application_id, duration_days),
    )
    plan_id = cur.lastrowid
    for mission in missions:
        conn.execute(
            """
            insert into readiness_missions (plan_id, user_id, title, mission_type, day_number, status)
            values (?, ?, ?, ?, ?, ?)
            """,
            (
                plan_id,
                user_id,
                mission["title"],
                mission["mission_type"],
                mission["day_number"],
                mission["status"],
            ),
        )
    conn.commit()
    conn.close()
    return get_readiness_plan(plan_id, user_id)


def get_readiness_plan(plan_id: int, user_id: str) -> dict[str, Any]:
    conn = get_conn()
    plan = conn.execute(
        "select * from readiness_plans where id = ? and user_id = ?", (plan_id, user_id)
    ).fetchone()
    missions = conn.execute(
        "select * from readiness_missions where plan_id = ? and user_id = ? order by day_number, id",
        (plan_id, user_id),
    ).fetchall()
    conn.close()
    mission_list = [dict(m) for m in missions]
    done = len([m for m in mission_list if m["status"] == "done"])
    total = max(1, len(mission_list))
    return {
        **dict(plan),
        "progress_pct": int((done / total) * 100),
        "missions": mission_list,
    }


def list_readiness_plans(user_id: str, application_id: int | None = None) -> list[dict[str, Any]]:
    conn = get_conn()
    if application_id is None:
        plans = conn.execute(
            "select * from readiness_plans where user_id = ? order by id desc", (user_id,)
        ).fetchall()
    else:
        plans = conn.execute(
            "select * from readiness_plans where user_id = ? and application_id = ? order by id desc",
            (user_id, application_id),
        ).fetchall()
    conn.close()
    return [get_readiness_plan(plan["id"], user_id) for plan in plans]


def update_readiness_mission_status(mission_id: int, user_id: str, status: str) -> dict[str, Any] | None:
    conn = get_conn()
    conn.execute(
        "update readiness_missions set status = ? where id = ? and user_id = ?",
        (status, mission_id, user_id),
    )
    conn.commit()
    row = conn.execute(
        "select * from readiness_missions where id = ? and user_id = ?", (mission_id, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
