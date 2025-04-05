import os
import re
import json
import pytesseract
import fitz  # PyMuPDF
from pdf2image import convert_from_path
from PIL import Image

def title = title.replace('\n', ' ').strip()
    sanitize_filename(title: str, max_length=150) -> str:
    safe = re.sub(r'[^\w\s-]', '', title)
    safe = re.sub(r'[\s]+', '_', safe)
    return safe[:max_length]

def perform_ocr_on_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text_output = ""
    for img in images:
        text_output += pytesseract.image_to_string(img)
    return text_output

def main():
    toc_path = "toc_output.json"
    pdf_folder = "output_segments"
    output_path = "segments_text.json"

    with open(toc_path, "r", encoding="utf-8") as f:
        toc_entries = json.load(f)

    ocr_results = {}

    filenames = os.listdir(pdf_folder)
    filenames_set = set(filenames)

    for entry in toc_entries:
        tab = entry.get("tab")
        title = entry.get("title")
        if not tab or not title:
            print(f"⚠️ Missing tab or title in entry: {entry}")
            continue

        expected_filename = f"{tab}_{sanitize_filename(title)}.pdf"
        match = next((f for f in filenames if f == expected_filename), None)

        if not match:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        full_path = os.path.join(pdf_folder, match)
        print(f"🔍 Checking {full_path}...")
        try:
            text = perform_ocr_on_pdf(full_path)
            ocr_results[match] = text
            print(f"✅ Finished: {match[:-4]}")
        except Exception as e:
            print(f"❌ Failed OCR on {match}: {e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ocr_results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")

if __name__ == "__main__":
    main()
