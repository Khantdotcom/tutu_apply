from app.schemas.models import JobPost

DATA = {
    "experience": [
        {
            "id": "exp_demo_1",
            "title": "Built student scheduler API",
            "impact": "Reduced admin coordination time by 30%",
            "skills": ["Python", "SQL", "APIs"],
        }
    ],
    "saved_jobs": set(),
    "jobs": [
        JobPost(
            id="job_1",
            title="Junior Backend Engineer",
            company="Acme Cloud",
            location="Remote",
            requirements=["Python", "SQL", "APIs"],
        ),
        JobPost(
            id="job_2",
            title="Data Analyst",
            company="Bright Metrics",
            location="New York",
            requirements=["SQL", "Tableau", "Statistics"],
        ),
    ],
}
