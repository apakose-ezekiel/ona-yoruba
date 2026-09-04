"""
Extract the 1,159-entry seed dataset embedded in the disposable prototype
(yoruba-knowledge-engine (1).html) into data/seed_raw.json.

Source of truth for the path below: the prototype lives outside this repo,
in the user's working planning folder. Adjust SOURCE_HTML if it moves.
"""
import json
import re
import sys
from pathlib import Path

SOURCE_HTML = Path(r"C:\Users\apako\Documents\YORUBA REVIVAL\yoruba-knowledge-engine (1).html")
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "seed_raw.json"
EXPECTED_COUNT = 1159


def main():
    if not SOURCE_HTML.exists():
        sys.exit(f"Source file not found: {SOURCE_HTML}")

    content = SOURCE_HTML.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="yke-seed">(.*?)</script>',
        content,
        re.DOTALL,
    )
    if not match:
        sys.exit("Could not find the yke-seed <script> tag in the source HTML.")

    data = json.loads(match.group(1))

    if len(data) != EXPECTED_COUNT:
        print(
            f"WARNING: expected {EXPECTED_COUNT} entries, found {len(data)}. "
            "The prototype may have changed — proceeding anyway.",
            file=sys.stderr,
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Wrote {len(data)} entries to {OUT_PATH}")


if __name__ == "__main__":
    main()
