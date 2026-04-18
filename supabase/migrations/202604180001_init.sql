create extension if not exists "pgcrypto";
create extension if not exists "vector";

create table if not exists public.users (
  id uuid primary key,
  email text unique not null,
  created_at timestamptz default now()
);

create table if not exists public.candidate_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  target_role text,
  summary text,
  skills text[] default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  file_path text,
  parsed_json jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.experience_items (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null,
  impact text,
  kind text,
  skills text[] default '{}',
  created_at timestamptz default now()
);

create table if not exists public.experience_chunks (
  id uuid primary key default gen_random_uuid(),
  experience_item_id uuid not null references public.experience_items(id) on delete cascade,
  chunk_text text not null,
  embedding vector(1536),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.job_posts (
  id uuid primary key default gen_random_uuid(),
  source text,
  source_job_id text,
  title text not null,
  company_name text not null,
  location text,
  normalized_requirements jsonb default '[]'::jsonb,
  description text,
  dedupe_key text unique,
  created_at timestamptz default now()
);

create table if not exists public.job_chunks (
  id uuid primary key default gen_random_uuid(),
  job_post_id uuid not null references public.job_posts(id) on delete cascade,
  chunk_text text,
  embedding vector(1536),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.company_profiles (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  website text,
  summary text,
  created_at timestamptz default now()
);

create table if not exists public.company_chunks (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.company_profiles(id) on delete cascade,
  chunk_text text,
  embedding vector(1536),
  metadata jsonb default '{}'::jsonb,
  created_at timestamptz default now()
);

create table if not exists public.applications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  job_post_id uuid references public.job_posts(id),
  status text default 'draft',
  submitted_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.application_steps (
  id uuid primary key default gen_random_uuid(),
  application_id uuid not null references public.applications(id) on delete cascade,
  step_name text not null,
  status text default 'pending',
  due_date date,
  created_at timestamptz default now()
);

create table if not exists public.fit_scores (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  job_post_id uuid not null references public.job_posts(id) on delete cascade,
  score int,
  confidence numeric,
  matched_requirements jsonb,
  missing_skills jsonb,
  reasoning jsonb,
  evidence_ids text[],
  created_at timestamptz default now()
);

create table if not exists public.readiness_plans (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  application_id uuid references public.applications(id),
  duration_days int check (duration_days in (7,14)),
  missions jsonb not null,
  created_at timestamptz default now()
);

create table if not exists public.prompt_registry (
  id uuid primary key default gen_random_uuid(),
  key text unique not null,
  description text,
  created_at timestamptz default now()
);

create table if not exists public.prompt_versions (
  id uuid primary key default gen_random_uuid(),
  registry_id uuid not null references public.prompt_registry(id) on delete cascade,
  version text not null,
  schema_version text not null,
  prompt_text text not null,
  created_at timestamptz default now(),
  unique(registry_id, version)
);

create table if not exists public.generation_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  prompt_version_id uuid references public.prompt_versions(id),
  run_type text not null,
  request_json jsonb,
  response_json jsonb,
  retrieval_ids text[],
  token_usage jsonb,
  latency_ms int,
  created_at timestamptz default now()
);

create table if not exists public.workflow_runs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  workflow_type text not null,
  status text not null,
  started_at timestamptz default now(),
  ended_at timestamptz
);

create table if not exists public.workflow_events (
  id uuid primary key default gen_random_uuid(),
  workflow_run_id uuid not null references public.workflow_runs(id) on delete cascade,
  event_type text not null,
  payload jsonb,
  created_at timestamptz default now()
);

create table if not exists public.tool_call_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  tool_name text,
  request_json jsonb,
  response_json jsonb,
  created_at timestamptz default now()
);

create table if not exists public.artifacts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  application_id uuid references public.applications(id),
  artifact_type text not null,
  content text,
  metadata jsonb,
  created_at timestamptz default now()
);

create table if not exists public.notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  title text not null,
  body text,
  read_at timestamptz,
  created_at timestamptz default now()
);

create table if not exists public.audit_logs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id),
  action text not null,
  actor text not null,
  target_type text,
  target_id text,
  metadata jsonb,
  created_at timestamptz default now()
);

alter table public.candidate_profiles enable row level security;
alter table public.experience_items enable row level security;
alter table public.applications enable row level security;
alter table public.artifacts enable row level security;
alter table public.fit_scores enable row level security;
alter table public.readiness_plans enable row level security;

create policy "own profile" on public.candidate_profiles for all using (auth.uid() = user_id);
create policy "own experience" on public.experience_items for all using (auth.uid() = user_id);
create policy "own applications" on public.applications for all using (auth.uid() = user_id);
create policy "own artifacts" on public.artifacts for all using (auth.uid() = user_id);
create policy "own fit" on public.fit_scores for all using (auth.uid() = user_id);
create policy "own plans" on public.readiness_plans for all using (auth.uid() = user_id);
