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


from rapidfuzz import process, fuzz
import unicodedata

def normalize_title(title, tab, max_words=20):
    full_title = f"{tab} {title}"

    # Normalize: lowercase, ASCII only
    title = unicodedata.normalize("NFKD", full_title).encode("ascii", "ignore").decode("ascii").lower()

    # Remove URLs, punctuation, extra spaces
    title = re.sub(r'https?://\S+', '', title)
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title.strip())

    # Limit to max_words
    words = title.split()[:max_words]
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
    print(f"\n🔍 Trying to match: {normalized_key}")
for match in matches:
    print(f"  → {match[0]} (score: {match[1]})")

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
