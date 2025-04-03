import fitz
import json
import re

def extract_toc_from_dict(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(3)  # Page 4 = TOC
    toc_entries = []

    text_dict = page.get_text("dict")

    # Flatten all lines into sequence of strings
    all_lines = []
    for block in text_dict["blocks"]:
        for line in block.get("lines", []):
            line_text = " ".join([span["text"].strip() for span in line["spans"] if span["text"].strip()])
            if line_text:
                all_lines.append(line_text)

    print("🔍 Structured TOC lines:\n")
    for i, line in enumerate(all_lines):
        print(f"[{i}] {line}")

    # Try parsing TOC from reconstructed lines
    i = 0
    while i < len(all_lines):
        line = all_lines[i]
        match = re.match(r"^([A-Z]{1,3})\.\s+(.*)", line)
        if match:
            tab = match.group(1)
            title = match.group(2)

            # Look ahead for a line that has a page range
            if i + 1 < len(all_lines):
                next_line = all_lines[i + 1]
                page_match = re.search(r"(\d+)\s*[–—-]\s*(\d+)", next_line)
                if page_match:
                    start = int(page_match.group(1))
                    end = int(page_match.group(2))
                    toc_entries.append({
                        "tab": tab,
                        "title": title,
                        "startPage": start,
                        "endPage": end
                    })
                    i += 1  # skip page line
        i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract TOC from structured PDF layout")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()
    toc_data = extract_toc_from_dict(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
