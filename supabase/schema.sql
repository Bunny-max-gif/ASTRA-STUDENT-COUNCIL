-- Run this whole file once in Supabase: SQL Editor > New query > Run.

create table clubs (
  id text primary key,
  name text not null,
  kind text not null check (kind in ('club','wing')),
  allocated numeric not null default 0
);
insert into clubs (id, name, kind) values
 ('aeromodeling','Aeromodeling','club'), ('rocketry','Rocketry','club'), ('astronomy','Astronomy','club'),
 ('cultural','Cultural','wing'), ('sports','Sports','wing'), ('technical','Technical','wing'),
 ('non-technical','Non-technical','wing'), ('research','Research','wing'),
 ('disciplinary','Disciplinary Committee','wing'), ('media','Media Team','wing');

create table profiles (
  id uuid primary key references auth.users on delete cascade,
  name text not null,
  role text not null check (role in ('president','vice_president','secretary','vice_secretary','treasurer','coordinator')),
  club_ids text[] not null default '{}'
);

create table items (
  id bigint generated always as identity primary key,
  type text not null check (type in ('event','project','budget','announcement')),
  club_id text not null references clubs(id),
  title text not null check (char_length(title) between 1 and 120),
  detail text not null default '' check (char_length(detail) <= 500),
  event_date date,
  progress int check (progress between 0 and 100),
  amount numeric check (amount >= 0),
  status text not null default 'pending' check (status in ('pending','approved','rejected')),
  comment text,
  edited boolean not null default false,
  submitted_by uuid not null default auth.uid() references auth.users,
  reviewed_by uuid references auth.users,
  created_at timestamptz not null default now()
);

-- Helper functions (security definer so policies can read profiles safely)
create function my_role() returns text language sql stable security definer set search_path = public
  as $$ select role from profiles where id = auth.uid() $$;
create function my_clubs() returns text[] language sql stable security definer set search_path = public
  as $$ select club_ids from profiles where id = auth.uid() $$;

alter table clubs enable row level security;
alter table profiles enable row level security;
alter table items enable row level security;

-- Clubs: everyone reads, only the Treasurer edits (the app only changes "allocated")
create policy "clubs read" on clubs for select using (true);
create policy "clubs treasurer update" on clubs for update
  using (my_role() = 'treasurer') with check (my_role() = 'treasurer');

-- Profiles: a person can read only their own row. Roles are set by an admin in the SQL editor.
create policy "own profile" on profiles for select using (id = auth.uid());

-- Items: the public sees approved only. Coordinators also see their own. Council officers see everything.
create policy "items read" on items for select using (
  status = 'approved'
  or submitted_by = auth.uid()
  or my_role() in ('president','vice_president','secretary','vice_secretary','treasurer')
);
-- Coordinators can add pending items for their own clubs only.
create policy "items coordinator insert" on items for insert with check (
  my_role() = 'coordinator' and club_id = any(my_clubs())
  and status = 'pending' and submitted_by = auth.uid() and reviewed_by is null
);
-- Only the Secretary and Vice Secretary approve, reject, edit or delete.
create policy "items approver update" on items for update
  using (my_role() in ('secretary','vice_secretary')) with check (my_role() in ('secretary','vice_secretary'));
create policy "items approver delete" on items for delete
  using (my_role() in ('secretary','vice_secretary'));

-- Public budget totals (approved expenses only)
create view club_budget as
  select c.id, c.name, c.kind, c.allocated,
         coalesce(sum(i.amount) filter (where i.type = 'budget' and i.status = 'approved'), 0) as spent
  from clubs c left join items i on i.club_id = c.id
  group by c.id;
grant select on club_budget to anon, authenticated;

-- For the provided staff role assignments, run staff_access.sql after inviting
-- users in Authentication > Users. For future staff, use a block like this:
-- insert into profiles (id, name, role, club_ids)
--   select id, 'Full Name', 'coordinator', '{rocketry}' from auth.users where email = 'their.email@college.edu';
-- Roles: president, vice_president, secretary, vice_secretary, treasurer, coordinator
-- A coordinator can own several clubs, e.g. '{technical,research}' or '{sports}'.
