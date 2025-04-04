import re
import fitz  # PyMuPDF
import json
import argparse

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    toc_lines = []
    for i, page in enumerate(doc):
        if i == 3:  # Page 4 is where the TOC starts
            lines = page.get_text("text").splitlines()
            toc_lines = [line.strip() for line in lines if line.strip()]
            break

    print("🔍 Structured TOC lines:\n")
    for idx, line in enumerate(toc_lines):
        print(f"[{idx}] {line}")

    toc_entries = []
    i = 0
    while i < len(toc_lines):
        line = toc_lines[i]

        # Match tab marker like "A.", "B.", ..., "ZZZ."
        if re.match(r"^[A-Z]{1,3}\.$", line.strip()):
            tab = line.strip().strip(".")

            # Collect title lines
            title_lines = []
            i += 1
            while i < len(toc_lines) and not re.match(r"^\d+\s*[–—-]?\s*\d*$", toc_lines[i]):
                title_lines.append(toc_lines[i])
                i += 1

            # Get page numbers
            if i < len(toc_lines):
                page_line = toc_lines[i].strip()
                page_match = re.match(r"^(\d+)\s*[–—-]?\s*(\d+)?$", page_line)
                if page_match:
                    start_page = int(page_match.group(1))
                    end_page = int(page_match.group(2)) if page_match.group(2) else start_page
                    title = " ".join(title_lines)
                    toc_entries.append({
                        "tab": tab,
                        "title": title,
                        "startPage": start_page,
                        "endPage": end_page
                    })
                i += 1
        else:
            i += 1

    return toc_entries

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse TOC PDF with labeled tabs")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save JSON")

    args = parser.parse_args()

    toc_data = extract_toc(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc_data, f, indent=2)

    print(f"\n✅ TOC parsed: {len(toc_data)} entries saved to {args.output}")
