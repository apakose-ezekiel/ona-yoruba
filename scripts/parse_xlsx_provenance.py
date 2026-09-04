"""
Pull fieldwork provenance (informant, consent, academic citation, verify status)
out of the author's master tracking spreadsheet and key it by the same `id`
values used in the seed dataset (e.g. "PRV-001", "VOC-001", "SPI-001").

Note on the xlsx's own "ENGINE IMPORT LOG" sheet: its "Engine ID" column is
NOT the seed JSON's `id` field (which is "YKE0001"-style for most domains) —
it's actually just each source sheet's own native ID (PRV-001, VOC-001, ...).
Conveniently, several seed domains (vocab, njeomo's siblings, oriki, gov,
family, spirit, interview, discourse, and a fraction of owe/aroko) already
carry that same native ID as their own `id` field — confirmed by spot-checking
VOCABULARY (173/173 match positionally and by ID). So provenance is pulled
straight from each source sheet, keyed by its own ID column, with no need to
go through ENGINE IMPORT LOG as an intermediate.

Sheets with a genuine per-row ID column usable this way: PROVERBS & ORAL,
VOCABULARY, SPIRITUALITY, DISCOURSE CLUSTERS, INTERVIEWS, GOVERNANCE,
FAMILY & COMMUNITY. NJE O MO and AROKO have no per-row ID column in the
source spreadsheet (sparse example-row layout) — no xlsx enrichment is
possible for those two; their entries fall back to the seed's own `verify`
field during normalization.
"""
import json
import sys
from pathlib import Path

import pandas as pd

XLSX_PATH = Path(r"C:\Users\apako\Documents\YORUBA REVIVAL\yoruba_master_database_v1.xlsx")
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "provenance_map.json"


def clean(v):
    if pd.isna(v):
        return None
    v = str(v).strip()
    return v or None


def load_proverbs_oral(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="PROVERBS & ORAL", header=3)
    for _, row in df.iterrows():
        rid = clean(row.get("ID"))
        if not rid:
            continue
        provenance[rid] = {
            "informant": clean(row.get("Informant Name\n/ Alias")),
            "informant_role": clean(row.get("Informant Role\n/ Title")),
            "consent_status": clean(row.get("Consent Given?")),
            "source_citation": clean(row.get("Academic Source\n(author + page)")),
            "verify_raw": clean(row.get("Verified?")),
            "field_notes": clean(row.get("Notes / Flag")),
            "sources_confirming": clean(row.get("No. of Sources\nConfirming")),
        }


def load_vocabulary(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="VOCABULARY", header=1)
    for _, row in df.iterrows():
        rid = clean(row.get("ID"))
        if not rid:
            continue
        provenance[rid] = {
            "source_citation": clean(row.get("Source Page")),
            "field_notes": clean(row.get("Notes")),
            "quiz_usable": clean(row.get("Quiz-Usable?")),
        }


def load_spirituality(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="SPIRITUALITY", header=3)
    for _, row in df.iterrows():
        rid = clean(row.get("ID"))
        if not rid:
            continue
        provenance[rid] = {
            "informant": clean(row.get("Oral Source — Name / Role")),
            "source_citation": clean(row.get("Scholarly Source\n(author + page)")),
            "verify_raw": clean(row.get("Verified?")),
            "field_notes": clean(row.get("Notes")),
        }


def load_discourse_clusters(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="DISCOURSE CLUSTERS", header=3)
    for _, row in df.iterrows():
        rid = clean(row.get("Engine ID"))
        if not rid:
            continue
        provenance[rid] = {
            "cluster_id": clean(row.get("Cluster")),
            "verify_raw": clean(row.get("Verify Status")),
            "field_notes": clean(row.get("Field Notes / Flags")),
            "source_citation": clean(row.get("Source MD File")),
        }


def load_interviews(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="INTERVIEWS", header=3)
    for _, row in df.iterrows():
        rid = clean(row.get("ID"))
        if not rid:
            continue
        provenance[rid] = {
            "informant": clean(row.get("Informant Name\n/ Alias")),
            "informant_role": clean(row.get("Role / Title")),
            "consent_status": clean(row.get("Consent Given?")),
            "verify_raw": clean(row.get("Reliability Rating")),
            "field_notes": clean(row.get("Notes")),
        }


def load_governance(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="GOVERNANCE", header=3)
    for _, row in df.iterrows():
        rid = clean(row.get("ID"))
        if not rid:
            continue
        provenance[rid] = {
            "informant": clean(row.get("Oral Source — Name / Role")),
            "source_citation": clean(row.get("Scholarly Source\n(author + page)")),
            "verify_raw": clean(row.get("Verified?")),
            "field_notes": clean(row.get("Notes / Flag")),
        }


def load_family_community(provenance: dict) -> None:
    df = pd.read_excel(XLSX_PATH, sheet_name="FAMILY & COMMUNITY", header=3)
    for _, row in df.iterrows():
        rid = clean(row.get("ID"))
        if not rid:
            continue
        provenance[rid] = {
            "informant": clean(row.get("Oral Source — Name / Role")),
            "source_citation": clean(row.get("Scholarly Source\n(author + page)")),
            "verify_raw": clean(row.get("Verified?")),
            "field_notes": clean(row.get("Notes")),
        }


def main():
    if not XLSX_PATH.exists():
        sys.exit(f"xlsx not found: {XLSX_PATH}")

    provenance: dict = {}
    loaders = [
        load_proverbs_oral,
        load_vocabulary,
        load_spirituality,
        load_discourse_clusters,
        load_interviews,
        load_governance,
        load_family_community,
    ]
    for loader in loaders:
        before = len(provenance)
        loader(provenance)
        print(f"{loader.__name__}: +{len(provenance) - before} rows")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote provenance for {len(provenance)} legacy IDs to {OUT_PATH}")


if __name__ == "__main__":
    main()
