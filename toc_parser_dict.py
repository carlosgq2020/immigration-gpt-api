import fitz  # PyMuPDF
import json
import re

def extract_toc_from_dict(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(3)  # Page 4 (index 3)

    text_dict = page.get_text("dict")
    lines = []

    for block in text_dict["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(span["text"].strip() for span in line["spans"] if span["text"].strip())
            if text:
                lines.append(text)

    print("\n🔍 Structured TOC lines:\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    toc_entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        tab_match = re.match(r"^([A-Z]{1,3})(?:\.)?$", line)
        if tab_match:
            tab = tab_match.group(1)
            i += 1

            title_lines = []
            start_page = end_page = None

            # Collect all title lines
            while i < len(lines):
                candidate = lines[i].strip()

                # Match page range (like "1 – 3" or "151–153")
                range_match = re.match(r"^(\d+)\s*[–—-]\s*(\d+)$", candidate)
                single_match = re.match(r"^(\d+)$", candidate)

                if range_match:
                    start_page = int(range_match.group(1))
                    end_page = int(range_match.group(2))
                    i += 1
                    break
                elif single_match:
                    start_page = end_page = int(single_match.group(1))
                    i += 1
                    break
                else:
                    title_lines.append(candidate)
                    i += 1

            if start_page is not None:
                toc_entries.append({
                    "tab": tab,
                    "title": " ".join(title_lines),
                    "startPage": start_page,
                    "endPage": end_page
                })
        else:
            i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC from PDF with tab labels")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()

    toc_data = extract_toc_from_dict(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
