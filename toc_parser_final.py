import re
import fitz  # PyMuPDF
import json
import argparse

def extract_toc(pdf_path):
    doc = fitz.open(pdf_path)
    lines = []
    for page in doc:
        lines.extend(page.get_text().splitlines())

    toc_entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        match = re.match(r"^([A-Z]{1,3})\.", line)
        if match:
            tab = match.group(1)
            i += 1
            title_lines = []
            while i < len(lines) and not re.search(r"\d+\s*[–—-]\s*\d+|\d+$", lines[i]):
                title_lines.append(lines[i].strip())
                i += 1
            if i < len(lines):
                page_info = lines[i].strip()
                page_range = re.findall(r"(\d+)\s*[–—-]?\s*(\d*)", page_info)
                if page_range:
                    start = int(page_range[0][0])
                    end = int(page_range[0][1]) if page_range[0][1] else start
                    title = " ".join(title_lines).strip()
                    toc_entries.append({
                        "tab": tab,
                        "title": title,
                        "startPage": start,
                        "endPage": end
                    })
        i += 1

    return toc_entries

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="TOC PDF")
    parser.add_argument("--output", default="toc_output.json")
    args = parser.parse_args()

    data = extract_toc(args.pdf_path)
    with open(args.output, "w") as f:
        json.dump(data, f, indent=2)
    print(f"✅ TOC parsed: {len(data)} entries saved to {args.output}")
