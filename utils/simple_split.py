#!/usr/bin/env python3
"""
Bucket PDFs in ~/lawqb-work/parts into
~/lawqb-work/out/{case_facts|country_conditions}.
"""

from __future__ import annotations
import re, sys, shutil, pathlib
from typing import Final
from PyPDF2 import PdfReader

# -------- folders -----------------------------------------------------------
HOME   = pathlib.Path.home()
SRC    = HOME / "lawqb-work" / "parts"
DEST   = HOME / "lawqb-work" / "out"
CF     = DEST / "case_facts"
CC     = DEST / "country_conditions"
for p in (CF, CC):
    p.mkdir(parents=True, exist_ok=True)

# -------- patterns ----------------------------------------------------------
CASE_FACTS_PAT: Final = re.compile(
    r"""
        \bTAB\s+[A-H]\b
      | \b(affidavit|declaration|sworn|statement)\b
      | \b(photo(?:graph)?s?|picture)\b
      | \b(medical|clinic|hospital|diagnosis|lab(?:\s+result)?)\b
      | \b(school|transcript|grade[s]?|certificate)\b
      | \b(birth|marriage|death|passport|visa|ID(?:entification)?)\b
    """,
    re.I | re.X,
)

COUNTRY_COND_PAT = re.compile(
    r"""
      (?:human\s*rights|country\s*(?:report|profile|conditions?))
    | (?:U\.?S\.?\s*(?:Department|DOS|State\s+Dept|Gov(?:ernment)?))
    | UNHCR|OHCHR|IACHR|OAS|IOM
    | CRS\s+Report
    | UK\s+Home\s+Office
    | Amnesty(?:\s+International)?            # old clauses …
    | Human\s+Rights\s+Watch
    | Freedom\s+House
    | Crisis\s+Group
    | WOLA
    | Canadian\s+IRB
    | World\s+Bank
    | UN\s*(?:News|Chief)                    # ← NEW
    | BBC                                    # ← NEW
    | Al\s*Jazeera                           # ← NEW
    | Reuters                                # ← NEW
    | Associated\s*Press                     # ← NEW
    | The\s*Guardian                         # ← NEW
    """,
    re.I | re.X,
)

SCAN_PAGES = 12  # how many pages of each chunk we inspect


def score_page(txt: str) -> int:
    if CASE_FACTS_PAT.search(txt):
        return 1
    if COUNTRY_COND_PAT.search(txt):
        return -1
    return 0


def bucket(pdf: pathlib.Path) -> pathlib.Path:
    try:
        reader = PdfReader(str(pdf))
        votes = 0
        for i in range(min(SCAN_PAGES, len(reader.pages))):
            votes += score_page(reader.pages[i].extract_text() or "")
        if votes > 0:
            return CF
        if votes < 0:
            return CC
        too_big  = pdf.stat().st_size > 2_000_000
        too_long = len(reader.pages)  > 40
        return CC if (too_big or too_long) else CF
    except Exception as exc:
        print(f"!! cannot read {pdf}: {exc}", file=sys.stderr)
        return CF


def main() -> None:
    moved = {CF: 0, CC: 0}
    for pdf in sorted(SRC.glob("*.pdf")):
        dest = bucket(pdf)
        shutil.move(str(pdf), dest / pdf.name)
        moved[dest] += 1
        print(f"{pdf.name:<32} → "
              f"{'case_facts' if dest is CF else 'country_conditions'}")
    print(f"\nSummary: {moved[CF]} case-facts   |   {moved[CC]} country-conditions")


if __name__ == "__main__":
    main()
