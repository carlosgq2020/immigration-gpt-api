import os
import json
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
from difflib import get_close_matches

# OCR function
def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    text = ""
    for i, img in enumerate(images):
        page_text = pytesseract.image_to_string(img, lang='eng+spa')
        text += f"\n\n--- Page {i+1} ---\n\n" + page_text
    return text.strip()

# Sanitize filenames for comparison
def sanitize_filename(text):
    return ''.join(c if c.isalnum() else '_' for c in text).lower()

# Fuzzy match: find the closest filename for a given TOC entry
def find_best_match_filename(title, tab, segment_dir):
    target = sanitize_filename(f"{tab}_{title}")
    all_files = os.listdir(segment_dir)
    pdfs = [f for f in all_files if f.lower().endswith(".pdf")]
    candidates = [f[:-4] for f in pdfs]  # remove .pdf
    match = get_close_matches(target, candidates, n=1, cutoff=0.4)
    if match:
        return os.path.join(segment_dir, match[0] + ".pdf")
    return None

def run_ocr_on_segments(toc_path, segment_dir, output_json="segments_text.json"):
    with open(toc_path, "r", encoding="utf-8") as f:
        toc_entries = json.load(f)

    results = {}

    for entry in toc_entries:
        tab = entry.get("tab")
        title = entry.get("title")

        if not tab or not title:
            print(f"⚠️ No match found for {tab} - {title}")
            continue

        filepath = find_best_match_filename(title, tab, segment_dir)

        if filepath:
            print(f"🔍 Checking {os.path.basename(filepath)}...")
            try:
                text = extract_text_from_pdf(filepath)
                results[f"{tab}_{title}"] = text
                print(f"✅ Finished: {os.path.basename(filepath)[:-4]}")
            except Exception as e:
                print(f"❌ Error reading {filepath}: {e}")
        else:
            print(f"⚠️ No match found for {tab} - {title}")

    # Save all extracted text
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_json}")

if __name__ == "__main__":
    run_ocr_on_segments("toc_output.json", "output_segments")
