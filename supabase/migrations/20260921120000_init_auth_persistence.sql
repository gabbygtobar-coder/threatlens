-- ThreatLens M4: user-scoped persistence (architecture Option A).
-- Next.js talks to Supabase (anon key + user JWT). FastAPI stays a stateless
-- parse/detect engine. Never put the service_role key in the web client.

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text,
  created_at timestamptz not null default now()
);

create table public.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  created_at timestamptz not null default now(),
  title text,
  raw_log_text text not null default '',
  events_count integer not null default 0 check (events_count >= 0),
  parse_errors_count integer not null default 0 check (parse_errors_count >= 0)
);

create table public.incidents (
  id uuid primary key default gen_random_uuid(),
  analysis_id uuid not null references public.analyses (id) on delete cascade,
  user_id uuid not null references auth.users (id) on delete cascade,
  engine_incident_id text,
  rule_id text not null,
  severity text not null,
  status text not null default 'open',
  title text not null,
  description text not null default '',
  evidence jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

comment on table public.profiles is
  'One row per auth.users id. Inserted by handle_new_user on signup.';
comment on table public.analyses is
  'A saved /detect run: original log text plus parse/event counts.';
comment on table public.incidents is
  'Engine findings persisted for the owning user. Row id is a UUID; engine_incident_id is the deterministic SHA-256 prefix from FastAPI.';
comment on column public.incidents.created_at is
  'Last contributing event time from the engine, not wall-clock save time.';

create index analyses_user_created_idx
  on public.analyses (user_id, created_at desc);

create index incidents_analysis_idx
  on public.incidents (analysis_id);

create index incidents_user_idx
  on public.incidents (user_id);

create unique index incidents_analysis_engine_id_idx
  on public.incidents (analysis_id, engine_incident_id)
  where engine_incident_id is not null;

-- Profile row on signup. SECURITY DEFINER so the insert succeeds despite RLS
-- (runs as the function owner, which bypasses RLS unless FORCE is set).
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.profiles (id, display_name)
  values (
    new.id,
    coalesce(
      new.raw_user_meta_data ->> 'display_name',
      split_part(new.email, '@', 1)
    )
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

revoke all on function public.handle_new_user() from public, anon, authenticated;

alter table public.profiles enable row level security;
alter table public.analyses enable row level security;
alter table public.incidents enable row level security;

-- profiles: users may only see/change their own row.
create policy profiles_select_own
  on public.profiles
  for select
  to authenticated
  using ((select auth.uid()) = id);

create policy profiles_insert_own
  on public.profiles
  for insert
  to authenticated
  with check ((select auth.uid()) = id);

create policy profiles_update_own
  on public.profiles
  for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

create policy profiles_delete_own
  on public.profiles
  for delete
  to authenticated
  using ((select auth.uid()) = id);

-- analyses: full CRUD, own rows only.
create policy analyses_select_own
  on public.analyses
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy analyses_insert_own
  on public.analyses
  for insert
  to authenticated
  with check ((select auth.uid()) = user_id);

create policy analyses_update_own
  on public.analyses
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check ((select auth.uid()) = user_id);

create policy analyses_delete_own
  on public.analyses
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

-- incidents: own rows only, and the parent analysis must also belong to the user.
create policy incidents_select_own
  on public.incidents
  for select
  to authenticated
  using ((select auth.uid()) = user_id);

create policy incidents_insert_own
  on public.incidents
  for insert
  to authenticated
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.analyses a
      where a.id = analysis_id
        and a.user_id = (select auth.uid())
    )
  );

create policy incidents_update_own
  on public.incidents
  for update
  to authenticated
  using ((select auth.uid()) = user_id)
  with check (
    (select auth.uid()) = user_id
    and exists (
      select 1
      from public.analyses a
      where a.id = analysis_id
        and a.user_id = (select auth.uid())
    )
  );

create policy incidents_delete_own
  on public.incidents
  for delete
  to authenticated
  using ((select auth.uid()) = user_id);

grant usage on schema public to anon, authenticated;

grant select, insert, update, delete on table public.profiles to authenticated;
grant select, insert, update, delete on table public.analyses to authenticated;
grant select, insert, update, delete on table public.incidents to authenticated;
