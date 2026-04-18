# TuTu Apply - Phase 1 Scaffold

Production-oriented monorepo scaffold for a mission-based career workflow app.

## Monorepo structure

```text
apps/
  web/                  # Next.js App Router + Tailwind + TanStack Query
  api/                  # FastAPI service (typed Pydantic schemas)
packages/
  shared/               # Shared TypeScript domain types
workers/
  temporal-worker/      # Temporal worker scaffold package
supabase/
  migrations/           # SQL schema + RLS + pgvector
  seed/                 # seed/demo SQL
scripts/
  bootstrap.sh          # quick setup
```

## Phase 1 features implemented

- Mobile-first app shell with tabs: **Path, Jobs, Vault, Coach, Profile**.
- Responsive bottom nav + top progress indicator.
- Onboarding flow with fields:
  - target role
  - career stage
  - preferred industries
  - preferred locations
  - daily commitment
  - resume upload
- Backend onboarding persistence in SQLite (`apps/api/data/tutu.db`) plus mission/path initialization.
- Seed/demo onboarding data for `demo-user` at API startup so flow is testable instantly.
- Job Fit Evaluator MVP: jobs list + job detail + fit-score endpoint with evidence-backed matches, missing skills, and confidence.
- Vault + Story Engine MVP: experience CRUD, story-card generation, job-targeted retrieval with audit logs, and evidence-attached application drafts.
- Application Generator MVP: create application from saved job, select stories, generate cover letter + short answer artifacts, and view generation history/status.
- Readiness Coach MVP: unlocked from saved/submitted applications, generates 7-day or 14-day interview+gap mission plans with progress tracking.

## Environment setup

```bash
cp apps/web/.env.example apps/web/.env.local
cp apps/api/.env.example apps/api/.env
cp workers/temporal-worker/.env.example workers/temporal-worker/.env
```

## Local setup

```bash
./scripts/bootstrap.sh
```

## Start each service

### API (FastAPI)

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

### Web (Next.js)

```bash
pnpm dev:web
```

Web runs on `http://localhost:3000`.

### Temporal worker scaffold

```bash
pnpm dev:worker
```

## Testable demo flow

1. Open `/onboarding` and submit the form (optionally upload a resume file).
2. Open `/path` and verify Level/XP/Streak and three generated missions.
3. Open `/jobs`, inspect fit rings, and open `/jobs/job_1` for matched evidence + missing skills.
4. Open `/vault` to add/edit/delete experience items and manage story cards.
5. Open `/jobs/job_1` to create an application from the saved job, select stories, generate cover letter/short-answer drafts, and inspect generation history/status.
6. Open `/coach` to generate a 7-day or 14-day readiness plan and track mission completion progress.

## Quality commands

```bash
pnpm lint
pnpm typecheck
pnpm format
cd apps/api && source .venv/bin/activate && pytest -q
```
