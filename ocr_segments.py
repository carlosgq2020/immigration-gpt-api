import os
import json
import re
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract
from rapidfuzz import process, fuzz

# Path setup
TOC_FILE = "toc_output.json"
SEGMENTS_DIR = "output_segments"
OUTPUT_JSON = "segments_text.json"

# Load TOC
with open(TOC_FILE, "r") as f:
    toc = json.load(f)

# Get available segment filenames (stem only)
pdf_segments = {
    Path(f).stem: f for f in os.listdir(SEGMENTS_DIR) if f.endswith(".pdf")
}

# Normalize helper
def normalize(text):
    return re.sub(r"[^\w\s]", "", text).strip().lower()

# Store OCR results
results = {}

# Try matching each TOC entry to a segment file
for entry in toc:
    key = entry["key"]
    title = entry["title"]
    raw = f"{key} - {title}"
    normalized_key = normalize(raw)

    matches = process.extract(
        normalized_key,
        pdf_segments.keys(),
        scorer=fuzz.partial_ratio,
        limit=3
    )

    if not matches:
        print(f"❌ No match candidates for: {raw}")
        continue

    best_match, score, _ = matches[0]

    if score >= 85:
        matched_filename = pdf_segments[best_match]
        print(f"✅ Match: {raw}\n   ↪ {matched_filename} (score: {score})")

    elif score >= 70:
        matched_filename = pdf_segments[best_match]
        print(f"⚠️ Low-confidence match for: {raw}")
        print(f"   ↪ {matched_filename} (score: {score})")

    else:
        print(f"❌ No match for: {raw}")
        print("   Top guesses:")
        for name, s, _ in matches:
            print(f"     - {name} (score: {s})")
        continue

    # OCR the PDF
    pdf_path = os.path.join(SEGMENTS_DIR, matched_filename)
    print(f"🔍 OCRing {matched_filename}...")
    try:
        images = convert_from_path(pdf_path)
        text = "\n".join(pytesseract.image_to_string(img) for img in images)
        results[raw] = text
        print(f"✅ Finished: {matched_filename}")
    except Exception as e:
        print(f"❌ OCR failed for {matched_filename}: {e}")

# Save results
with open(OUTPUT_JSON, "w") as f:
    json.dump(results, f, indent=2)

print(f"\n📝 Saved OCR results to: {OUTPUT_JSON}")
