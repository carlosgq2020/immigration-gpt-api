import re
import fitz  # PyMuPDF
import json

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc_text = ""
    
    # Extract all text from page 4 where the TOC actually is
    page = doc.load_page(3)  # Page 4 is index 3
    lines = page.get_text("text").splitlines()

    print("🔍 Debugging Page 4 - Line Output\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    toc_entries = []
    
    current_tab = None
    current_title = ""
    for line in lines:
        match = re.match(r"^([A-Z]{1,3})\.\s+(.*)", line)
        page_range = re.search(r"(\d+)\s*[–-]\s*(\d+)$", line.strip())

        # Line starts with a tab label like "A."
        if match:
            current_tab = match.group(1).strip()
            current_title = match.group(2).strip()

        # Line ends with something like "1 – 3"
        elif page_range and current_tab:
            start_page = int(page_range.group(1))
            end_page = int(page_range.group(2))
            toc_entries.append({
                "tab": current_tab,
                "title": current_title,
                "startPage": start_page,
                "endPage": end_page
            })
            current_tab = None
            current_title = ""

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
