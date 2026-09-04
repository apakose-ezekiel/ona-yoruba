-- Ọ̀NÀ — Database Schema
-- Target: Supabase (Postgres). Run in the Supabase SQL Editor.

-- ============================================================
-- ENUMS
-- ============================================================
create type domain_enum as enum (
  'owe','njeomo','vocab','aroko','ifa','discourse','ethics',
  'orisa','spirit','interview','family','gov','oriki'
);

create type entry_type_enum as enum (
  'proverb','vocabulary','knowledge_drop','concept','royal_title',
  'history','deity','odu','ese_ifa','attributes','fieldwork_note',
  'interview_excerpt','symbolic_message','oriki'
);

create type difficulty_enum as enum ('easy','medium','hard');

create type pillar_enum as enum (
  'linguistic_purity','natural_science','applied_ethics',
  'identity_genealogy','philosophy_cosmology'
);

-- replaces 49 messy freeform `verify` strings from the source dataset
create type verify_status_enum as enum (
  'verified_multi_source',            -- passed the 3-source VERIFY GATE
  'verified_single_source',
  'fieldwork_verified',               -- informant + consent + academic cross-check
  'fieldwork_partial',                -- informant recorded, not fully cross-checked
  'ai_generated_unverified',          -- discourse-cluster rows
  'web_sourced_pending_verification', -- new gap-fill research (e.g. Ifa/Odu)
  'disputed',                         -- conflicting sources, flagged honestly
  'unverified'
);

create type content_origin_enum as enum (
  'own_material',        -- user's personal notebook / original work
  'fieldwork_verified',  -- collected via the author's fieldwork SOP
  'published_source',    -- from a cited book/academic source
  'ai_research',         -- AI-generated research brief (discourse clusters)
  'web_sourced_new'      -- gap-fill research added by this pipeline
);

-- ============================================================
-- ENTRIES (core content table, shared across all domains)
-- ============================================================
create table entries (
  id                bigserial primary key,
  legacy_id         text unique,          -- original seed `id`, e.g. "YKE0001"
  domain            domain_enum not null,
  type              entry_type_enum not null,
  category          text,                 -- `cat`
  pillar            pillar_enum,
  yoruba            text,                 -- `yor`
  yoruba_alt        text,                 -- `yot` — alternate phrasing
  english           text,                 -- `eng`
  question          text,                 -- `q`
  question_english  text,                 -- `qEng`
  drop_text         text,                 -- `drop` — the "knowledge drop" answer/explanation
  drop_english      text,                 -- `dropEng`
  difficulty        difficulty_enum,
  source_citation   text,                 -- `src`
  tags              text[] not null default '{}',
  verify_status     verify_status_enum not null default 'unverified',
  content_origin    content_origin_enum not null default 'published_source',
  search_vector tsvector generated always as (
    setweight(to_tsvector('simple', coalesce(yoruba, '') || ' ' || coalesce(yoruba_alt, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(english, '') || ' ' || coalesce(drop_english, '')), 'B')
  ) stored,
  created_at        timestamptz not null default now(),
  updated_at        timestamptz not null default now()
);

create index entries_search_idx on entries using gin (search_vector);
create index entries_domain_idx on entries (domain);
create index entries_type_idx on entries (type);
create index entries_pillar_idx on entries (pillar);
create index entries_tags_idx on entries using gin (tags);
create index entries_verify_idx on entries (verify_status);

-- ============================================================
-- NARROW EXTENSION TABLES (only apply to a minority of rows)
-- ============================================================
create table entry_ifa_details (
  entry_id bigint primary key references entries(id) on delete cascade,
  odu      text,   -- Ifá odù cross-reference
  ebo      text    -- prescribed ẹbọ (sacrifice/offering)
);

create table entry_fieldwork (
  entry_id        bigint primary key references entries(id) on delete cascade,
  informant       text,
  informant_role  text,
  consent_status  text,
  field_notes     text,
  yor_status      text,
  cluster_id      text
);

-- ============================================================
-- TELEGRAM / SITE USERS
-- ============================================================
create type language_pref_enum as enum ('en', 'yo', 'both');

create table users (
  id             bigserial primary key,
  telegram_id    bigint unique not null,
  username       text,
  first_name     text,
  language_pref  language_pref_enum not null default 'both',
  created_at     timestamptz not null default now(),
  last_active_at timestamptz not null default now()
);

-- ============================================================
-- FAVORITES
-- ============================================================
create table favorites (
  id         bigserial primary key,
  user_id    bigint not null references users(id) on delete cascade,
  entry_id   bigint not null references entries(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (user_id, entry_id)
);

-- ============================================================
-- USER-CREATED COLLECTIONS ("sets")
-- ============================================================
create table entry_sets (
  id          bigserial primary key,
  user_id     bigint not null references users(id) on delete cascade,
  name        text not null,
  description text,
  is_public   boolean not null default false,
  created_at  timestamptz not null default now()
);

create table entry_set_items (
  set_id   bigint not null references entry_sets(id) on delete cascade,
  entry_id bigint not null references entries(id) on delete cascade,
  position int,
  primary key (set_id, entry_id)
);

-- ============================================================
-- DAILY PICKS (word-of-the-day / proverb-of-the-day, shared by site + bot)
-- ============================================================
create table daily_picks (
  pick_date date not null,
  domain    domain_enum not null,
  entry_id  bigint references entries(id),
  primary key (pick_date, domain)
);

-- ============================================================
-- QUIZ ATTEMPTS
-- ============================================================
create table quiz_attempts (
  id         bigserial primary key,
  user_id    bigint not null references users(id) on delete cascade,
  entry_id   bigint references entries(id),
  correct    boolean not null,
  created_at timestamptz not null default now()
);
