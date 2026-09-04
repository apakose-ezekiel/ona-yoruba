"""
Upsert data/entries_clean.json (+ entry_ifa_details.json, entry_fieldwork.json,
and any gap-fill / notebook-transcription batches) into Supabase.

Requires env vars:
  SUPABASE_URL          -- e.g. https://xxxx.supabase.co
  SUPABASE_SERVICE_KEY  -- the service_role key (never the anon key: this
                           script needs to bypass RLS to write)

Usage:
  python scripts/load_to_supabase.py                     # base 1159 entries
  python scripts/load_to_supabase.py --file data/entries_ifa_gapfill.json
  python scripts/load_to_supabase.py --file data/entries_notebook_transcribed.json
"""
import argparse
import json
import os
import sys
from pathlib import Path

from supabase import create_client

ROOT = Path(__file__).resolve().parent.parent


def get_client():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not url or not key:
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables first.")
    return create_client(url, key)


def load_entries(client, path: Path):
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not entries:
        print(f"{path.name}: nothing to load")
        return {}

    result = client.table("entries").upsert(entries, on_conflict="legacy_id").execute()
    loaded = result.data
    print(f"{path.name}: upserted {len(loaded)} entries")
    return {row["legacy_id"]: row["id"] for row in loaded}


def load_extension(client, table: str, path: Path, id_map: dict):
    if not path.exists():
        return
    rows = json.loads(path.read_text(encoding="utf-8"))
    payload = []
    for row in rows:
        entry_id = id_map.get(row["legacy_id"])
        if entry_id is None:
            print(f"WARNING: no entries.id found for legacy_id={row['legacy_id']!r}, skipping")
            continue
        row = dict(row)
        row.pop("legacy_id")
        row["entry_id"] = entry_id
        payload.append(row)
    if payload:
        client.table(table).upsert(payload, on_conflict="entry_id").execute()
        print(f"{table}: upserted {len(payload)} rows")


def verify_domain_counts(client):
    expected = {
        "owe": 480, "vocab": 173, "njeomo": 167, "aroko": 149, "ifa": 65,
        "ethics": 45, "discourse": 38, "orisa": 24, "spirit": 12,
        "family": 2, "interview": 2, "oriki": 1, "gov": 1,
    }
    for domain, expected_count in expected.items():
        result = (
            client.table("entries")
            .select("id", count="exact")
            .eq("domain", domain)
            .execute()
        )
        actual = result.count
        flag = "" if actual is not None and actual >= expected_count else "  <-- LOWER THAN EXPECTED"
        print(f"  {domain}: {actual} (base dataset had {expected_count}){flag}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file",
        default=str(ROOT / "data" / "entries_clean.json"),
        help="Which entries JSON file to load (default: the base 1159-entry set).",
    )
    parser.add_argument("--skip-extensions", action="store_true")
    args = parser.parse_args()

    client = get_client()
    entries_path = Path(args.file)
    id_map = load_entries(client, entries_path)

    if not args.skip_extensions and entries_path.name == "entries_clean.json":
        load_extension(client, "entry_ifa_details", ROOT / "data" / "entry_ifa_details.json", id_map)
        load_extension(client, "entry_fieldwork", ROOT / "data" / "entry_fieldwork.json", id_map)

    print("\nDomain counts in Supabase after load:")
    verify_domain_counts(client)


if __name__ == "__main__":
    main()
