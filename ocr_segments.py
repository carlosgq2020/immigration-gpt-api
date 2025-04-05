import os
import json
import re
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from rapidfuzz import process, fuzz


def ocr_pdf(pdf_path):
    text = ''
    images = convert_from_path(pdf_path, dpi=300)
    for image in images:
        text += pytesseract.image_to_string(image)
    return text


def clean_string(s):
    s = s.replace("“", "").replace("”", "").replace("’", "").replace("‘", "")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r'https?://\S+', '', s)       # remove URLs
    s = re.sub(r'[^\w\s-]', '', s)           # remove special characters
    s = re.sub(r'\s+', '_', s.strip())       # replace spaces with underscores
    return s.lower()


def simplify_title(title, max_words=10):
    """Extract first N words of cleaned title."""
    title = re.sub(r'https?://\S+', '', title)
    title = re.sub(r'[^\w\s-]', '', title)
    title = title.replace("“", "").replace("”", "").replace("’", "").replace("‘", "")
    words = title.strip().split()
    return '_'.join(words[:max_words]).lower()


import re
import unicodedata

def normalize_title(title, tab, max_words=25):
    # Combine tab and title
    full_title = f"{tab} {title}"

    # Normalize to ASCII
    full_title = unicodedata.normalize("NFKD", full_title).encode("ascii", "ignore").decode("ascii").lower()

    # Remove URLs
    full_title = re.sub(r'https?://\S+', '', full_title)

    # Remove anything in quotes or parentheses
    full_title = re.sub(r'["“”‘’\'()]', '', full_title)

    # Strip common terms
    full_title = full_title.replace("available at", "").replace("last accessed", "")

    # Remove punctuation
    full_title = re.sub(r'[^\w\s]', '', full_title)

    # Collapse multiple spaces
    full_title = re.sub(r'\s+', ' ', full_title.strip())

    # Limit words
    words = full_title.split()[:max_words]
    return "_".join(words)

    for entry in toc:
    tab = entry.get("tab", "").strip()
    title = entry.get("title", "").strip()

    if not tab or not title:
        continue

    normalized_key = normalize_title(title, tab)

    # Prepare filenames for comparison (without .pdf)
    cleaned_filenames = [os.path.splitext(f)[0].lower() for f in segment_filenames]

    matches = process.extract(normalized_key, cleaned_filenames, scorer=fuzz.partial_ratio, limit=5)
print(f"\n🔎 No match for TOC entry: {tab} - {title}")
print(f"   Normalized key: {normalized_key}")
print("   Top guesses:")
for name, score, _ in matches:
    print(f"     → {name} (score: {score})")
    
    if score >= 55:
        matched_index = cleaned_filenames.index(best_match)
        matched_filename = segment_filenames[matched_index]
        filepath = os.path.join(segments_dir, matched_filename)
    else:
        print(f"⚠️ No match found for {tab} - {title[:70]}... (score: {score})")
        continue
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📝 Saved OCR results to: {output_path}")


if __name__ == "__main__":
    process_segments("toc_output.json", "output_segments")
