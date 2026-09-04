"""
Join data/seed_raw.json (1,159 entries from the prototype) with
data/provenance_map.json (xlsx fieldwork provenance, keyed by the same IDs),
apply type/verify normalization, and emit the three files the Supabase
loader needs:

  data/entries_clean.json          -> `entries` table rows
  data/entry_ifa_details.json      -> `entry_ifa_details` extension rows
  data/entry_fieldwork.json        -> `entry_fieldwork` extension rows
  data/verify_status_mapping_review.csv -> anything the normalizer had to
                                           guess at via keyword fallback,
                                           for a quick manual skim
"""
import csv
import json
from pathlib import Path

from normalize_type_verify import normalize_type, normalize_verify, infer_content_origin, VERIFY_EXACT_MAP

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "seed_raw.json"
PROVENANCE_PATH = ROOT / "data" / "provenance_map.json"

# Domain -> site navigation pillar. The seed's own `pillar` field is a
# fine-grained thematic tag (e.g. "destiny", "wisdom"), not the 5-pillar site
# taxonomy from the user's planning docs, so it's preserved in `tags` instead
# and this mapping supplies the actual `pillar` column.
DOMAIN_PILLAR_MAP = {
    "vocab": "linguistic_purity",
    "owe": "philosophy_cosmology",
    "njeomo": None,
    "aroko": "identity_genealogy",
    "ifa": "applied_ethics",
    "discourse": "philosophy_cosmology",
    "ethics": "applied_ethics",
    "orisa": "applied_ethics",
    "spirit": "applied_ethics",
    "interview": "identity_genealogy",
    "family": "identity_genealogy",
    "gov": "identity_genealogy",
    "oriki": "identity_genealogy",
}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_tags(seed_row, provenance_row) -> list:
    tags = set()
    raw_tags = seed_row.get("tags") or ""
    for t in raw_tags.split(","):
        t = t.strip()
        if t:
            tags.add(t)
    raw_pillar = seed_row.get("pillar") or ""
    if raw_pillar:
        tags.add(raw_pillar.strip())
    if seed_row.get("domain") == "discourse":
        raw_verify = seed_row.get("verify") or ""
        if raw_verify:
            tags.add(raw_verify.strip())
    return sorted(tags)


def main():
    seed = load_json(SEED_PATH)
    provenance = load_json(PROVENANCE_PATH) if PROVENANCE_PATH.exists() else {}

    entries_clean = []
    ifa_details = []
    fieldwork_rows = []
    review_rows = []

    for row in seed:
        legacy_id = row["id"]
        domain = row.get("domain")
        raw_type = row.get("type")
        raw_verify = row.get("verify") or ""
        prov = provenance.get(legacy_id, {})

        entry_type = normalize_type(raw_type)
        verify_status = normalize_verify(domain, raw_verify)
        has_citation = bool(row.get("src") or prov.get("source_citation"))
        content_origin = infer_content_origin(domain, raw_verify, has_citation)

        if domain != "discourse" and raw_verify not in VERIFY_EXACT_MAP:
            review_rows.append(
                {
                    "legacy_id": legacy_id,
                    "domain": domain,
                    "raw_verify": raw_verify,
                    "mapped_to": verify_status,
                }
            )

        source_citation = prov.get("source_citation") or row.get("src") or None

        entry = {
            "legacy_id": legacy_id,
            "domain": domain,
            "type": entry_type,
            "category": row.get("cat") or None,
            "pillar": DOMAIN_PILLAR_MAP.get(domain),
            "yoruba": row.get("yor") or None,
            "yoruba_alt": row.get("yot") or None,
            "english": row.get("eng") or None,
            "question": row.get("q") or None,
            "question_english": row.get("qEng") or None,
            "drop_text": row.get("drop") or None,
            "drop_english": row.get("dropEng") or None,
            "difficulty": row.get("diff") or None,
            "source_citation": source_citation,
            "tags": build_tags(row, prov),
            "verify_status": verify_status,
            "content_origin": content_origin,
        }
        entries_clean.append(entry)

        odu = row.get("odu") or None
        ebo = row.get("ebo") or None
        if odu or ebo:
            ifa_details.append({"legacy_id": legacy_id, "odu": odu, "ebo": ebo})

        informant = row.get("informant") or prov.get("informant")
        informant_role = row.get("informant_role") or prov.get("informant_role")
        consent_status = row.get("consent_status") or prov.get("consent_status")
        field_notes = row.get("field_notes") or prov.get("field_notes")
        yor_status = row.get("yor_status")
        cluster_id = row.get("cluster_id") or prov.get("cluster_id")
        if any([informant, informant_role, consent_status, field_notes, yor_status, cluster_id]):
            fieldwork_rows.append(
                {
                    "legacy_id": legacy_id,
                    "informant": informant,
                    "informant_role": informant_role,
                    "consent_status": consent_status,
                    "field_notes": field_notes,
                    "yor_status": yor_status,
                    "cluster_id": cluster_id,
                }
            )

    (ROOT / "data" / "entries_clean.json").write_text(
        json.dumps(entries_clean, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "data" / "entry_ifa_details.json").write_text(
        json.dumps(ifa_details, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "data" / "entry_fieldwork.json").write_text(
        json.dumps(fieldwork_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    review_path = ROOT / "data" / "verify_status_mapping_review.csv"
    with review_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["legacy_id", "domain", "raw_verify", "mapped_to"])
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"entries_clean.json: {len(entries_clean)} rows")
    print(f"entry_ifa_details.json: {len(ifa_details)} rows")
    print(f"entry_fieldwork.json: {len(fieldwork_rows)} rows")
    print(f"verify_status_mapping_review.csv: {len(review_rows)} rows needing a quick skim")


if __name__ == "__main__":
    main()
