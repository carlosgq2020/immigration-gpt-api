import argparse
import json
import os
import fitz  # PyMuPDF
import re

def sanitize_filename(title: str, max_length=150) -> str:
    # Replace unsafe characters with underscores
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:max_length]

def segment_pdf_by_toc(pdf_path, toc_path, output_dir):
    # Load TOC entries from JSON
    with open(toc_path, "r", encoding="utf-8") as f:
        toc_entries = json.load(f)

    # Open the full PDF document
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

        # PyMuPDF uses 0-based indexing
        subdoc = doc[start - 1:end]

        # Build a sanitized, safe filename
        filename = f"{entry['tab']}_{sanitize_filename(entry['title'])}.pdf"
        filepath = os.path.join(output_dir, filename)

        try:
    subdoc.save(filepath)
    print(f"✅ Saved {filename} ({entry['startPage']}–{entry['endPage']})")
except Exception as e:
    print(f"❌ Failed to save {filename}: {e}")

    return saved_entries


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Path to the full PDF file")
    parser.add_argument("toc_path", help="Path to the TOC JSON file")
    parser.add_argument("--output_dir", default="output_segments", help="Output directory")
    args = parser.parse_args()

    segment_pdf_by_toc(args.pdf_path, args.toc_path, args.output_dir)
