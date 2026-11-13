-- Run in Supabase SQL Editor after all listed users exist in Authentication > Users.
-- This assigns application roles only; it does not create accounts or set passwords.
do $$
declare
  staff_access jsonb := '[
    {"email":"shivadurishetti.aero@sandipuniversity.edu.in","name":"Rocketry Coordinator","role":"coordinator","club_ids":["rocketry"]},
    {"email":"gaudavenkatesh.aero@sandipuniversity.edu.in","name":"Cultural Coordinator","role":"coordinator","club_ids":["cultural"]},
    {"email":"rathnakarbhoompally.aero@sandipuniversity.edu.in","name":"Secretary","role":"secretary","club_ids":[]},
    {"email":"singhanushka.aero@sandipuniversity.edu.in","name":"Non-Technical Coordinator","role":"coordinator","club_ids":["non-technical"]},
    {"email":"jayaramgadipally.aero@sandipuniversity.edu.in","name":"Vice President","role":"vice_president","club_ids":[]},
    {"email":"srivastavaaarvy.aero@sandipuniversity.edu.in","name":"Aero Modeling Coordinator","role":"coordinator","club_ids":["aeromodeling"]},
    {"email":"abhinayapuram.aero@sandipuniversity.edu.in","name":"President","role":"president","club_ids":[]},
    {"email":"rajkothuru.aero@sandipuniversity.edu.in","name":"Disciplinary Committee Coordinator","role":"coordinator","club_ids":["disciplinary"]},
    {"email":"shreyagavhane.aero@sandipuniversity.edu.in","name":"Sports Coordinator","role":"coordinator","club_ids":["sports"]},
    {"email":"jaswanthsista20@gmail.com","name":"Astronomy Coordinator","role":"coordinator","club_ids":["astronomy"]},
    {"email":"lohakarekrushnalohakare.aero@sandipuniversity.edu.in","name":"Vice Secretary","role":"vice_secretary","club_ids":[]},
    {"email":"pushpalanaiudu.aero@sandipuniversity.edu.in","name":"Technical and Research Coordinator","role":"coordinator","club_ids":["technical","research"]},
    {"email":"jayasompalli.aero@sandipuniversity.edu.in","name":"Sports Coordinator","role":"coordinator","club_ids":["sports"]},
    {"email":"garikumarsreeramulu.aero@sandipuniversity.edu.in","name":"Treasurer","role":"treasurer","club_ids":[]},
    {"email":"rajatdeshmukh.aero@sandipuniversity.edu.in","name":"Media Team Coordinator","role":"coordinator","club_ids":["media"]}
  ]'::jsonb;
  missing_emails text;
begin
  select string_agg(staff.email, ', ' order by staff.email)
    into missing_emails
    from jsonb_to_recordset(staff_access) as staff(email text, name text, role text, club_ids text[])
    left join auth.users as auth_user on lower(auth_user.email) = lower(staff.email)
    where auth_user.id is null;

  if missing_emails is not null then
    raise exception 'Create or invite these Supabase Auth users before assigning profiles: %', missing_emails;
  end if;

  insert into public.profiles (id, name, role, club_ids)
    select auth_user.id,
           coalesce(
             nullif(auth_user.raw_user_meta_data ->> 'full_name', ''),
             nullif(auth_user.raw_user_meta_data ->> 'name', ''),
             staff.name
           ),
           staff.role,
           staff.club_ids
      from jsonb_to_recordset(staff_access) as staff(email text, name text, role text, club_ids text[])
      join auth.users as auth_user on lower(auth_user.email) = lower(staff.email)
    on conflict (id) do update
      set name = coalesce(nullif(profiles.name, ''), excluded.name),
          role = excluded.role,
          club_ids = excluded.club_ids;
end
$$;
