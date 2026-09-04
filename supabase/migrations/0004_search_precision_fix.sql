-- Ọ̀NÀ — search precision fix
--
-- 0003's OR-based fallback treated every query word as equally significant,
-- including "yoruba"/"ile" and Yoruba function words (ni/ti/to/wa/abe/won)
-- that appear in nearly every entry in a Yoruba-culture corpus. A query
-- like "ilu to wa ni abe ile yoruba" (a town within Yoruba land) matched
-- almost the whole table via "yoruba" alone, drowning out the one word
-- that actually mattered ("ilu" = town). Postgres's ts_rank has no
-- corpus-wide term-frequency weighting (no IDF), so a ubiquitous word
-- isn't automatically down-weighted the way a real search engine would.
--
-- Fix: search like a search engine actually would --
--   1. Require ALL words to match first (highest precision).
--   2. If that fails, strip out corpus-common/function words that add no
--      discriminating signal, and retry requiring all the *remaining*
--      words.
--   3. Only then fall back to OR-matching the remaining meaningful words,
--      ranked by relevance.
--   4. Trigram similarity (typo/near-miss tolerance) is the last resort,
--      run against the stopword-stripped query so "yoruba" doesn't
--      inflate similarity scores there either.

create or replace function search_entries(q text, max_results int default 6)
returns setof entries
language plpgsql
stable
as $$
declare
  and_query tsquery;
  or_query tsquery;
  stripped_q text := '';
  found_count int;
  -- Yoruba function/filler words plus corpus-ubiquitous terms ("yoruba",
  -- "ile") that carry no topic signal in this dataset. English stopwords
  -- are already handled by websearch_to_tsquery's 'english' config.
  filler_words text[] := array[
    'yoruba','ile','ni','ti','to','wa','abe','won','ki','ati','si','fun',
    'bi','pe','kan','se','ma','kini','tani','nibo','bawo','wo','ha','na',
    'gbogbo','pelu','ninu','lati','lori','ile-yoruba','o'
  ];
  word text;
  kept_words text[] := '{}';
begin
  -- Tier 1: strict AND match on the full query (highest precision)
  and_query := websearch_to_tsquery('english', trim(q));
  if and_query is not null and and_query != ''::tsquery then
    return query
      select e.* from entries e
      where e.search_vector @@ and_query
      order by ts_rank(e.search_vector, and_query) desc
      limit max_results;
    get diagnostics found_count = row_count;
    if found_count > 0 then
      return;
    end if;
  end if;

  -- Build the stopword-stripped query once, reused by tiers 2-4
  foreach word in array regexp_split_to_array(lower(trim(q)), '\s+') loop
    if word <> '' and not (word = any(filler_words)) then
      kept_words := array_append(kept_words, word);
    end if;
  end loop;
  if array_length(kept_words, 1) > 0 then
    stripped_q := array_to_string(kept_words, ' ');
  end if;

  if stripped_q <> '' then
    -- Tier 2: AND match on the remaining meaningful words only
    and_query := websearch_to_tsquery('english', stripped_q);
    if and_query is not null and and_query != ''::tsquery then
      return query
        select e.* from entries e
        where e.search_vector @@ and_query
        order by ts_rank(e.search_vector, and_query) desc
        limit max_results;
      get diagnostics found_count = row_count;
      if found_count > 0 then
        return;
      end if;
    end if;

    -- Tier 3: OR match on the remaining meaningful words, ranked by relevance
    or_query := websearch_to_tsquery('english', regexp_replace(stripped_q, '\s+', ' or ', 'g'));
    if or_query is not null and or_query != ''::tsquery then
      return query
        select e.* from entries e
        where e.search_vector @@ or_query
        order by ts_rank(e.search_vector, or_query) desc
        limit max_results;
      get diagnostics found_count = row_count;
      if found_count > 0 then
        return;
      end if;
    end if;
  end if;

  -- Tier 4: trigram similarity fallback (typos/near-misses), on the
  -- stopword-stripped text so "yoruba" doesn't inflate every row's score
  return query
    select e.*
    from entries e
    where similarity(
      coalesce(e.yoruba, '') || ' ' || coalesce(e.yoruba_alt, '') || ' ' ||
      coalesce(e.english, '') || ' ' || coalesce(e.category, ''),
      case when stripped_q <> '' then stripped_q else q end
    ) > 0.15
    order by similarity(
      coalesce(e.yoruba, '') || ' ' || coalesce(e.yoruba_alt, '') || ' ' ||
      coalesce(e.english, '') || ' ' || coalesce(e.category, ''),
      case when stripped_q <> '' then stripped_q else q end
    ) desc
    limit max_results;
end;
$$;
