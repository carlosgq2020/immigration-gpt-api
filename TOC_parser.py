import fitz  # PyMuPDF
import json
import re

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[3]  # TOC is on page 4
    lines = page.get_text("text").splitlines()

    toc_entries = []
    current_tab = None
    current_title = ""
    collecting = False

    page_range_pattern = re.compile(r"(\d+)\s*[–—-]\s*(\d+)$")  # Matches: 12 – 13 or 12-13

    for i, line in enumerate(lines):
        line = line.strip()

        # Start collecting when we pass the TABLE OF CONTENTS marker
        if "TABLE OF CONTENTS" in line:
            collecting = True
            continue
        if not collecting:
            continue

        # Line like: "A." or "AA."
        if re.match(r"^[A-Z]{1,3}\.$", line):
            current_tab = line.rstrip(".")
            current_title = ""
            continue

        # Try to extract a page range from the current line
        match = page_range_pattern.search(line)
        if match:
            start_page = int(match.group(1))
            end_page = int(match.group(2))
            title = current_title.strip() if current_title else line[:match.start()].strip()

            toc_entries.append({
                "tab": current_tab,
                "title": title,
                "startPage": start_page,
                "endPage": end_page
            })
            current_tab = None
            current_title = ""
        else:
            current_title += " " + line if current_title else line

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

    print(f"✅ TOC parsed: {len(toc_data)} items saved to {args.output}")
