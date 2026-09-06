-- Ọ̀NÀ — search intent-matching fix
--
-- Root cause (confirmed by direct testing against the live database):
-- casual question phrasing -- "what does this word mean: X", "tell me
-- about X" -- was NOT being stripped of English conversational filler the
-- way Yoruba filler words already were. With 4,300+ entries, generic verbs
-- like "tell" and "mean" appear in hundreds of English translations
-- ("... will tell", "one tells", "meaning of..."), so ts_rank scored those
-- common words as highly as the one distinctive keyword actually asked
-- about, burying (or losing entirely) the correct answer under unrelated
-- content that merely shared "tell"/"mean"/"about". "history of yoruba"
-- and "oriki" already worked correctly (verified directly) because those
-- ARE real topic keywords and were never being stripped -- the bug was
-- specifically the surrounding question-frame words.
--
-- Two fixes:
--   1. Extend the filler-word list to also strip English conversational
--      scaffolding (what/does/tell/me/about/mean/etc), leaving only the
--      actual topic words to search on -- mirrors the existing Yoruba
--      filler-stripping tier, doesn't touch real topic words like
--      "history"/"oriki"/"proverb"/"ifa".
--   2. Category-first matching: if the query names a domain explicitly
--      ("oriki", "proverb", "history", "ifa", "quiz"), search within that
--      domain first before falling back to the unrestricted tiers --
--      exactly the "classify intent, then search that category" behavior
--      requested.

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
  hint_domain domain_enum;
  lower_q text := lower(trim(q));
  filler_words text[] := array[
    -- Yoruba function/filler + corpus-ubiquitous words
    'yoruba','ile','ni','ti','to','wa','abe','won','ki','ati','si','fun',
    'bi','pe','kan','se','ma','kini','tani','nibo','bawo','wo','ha','na',
    'gbogbo','pelu','ninu','lati','lori','ile-yoruba','o',
    -- English conversational/question-frame filler -- NOT topic words
    'what','does','do','this','that','these','those','mean','meaning',
    'tell','me','about','who','is','are','a','an','the','please','can',
    'you','know','of','in','on','for','and','or','with','explain',
    'describe','define','definition','word','words','something','me:'
  ];
  word text;
  kept_words text[] := '{}';
begin
  -- Category-first: if the query names a domain explicitly, search that
  -- domain first (both AND and OR tiers), before the unrestricted tiers.
  hint_domain := case
    when lower_q ~ '\moriki\M' then 'oriki'
    when lower_q ~ '\m(owe|proverb)s?\M' then 'owe'
    when lower_q ~ '\m(itan|history)\M' then 'aroko'
    when lower_q ~ '\m(ifa|odu|orisa)\M' then 'ifa'
    when lower_q ~ '\m(quiz|nje ?o ?mo)\M' then 'njeomo'
    when lower_q ~ '\m(aroko)\M' then 'aroko'
    else null
  end;

  if hint_domain is not null then
    or_query := websearch_to_tsquery('english', regexp_replace(trim(q), '\s+', ' or ', 'g'));
    if or_query is not null and or_query != ''::tsquery then
      return query
        select e.* from entries e
        where e.domain = hint_domain and e.search_vector @@ or_query
        order by ts_rank(e.search_vector, or_query) desc
        limit max_results;
      get diagnostics found_count = row_count;
      if found_count > 0 then
        return;
      end if;
    end if;
    -- domain named but no keyword match within it: fall through to the
    -- general tiers below rather than returning nothing.
  end if;

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
  foreach word in array regexp_split_to_array(lower_q, '\s+') loop
    word := regexp_replace(word, '[:,.?!]+$', '');
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
  -- stopword-stripped text, with a real relevance floor -- if nothing
  -- clears it, return zero rows (honest "not found") rather than forcing
  -- an unrelated match.
  return query
    select e.*
    from entries e
    where similarity(
      coalesce(e.yoruba, '') || ' ' || coalesce(e.yoruba_alt, '') || ' ' ||
      coalesce(e.english, '') || ' ' || coalesce(e.category, ''),
      case when stripped_q <> '' then stripped_q else q end
    ) > 0.2
    order by similarity(
      coalesce(e.yoruba, '') || ' ' || coalesce(e.yoruba_alt, '') || ' ' ||
      coalesce(e.english, '') || ' ' || coalesce(e.category, ''),
      case when stripped_q <> '' then stripped_q else q end
    ) desc
    limit max_results;
end;
$$;
