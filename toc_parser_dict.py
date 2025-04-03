import fitz  # PyMuPDF
import json
import re

def extract_toc_from_dict(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(3)  # Page 4 of the PDF
    text_dict = page.get_text("dict")

    all_lines = []
    for block in text_dict["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(span["text"].strip() for span in line["spans"] if span["text"].strip())
            if text:
                all_lines.append(text)

    print("🔍 Structured TOC lines:\n")
    for i, line in enumerate(all_lines):
        print(f"[{i}] {line}")

    toc_entries = []
    i = 0
    while i < len(all_lines):
        line = all_lines[i].strip()
        tab_match = re.match(r"^([A-Z]{1,3})(?:\.)?$", line)

        if tab_match:
            tab = tab_match.group(1)
            i += 1
            title_lines = []
            page_range = None

            while i < len(all_lines):
                next_line = all_lines[i].strip()
                page_match = re.search(r"(\d+)\s*[–—-]\s*(\d+)", next_line)

                if page_match:
                    start_page = int(page_match.group(1))
                    end_page = int(page_match.group(2))
                    page_range = (start_page, end_page)
                    break
                else:
                    title_lines.append(next_line)
                i += 1

            if page_range:
                toc_entries.append({
                    "tab": tab,
                    "title": " ".join(title_lines).strip(),
                    "startPage": page_range[0],
                    "endPage": page_range[1]
                })

        i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC with tab labels from structured PDF")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Output JSON file")

    args = parser.parse_args()
    toc_data = extract_toc_from_dict(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
