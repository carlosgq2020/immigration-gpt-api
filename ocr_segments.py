import os
import json
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import tempfile
import re
from pdf2image import convert_from_path

# ⛑️ Helper to match TOC naming logic
def sanitize_filename(title: str, max_length=150) -> str:
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'\s+', '_', safe)
    return safe[:max_length]

# ⛑️ OCR one PDF file
def ocr_pdf(pdf_path):
    text = ''
    images = convert_from_path(pdf_path, dpi=300)
    for image in images:
        text += pytesseract.image_to_string(image)
    return text

# 🔁 Loop through TOC + segments and perform OCR
def process_segments(toc_path, segments_dir, output_path="segments_text.json"):
    with open(toc_path, "r", encoding="utf-8") as f:
        toc = json.load(f)

    results = {}
    segment_filenames = set(os.listdir(segments_dir))

    for entry in toc:
        tab = entry.get("tab")
        title = entry.get("title")

        if not tab or not title:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        # Build the expected filename
        sanitized_title = sanitize_filename(title.strip())
        expected_filename = f"{tab}_{sanitized_title}.pdf"
        segment_path = os.path.join(segments_dir, expected_filename)

        # Fallback: try partial matching
        if not os.path.exists(segment_path):
            matches = [f for f in segment_filenames if f.lower().startswith(f"{tab}_{sanitized_title[:40].lower()}")]
            if matches:
                segment_path = os.path.join(segments_dir, matches[0])
            else:
                print(f"⚠️ No match found for {tab} - {title}")
                continue

        print(f"🔍 Checking {segment_path}...")
        try:
            text = ocr_pdf(segment_path)
            results[expected_filename] = text
            print(f"✅ Finished: {expected_filename[:-4]}")
        except Exception as e:
            print(f"❌ Error processing {expected_filename}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
