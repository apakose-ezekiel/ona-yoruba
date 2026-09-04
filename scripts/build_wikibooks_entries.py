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


def add(category, yoruba, english, pillar="linguistic_purity", page="Numbers"):
    entries.append(
        {
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
    ("15", "Márùndínlógún"), ("16", "Ẹ́rìndínlógún"), ("17", "Ẹ́tàdínlógún"),
    ("18", "Éjìdínlógún"), ("19", "Ọ́kàndínlógún"), ("20", "Ogún"),
    ("21", "Ọ́kànlélógún"), ("30", "Ọgbọ̀n"), ("40", "Ogójì"), ("50", "Àádọ́ta"),
    ("60", "Ọgọ́ta"), ("70", "Àádọ́rin"), ("80", "Ọgọ́rin"), ("90", "Àádọ́rùn-ún"),
    ("100", "Ọgọ́rùn-ún"), ("200", "Igba"), ("300", "Ọ̀ọ́dúnrún"), ("400", "Irinwó"),
    ("500", "Ẹ̀ẹ́dẹ́gbẹ̀ta"), ("1,000", "Ẹgbẹ̀rún"), ("2,000", "Ẹgbàá"),
    ("10,000", "Ẹgbààrún"), ("20,000", "Ọ̀kẹ́"), ("100,000", "Ọ̀kẹ́ márùn-ún"),
    ("1,000,000", "Àádọ́ta ọ̀kẹ́"),
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
