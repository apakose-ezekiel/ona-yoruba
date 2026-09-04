-- Ọ̀NÀ — Row Level Security
-- All writes go through the service_role key (bot server, migration scripts),
-- which bypasses RLS entirely. These policies only govern anon/authenticated
-- (site build + any future client-side reads), and are read-only.

alter table entries enable row level security;
create policy entries_public_read on entries for select using (true);

alter table entry_ifa_details enable row level security;
create policy entry_ifa_details_public_read on entry_ifa_details for select using (true);

alter table entry_fieldwork enable row level security;
-- fieldwork provenance (informant names etc.) is not exposed publicly by default
create policy entry_fieldwork_no_public_read on entry_fieldwork for select using (false);

alter table users enable row level security;
alter table favorites enable row level security;
alter table entry_sets enable row level security;
create policy entry_sets_public_read on entry_sets for select using (is_public = true);
alter table entry_set_items enable row level security;
alter table daily_picks enable row level security;
create policy daily_picks_public_read on daily_picks for select using (true);
alter table quiz_attempts enable row level security;

-- No insert/update/delete policies anywhere: only the service_role key
-- (used by scripts/load_to_supabase.py and the Telegram bot on Render) can write.
