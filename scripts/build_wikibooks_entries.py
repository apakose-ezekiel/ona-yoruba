"""
Build entries from the 4 small Yoruba grammar Wikibooks PDFs (Numbers, Verbs,
Adjectives, Food and Fruits) -- all CC-BY-SA licensed, freely reusable with
attribution. Text was already extracted and read directly; hardcoded here
since the source is small and stable.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITATION = "Wikibooks contributors, Yoruba/{page} (CC BY-SA), en.wikibooks.org"

entries = []


from collections import defaultdict

_counters = defaultdict(int)


def add(category, yoruba, english, pillar="linguistic_purity", page="Numbers"):
    _counters[page] += 1
    entries.append(
        {
            "legacy_id": f"WIKI-{page.upper().replace(' ', '')}-{_counters[page]:04d}",
            "domain": "vocab",
            "type": "vocabulary",
            "category": category,
            "pillar": pillar,
            "yoruba": yoruba,
            "yoruba_alt": None,
            "english": english,
            "question": None,
            "question_english": None,
            "drop_text": None,
            "drop_english": None,
            "difficulty": "easy",
            "source_citation": CITATION.format(page=page),
            "tags": ["wikibooks", "cc-by-sa", category.lower().replace(" ", "-")],
            "verify_status": "verified_single_source",
            "content_origin": "published_source",
        }
    )


NUMBERS = [
    ("1", "Oókan"), ("2", "Eéjì"), ("3", "Ẹẹ́ta"), ("4", "Ẹẹ́rin"), ("5", "Aárùn-ún"),
    ("6", "Ẹẹ́fà"), ("7", "Eéje"), ("8", "Ẹẹ́jọ"), ("9", "Ẹẹ́sàán"), ("10", "Ẹẹ́wàá"),
    ("11", "Ọọ́kànlá"), ("12", "Eéjìlá"), ("13", "Ẹẹ́tàlá"), ("14", "Ẹ́rìnlá"),
    ("15", "Márùndínlógún/Mẹ́ẹ̀ẹ́dógún"), ("16", "Ẹ́rìndínlógún"), ("17", "Ẹ́tàdínlógún"),
    ("18", "Éjìdínlógún"), ("19", "Ọ́kàndínlógún"), ("20", "Ogún"),
    ("21", "Ọ́kànlélógún"), ("22", "Méjìlélógún"), ("23", "Mẹ́tàlélógún"),
    ("24", "Mẹ́rìnlélógún"), ("25", "Márùndínlọ́gbọ̀n"), ("26", "Mẹ́rìndínlọ́gbọ̀n"),
    ("27", "Mẹ́tàdínlọ́gbọ̀n"), ("28", "Méjìdínlọ́gbọ̀n"), ("29", "Ọ̀kándínlọ́gbọ̀n"),
    ("30", "Ọgbọ̀n"), ("40", "Ogójì"), ("50", "Àádọ́ta"),
    ("60", "Ọgọ́ta"), ("70", "Àádọ́rin"), ("80", "Ọgọ́rin"), ("90", "Àádọ́rùn-ún"),
    ("100", "Ọgọ́rùn-ún"), ("101", "Ọ́kàn lé lọ́gọ́rùn-ún"), ("102", "Méjì lé lọ́gọ́rùn-ún"),
    ("103", "Mẹ́tà lé lọ́gọ́rùn-ún"), ("104", "Mẹ́rìn lé lọ́gọ́rùn-ún"),
    ("105", "Márùn dín láàádọ́fà"), ("110", "Àádọ́fà"), ("120", "Ọgọ́fà"),
    ("130", "Àádọ́je"), ("140", "Ọgọ́je"), ("150", "Àádọ́jọ"), ("160", "Ọgọ́jọ"),
    ("170", "Àádọ́sàn-án"), ("180", "Ọgọ́sàn-án"), ("190", "Àádọ́wàá"),
    ("200", "Igba"), ("300", "Ọ̀ọ́dúnrún"), ("400", "Irinwó"),
    ("500", "Ẹ̀ẹ́dẹ́gbẹ̀ta"), ("600", "Ẹgbẹ̀ta"), ("700", "Ẹ̀ẹ́dẹ́gbẹ̀rin"),
    ("800", "Ẹgbẹ̀rin"), ("900", "Ẹ̀ẹ́dẹ́gbẹ̀rún"), ("1,000", "Ẹgbẹ̀rún"),
    ("2,000", "Ẹgbẹ̀wá/Ẹgbàá"), ("2,500", "Ẹ̀ẹ́dẹ́gbẹ̀tàlá"), ("3,000", "Ẹgbẹ̀ẹ̀ẹ́dógún"),
    ("4,000", "Ẹgbààjì"), ("5,000", "Ẹ̀ẹ́dẹ́gbàta"), ("6,000", "Ẹgbàáta"),
    ("7,000", "Ẹ̀ẹ́dẹ́gbàrin"), ("8,000", "Ẹgbàárin"), ("9,000", "Ẹ̀ẹ́dẹ́gbàrún"),
    ("10,000", "Ẹgbààrún"), ("20,000", "Ọ̀kẹ́"), ("50,000", "Ọ̀kẹ́ méjì àti ààbọ̀"),
    ("100,000", "Ọ̀kẹ́ márùn-ún"), ("1,000,000", "Àádọ́ta ọ̀kẹ́ / egberun egberun / egbelegbe"),
    ("10,000,000", "egbelegbe mewaa"), ("100,000,000", "egbelegbe ogorun"),
    ("1,000,000,000", "egbelegbéji"), ("10,000,000,000", "egbelegbéta"),
    ("100,000,000,000", "egbelegbérin"), ("1,000,000,000,000", "egbelegbarun"),
    ("10,000,000,000,000", "egbelegbéfà"), ("100,000,000,000,000", "egbelegbèje"),
    ("1,000,000,000,000,000", "egbelegbéjo"),
]
for num, yor in NUMBERS:
    add("numbers", yor, num, page="Numbers")

VERBS = [
    ("Jẹ", "to eat"), ("Mu", "to drink"), ("Pè", "to call / to pronounce"),
    ("Rìn", "to walk"), ("Sùn", "to sleep"), ("Gbà", "to accept / to allow"),
    ("Dàpọ̀", "to mix / to be added"), ("Gbà", "to admit"),
    ("Fún ni ìmọ̀ràn", "to advise"), ("Farada mọ́", "to agree"),
    ("Sọ̀rọ̀", "to speak"), ("Kọ̀wé", "to write"), ("Wa mọ́tò", "to drive"),
]
for yor, eng in VERBS:
    add("verbs", yor, eng, page="Verbs")

ADJECTIVES = [
    ("Dúdú", "black"), ("Aláwọ̀ ẹ̀jẹ̀", "red"), ("Aláwọ̀ ewé", "green"),
    ("Gíga", "tall"), ("Gùn", "long"), ("Jin", "deep"),
    ("Aláwọ̀ efun", "white"), ("Ńlá", "big"), ("Tínrín", "narrow"),
    ("Kékeré", "small"), ("Nípọn", "thick"), ("Gbòrò", "wide"),
    ("Tọ́ọ́rọ́", "straight"), ("Iyọ̀ jà", "salty"), ("Ọ̀lẹ", "difficult"),
    ("Ìrọ̀rùn", "easy"), ("Dùn", "sweet"),
]
for yor, eng in ADJECTIVES:
    add("adjectives", yor, eng, page="Adjectives")

FOOD = [
    ("Ọsàn òrombó", "orange"), ("Ìbẹ́pẹ", "paw-paw"), ("Ọ̀gẹ̀dẹ̀", "banana"),
    ("Ọsàn wẹ́wẹ́", "lime"), ("Àgbàdo", "corn"), ("Àgbálùmọ́", "cherry"),
    ("Ẹ̀wà", "beans"), ("Ìrẹsì", "rice"), ("Búrẹ́dì", "bread"),
    ("Àsáró", "pottage"), ("Àkàrà", "beans cake"), ("Ìkàn", "garden egg"),
    ("Ẹ̀gẹ́", "cassava"), ("Mọ́í-mọ́í", "bean pudding"), ("Ògì", "pap"),
    ("Iṣu", "yam"), ("Iyán", "pounded yam"), ("Rèké", "sugarcane"),
    ("Àgbọn", "coconut"), ("Ọ̀pẹ òyìnbó", "pineapple"), ("Máńgòrò", "mango"),
    ("Ànàmọ́", "potato"), ("Iṣu Kóókò", "cocoyam / taro"),
]
for yor, eng in FOOD:
    add("food", yor, eng, pillar="natural_science", page="Food and Fruits")

OUT = ROOT / "data" / "entries_wikibooks.json"
OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Wrote {len(entries)} entries to {OUT}")
