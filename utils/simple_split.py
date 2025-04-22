
import re, sys, shutil, pathlib
from PyPDF2 import PdfReader

SRC  = pathlib.Path.home() / "lawqb-work" / "parts"
DEST = pathlib.Path.home() / "lawqb-work" / "out"
CC   = DEST / "country_conditions"
CF   = DEST / "case_facts"

for p in (CC, CF):
    p.mkdir(parents=True, exist_ok=True)

trigger = re.compile(
    r"""(
        (?:human\s*rights|country\s*(?:report|profile|conditions?))
      | (?:U\.?S\.?\s*(?:Department|DOS|State\s+Dept))
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
    )""",
    re.I | re.X,
)

def bucket(pdf: pathlib.Path) -> pathlib.Path:
    """Return CC or CF depending on the first two pages’ text."""
    try:
        reader = PdfReader(str(pdf))
        sample = "".join(
            (reader.pages[i].extract_text() or "")
            for i in range(min(2, len(reader.pages)))
        )
        return CC if trigger.search(sample) else CF
    except Exception as exc:
        print(f"!! cannot read {pdf}: {exc}", file=sys.stderr)
        return CF

def main() -> None:
    moved = {CC: 0, CF: 0}
    for pdf in sorted(SRC.glob("*.pdf")):
        dest_dir = bucket(pdf)
        shutil.move(str(pdf), dest_dir / pdf.name)
        moved[dest_dir] += 1
        print(f"{pdf.name:<34} → "
              f"{'country_conditions' if dest_dir is CC else 'case_facts'}")

    print(f"\nSummary: {moved[CF]} case‑facts   |   {moved[CC]} country‑conditions")

if __name__ == "__main__":
    main()
