import fitz
import json
import os
import argparse
import re

def safe_filename(tab, title, max_length=100):
    # Slugify-like cleanup
    clean = re.sub(r"[^\w\s-]", "", title)           # Remove special chars
    clean = re.sub(r"[\s_-]+", "_", clean).strip("_")  # Normalize spacing
    base = f"{tab}_{clean}"
    return base[:max_length] + ".pdf"  # Truncate if too long
    
def sanitize_filename(text):
    return "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in text).strip().replace(" ", "_")

def segment_pdf_by_toc(input_pdf, toc_json_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    with open(toc_json_path, "r") as f:
        toc = json.load(f)

    doc = fitz.open(input_pdf)
    segments = []

    for entry in toc:
        if "startPage" not in entry or "endPage" not in entry:
            continue

        start = entry["startPage"] - 1
        end = entry["endPage"]
        subdoc = fitz.open()
        for page_num in range(start, end):
            subdoc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        filename = safe_filename(entry["tab"], entry["title"])
        filepath = os.path.join(output_dir, filename)
        subdoc.save(filepath)
        segments.append({
            "tab": entry["tab"],
            "title": entry["title"],
            "file": filename,
            "startPage": entry["startPage"],
            "endPage": entry["endPage"]
        })
        print(f"✅ Saved {filename} ({entry['startPage']}–{entry['endPage']})")

    return segments

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="Full document PDF")
    parser.add_argument("toc_path", help="Path to toc_output.json")
    parser.add_argument("--output_dir", default="exhibits")

    args = parser.parse_args()
    entries = segment_pdf_by_toc(args.pdf_path, args.toc_path, args.output_dir)

    with open("segmented_index.json", "w") as f:
        json.dump(entries, f, indent=2)

    print(f"\n🎉 Done! {len(entries)} exhibits saved to '{args.output_dir}'")
  
