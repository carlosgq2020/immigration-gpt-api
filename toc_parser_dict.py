import fitz  # PyMuPDF
import json
import re

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    
    # Extract text line by line from page 4 (TOC is on page 4)
    toc_page = doc[3]  # 0-based index, so 3 = Page 4
    blocks = toc_page.get_text("blocks")
    for block in sorted(blocks, key=lambda b: b[1]):  # sort by vertical position
        block_lines = block[4].split('\n')
        for line in block_lines:
            lines.append(line.strip())

    print("\n🔍 Structured TOC lines:\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    # TOC parsing logic
    toc_entries = []
    current = {}

    tab_pattern = re.compile(r"^[A-Z]{1,3}\.?$")
    page_pattern = re.compile(r"^\d+\s*[–—-]\s*\d+$|^\d+$")

    i = 0
    while i < len(lines):
        line = lines[i]

        # Detect tab (e.g., A., B., CC.)
        if tab_pattern.match(line):
            current = {"tab": line.strip("."), "title": "", "startPage": None, "endPage": None}
            i += 1
            # Title might span 1 or 2 lines
            title = lines[i]
            if not page_pattern.match(lines[i + 1]):
                title += " " + lines[i + 1]
                i += 1
            current["title"] = title.strip()

            i += 1
            # Now get page numbers
            page_line = lines[i]
            page_match = re.match(r"(\d+)\s*[–—-]\s*(\d+)", page_line)
            if page_match:
                current["startPage"] = int(page_match.group(1))
                current["endPage"] = int(page_match.group(2))
            elif page_line.isdigit():
                current["startPage"] = current["endPage"] = int(page_line)
            else:
                print(f"⚠️ Page not matched: {page_line}")
            toc_entries.append(current)
        i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC PDF with multi-line entries")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()

    toc_data = extract_toc(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
