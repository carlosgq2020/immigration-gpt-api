import fitz  # PyMuPDF
import re
import json
import sys

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    toc_page = doc[3]  # TOC is on page 4 (0-indexed)
    for block in toc_page.get_text("blocks"):
        lines.extend(block[4].splitlines())

    lines = [line.strip() for line in lines if line.strip()]
    print("\n🔍 Structured TOC lines:\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    toc_entries = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for label (e.g., "A.")
        match = re.match(r"^([A-Z]{1,3})\.$", line)
        if match:
            tab = match.group(1)
            title_parts = []
            page_range = None

            # Collect title lines
            i += 1
            while i < len(lines) and not re.match(r"^\d+\s*[–—-]\s*\d+$", lines[i]) and not re.match(r"^\d+$", lines[i]):
                title_parts.append(lines[i])
                i += 1

            # Grab page range line
            if i < len(lines) and (re.match(r"^\d+\s*[–—-]\s*\d+$", lines[i]) or re.match(r"^\d+$", lines[i])):
                page_range = lines[i]
                i += 1
            else:
                i += 1
                continue

            # Parse page range
            if page_range:
                if "–" in page_range or "-" in page_range:
                    pages = re.split(r"\s*[–—-]\s*", page_range)
                    start_page = int(pages[0])
                    end_page = int(pages[1])
                else:
                    start_page = end_page = int(page_range)

                toc_entries.append({
                    "tab": tab,
                    "title": " ".join(title_parts),
                    "startPage": start_page,
                    "endPage": end_page
                })
        else:
            i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC PDF with labeled tabs")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()

    toc_data = extract_toc(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
