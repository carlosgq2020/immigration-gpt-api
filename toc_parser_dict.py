import fitz
import json
import re

def extract_toc_from_lines(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc.load_page(3)  # TOC is on page 4 (0-indexed)
    text_dict = page.get_text("dict")

    lines = []
    for block in text_dict["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(span["text"] for span in line["spans"]).strip()
            if text:
                text = text.replace("–", "-").replace("—", "-")
                lines.append(text)

    print("\n🔍 Structured TOC lines:\n")
    for i, line in enumerate(lines):
        print(f"[{i}] {line}")

    toc_entries = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Match tab label like A. or AA. or Z.
        tab_match = re.match(r"^([A-Z]{1,3})(?:\.)?$", line)
        if tab_match:
            tab = tab_match.group(1)
            i += 1

            # Collect title lines until we find page range
            title_parts = []
            while i < len(lines):
                current_line = lines[i].strip()
                range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", current_line)
                single_page_match = re.match(r"^(\d+)$", current_line)

                if range_match:
                    start_page = int(range_match.group(1))
                    end_page = int(range_match.group(2))
                    i += 1
                    break
                elif single_page_match:
                    start_page = end_page = int(single_page_match.group(1))
                    i += 1
                    break
                else:
                    title_parts.append(current_line)
                    i += 1

            title = " ".join(title_parts)
            toc_entries.append({
                "tab": tab,
                "title": title,
                "startPage": start_page,
                "endPage": end_page
            })
        else:
            i += 1

    return toc_entries

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC from PDF lines")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()
    toc_data = extract_toc_from_lines(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
