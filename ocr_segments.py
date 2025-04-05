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
def normalize_for_matching(text):
    text = text.lower()
    text = re.sub(r'https?://\S+', '', text)  # Remove URLs
    text = re.sub(r'“|”|‘|’', '', text)        # Normalize quotes
    text = re.sub(r'last accessed.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'[^a-z0-9\s]', '', text)    # Strip punctuation
    text = re.sub(r'\s+', ' ', text)           # Collapse spaces
    return text.strip()

for entry in toc:
    key = entry["key"]
    title = entry["title"]
    raw_title = f"{key} - {title}"
    cleaned_title = normalize_for_matching(raw_title)

    candidates = [normalize_for_matching(name) for name in pdf_segments.keys()]
    name_map = dict(zip(candidates, pdf_segments.keys()))

    matches = process.extract(
        cleaned_title,
        candidates,
        scorer=fuzz.token_set_ratio,
        limit=3
    )

    best_match, score, _ = matches[0]
    matched_filename = pdf_segments[name_map[best_match]]

    if score >= 85:
        print(f"✅ Match: {raw_title}\n   ↪ {matched_filename} (score: {score})")
    elif score >= 70:
        print(f"⚠️ Low-confidence match for: {raw_title}")
        print(f"   ↪ {matched_filename} (score: {score})")
    else:
        print(f"❌ No match for: {raw_title}")
        print("   Top guesses:")
        for m, s, _ in matches:
            print(f"     - {name_map[m]} (score: {s})")
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
