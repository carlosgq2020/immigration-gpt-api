import os
import json
import pytesseract
import fitz  # PyMuPDF
import re
from pdf2image import convert_from_path

# Helper to sanitize filenames like in segment_by_toc.py
def sanitize_filename(title: str, max_length=150) -> str:
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:max_length]

def extract_text_from_pdf(pdf_path):
    try:
        # Convert PDF to image per page (for scanned OCR)
        images = convert_from_path(pdf_path)
        text = ""
        for image in images:
            page_text = pytesseract.image_to_string(image)
            text += page_text + "\n\n"
        return text.strip()
    except Exception as e:
        print(f"❌ OCR failed for {pdf_path}: {e}")
        return ""

def main():
    toc_path = "toc_output.json"
    segments_dir = "output_segments"
    output_json = "segments_text.json"

    if not os.path.exists(toc_path):
        print("❌ toc_output.json not found")
        return

    with open(toc_path, "r", encoding="utf-8") as f:
        toc_entries = json.load(f)

    segment_filenames = os.listdir(segments_dir)
    results = {}

    for entry in toc_entries:
        tab = entry.get("tab")
        title = entry.get("title")

        if not tab or not title:
            continue

        # Normalize title exactly like segment_by_toc.py
title = title.replace("\n", " ").strip()
sanitized_title = sanitize_filename(title)
expected_filename = f"{tab}_{sanitized_title}.pdf"
segment_path = os.path.join(segments_dir, expected_filename)

# Try to match ignoring case and whitespace if filename not found
if not os.path.exists(segment_path):
    # Attempt fuzzy matching with available filenames
    matches = [f for f in segment_filenames if f.lower().startswith(f"{tab}_{sanitized_title[:40].lower()}")]
    if matches:
        segment_path = os.path.join(segments_dir, matches[0])
    else:
        print(f"⚠️ No match found for {tab} - {title}")
        continue

        print(f"🔍 Checking {segment_path}...")
        text = extract_text_from_pdf(segment_path)
        results[expected_filename] = text
        print(f"✅ Finished: {expected_filename[:-4]}")  # strip .pdf in log

    # Save results
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_json}")

if __name__ == "__main__":
    main()
