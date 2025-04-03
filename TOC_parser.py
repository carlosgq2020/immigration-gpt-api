import re
import fitz  # PyMuPDF
import json

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc_entries = []

    # Capture blocks of text instead of plain linear text
    all_text = []
    for page in doc:
        blocks = page.get_text("blocks")
        for block in sorted(blocks, key=lambda b: (b[1], b[0])):  # Sort by vertical position
            all_text.append(block[4].strip())

    # Combine lines into one string
    toc_text = "\n".join(all_text)

    print("🔍 TOC Text Preview:\n", toc_text[:2000])  # Print first 2,000 chars for debug

    # Adjusted pattern for table-like content with tab and page ranges
    toc_pattern = re.compile(r"([A-Z]{1,3})\.\s+(.*?)\s+(\d{1,3})\s*[-–—]\s*(\d{1,3})")

    for match in toc_pattern.finditer(toc_text):
        tab_label = match.group(1)
        title = match.group(2).strip()
        start_page = int(match.group(3))
        end_page = int(match.group(4))

        toc_entries.append({
            "tab": tab_label,
            "title": title,
            "startPage": start_page,
            "endPage": end_page
        })

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC from PDF (including table format)")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()
    toc_data = extract_toc(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"✅ TOC parsed: {len(toc_data)} items saved to {args.output}")
