import re, sys, shutil, pathlib
from PyPDF2 import PdfReader

# source folder with the 30‑page chunks
SRC  = pathlib.Path.home() / "lawqb-work" / "parts"
# destination buckets
DEST = pathlib.Path.home() / "lawqb-work" / "out"
CC   = DEST / "country_conditions"
CF   = DEST / "case_facts"
for p in (CC, CF):
    p.mkdir(parents=True, exist_ok=True)

# very naïve trigger words → treat as country‑conditions
trigger = re.compile(r"(state department|human rights|country report)", re.I)

def bucket(pdf):
    """Return CC or CF depending on first 2 pages’ text."""
    try:
        reader = PdfReader(str(pdf))
        text   = "".join(
            (reader.pages[i].extract_text() or "")
            for i in range(min(2, len(reader.pages)))
        )
        return CC if trigger.search(text) else CF
    except Exception as e:
        print("!! cannot read", pdf.name, e, file=sys.stderr)
        return CF   # play safe, keep with case facts

for pdf in SRC.glob("*.pdf"):
    target_dir = bucket(pdf)
    shutil.copy2(pdf, target_dir / pdf.name)
    print(f"{pdf.name:35} →  {target_dir.name}")

