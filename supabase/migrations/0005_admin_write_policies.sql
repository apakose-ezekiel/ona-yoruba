-- Ọ̀NÀ — admin write access via Supabase Auth (GitHub OAuth login)
--
-- Adds a real authenticated write path for the admin panel, gated on the
-- admin's own account via the JWT Supabase issues after GitHub login.
-- Checked against the GitHub username (always present, regardless of
-- whether the GitHub email is public) OR the email, whichever the OAuth
-- flow populates. The public read policies from 0002 are untouched; this
-- only adds INSERT/UPDATE/DELETE for one specific account, enforced by
-- Postgres itself on every request -- not just hidden client-side -- so
-- the anon key + a real login session is all the admin page needs, never
-- the service_role key.

create or replace function is_ona_admin()
returns boolean
language sql
stable
as $$
  select
    coalesce(auth.jwt() -> 'user_metadata' ->> 'user_name', '') = 'apakose-ezekiel'
    or coalesce(auth.jwt() ->> 'email', '') = 'apakosee@gmail.com';
$$;

drop policy if exists entries_admin_write on entries;
create policy entries_admin_write on entries for all
  using (is_ona_admin())
  with check (is_ona_admin());

drop policy if exists entry_ifa_details_admin_write on entry_ifa_details;
create policy entry_ifa_details_admin_write on entry_ifa_details for all
  using (is_ona_admin())
  with check (is_ona_admin());

drop policy if exists entry_fieldwork_admin_write on entry_fieldwork;
create policy entry_fieldwork_admin_write on entry_fieldwork for all
  using (is_ona_admin())
  with check (is_ona_admin());
