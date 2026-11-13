# ASTRA Student Council Dashboard

Next.js + Supabase. Free to host (Vercel + Supabase + GitHub). Public dashboard for everyone, staff area for coordinators and officers.

## Setup (about 30 minutes)

1. **Supabase**: create a project at supabase.com (free plan). Open **SQL Editor**, paste all of `supabase/schema.sql`, click Run.
2. **Keys**: in Supabase go to **Project Settings > API**. Copy the Project URL and the `anon public` key. Never use the `service_role` key in this project.
3. **Run locally (optional)**: copy `.env.example` to `.env.local`, paste the two values, then `npm install` and `npm run dev`.
4. **GitHub**: create a new repository and upload this folder (`.env.local` is ignored by `.gitignore`).
5. **Vercel**: sign in with GitHub, import the repository, add the two environment variables from `.env.example`, click Deploy.
6. **Tell Supabase your site address**: Authentication > URL Configuration. Set Site URL to your Vercel link and add `https://YOUR-SITE/set-password` to Redirect URLs.
7. **Invite people**: Authentication > Users > Invite user, one college email each. Existing Auth users do not need another invite. Staff should set their own password using the invite or password-reset flow.
8. **Assign staff access**: after all listed accounts exist in Authentication > Users, run `supabase/staff_access.sql` in the SQL Editor. It assigns roles and coordinator club access, and stops with an explicit error if an email has not been invited. Re-running it safely updates those profiles. Do not add passwords to this file or the repository.
9. **Keep the free project awake**: in GitHub go to Settings > Secrets and variables > Actions, add `SUPABASE_URL` and `SUPABASE_ANON_KEY`. The included workflow pings the database every 3 days.
10. **Test**: log in as a coordinator and submit; log in as the Secretary and approve; open the public link and check it appears.

## Who can do what (enforced by the database, not the page)

| Role | Can do |
|---|---|
| Public | See approved items only |
| Coordinator | Add pending items for their own clubs only; see their own submissions |
| Secretary, Vice Secretary | Approve, reject, edit, delete |
| Treasurer | Set each club's budget; see all expenses |
| President, Vice President | See everything, including pending items |

## Good habits
- Use one shared club email for the Supabase, GitHub and Vercel accounts, and pass it to next year's council.
- Never put passwords in a spreadsheet. Use the invite and "Forgot password" flow.
- Export data monthly (Supabase > Table Editor > Export). The free plan has no automatic backups.
- Adding a new club or wing: add a row to the `clubs` table.
