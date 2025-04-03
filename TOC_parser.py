import re
import fitz  # PyMuPDF
import json

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc_text = ""

    for i, page in enumerate(doc):
        text = page.get_text()
        print(f"\n📄 Page {i + 1} Text:\n{text}")  # DEBUG: Print each page's text
        toc_text += text

    # This pattern matches: A. Title text here 1 – 3
    toc_pattern = re.compile(r"([A-Z]{1,3})\.\s+(.*?)\s+(\d+)\s*[–—-]\s*(\d+)", re.DOTALL)

    toc_entries = []

    for match in toc_pattern.finditer(toc_text):
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

    print(f"✅ TOC parsed: {len(toc_data)} items saved to {args.output}")
