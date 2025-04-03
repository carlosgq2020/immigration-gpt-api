import fitz
import json
import re

def extract_multiline_toc(pdf_path, page_num=3):
    doc = fitz.open(pdf_path)
    lines = doc[page_num].get_text("text").splitlines()

    exhibits = []
    current = {}

    page_range_pattern = re.compile(r"(\d+)\s*[–—-]\s*(\d+)$")
    single_page_pattern = re.compile(r"^\d+$")

    for line in lines:
        line = line.strip()

        if re.match(r"^[A-Z]{1,3}\.$", line):  # e.g. A., B., AA.
            if current:
                exhibits.append(current)
            current = {"tab": line, "title": "", "startPage": None, "endPage": None}

        elif page_range_pattern.search(line):
            match = page_range_pattern.search(line)
            current["startPage"] = int(match.group(1))
            current["endPage"] = int(match.group(2))
        
        elif single_page_pattern.match(line):
            current["startPage"] = int(line)
            current["endPage"] = int(line)

        elif current:
            current["title"] += (" " + line).strip()

    if current:
        exhibits.append(current)

    return exhibits


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parse TOC with labeled tabs and multiline titles")
    parser.add_argument("pdf_path", help="Path to the TOC PDF file")
    parser.add_argument("--output", default="toc_output.json", help="Path to save output JSON")

    args = parser.parse_args()
    toc = extract_multiline_toc(args.pdf_path)

    with open(args.output, "w") as f:
        json.dump(toc, f, indent=2)

    print(f"✅ TOC parsed: {len(toc)} exhibits saved to {args.output}")
