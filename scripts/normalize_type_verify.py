"""
Normalization rules for the two messiest fields in the seed dataset:
`type` (inconsistent casing/naming across import batches) and `verify`
(49 distinct freeform strings) -> the clean Postgres enums defined in
supabase/migrations/0001_schema.sql.

Also derives `content_origin`, which the seed data never states directly.
"""

TYPE_MAP = {
    "proverb": "proverb",
    "Proverb": "proverb",
    "vocabulary": "vocabulary",
    "Vocabulary": "vocabulary",
    "Did You Know": "knowledge_drop",
    "Discourse / Research Cluster": "knowledge_drop",
    "concept": "concept",
    "royal-title": "royal_title",
    "history": "history",
    "deity": "deity",
    "odu": "odu",
    "ese-ifa": "ese_ifa",
    "attributes": "attributes",
    "Spirituality/Ritual": "fieldwork_note",
    "Family/Community Finding": "fieldwork_note",
    "Governance Finding": "fieldwork_note",
    "Field Interview Record": "interview_excerpt",
    "Aroko Symbol": "symbolic_message",
    "Oriki": "oriki",
}

# Exact-match verify_status mapping, covering the high-volume and
# structurally-meaningful values (built from the actual 43-value distribution
# in data/seed_raw.json).
VERIFY_EXACT_MAP = {
    "sourced": "verified_single_source",
    "sourced-fieldwork-verified": "fieldwork_verified",
    "fieldwork-quiz-unverified": "fieldwork_partial",
    "fieldwork-vocab-list": "fieldwork_partial",
    "unverified-fieldwork": "fieldwork_partial",
    "fieldwork-vocab-unreviewed": "fieldwork_partial",
    "fieldwork-partial-verification": "fieldwork_partial",
    "fieldwork-unverified-single-source": "fieldwork_partial",
    "fieldwork-interview-consent:Yes": "fieldwork_partial",
    "fieldwork-interview-consent:Yes — anonymous only": "fieldwork_partial",
    "internal-contradiction-flagged": "disputed",
    "internal-contradiction-major": "disputed",
    "internal-term-conflict-flagged": "disputed",
    "named-tension-not-resolved-by-source": "disputed",
    "flagged-weak-derivation": "disputed",
    "tonal-ambiguity-flagged": "disputed",
    "arithmetic-verified-source-figures-unverified": "disputed",
    "incomplete-source": "unverified",
    "incomplete-unverified": "unverified",
    "reasonably-established": "verified_single_source",
    "reasonably-well-supported": "verified_single_source",
    "partially-established": "verified_single_source",
    "standard-usage": "verified_single_source",
    "well-supported-idiom": "verified_single_source",
    "explicit-source-position": "verified_single_source",
    "explicit-ethical-position-named-source": "verified_single_source",
    "consistent-across-sources": "verified_multi_source",
}


def normalize_type(raw_type: str) -> str:
    return TYPE_MAP.get(raw_type, "fieldwork_note")


def normalize_verify(domain: str, raw_verify: str) -> str:
    """
    The 'discourse' domain is, by the source spreadsheet's own description,
    single-source AI-cleaned research briefs -- every one of its ~30 distinct
    freeform verify labels collapses to the same status. Preserve the
    original nuance separately (tags / field_notes), not in verify_status.
    """
    if domain == "discourse":
        return "ai_generated_unverified"

    if raw_verify in VERIFY_EXACT_MAP:
        return VERIFY_EXACT_MAP[raw_verify]

    v = (raw_verify or "").lower()
    if "disput" in v or "contradiction" in v or "conflict" in v or "tension" in v:
        return "disputed"
    if "fieldwork" in v:
        return "fieldwork_partial"
    if "unverified" in v:
        return "unverified"
    return "unverified"


def infer_content_origin(domain: str, raw_verify: str, has_academic_citation: bool) -> str:
    if domain == "discourse":
        return "ai_research"
    v = (raw_verify or "").lower()
    if "fieldwork" in v:
        return "fieldwork_verified"
    if has_academic_citation:
        return "published_source"
    return "published_source"
