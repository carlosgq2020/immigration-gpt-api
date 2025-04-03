import re
import fitz  # PyMuPDF
import json

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    lines = doc.load_page(3).get_text("text").splitlines()  # TOC is on page 4 (index 3)

    print("🔍 Debugging Page 4 - Block Lines\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    toc_entries = []
    buffer = ""
    current_tab = None
    current_title = ""
    
    for line in lines:
        line = line.strip()

        # Match a new tab label like "A. Something something"
        tab_match = re.match(r"^([A-Z]{1,3})\.\s+(.*)", line)
        page_range_match = re.search(r"(\d+)\s*[–-]\s*(\d+)$", line)

        # Handle line like "A. Copy of birth certificate"
        if tab_match:
            current_tab = tab_match.group(1)
            current_title = tab_match.group(2)
            buffer = ""

        # Line with a page range (may be separate)
        elif page_range_match and current_tab:
            start = int(page_range_match.group(1))
            end = int(page_range_match.group(2))
            full_title = f"{current_title} {buffer}".strip()
            toc_entries.append({
                "tab": current_tab,
                "title": full_title,
                "startPage": start,
                "endPage": end
            })
            current_tab = None
            current_title = ""
            buffer = ""

        # Accumulate lines like:
        # "Copy of ID card with translation"
        elif current_tab:
            buffer += " " + line

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

    print(f"\n✅ TOC parsed: {len(toc_data)} items saved to {args.output}")
    
