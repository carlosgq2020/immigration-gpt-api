import os
import json
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

def is_scanned(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        if page.get_text().strip():
            return False
    return True

def ocr_pdf(pdf_path):
    images = convert_from_path(pdf_path, dpi=300)
    full_text = ""
    for img in images:
        text = pytesseract.image_to_string(img)
        full_text += text + "\n"
    return full_text.strip()

def extract_ocr_for_segments(segment_dir, toc_path, output_json):
    with open(toc_path, "r", encoding="utf-8") as f:
        toc_entries = json.load(f)

    output_data = []
    for entry in toc_entries:
        tab = entry.get("tab")
        title = entry.get("title")
        safe_title = title.replace("’", "").replace("'", "").replace(" ", "_")
        filename_prefix = f"{tab}_{safe_title}"
        matches = [f for f in os.listdir(segment_dir) if f.startswith(filename_prefix[:40])]  # allow truncated matches

        if not matches:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        filepath = os.path.join(segment_dir, matches[0])
        print(f"🔍 Checking {filepath}...")

        if is_scanned(filepath):
            print(f"🧾 Running OCR on: {filepath}")
            text = ocr_pdf(filepath)
        else:
            doc = fitz.open(filepath)
            text = "\n".join([page.get_text() for page in doc])

        output_data.append({
            "tab": tab,
            "title": title,
            "text": text.strip()
        })
        print(f"✅ Finished: {filename_prefix}")

    with open(output_json, "w", encoding="utf-8") as out:
        json.dump(output_data, out, indent=2, ensure_ascii=False)
    print(f"\n📝 Saved OCR results to: {output_json}")

if __name__ == "__main__":
    extract_ocr_for_segments(
        segment_dir="output_segments",
        toc_path="toc_output.json",
        output_json="segments_text.json"
    )
