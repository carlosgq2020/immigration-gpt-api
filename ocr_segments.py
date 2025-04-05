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
    # Lowercase
    text = text.lower()
    # Remove URLs
    text = re.sub(r'https?://\S+', '', text)
    # Remove smart quotes, line breaks, punctuation (except dashes and underscores)
    text = text.replace('“', '').replace('”', '').replace('‘', '').replace('’', '')
    text = text.replace('–', '-').replace('—', '-')  # normalize em/en dash
    text = re.sub(r'[^a-z0-9\s\-_]', '', text)
    text = re.sub(r'last accessed.*$', '', text, flags=re.IGNORECASE)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

for entry in toc:
    key = entry["key"]
    title = entry["title"]
    raw_title = f"{key} - {title}"
    cleaned_title = normalize_for_matching(raw_title)

    # Map: normalized -> original filename
    normalized_to_filename = {
        normalize_for_matching(name): name for name in pdf_segments.keys()
    }

    # Fuzzy match
    match_results = process.extract(
        cleaned_title,
        normalized_to_filename.keys(),
        scorer=fuzz.token_sort_ratio,
        limit=3
    )

    best_match, score, _ = match_results[0]
    matched_filename = normalized_to_filename[best_match]

    if score >= 85:
        print(f"✅ Match: {raw_title}")
        print(f"   ↪ {matched_filename} (score: {score})")
    else:
        print(f"⚠️ No strong match for: {raw_title}")
        print(f"   Best guess: {matched_filename} (score: {score})")
        print("   Top guesses:")
        for guess, guess_score, _ in match_results:
            print(f"     - {normalized_to_filename[guess]} (score: {guess_score})")
        continue

    # Fallback: try matching on just the key (like 'H', 'M', etc.)
fallback_filename = next(
    (f for f in pdf_segments if f.startswith(f"{key}_")),
    None
    )

    if fallback_filename:
        print(f"🟡 Fallback match using key '{key}': {fallback_filename}")
    else:
        print(f"⚠️ Still no match for: {raw_title}")

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
