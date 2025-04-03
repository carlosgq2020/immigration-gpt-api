import re
import fitz  # PyMuPDF
import json

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc_lines = []

    for page_num, page in enumerate(doc, 1):
        blocks = page.get_text("blocks")
        for block in blocks:
            text = block[4].strip()
            if text:
                toc_lines.append(text)

    print("\n🔍 TOC Text Line-by-Line:\n" + "-"*40)
    for i, line in enumerate(toc_lines):
        print(f"{i+1:02}: {line}")
    print("-" * 40)

    # Placeholder regex (will refine after we see output)
    toc_entries = []
    toc_pattern = re.compile(r"([A-Z]{1,3})\.\s+(.*?)\s+(\d+)\s*[–—-]\s*(\d+)", re.DOTALL)

    for line in toc_lines:
        match = toc_pattern.search(line)
        if match:
            tab_label = match.group(1).strip()
            title = match.group(2).strip()
            start_page = int(match.group(3).strip())
            end_page = int(match.group(4).strip())

            toc_entries.append({
                "tab": tab_label,
                "title": title,
                "startPage": start_page,
                "endPage": end_page
            })

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
