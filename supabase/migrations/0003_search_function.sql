-- Ọ̀NÀ — shared search function, used by both the site and the Telegram bot
-- so "ask a question" behaves identically everywhere.
--
-- Fixes the plain `search_vector=fts.<term>` approach being too strict
-- (AND-only matching meant "history of yoruba" or "itan Yoruba" often
-- matched nothing, since content is short phrases that rarely repeat every
-- query word). This does two things instead:
--   1. OR-based full-text search (any query word can match), ranked by
--      relevance so the best matches surface first.
--   2. If that finds nothing, a trigram-similarity fallback across the
--      Yoruba/English/category text -- catches typos, partial words, and
--      near-misses, surfacing the closest entries instead of a dead end.

create extension if not exists pg_trgm;

create or replace function search_entries(q text, max_results int default 6)
returns setof entries
language plpgsql
stable
as $$
declare
  or_query tsquery;
  found_count int;
begin
  or_query := websearch_to_tsquery('english', regexp_replace(trim(q), '\s+', ' or ', 'g'));

  if or_query is not null and or_query != ''::tsquery then
    return query
      select e.*
      from entries e
      where e.search_vector @@ or_query
      order by ts_rank(e.search_vector, or_query) desc
      limit max_results;

    get diagnostics found_count = row_count;
    if found_count > 0 then
      return;
    end if;
  end if;

  -- fallback: closest entries by trigram similarity (typos, partial words,
  -- near-misses -- e.g. "itan yoruba" still surfaces history/oriki entries)
  return query
    select e.*
    from entries e
    where similarity(
      coalesce(e.yoruba, '') || ' ' || coalesce(e.yoruba_alt, '') || ' ' ||
      coalesce(e.english, '') || ' ' || coalesce(e.category, ''),
      q
    ) > 0.1
    order by similarity(
      coalesce(e.yoruba, '') || ' ' || coalesce(e.yoruba_alt, '') || ' ' ||
      coalesce(e.english, '') || ' ' || coalesce(e.category, ''),
      q
    ) desc
    limit max_results;
end;
$$;

grant execute on function search_entries(text, int) to anon, authenticated;
