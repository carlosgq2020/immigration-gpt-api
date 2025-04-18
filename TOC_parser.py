import fitz  # PyMuPDF
import json
import re

def extract_toc_blocks(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(3)  # TOC is on page 4
    blocks = page.get_text("blocks")  # returns list of (x0, y0, x1, y1, text, block_no, block_type)

    # Sort by Y position (top to bottom), then X (left to right)
    sorted_blocks = sorted(blocks, key=lambda b: (round(b[1]), b[0]))

    lines = []
    for b in sorted_blocks:
        lines.append(b[4].strip())

    print("🔍 Block-based TOC lines:\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    # Match "A." line + page range line
    toc_entries = []
    i = 0
    while i < len(lines):
        line = lines[i]
        tab_match = re.match(r"^([A-Z]{1,3})\.\s+(.*)", line)
        if tab_match:
            tab = tab_match.group(1)
            title = tab_match.group(2)
            # Check if next line is a page range
            if i + 1 < len(lines):
                page_line = lines[i + 1]
                page_match = re.search(r"(\d+)\s*[–—-]\s*(\d+)", page_line)
                if page_match:
                    start = int(page_match.group(1))
                    end = int(page_match.group(2))
                    toc_entries.append({
                        "tab": tab,
                        "title": title,
                        "startPage": start,
                        "endPage": end
                    })
                    i += 1  # skip the page range line
        i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC PDF using block layout")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()
    toc_data = extract_toc_blocks(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
