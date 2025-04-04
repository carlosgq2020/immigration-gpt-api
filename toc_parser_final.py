import re
import fitz  # PyMuPDF
import json
import argparse

def extract_toc_lines(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[3]  # TOC is on page 4 (index 3)
    lines = page.get_text("text").splitlines()
    cleaned = [line.strip() for line in lines if line.strip()]
    print("🔍 Structured TOC lines:\n")
    for i, line in enumerate(cleaned):
        print(f"[{i}] {line}")
    return cleaned

def parse_toc(lines):
    toc_entries = []
    current = {}
    i = 0

    tab_pattern = re.compile(r"^([A-Z]{1,3})\.?$")
    page_pattern = re.compile(r"^(\d+)\s*[–—-]?\s*(\d+)?$")

    while i < len(lines):
        line = lines[i]
        tab_match = tab_pattern.match(line)

        if tab_match:
            if current:
                toc_entries.append(current)
                current = {}

            current["tab"] = tab_match.group(1)
            i += 1

            # Title (could span one or two lines)
            title_parts = []
            while i < len(lines) and not page_pattern.match(lines[i]) and not tab_pattern.match(lines[i]):
                title_parts.append(lines[i])
                i += 1
            current["title"] = " ".join(title_parts).strip()

            # Page range
            if i < len(lines) and page_pattern.match(lines[i]):
                page_match = page_pattern.match(lines[i])
                current["startPage"] = int(page_match.group(1))
                current["endPage"] = int(page_match.group(2)) if page_match.group(2) else int(page_match.group(1))
                i += 1
        else:
            i += 1

    if current:
        toc_entries.append(current)

    return toc_entries

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse TOC PDF with labeled tabs")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")
    args = parser.parse_args()

    lines = extract_toc_lines(args.pdf_path)
    toc_data = parse_toc(lines)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
