import fitz  # PyMuPDF
import json
import re

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []

    toc_page = doc[3]  # TOC is on page 4 (0-indexed)
    blocks = toc_page.get_text("blocks")
    for block in sorted(blocks, key=lambda b: b[1]):  # sort top-down
        block_lines = block[4].split('\n')
        for line in block_lines:
            lines.append(line.strip())

    print("\n🔍 Structured TOC lines:\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    toc_entries = []
    current = None
    tab_pattern = re.compile(r"^[A-Z]{1,3}\.?$")
    page_pattern = re.compile(r"^(\d+)\s*[–—-]\s*(\d+)$|^(\d+)$")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect new tab section
        if tab_pattern.match(line):
            if current:
                toc_entries.append(current)

            current = {"tab": line.strip("."), "title": "", "startPage": None, "endPage": None}
            i += 1
            title_lines = []

            # Capture title (until we hit a page number)
            while i < len(lines) and not page_pattern.match(lines[i]):
                title_lines.append(lines[i].strip())
                i += 1

            current["title"] = " ".join(title_lines).strip()

            # Capture page range
            if i < len(lines):
                page_line = lines[i].strip()
                match = page_pattern.match(page_line)
                if match:
                    if match.group(1) and match.group(2):
                        current["startPage"] = int(match.group(1))
                        current["endPage"] = int(match.group(2))
                    elif match.group(3):
                        current["startPage"] = current["endPage"] = int(match.group(3))
        else:
            i += 1

    # Append last item if valid
    if current and current.get("startPage"):
        toc_entries.append(current)

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC from multi-line structured exhibit PDF")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save output JSON")

    args = parser.parse_args()

    toc_data = extract_toc(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
