require("dotenv").config({ path: require("path").join(__dirname, "..", "..", "..", ".env") });

// Safe to expose client-side: this is the anon/publishable key, restricted
// by Postgres RLS (supabase/migrations/0002_rls.sql) to read-only SELECT.
module.exports = {
  supabaseUrl: process.env.SUPABASE_URL || "",
  supabaseAnonKey: process.env.SUPABASE_ANON_KEY || "",
};
