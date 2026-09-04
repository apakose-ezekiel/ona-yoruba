// Build-time fetch from Supabase. Runs once per `eleventy` build, not per
// page view -- keeps the deployed site static (survives a paused free-tier
// Supabase project) while still reflecting the live database as of the last
// build/deploy.
require("dotenv").config({ path: require("path").join(__dirname, "..", "..", "..", ".env") });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;

module.exports = async function () {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    console.warn("SUPABASE_URL / SUPABASE_ANON_KEY not set -- building with an empty entry set.");
    return [];
  }

  // PostgREST caps a single response at 1000 rows by default -- page through
  // with Range headers until a response comes back short of the page size.
  const PAGE_SIZE = 1000;
  let rows = [];
  for (let offset = 0; ; offset += PAGE_SIZE) {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/entries?select=*,entry_ifa_details(odu,ebo)&order=id.asc`,
      {
        headers: {
          apikey: SUPABASE_ANON_KEY,
          Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
          Range: `${offset}-${offset + PAGE_SIZE - 1}`,
        },
      }
    );

    if (!res.ok) {
      throw new Error(`Supabase fetch failed: ${res.status} ${await res.text()}`);
    }

    const page = await res.json();
    rows = rows.concat(page);
    if (page.length < PAGE_SIZE) break;
  }

  return rows.map((row) => ({
    ...row,
    ifa: row.entry_ifa_details && row.entry_ifa_details[0] ? row.entry_ifa_details[0] : null,
  }));
};
