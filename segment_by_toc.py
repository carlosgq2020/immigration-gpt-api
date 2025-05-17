import argparse
import json
import os
import fitz  # PyMuPDF
import re
from typing import List

from toc_parser import extract_toc_lines, parse_toc

def sanitize_filename(title: str, max_length=150) -> str:
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:max_length]

def segment_pdf_by_toc(pdf_path: str, toc_path: str | None, output_dir: str, page_index: int = 3) -> List[str]:
    """Parse the TOC if needed and segment the PDF."""
    if toc_path and os.path.exists(toc_path):
        with open(toc_path, "r", encoding="utf-8") as f:
            toc_entries = json.load(f)
    else:
        lines = extract_toc_lines(pdf_path, page_index)
        toc_entries = parse_toc(lines)
        if toc_path:
            with open(toc_path, "w", encoding="utf-8") as f:
                json.dump(toc_entries, f, indent=2)

    doc = fitz.open(pdf_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    saved_entries = []

    for entry in toc_entries:
        start = entry.get("startPage")
        end = entry.get("endPage")
        title = entry.get("title")
        tab = entry.get("tab")

        if start is None or end is None or title is None or tab is None:
            continue

        filename = f"{tab}_{sanitize_filename(title)}.pdf"
        filepath = os.path.join(output_dir, filename)

        try:
            subdoc = fitz.open()
            subdoc.insert_pdf(doc, from_page=start - 1, to_page=end - 1)
            subdoc.save(filepath)
            print(f"✅ Saved {filename} ({start}–{end})")
            saved_entries.append(filepath)
        except Exception as e:
            print(f"❌ Failed to save {filename}: {e}")

    return saved_entries

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to the full PDF file")
    parser.add_argument("--toc_path", help="Optional path to TOC JSON")
    parser.add_argument("--output_dir", default="output_segments", help="Output directory")
    parser.add_argument("--page_index", type=int, default=3, help="0-based page index of TOC")
    args = parser.parse_args()

    segment_pdf_by_toc(args.pdf_path, args.toc_path, args.output_dir, args.page_index)

