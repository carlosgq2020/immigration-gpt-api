#!/usr/bin/env python3
"""
Split the 30-page chunks in ~/lawqb-work/parts into
~/lawqb-work/out/{case_facts|country_conditions}.

✔  case-facts triggers checked first
✔  country-conditions triggers second
✔  fallback: big or long ⇒ country-conditions
"""

import re, sys, shutil, pathlib
from PyPDF2 import PdfReader

SRC  = pathlib.Path.home() / "lawqb-work" / "parts"
DEST = pathlib.Path.home() / "lawqb-work" / "out"
CF   = DEST / "case_facts"
CC   = DEST / "country_conditions"
for p in (CF, CC):
    p.mkdir(parents=True, exist_ok=True)

# ---------- keyword patterns -----------------------------------------------
CASE_FACTS_PAT = re.compile(
    r"""
    \btab\s+[A-H]\b                              # Tab A-H coversheets
  | \b(affidavit|declaration|sworn|statement)\b
  | \bphotos?(?:graphs?)?|picture\b
  | \b(medical|clinic|hospital|diagnosis|lab\s+result)\b
  | \b(school|transcript|grades|certificate)\b
  | \b(birth|marriage|death|id(?:entification)?|passport|visa)\b
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
  | Amnesty(?:\s+International)?
  | Human\s+Rights\s+Watch
  | Freedom\s+House
  | Crisis\s+Group
  | WOLA
  | Canadian\s+IRB
  | World\s+Bank
    """,
    re.I | re.X,
)

# ---------- classify --------------------------------------------------------
def classify_text(text: str, *, size_bytes: int = 0, num_pages: int = 0) -> str:
    """Return 'case facts' or 'country conditions' for *text*."""
    if CASE_FACTS_PAT.search(text):
        return "case facts"
    if COUNTRY_COND_PAT.search(text):
        return "country conditions"

    too_big = size_bytes > 2_000_000
    too_long = num_pages > 40 or len(text) > 20_000
    return "country conditions" if (too_big or too_long) else "case facts"

# ---------- helper ----------------------------------------------------------
def bucket(pdf: pathlib.Path) -> pathlib.Path:
    """Return CF or CC for *pdf*."""
    try:
        reader = PdfReader(str(pdf))
        sample = "".join(
            (reader.pages[i].extract_text() or "") for i in range(min(3, len(reader.pages)))
        )
        category = classify_text(sample, size_bytes=pdf.stat().st_size, num_pages=len(reader.pages))
        return CF if category == "case facts" else CC

    except Exception as exc:
        print(f"!! cannot read {pdf}: {exc}", file=sys.stderr)
        return CF

# ---------- main ------------------------------------------------------------
def main() -> None:
    moved = {CF: 0, CC: 0}
    for pdf in sorted(SRC.glob("*.pdf")):
        dest = bucket(pdf)
        shutil.move(str(pdf), dest / pdf.name)
        moved[dest] += 1
        print(f"{pdf.name:<30} → {'case_facts' if dest is CF else 'country_conditions'}")

    print(f"\nSummary: {moved[CF]} case-facts   |   {moved[CC]} country-conditions")

if __name__ == "__main__":
    main()
