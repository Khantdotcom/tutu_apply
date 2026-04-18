insert into public.users (id, email) values
('00000000-0000-0000-0000-000000000001', 'demo@tutu.apply')
on conflict do nothing;

insert into public.candidate_profiles (user_id, target_role, summary, skills)
values ('00000000-0000-0000-0000-000000000001', 'Backend Engineer', 'Early-career student builder', array['Python','SQL','FastAPI'])
on conflict do nothing;
