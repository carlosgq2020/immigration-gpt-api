import fitz  # PyMuPDF
import json
import re

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[3]  # TOC is on Page 4 (zero-based)
    blocks = page.get_text("blocks")

    lines = [block[4].strip() for block in blocks if block[4].strip()]
    
    toc_entries = []
    i = 0

    while i < len(lines):
        line = lines[i]
        
        # Match something like "A.", "BB.", etc.
        match = re.match(r"^([A-Z]{1,3})\.\s*(.*)", line)
        if match:
            tab = match.group(1)
            title = match.group(2).strip()

            # If the title got split across lines (no page numbers yet)
            j = i + 1
            while j < len(lines) and not re.search(r"\d+\s*[–—-]\s*\d+", lines[j]):
                title += " " + lines[j]
                j += 1

            # Now j should be the line with page numbers like "12 – 17"
            if j < len(lines):
                page_range_match = re.search(r"(\d+)\s*[–—-]\s*(\d+)", lines[j])
                if page_range_match:
                    start_page = int(page_range_match.group(1))
                    end_page = int(page_range_match.group(2))

                    toc_entries.append({
                        "tab": tab,
                        "title": title,
                        "startPage": start_page,
                        "endPage": end_page
                    })
                    i = j + 1
                    continue
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

    print(f"✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
