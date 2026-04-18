from dataclasses import dataclass


@dataclass
class DeterministicReadinessCoach:
    prompt_version: str = "readiness-v1-stub"
    schema_version: str = "2026-04-18"

    def build_plan(self, missing_skills: list[str], duration_days: int) -> list[dict]:
        missions: list[dict] = []
        capped_skills = missing_skills[: max(2, duration_days // 3)] or ["Core role fundamentals"]

        day = 1
        for skill in capped_skills:
            missions.append(
                {
                    "title": f"Close gap: {skill} practice sprint",
                    "mission_type": "gap_task",
                    "day_number": day,
                    "status": "todo",
                }
            )
            day += 1
            missions.append(
                {
                    "title": f"Interview drill: explain {skill} project evidence",
                    "mission_type": "interview_drill",
                    "day_number": day,
                    "status": "todo",
                }
            )
            day += 1

        while day <= duration_days:
            missions.append(
                {
                    "title": f"Application follow-up prep day {day}",
                    "mission_type": "application_followup",
                    "day_number": day,
                    "status": "todo",
                }
            )
            day += 1

        return missions[:duration_days]
